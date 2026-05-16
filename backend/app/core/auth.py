"""Lightweight API key authentication for AInewsroom.

If API_KEY is empty in config, all requests pass (dev mode).
Set API_KEY in .env to enable header-based authentication.
"""
from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader

from ..config import settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(api_key: str | None = Security(_api_key_header)) -> None:
    if not settings.API_KEY:
        return  # dev mode — open access
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing X-API-Key header",
        )
