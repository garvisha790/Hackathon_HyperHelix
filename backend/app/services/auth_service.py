import uuid
import boto3
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import get_settings
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse

settings = get_settings()


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

    cognito_resp = cognito.sign_up(
        ClientId=settings.cognito_app_client_id,
        Username=req.email,
        Password=req.password,
        UserAttributes=[{"Name": "email", "Value": req.email}, {"Name": "name", "Value": req.name}],
    )
    cognito_sub = cognito_resp["UserSub"]

    cognito.admin_confirm_sign_up(
        UserPoolId=settings.cognito_user_pool_id,
        Username=req.email,
    )

    tenant = Tenant(name=req.tenant_name, fy_start_month=4, tax_regime="new")
    db.add(tenant)
    await db.flush()

    user = User(
        tenant_id=tenant.id,
        email=req.email,
        name=req.name,
        cognito_sub=cognito_sub,
        role=req.role,
    )
    db.add(user)
    await db.flush()

    auth_resp = cognito.initiate_auth(
        ClientId=settings.cognito_app_client_id,
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters={"USERNAME": req.email, "PASSWORD": req.password},
    )

    return TokenResponse(
        access_token=auth_resp["AuthenticationResult"]["AccessToken"],
        user_id=str(user.id),
        tenant_id=str(tenant.id),
        role=user.role,
    )


async def login(db: AsyncSession, req: LoginRequest) -> TokenResponse:
    cognito = _get_cognito_client()

    auth_resp = cognito.initiate_auth(
        ClientId=settings.cognito_app_client_id,
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters={"USERNAME": req.email, "PASSWORD": req.password},
    )

    access_token = auth_resp["AuthenticationResult"]["AccessToken"]

    user_info = cognito.get_user(AccessToken=access_token)
    cognito_sub = user_info["Username"]
    for attr in user_info.get("UserAttributes", []):
        if attr["Name"] == "sub":
            cognito_sub = attr["Value"]

    result = await db.execute(
        select(User).where(User.cognito_sub == cognito_sub, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError("User not found in database")

    return TokenResponse(
        access_token=access_token,
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
