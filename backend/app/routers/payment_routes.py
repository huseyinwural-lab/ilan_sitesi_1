
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, get_current_user, check_permissions
from app.services.stripe_service import StripeService
from app.models.user import User
from pydantic import BaseModel

router = APIRouter(prefix="/payments", tags=["payments"])

class CheckoutRequest(BaseModel):
    success_url: str
    cancel_url: str

class RefundRequest(BaseModel):
    amount: float
    reason: str = "requested_by_customer"

@router.post("/invoices/{invoice_id}/checkout")
async def create_checkout(
    invoice_id: str, 
    req: CheckoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin", "finance"]))
):
    service = StripeService(db)
    return await service.create_checkout_session(
        invoice_id=invoice_id,
        success_url=req.success_url,
        cancel_url=req.cancel_url,
        user_email=current_user.email
    )

@router.post("/invoices/{invoice_id}/refund")
async def refund_invoice(
    invoice_id: str,
    req: RefundRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin", "finance"]))
):
    service = StripeService(db)
    return await service.create_refund(
        invoice_id=invoice_id,
        amount=req.amount,
        reason=req.reason,
        admin_id=str(current_user.id)
    )

@router.post("/webhook/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    payload = await request.body()
    service = StripeService(db)
    return await service.handle_webhook(payload, stripe_signature)
