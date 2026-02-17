from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.user_core import UserProfileResponse, UserProfileUpdate, SecurityStatusResponse

router = APIRouter()

@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    return UserProfileResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        user_type=current_user.user_type,
        kyc_status=current_user.kyc_status,
        default_country=current_user.default_country,
        is_phone_verified=current_user.is_phone_verified,
        email_verified=current_user.email_verified,
        trust_score=current_user.trust_score
    )

@router.patch("/me", response_model=UserProfileResponse)
async def update_my_profile(
    update_data: UserProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if update_data.full_name:
        current_user.full_name = update_data.full_name
        
    if update_data.default_country:
        current_user.default_country = update_data.default_country.upper()
        
    await db.commit()
    await db.refresh(current_user)
    
    return UserProfileResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        user_type=current_user.user_type,
        kyc_status=current_user.kyc_status,
        default_country=current_user.default_country,
        is_phone_verified=current_user.is_phone_verified,
        email_verified=current_user.email_verified,
        trust_score=current_user.trust_score
    )

@router.get("/me/security", response_model=SecurityStatusResponse)
async def get_security_status(current_user: User = Depends(get_current_user)):
    return SecurityStatusResponse(
        email_verified=current_user.email_verified,
        phone_verified=current_user.is_phone_verified,
        kyc_status=current_user.kyc_status
    )
