"""
User Profile Management API
Handles user profile operations, preferences, and settings
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies import CurrentUser
from app.models.user import User
from app.schemas.user import UserUpdateRequest, UserProfileResponse
from app.middleware.audit import log_action

router = APIRouter()


@router.get("/me", response_model=UserProfileResponse)
async def get_user_profile(current_user: CurrentUser):
    """
    Get current user's complete profile information
    
    Returns:
        UserProfileResponse: Complete user profile with tenant info
    """
    try:
        return UserProfileResponse(
            id=str(current_user.id),
            email=current_user.email,
            name=current_user.name,
            role=current_user.role,
            avatar_url=None,  # Will implement avatar upload later
            tenant_id=str(current_user.tenant_id),
            tenant={
                "name": current_user.tenant.name if current_user.tenant else None,
                "business_type": getattr(current_user.tenant, "business_type", None),
            } if current_user.tenant else None,
            created_at=current_user.created_at,
        )
    except Exception as e:
        import traceback
        print(f"[USERS/ME] Error retrieving user profile: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user profile: {str(e)}")


@router.put("/me", response_model=UserProfileResponse)
async def update_user_profile(
    update: UserUpdateRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user's profile information
    
    Args:
        update: User update request with new values
        current_user: Authenticated user from token
        db: Database session
        
    Returns:
        UserProfileResponse: Updated user profile
    """
    try:
        print(f"[USERS/UPDATE] Updating profile for user: {current_user.email}")
        
        # Fetch user from database to update
        result = await db.execute(
            select(User).where(User.id == current_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update fields
        update_data = update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(user, field, value)
                print(f"[USERS/UPDATE] Updated {field} to: {value}")
        
        await db.flush()
        
        # Log the action for audit trail
        await log_action(
            db, 
            user.tenant_id, 
            user.id, 
            "user.profile.update", 
            "user", 
            user.id
        )
        
        await db.commit()
        
        # Refresh to get updated data
        await db.refresh(user)
        
        print(f"[USERS/UPDATE] Successfully updated profile for: {user.email}")
        
        return UserProfileResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            role=user.role,
            avatar_url=None,
            tenant_id=str(user.tenant_id),
            tenant={
                "name": user.tenant.name if user.tenant else None,
                "business_type": getattr(user.tenant, "business_type", None),
            } if user.tenant else None,
            created_at=user.created_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[USERS/UPDATE] Error updating profile: {str(e)}")
        traceback.print_exc()
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")
