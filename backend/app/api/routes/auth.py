"""Authentication routes — register, login, me.

Users are stored in Redis as HSET users:all {email} {json}.
This is suitable for single-org newsroom deployments.
For multi-tenant SaaS, migrate to PostgreSQL User table.
"""
import json
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional

from ...core.redis_client import redis_client
from ...core.security import verify_password, get_password_hash, create_access_token, decode_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

USERS_KEY = "users:all"
VALID_ROLES = {"admin", "editor", "reporter", "viewer"}
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


class UpdateUserRequest(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None
    full_name: Optional[str] = None


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


def require_role(*roles: str):
    """Role-based access control — raises 403 if user's role not in allowed set."""
    async def _check(user: dict = Depends(require_user)) -> dict:
        if user.get("role") not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"ต้องการสิทธิ์: {', '.join(roles)}",
            )
        return user
    return Depends(_check)


@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest):
    """Register a new newsroom user."""
    existing = await redis_client.hget(USERS_KEY, request.email)
    if existing:
        raise HTTPException(status_code=400, detail="อีเมลนี้ถูกใช้งานแล้ว")

    role = request.role if request.role in VALID_ROLES else "reporter"
    # First user ever registered becomes admin automatically
    if await redis_client.hlen(USERS_KEY) == 0:
        role = "admin"

    user = {
        "email": request.email,
        "hashed_password": get_password_hash(request.password),
        "full_name": request.full_name,
        "role": role,
        "is_active": True,
        "organization_id": "org-default",
    }
    await redis_client.hset(USERS_KEY, request.email, json.dumps(user))

    token = create_access_token({"sub": request.email, "name": request.full_name, "role": role})
    user_out = {k: v for k, v in user.items() if k != "hashed_password"}
    return {"access_token": token, "token_type": "bearer", "user": user_out}


@router.post("/login", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends()):
    """Log in with email + password, returns JWT access token."""
    raw = await redis_client.hget(USERS_KEY, form.username)
    if not raw:
        raise HTTPException(status_code=401, detail="อีเมลหรือรหัสผ่านไม่ถูกต้อง")

    user = json.loads(raw)
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="บัญชีถูกระงับการใช้งาน")
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


@router.get("/users")
async def list_users(admin: dict = require_role("admin")):
    """[Admin] List all registered users."""
    all_raw = await redis_client.hgetall(USERS_KEY)
    users = []
    for raw in all_raw.values():
        u = json.loads(raw)
        u.pop("hashed_password", None)
        users.append(u)
    users.sort(key=lambda u: u.get("email", ""))
    return {"users": users, "total": len(users)}


@router.patch("/users/{email}")
async def update_user(
    email: str,
    req: UpdateUserRequest,
    admin: dict = require_role("admin"),
):
    """[Admin] Update user role, active status, or display name."""
    raw = await redis_client.hget(USERS_KEY, email)
    if not raw:
        raise HTTPException(status_code=404, detail="ไม่พบผู้ใช้งาน")
    user = json.loads(raw)

    if req.role is not None:
        if req.role not in VALID_ROLES:
            raise HTTPException(status_code=400, detail=f"Role ต้องเป็น: {', '.join(VALID_ROLES)}")
        user["role"] = req.role
    if req.is_active is not None:
        user["is_active"] = req.is_active
    if req.full_name is not None:
        user["full_name"] = req.full_name.strip()

    await redis_client.hset(USERS_KEY, email, json.dumps(user))
    user.pop("hashed_password", None)
    return user


@router.delete("/users/{email}")
async def delete_user(email: str, admin: dict = require_role("admin")):
    """[Admin] Remove a user account."""
    if email == admin.get("email"):
        raise HTTPException(status_code=400, detail="ไม่สามารถลบบัญชีตัวเองได้")
    deleted = await redis_client.hdel(USERS_KEY, email)
    if not deleted:
        raise HTTPException(status_code=404, detail="ไม่พบผู้ใช้งาน")
    return {"deleted": email}
