
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.dependencies import get_db, check_permissions
from app.models.user import User
from app.models.affiliate import Affiliate
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/v1/admin/affiliates", tags=["admin-affiliate"])

class ReviewRequest(BaseModel):
    action: str # approve, reject
    reject_reason: str = None

@router.get("")
async def list_applications(
    status: str = "pending",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin"]))
):
    stmt = select(Affiliate).where(Affiliate.status == status)
    res = await db.execute(stmt)
    apps = res.scalars().all()
    
    return [{
        "id": str(a.id),
        "user_id": str(a.user_id),
        "slug": a.custom_slug,
        "payout": a.payout_details,
        "created_at": a.created_at
    } for a in apps]

@router.post("/{affiliate_id}/review")
async def review_application(
    affiliate_id: str,
    data: ReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin"]))
):
    stmt = select(Affiliate).where(Affiliate.id == uuid.UUID(affiliate_id))
    affiliate = (await db.execute(stmt)).scalar_one_or_none()
    
    if not affiliate:
        raise HTTPException(status_code=404, detail="Application not found")
        
    if data.action == "approve":
        affiliate.status = "approved"
        # Update User Flag
        user_stmt = select(User).where(User.id == affiliate.user_id)
        user = (await db.execute(user_stmt)).scalar_one()
        user.is_affiliate = True
        
    elif data.action == "reject":
        affiliate.status = "rejected"
        # Logic to store reject reason (Audit log or separate field)
        
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
        
    await db.commit()
    return {"status": affiliate.status}
