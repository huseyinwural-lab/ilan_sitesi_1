from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.escrow import EscrowTransaction
from app.models.moderation import Listing
from app.models.user import User
from fastapi import HTTPException
import uuid
from decimal import Decimal

class EscrowService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def initiate_transaction(self, buyer_id: uuid.UUID, listing_id: uuid.UUID) -> EscrowTransaction:
        listing = await self.db.get(Listing, listing_id)
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
            
        if listing.status != "active":
            raise HTTPException(status_code=400, detail="Listing is not active")
            
        # Check Seller Tier (Mock check for P27)
        # In real app: Check UserSubscription or DealerPackage
        seller = await self.db.get(User, listing.user_id)
        is_trusted = seller.is_identity_verified and seller.rating_avg > 4.5
        
        # Calc Fee
        base_rate = Decimal("0.03") if is_trusted else Decimal("0.05")
        amount = Decimal(listing.price)
        
        # Dynamic Tiering
        if amount > 2000:
            base_rate -= Decimal("0.02")
        elif amount > 500:
            base_rate -= Decimal("0.01")
            
        # Floor
        base_rate = max(base_rate, Decimal("0.01"))
        
        fee = amount * base_rate
        
        trx = EscrowTransaction(
            listing_id=listing_id,
            buyer_id=buyer_id,
            seller_id=listing.user_id,
            amount=amount,
            fee_amount=fee,
            currency=listing.currency,
            status="initiated"
        )
        self.db.add(trx)
        await self.db.commit()
        return trx

    async def mark_funded(self, trx_id: uuid.UUID, payment_intent_id: str):
        trx = await self.db.get(EscrowTransaction, trx_id)
        if trx:
            trx.status = "funded"
            trx.stripe_payment_intent_id = payment_intent_id
            await self.db.commit()
            
    async def release_funds(self, trx_id: uuid.UUID):
        trx = await self.db.get(EscrowTransaction, trx_id)
        if trx and trx.status == "funded":
            trx.status = "released"
            # Trigger Payout Logic Here
            await self.db.commit()
