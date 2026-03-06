from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import get_settings
from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse
from app.services import auth_service
from app.dependencies import CurrentUser

router = APIRouter()
settings = get_settings()


@router.post("/signup", response_model=TokenResponse)
async def signup(req: SignupRequest, db: AsyncSession = Depends(get_db)):
    try:
        print(f"[AUTH/SIGNUP] Signup attempt for: {req.email}")
        print(f"[DIAGNOSTIC] Cognito Region: '{settings.cognito_region}'")
        print(f"[DIAGNOSTIC] App Client ID: '{settings.cognito_app_client_id}'")
        print(f"[DIAGNOSTIC] User Pool ID: '{settings.cognito_user_pool_id}'")
        result = await auth_service.signup(db, req)
        print(f"[AUTH/SIGNUP] Signup successful for: {req.email}")
        return result
    except Exception as e:
        import traceback
        print(f"[AUTH/SIGNUP] Signup failed for {req.email}: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        print(f"[AUTH/LOGIN] Login attempt for: {req.email}")
        result = await auth_service.login(db, req)
        print(f"[AUTH/LOGIN] Login successful for: {req.email}")
        return result
    except Exception as e:
        import traceback
        print(f"[AUTH/LOGIN] Login failed for {req.email}: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=401, detail=str(e))

@router.get("/me")
async def get_me(current_user: CurrentUser):
    try:
        print(f"[AUTH/ME] Successfully retrieved user: {current_user.email} (ID: {current_user.id})")
        return {
            "id": str(current_user.id),
            "email": current_user.email,
            "name": current_user.name,
            "role": current_user.role,
            "tenant_id": str(current_user.tenant_id),
            "tenant": {
                "name": current_user.tenant.name if current_user.tenant else None,
                "business_type": current_user.tenant.business_type if getattr(current_user.tenant, "business_type", None) else None,
            }
        }
    except Exception as e:
        import traceback
        print(f"[AUTH/ME] Error retrieving user: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
