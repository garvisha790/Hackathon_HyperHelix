from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import get_settings
from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse
from app.services import auth_service

router = APIRouter()
settings = get_settings()


@router.post("/signup", response_model=TokenResponse)
async def signup(req: SignupRequest, db: AsyncSession = Depends(get_db)):
    try:
        return await auth_service.signup(db, req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        if settings.app_env == "development":
            return await auth_service.dev_login(db, req.email)
        return await auth_service.login(db, req)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
