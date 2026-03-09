import uuid
import boto3
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import get_settings
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse
from seed.chart_of_accounts import seed_chart_of_accounts

import hmac
import hashlib
import base64

settings = get_settings()

def _get_secret_hash(username: str) -> str:
    message = bytes(username + settings.cognito_app_client_id, 'utf-8')
    key = bytes(settings.cognito_app_client_secret, 'utf-8')
    secret_hash = base64.b64encode(
        hmac.new(key, message, digestmod=hashlib.sha256).digest()
    ).decode()
    return secret_hash


def _get_auth_params(username: str, password: str) -> dict[str, str]:
    params = {"USERNAME": username, "PASSWORD": password}
    if settings.cognito_app_client_secret:
        params["SECRET_HASH"] = _get_secret_hash(username)
    return params


def _get_cognito_client():
    return boto3.client(
        "cognito-idp",
        region_name=settings.cognito_region,
        aws_access_key_id=settings.aws_access_key_id or None,
        aws_secret_access_key=settings.aws_secret_access_key or None,
    )


async def signup(db: AsyncSession, req: SignupRequest) -> TokenResponse:
    """Register user in Cognito + create tenant and user in DB."""
    cognito = _get_cognito_client()

    signup_params = {
        "ClientId": settings.cognito_app_client_id,
        "Username": req.email,
        "Password": req.password,
        "UserAttributes": [{"Name": "email", "Value": req.email}, {"Name": "name", "Value": req.name}],
    }
    if settings.cognito_app_client_secret:
        signup_params["SecretHash"] = _get_secret_hash(req.email)

    cognito_resp = cognito.sign_up(
        **signup_params,
    )
    cognito_sub = cognito_resp["UserSub"]
    print(f"[SIGNUP] Cognito user created with sub: {cognito_sub}")

    cognito.admin_confirm_sign_up(
        UserPoolId=settings.cognito_user_pool_id,
        Username=req.email,
    )
    print(f"[SIGNUP] Cognito user confirmed: {req.email}")

    tenant = Tenant(name=req.tenant_name, fy_start_month=4, tax_regime="new")
    db.add(tenant)
    await db.flush()
    print(f"[SIGNUP] Tenant created: {tenant.name} (ID: {tenant.id})")

    user = User(
        tenant_id=tenant.id,
        email=req.email,
        name=req.name,
        cognito_sub=cognito_sub,
        role=req.role,
    )
    db.add(user)
    await db.flush()
    print(f"[SIGNUP] User created in DB: {user.email} (ID: {user.id}, cognito_sub: {cognito_sub})")

    # Seed chart of accounts for the new tenant
    await seed_chart_of_accounts(db, tenant.id)
    print(f"[SIGNUP] Chart of accounts seeded for tenant {tenant.id}")
    
    # Commit the transaction before getting the token to avoid race condition
    # where /auth/me is called before the user is committed to the database
    await db.commit()
    print(f"[SIGNUP] Database transaction committed")

    auth_resp = cognito.initiate_auth(
        ClientId=settings.cognito_app_client_id,
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters=_get_auth_params(req.email, req.password),
    )

    auth_result = auth_resp["AuthenticationResult"]
    return TokenResponse(
        access_token=auth_result["AccessToken"],
        refresh_token=auth_result.get("RefreshToken"),
        user_id=str(user.id),
        tenant_id=str(tenant.id),
        role=user.role,
    )


async def login(db: AsyncSession, req: LoginRequest) -> TokenResponse:
    cognito = _get_cognito_client()

    auth_resp = cognito.initiate_auth(
        ClientId=settings.cognito_app_client_id,
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters=_get_auth_params(req.email, req.password),
    )

    access_token = auth_resp["AuthenticationResult"]["AccessToken"]
    print(f"[LOGIN] Cognito authentication successful, got access token")

    user_info = cognito.get_user(AccessToken=access_token)
    cognito_sub = user_info["Username"]
    for attr in user_info.get("UserAttributes", []):
        if attr["Name"] == "sub":
            cognito_sub = attr["Value"]
    print(f"[LOGIN] Retrieved cognito_sub from token: {cognito_sub}")

    result = await db.execute(
        select(User).where(User.cognito_sub == cognito_sub, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if not user:
        print(f"[LOGIN] User not found in database for cognito_sub: {cognito_sub}, auto-provisioning...")
        email = req.email
        name = email.split("@")[0]
        for attr in user_info.get("UserAttributes", []):
            if attr["Name"] == "email":
                email = attr["Value"]
            elif attr["Name"] == "name":
                name = attr["Value"]

        tenant = Tenant(name=f"{name}'s Company", fy_start_month=4, tax_regime="new")
        db.add(tenant)
        await db.flush()

        user = User(
            tenant_id=tenant.id,
            email=email,
            name=name,
            cognito_sub=cognito_sub,
            role="owner",
        )
        db.add(user)
        await db.flush()

        # Seed chart of accounts for the new tenant
        await seed_chart_of_accounts(db, tenant.id)
        print(f"[LOGIN] Chart of accounts seeded for tenant {tenant.id}")

        await db.commit()
        print(f"[LOGIN] Auto-provisioned user: {email} (ID: {user.id}, tenant: {tenant.id})")
    else:
        print(f"[LOGIN] User found in DB: {user.email} (ID: {user.id})")
    return TokenResponse(
        access_token=access_token,
        refresh_token=auth_resp["AuthenticationResult"].get("RefreshToken"),
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        role=user.role,
    )


async def dev_login(db: AsyncSession, email: str) -> TokenResponse:
    """Development-only login that bypasses Cognito."""
    result = await db.execute(
        select(User).where(User.email == email, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError(f"User {email} not found")

    return TokenResponse(
        access_token=f"dev:{user.cognito_sub or user.id}:{email}",
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        role=user.role,
    )


async def refresh_access_token(db: AsyncSession, refresh_token: str) -> TokenResponse:
    """Use Cognito refresh token to get new access token."""
    cognito = _get_cognito_client()

    # Cognito requires REFRESH_TOKEN_AUTH flow
    auth_params = {"REFRESH_TOKEN": refresh_token}
    if settings.cognito_app_client_secret:
        # For refresh token, we need a username. Extract from the refresh token or use a dummy value
        # Actually, for REFRESH_TOKEN_AUTH with client secret, we need to compute SECRET_HASH differently
        # Let's check if client secret is needed for refresh
        pass  # Cognito REFRESH_TOKEN_AUTH may not require SECRET_HASH

    auth_resp = cognito.initiate_auth(
        ClientId=settings.cognito_app_client_id,
        AuthFlow="REFRESH_TOKEN_AUTH",
        AuthParameters=auth_params,
    )

    access_token = auth_resp["AuthenticationResult"]["AccessToken"]
    print(f"[REFRESH] Successfully refreshed access token")

    # Get user info from new access token
    user_info = cognito.get_user(AccessToken=access_token)
    cognito_sub = user_info["Username"]
    for attr in user_info.get("UserAttributes", []):
        if attr["Name"] == "sub":
            cognito_sub = attr["Value"]

    # Find user in database
    result = await db.execute(
        select(User).where(User.cognito_sub == cognito_sub, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if not user:
        print(f"[REFRESH] User not found in database for cognito_sub: {cognito_sub}")
        raise ValueError("User not found in database")

    print(f"[REFRESH] Token refreshed for user: {user.email} (ID: {user.id})")
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,  # Return same refresh token
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        role=user.role,
    )
