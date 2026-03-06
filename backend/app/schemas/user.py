from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserUpdateRequest(BaseModel):
    """Request schema for updating user profile"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="User's full name")


class UserPreferences(BaseModel):
    """User preferences and settings"""
    email_notifications: bool = True
    system_updates: bool = True
    marketing_emails: bool = False
    theme: str = Field("system", pattern="^(light|dark|system)$")
    timezone: str = "Asia/Kolkata"


class UserProfileResponse(BaseModel):
    """Complete user profile response"""
    id: str
    email: str
    name: Optional[str]
    role: str
    avatar_url: Optional[str] = None
    tenant_id: str
    tenant: Optional[dict] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
