
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_
from app.dependencies import get_db, check_permissions
from app.models.user import User
from app.models.promotion import Promotion, Coupon, CouponRedemption
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime, timezone
from decimal import Decimal
import uuid
import random
import string

router = APIRouter(prefix="/admin", tags=["admin-promotions"])

# --- Pydantic Models ---

class PromotionCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    promo_type: str = Field(..., pattern="^(percentage|fixed_amount)$")
    value: float = Field(..., gt=0)
    currency: str = "EUR"
    start_at: datetime
    end_at: Optional[datetime] = None
    max_redemptions: Optional[int] = Field(None, gt=0)

    @validator('value')
    def validate_value(cls, v, values):
        if 'promo_type' in values and values['promo_type'] == 'percentage':
            if v > 100:
                raise ValueError('Percentage value must be <= 100')
        return v

    @validator('end_at')
    def validate_dates(cls, v, values):
        if v and 'start_at' in values and v <= values['start_at']:
            raise ValueError('end_at must be after start_at')
        return v

class PromotionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    end_at: Optional[datetime] = None
    max_redemptions: Optional[int] = Field(None, gt=0)
    # is_active handled by separate endpoint

class CouponCreate(BaseModel):
    code_prefix: Optional[str] = Field(None, min_length=2, max_length=10, pattern="^[A-Z0-9]+$")
    code: Optional[str] = Field(None, min_length=3, max_length=20, pattern="^[A-Z0-9-]+$") # Single code
    count: int = Field(1, ge=1, le=1000) # Bulk limit
    usage_limit: Optional[int] = Field(None, gt=0)
    per_user_limit: int = Field(1, ge=1)

# --- Helper ---
async def log_action(db, action, res_type, res_id, user_id, new_values=None, old_values=None):
    from app.models.core import AuditLog
    db.add(AuditLog(
        action=action, 
        resource_type=res_type, 
        resource_id=res_id, 
        user_id=user_id,
        new_values=new_values,
        old_values=old_values
    ))

def generate_code(prefix: str = "", length: int = 8) -> str:
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(random.choices(chars, k=length))
    return f"{prefix}-{random_part}" if prefix else random_part

# --- Endpoints ---

@router.get("/promotions")
async def get_promotions(
    skip: int = 0, 
    limit: int = 50, 
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin", "finance", "support"]))
):
    query = select(Promotion).order_by(desc(Promotion.created_at))
    if is_active is not None:
        query = query.where(Promotion.is_active == is_active)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    promotions = result.scalars().all()
    
    return [{
        "id": str(p.id),
        "name": p.name,
        "type": p.promo_type,
        "value": float(p.value),
        "currency": p.currency,
        "start_at": p.start_at,
        "end_at": p.end_at,
        "is_active": p.is_active,
        "max_redemptions": p.max_redemptions
    } for p in promotions]

@router.post("/promotions", status_code=201)
async def create_promotion(
    data: PromotionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin"]))
):
    promo = Promotion(
        name=data.name,
        description=data.description,
        promo_type=data.promo_type,
        value=Decimal(str(data.value)),
        currency=data.currency,
        start_at=data.start_at,
        end_at=data.end_at,
        max_redemptions=data.max_redemptions,
        is_active=True
    )
    db.add(promo)
    await db.commit()
    await db.refresh(promo)
    
    await log_action(db, "PROMOTION_CREATE", "promotion", str(promo.id), current_user.id, new_values=data.dict())
    
    return {"id": str(promo.id), "status": "created"}

