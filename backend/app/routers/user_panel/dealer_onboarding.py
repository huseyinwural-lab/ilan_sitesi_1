from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.dealer import Dealer
from app.utils.slug import slugify
from pydantic import BaseModel

router = APIRouter()

class DealerUpgradeRequest(BaseModel):
    company_name: str
    tax_id: str
    country: str = "DE"
    dealer_type: str = "auto_dealer" # or real_estate_agent

@router.post("/upgrade", response_model=dict)
async def upgrade_to_dealer(
    data: DealerUpgradeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Check existing
    existing = (await db.execute(select(Dealer).where(Dealer.user_id == current_user.id))).scalar_one_or_none()
    if existing:
        return {"message": "Dealer account already exists", "status": existing.status}
        
    # 2. Create Dealer (Pending)
    slug = slugify(data.company_name) # Need to handle collision in prod
    
    dealer = Dealer(
        user_id=current_user.id,
        company_name=data.company_name,
        tax_id=data.tax_id,
        country=data.country,
        dealer_type=data.dealer_type,
        slug=slug,
        status="pending",
        is_active=False
    )
    db.add(dealer)
    await db.commit()
    
    # 3. Notification (Mock)
    print(f"🔔 New Dealer Application: {data.company_name}")
    
    return {"message": "Application submitted", "status": "pending"}

@router.get("/status", response_model=dict)
async def get_dealer_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dealer = (await db.execute(select(Dealer).where(Dealer.user_id == current_user.id))).scalar_one_or_none()
    if not dealer:
        return {"status": "none"}
        
    return {
        "status": dealer.status,
        "company_name": dealer.company_name,
        "slug": dealer.slug
    }
