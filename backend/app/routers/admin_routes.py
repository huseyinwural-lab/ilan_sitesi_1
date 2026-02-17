
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.dependencies import get_db, check_permissions
from app.models.user import User
# from app.server import get_password_hash # Circular import risk if server.py imports admin_routes
# Import helper locally or from dependencies if moved
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
import logging
import uuid

logger = logging.getLogger(__name__)
# Router is already defined in admin_routes.py, we will extend it.
# However, to avoid circular imports or re-definition issues if I overwrite, 
# I will check if admin_routes.py exists and append to it or rewrite it safely.
# Strategy: Rewrite admin_routes.py to include this new endpoint.

# Re-importing existing dependencies for the rewrite
from app.models.commercial import DealerPackage, DealerSubscription
from app.models.dealer import Dealer
from app.core.redis_rate_limit import RedisRateLimiter
import os

from app.models.user import SignupAllowlist
# Helper from previous implementation
async def log_action(db, action, res_type, res_id, user_id, new_values):
    from app.models.core import AuditLog
    db.add(AuditLog(
        action=action, 
        resource_type=res_type, 
        resource_id=res_id, 
        user_id=user_id,
        new_values=new_values
    ))

redis_limiter = RedisRateLimiter(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))

router = APIRouter(prefix="/admin", tags=["admin"])

# --- EXISTING ENDPOINTS ---

@router.patch("/dealers/{dealer_id}/tier")
async def update_dealer_tier(
    dealer_id: str,
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin"]))
):
    """
    Admin Override for Dealer Tier.
    Forces immediate Rate Limit update.
    """
    new_tier = payload.get("tier")
    target_user_id = payload.get("target_user_id")

    if new_tier not in ["STANDARD", "PREMIUM", "ENTERPRISE"]:
        raise HTTPException(status_code=400, detail="Invalid Tier")

    # Fetch Dealer
    d_res = await db.execute(select(Dealer).where(Dealer.id == uuid.UUID(dealer_id)))
    dealer = d_res.scalar_one_or_none()
    if not dealer:
        raise HTTPException(status_code=404, detail="Dealer not found")
        
    # Fetch Target Package
    p_res = await db.execute(select(DealerPackage).where(
        DealerPackage.country == dealer.country,
        DealerPackage.tier == new_tier,
        DealerPackage.is_active == True
    ))
    target_pkg = p_res.scalars().first()
    if not target_pkg:
        # Fallback to any package of that tier if specific country match fails in dev env
        p_res = await db.execute(select(DealerPackage).where(DealerPackage.tier == new_tier))
        target_pkg = p_res.scalars().first()
        if not target_pkg:
             raise HTTPException(status_code=400, detail=f"No active package found for tier {new_tier}")
        
    # Update Subscription
    s_res = await db.execute(select(DealerSubscription).where(
        DealerSubscription.dealer_id == dealer.id,
        DealerSubscription.status == 'active'
    ))
    sub = s_res.scalars().first()
    
    if sub:
        sub.package_id = target_pkg.id
        sub.included_listing_quota = target_pkg.listing_limit 
    
    await db.commit()
    
    if target_user_id:
        await redis_limiter.invalidate_context(target_user_id)
        logger.info(f"Invalidated context for {target_user_id}")
    
    await log_action(db, "ADMIN_CHANGE_TIER", "dealer", dealer_id, 
                     user_id=current_user.id, 
                     new_values={"tier": new_tier})
                     
    return {"status": "updated", "tier": new_tier, "invalidated": bool(target_user_id)}

# --- NEW ENDPOINT: CREATE USER ---

from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional

class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    role: str
    country_scope: List[str] = []

@router.post("/users", status_code=201)
async def create_system_user(
    user_data: AdminUserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin"]))
):
    """
    Super Admin creates a new system user (Admin, Support, Moderator).
    """
    # 1. Check Role Validity
    allowed_roles = ["super_admin", "country_admin", "moderator", "support", "finance"]
    if user_data.role not in allowed_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Allowed: {allowed_roles}")

    # 2. Check Email Uniqueness
    exists = await db.execute(select(User).where(User.email == user_data.email))
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already exists")

    # 3. Create User
    new_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        country_scope=user_data.country_scope,
        is_active=True,
        is_verified=True # Auto-verify admin created users
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # 4. Audit Log
    await log_action(db, "ADMIN_CREATE_USER", "user", str(new_user.id),
                     user_id=current_user.id,
                     new_values={"email": new_user.email, "role": new_user.role})

    return {
        "id": str(new_user.id),
        "email": new_user.email,
        "role": new_user.role,
        "status": "created"
    }


# --- ALLOWLIST ENDPOINTS ---

class AllowlistCreate(BaseModel):
    email: EmailStr

@router.get("/allowlist")
async def get_allowlist(
    skip: int = 0, 
    limit: int = 50, 
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))
):
    query = select(SignupAllowlist).order_by(SignupAllowlist.created_at.desc())
    if search:
        query = query.where(SignupAllowlist.email.ilike(f"%{search}%"))
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return [{
        "id": str(i.id),
        "email": i.email,
        "is_used": i.is_used,
        "created_at": i.created_at.isoformat() if i.created_at else None
    } for i in items]

@router.post("/allowlist", status_code=201)
async def add_to_allowlist(
    data: AllowlistCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))
):
    # Check if exists
    exists = await db.execute(select(SignupAllowlist).where(SignupAllowlist.email == data.email))
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already in allowlist")
        
    entry = SignupAllowlist(
        email=data.email,
        created_by=current_user.id
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    
    await log_action(db, "ADMIN_ADD_ALLOWLIST", "signup_allowlist", str(entry.id),
                     user_id=current_user.id,
                     new_values={"email": entry.email})
                     
    return {"id": str(entry.id), "email": entry.email, "status": "added"}

@router.delete("/allowlist/{entry_id}")
async def remove_from_allowlist(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin"]))
):
    result = await db.execute(select(SignupAllowlist).where(SignupAllowlist.id == uuid.UUID(entry_id)))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
        
    await db.delete(entry)
    await db.commit()
    
    await log_action(db, "ADMIN_REMOVE_ALLOWLIST", "signup_allowlist", entry_id,
                     user_id=current_user.id,
                     old_values={"email": entry.email})
                     
    return {"message": "Removed from allowlist"}