@router.get("/promotions/{promo_id}")
async def get_promotion_detail(
    promo_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin", "finance", "support"]))
):
    try:
        uuid_id = uuid.UUID(promo_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid ID")
        
    result = await db.execute(select(Promotion).where(Promotion.id == uuid_id))
    promo = result.scalar_one_or_none()
    if not promo:
        raise HTTPException(status_code=404, detail="Promotion not found")
        
    # Stats
    count_res = await db.execute(select(func.count(Coupon.id)).where(Coupon.promotion_id == uuid_id))
    coupon_count = count_res.scalar()
    
    return {
        "id": str(promo.id),
        "name": promo.name,
        "description": promo.description,
        "promo_type": promo.promo_type,
        "value": float(promo.value),
        "currency": promo.currency,
        "start_at": promo.start_at,
        "end_at": promo.end_at,
        "is_active": promo.is_active,
        "max_redemptions": promo.max_redemptions,
        "coupon_count": coupon_count
    }

@router.patch("/promotions/{promo_id}")
async def update_promotion(
    promo_id: str,
    data: PromotionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin"]))
):
    result = await db.execute(select(Promotion).where(Promotion.id == uuid.UUID(promo_id)))
    promo = result.scalar_one_or_none()
    if not promo:
        raise HTTPException(status_code=404, detail="Promotion not found")
    
    old_values = {}
    new_values = data.dict(exclude_unset=True)
    
    for k, v in new_values.items():
        old_values[k] = getattr(promo, k)
        setattr(promo, k, v)
    
    promo.updated_at = datetime.now(timezone.utc)
    await db.commit()
    
    await log_action(db, "PROMOTION_UPDATE", "promotion", str(promo.id), current_user.id, new_values=new_values, old_values=str(old_values))
    
    return {"id": str(promo.id), "status": "updated"}

@router.post("/promotions/{promo_id}/deactivate")
async def deactivate_promotion(
    promo_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin"]))
):
    result = await db.execute(select(Promotion).where(Promotion.id == uuid.UUID(promo_id)))
    promo = result.scalar_one_or_none()
    if not promo:
        raise HTTPException(status_code=404, detail="Promotion not found")
        
    promo.is_active = False
    promo.updated_at = datetime.now(timezone.utc)
    await db.commit()
    
    await log_action(db, "PROMOTION_DEACTIVATE", "promotion", str(promo.id), current_user.id)
    
    return {"id": str(promo.id), "status": "deactivated"}

# --- Coupon Endpoints ---

@router.get("/promotions/{promo_id}/coupons")
async def list_coupons(
    promo_id: str,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin", "finance", "support"]))
):
    query = select(Coupon).where(Coupon.promotion_id == uuid.UUID(promo_id)).offset(skip).limit(limit)
    result = await db.execute(query)
    coupons = result.scalars().all()
    
    return [{
        "id": str(c.id),
        "code": c.code,
        "usage_limit": c.usage_limit,
        "usage_count": c.usage_count,
        "is_active": c.is_active
    } for c in coupons]

@router.post("/promotions/{promo_id}/coupons")
async def create_coupons(
    promo_id: str,
    data: CouponCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin"]))
):
    # Check Promo
    promo_res = await db.execute(select(Promotion).where(Promotion.id == uuid.UUID(promo_id)))
    promo = promo_res.scalar_one_or_none()
    if not promo:
        raise HTTPException(status_code=404, detail="Promotion not found")
        
    created_codes = []
    
    if data.code: # Single Specific Code
        if data.count > 1:
             raise HTTPException(status_code=400, detail="Cannot create bulk with single specific code")
        
        # Check uniqueness
        exist = await db.execute(select(Coupon).where(Coupon.code == data.code.upper()))
        if exist.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Coupon code already exists")
            
        c = Coupon(
            promotion_id=promo.id,
            code=data.code.upper(),
            usage_limit=data.usage_limit,
            per_user_limit=data.per_user_limit
        )
        db.add(c)
        created_codes.append(c.code)
        
    else: # Bulk or Random
        for _ in range(data.count):
            # Retry logic for random code collision could be added, but minimal probability with uuid/long string
            code = generate_code(data.code_prefix)
            c = Coupon(
                promotion_id=promo.id,
                code=code,
                usage_limit=data.usage_limit,
                per_user_limit=data.per_user_limit
            )
            db.add(c)
            created_codes.append(code)
    
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Collision detected during creation, please retry")
    
    await log_action(db, "COUPON_CREATE", "promotion", str(promo.id), current_user.id, new_values={"count": len(created_codes), "codes": created_codes[:5]}) # Log first 5
    
    return {"count": len(created_codes), "codes": created_codes}

@router.post("/coupons/{coupon_id}/disable")
async def disable_coupon(
    coupon_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin"]))
):
    result = await db.execute(select(Coupon).where(Coupon.id == uuid.UUID(coupon_id)))
    coupon = result.scalar_one_or_none()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
        
    coupon.is_active = False
    await db.commit()
    
    await log_action(db, "COUPON_DISABLE", "coupon", str(coupon.id), current_user.id)
    return {"status": "disabled"}

@router.get("/redemptions")
async def get_redemptions(
    promo_id: Optional[str] = None,
    user_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin", "finance"]))
):
    query = select(CouponRedemption).order_by(desc(CouponRedemption.redeemed_at))
    
    if promo_id:
        query = query.join(Coupon).where(Coupon.promotion_id == uuid.UUID(promo_id))
    
    if user_id:
        query = query.where(CouponRedemption.user_id == uuid.UUID(user_id))
        
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    redemptions = result.scalars().all()
    
    return [{
        "id": str(r.id),
        "user_id": str(r.user_id),
        "coupon_id": str(r.coupon_id),
        "redeemed_at": r.redeemed_at,
        "discount_amount": float(r.discount_amount) if r.discount_amount else 0
    } for r in redemptions]
