
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.dependencies import get_db
from app.models.affiliate import Affiliate, AffiliateClick
from datetime import datetime, timezone
import hashlib
import os

router = APIRouter(tags=["affiliate-tracking"])

DOMAIN = os.environ.get("FRONTEND_URL", "http://localhost:3000")

@router.get("/ref/{slug}")
async def track_affiliate_link(
    slug: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Tracks affiliate click and redirects to home.
    Sets 'aff_ref' cookie.
    """
    # 1. Find Affiliate
    stmt = select(Affiliate).where(Affiliate.custom_slug == slug)
    affiliate = (await db.execute(stmt)).scalar_one_or_none()
    
    if not affiliate or affiliate.status != 'approved':
        # Invalid or inactive link -> Redirect without tracking
        return RedirectResponse(url=f"{DOMAIN}?error=invalid_ref")
        
    # 2. Track Click (Async fire & forget ideal, but simple await here)
    try:
        ip = request.client.host if request.client else "unknown"
        ip_hash = hashlib.sha256(ip.encode()).hexdigest()
        
        click = AffiliateClick(
            affiliate_id=affiliate.id,
            ip_hash=ip_hash,
            created_at=datetime.now(timezone.utc)
        )
        db.add(click)
        await db.commit()
    except Exception as e:
        print(f"Tracking error: {e}")
        
    # 3. Redirect with Cookie
    response = RedirectResponse(url=f"{DOMAIN}?ref={slug}")
    
    # Set Cookie (30 Days)
    response.set_cookie(
        key="aff_ref",
        value=str(affiliate.id),
        max_age=30 * 24 * 60 * 60, # 30 days
        httponly=True,
        samesite="lax",
        secure=False # True in prod
    )
    
    return response
