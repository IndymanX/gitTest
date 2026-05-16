"""Authentication routes — register, login, me.

Users are stored in Redis as HSET users:all {email} {json}.
This is suitable for single-org newsroom deployments.
For multi-tenant SaaS, migrate to PostgreSQL User table.
"""
import json
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional

from ...core.redis_client import redis_client
from ...core.security import verify_password, get_password_hash, create_access_token, decode_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

USERS_KEY = "users:all"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    role: str = "reporter"  # admin / editor / reporter / viewer


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[dict]:
    """Soft dependency — returns None if no token (routes handle themselves)."""
    if not token:
        return None
    payload = decode_access_token(token)
    email = payload.get("sub")
    if not email:
        return None
    raw = await redis_client.hget(USERS_KEY, email)
    if not raw:
        return None
    user = json.loads(raw)
    user.pop("hashed_password", None)
    return user


async def require_user(token: Optional[str] = Depends(oauth2_scheme)) -> dict:
    """Hard dependency — raises 401 if no valid token."""
    user = await get_current_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="กรุณาเข้าสู่ระบบ",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest):
    """Register a new newsroom user."""
    existing = await redis_client.hget(USERS_KEY, request.email)
    if existing:
        raise HTTPException(status_code=400, detail="อีเมลนี้ถูกใช้งานแล้ว")

    user = {
        "email": request.email,
        "hashed_password": get_password_hash(request.password),
        "full_name": request.full_name,
        "role": request.role,
        "is_active": True,
        "organization_id": "org-default",
    }
    await redis_client.hset(USERS_KEY, request.email, json.dumps(user))

    token = create_access_token({"sub": request.email, "name": request.full_name, "role": request.role})
    user_out = {k: v for k, v in user.items() if k != "hashed_password"}
    return {"access_token": token, "token_type": "bearer", "user": user_out}


@router.post("/login", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends()):
    """Log in with email + password, returns JWT access token."""
    raw = await redis_client.hget(USERS_KEY, form.username)
    if not raw:
        raise HTTPException(status_code=401, detail="อีเมลหรือรหัสผ่านไม่ถูกต้อง")

    user = json.loads(raw)
    if not verify_password(form.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="อีเมลหรือรหัสผ่านไม่ถูกต้อง")

    token = create_access_token({"sub": user["email"], "name": user["full_name"], "role": user["role"]})
    user_out = {k: v for k, v in user.items() if k != "hashed_password"}
    return {"access_token": token, "token_type": "bearer", "user": user_out}


@router.get("/me")
async def me(current_user: dict = Depends(require_user)):
    """Return current authenticated user info."""
    return current_user


@router.get("/check")
async def check_setup():
    """Return whether any users are registered yet (for first-run onboarding)."""
    count = await redis_client.hlen(USERS_KEY)
    return {"has_users": count > 0, "user_count": count}
