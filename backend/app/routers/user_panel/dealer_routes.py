from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.dealer_profile import DealerProfile

router = APIRouter()

class DealerProfileSchema(BaseModel):
    company_name: str
    vat_number: Optional[str] = None
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    impressum_text: Optional[str] = None

@router.get("/", response_model=Optional[DealerProfileSchema])
async def get_my_dealer_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.user_type != "commercial":
        raise HTTPException(status_code=400, detail="User is not commercial")
        
    query = select(DealerProfile).where(DealerProfile.user_id == current_user.id)
    profile = (await db.execute(query)).scalar_one_or_none()
    
    if not profile:
        return None
        
    return DealerProfileSchema(
        company_name=profile.company_name,
        vat_number=profile.vat_number,
        address_street=profile.address_street,
        address_city=profile.address_city,
        impressum_text=profile.impressum_text
    )

@router.put("/", response_model=DealerProfileSchema)
async def update_dealer_profile(
    data: DealerProfileSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.user_type != "commercial":
        raise HTTPException(status_code=400, detail="User is not commercial")
        
    query = select(DealerProfile).where(DealerProfile.user_id == current_user.id)
    profile = (await db.execute(query)).scalar_one_or_none()
    
    if not profile:
        profile = DealerProfile(user_id=current_user.id, company_name=data.company_name)
        db.add(profile)
        
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(profile, k, v)
        
    await db.commit()
    await db.refresh(profile)
    
    return DealerProfileSchema(
        company_name=profile.company_name,
        vat_number=profile.vat_number,
        address_street=profile.address_street,
        address_city=profile.address_city,
        impressum_text=profile.impressum_text
    )
