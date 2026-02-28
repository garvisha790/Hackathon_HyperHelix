import uuid
from typing import Annotated
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt, JWTError
import httpx

from app.database import get_db
from app.config import get_settings
from app.models.user import User

settings = get_settings()
security = HTTPBearer()

_jwks_cache: dict | None = None


async def _get_cognito_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is None:
        url = (
            f"https://cognito-idp.{settings.cognito_region}.amazonaws.com/"
            f"{settings.cognito_user_pool_id}/.well-known/jwks.json"
        )
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            _jwks_cache = resp.json()
    return _jwks_cache


def _decode_token(token: str) -> dict:
    """Decode and validate JWT. In dev mode, accept a simple JSON payload for testing."""
    if settings.app_env == "development" and token.startswith("dev:"):
        parts = token.split(":", 2)
        if len(parts) == 3:
            return {"sub": parts[1], "email": parts[2]}

    try:
        unverified_header = jwt.get_unverified_header(token)
        payload = jwt.decode(
            token,
            key="",
            algorithms=["RS256"],
            audience=settings.cognito_app_client_id,
            options={"verify_signature": False} if settings.app_env == "development" else {},
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = _decode_token(credentials.credentials)
    cognito_sub = payload.get("sub")
    if not cognito_sub:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    result = await db.execute(
        select(User).where(User.cognito_sub == cognito_sub, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


async def get_tenant_id(user: User = Depends(get_current_user)) -> uuid.UUID:
    return user.tenant_id


def require_role(*roles: str):
    """Dependency factory that enforces RBAC."""
    async def _check(user: User = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' not permitted. Required: {roles}",
            )
        return user
    return _check


CurrentUser = Annotated[User, Depends(get_current_user)]
TenantId = Annotated[uuid.UUID, Depends(get_tenant_id)]
DB = Annotated[AsyncSession, Depends(get_db)]
