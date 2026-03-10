import uuid
from typing import Annotated
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
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
            f"https://cognito-idp.{settings.cognito_effective_region}.amazonaws.com/"
            f"{settings.cognito_user_pool_id}/.well-known/jwks.json"
        )
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            _jwks_cache = resp.json()
    return _jwks_cache


async def _decode_token(token: str) -> dict:
    """Decode and cryptographically validate JWT against AWS Cognito JWKS."""
    # Allow dev-mode bypass only if configured and token is fake
    if settings.app_env == "development" and token.startswith("dev:"):
        parts = token.split(":", 2)
        if len(parts) == 3:
            return {"sub": parts[1], "email": parts[2]}

    try:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        if not kid:
            raise HTTPException(status_code=401, detail="Invalid token: missing kid")

        jwks = await _get_cognito_jwks()
        rsa_key = {}
        for key in jwks.get("keys", []):
            if key["kid"] == kid:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
                break
        
        if not rsa_key:
            raise HTTPException(status_code=401, detail="Invalid token: kid not found in JWKS")

        payload = jwt.decode(
            token,
            key=rsa_key,
            algorithms=["RS256"],
            # Cognito Access Tokens don't have an audience, only ID tokens do.
            # So we check client_id explicitly instead.
            options={"verify_aud": False},
        )
        
        if payload.get("client_id") != settings.cognito_app_client_id:
            raise HTTPException(status_code=401, detail="Invalid token: wrong client_id")
            
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token signature: {e}",
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        print(f"[AUTH] Decoding token...")
        payload = await _decode_token(credentials.credentials)
        cognito_sub = payload.get("sub")
        print(f"[AUTH] Token decoded, cognito_sub: {cognito_sub}")
        
        # If the sub property contains the dev prefix, do a simple lookup
        if cognito_sub and cognito_sub.startswith("dev:"):
             pass # handled by DB lookup below
             
        print(f"[AUTH] Looking up user with cognito_sub: {cognito_sub}")
        result = await db.execute(
            select(User).options(selectinload(User.tenant)).where(User.cognito_sub == cognito_sub)
        )
        user = result.scalar_one_or_none()
        if not user:
            print(f"[AUTH] User not found for cognito_sub: {cognito_sub}")
            raise HTTPException(status_code=404, detail="User not found")
        # Try accessing the tenant here to trigger lazy load if it wasn't eager loaded
        _ = user.tenant
        print(f"[AUTH] User found: {user.email} (ID: {user.id})")
        return user
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[AUTH] Error in get_current_user: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"get_current_user explicit error: {str(e)}")


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
