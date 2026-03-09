from pydantic import BaseModel, EmailStr


class SignupRequest(BaseModel):
    email: str
    password: str
    name: str
    tenant_name: str
    role: str = "owner"


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    user_id: str
    tenant_id: str
    role: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str
