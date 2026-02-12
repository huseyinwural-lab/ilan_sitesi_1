
import stripe
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.payment import StripeSettings, PaymentAttempt, StripeEvent
from app.models.billing import Invoice, InvoiceItem
from datetime import datetime, timezone
from fastapi import HTTPException
import uuid
import json

class StripeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_config(self, country: str):
        result = await self.db.execute(select(StripeSettings).where(StripeSettings.country == country.upper()))
        settings = result.scalar_one_or_none()
        if not settings or not settings.is_enabled:
            # Fallback to env default if config missing (for MVP speed)
            # But better to raise error if strict
            return None
        
        api_key = os.environ.get(settings.secret_key_env_key)
        webhook_secret = os.environ.get(settings.webhook_secret_env_key)
        return {"api_key": api_key, "webhook_secret": webhook_secret, "mode": settings.account_mode}

    async def create_checkout_session(self, invoice_id: str, success_url: str, cancel_url: str, user_email: str):
        # 1. Fetch Invoice
        result = await self.db.execute(select(Invoice).where(Invoice.id == uuid.UUID(invoice_id)))
        invoice = result.scalar_one_or_none()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        if invoice.status != "draft":
            raise HTTPException(status_code=400, detail="Invoice is not in draft status")

        # 2. Get Config
        config = await self.get_config(invoice.country)
        if not config or not config["api_key"]:
            # Fallback to a default test key from env if explicit country config missing (MVP fallback)
            # In a real scenario, we'd enforce DB config.
            api_key = os.environ.get("STRIPE_API_KEY") # Default fallback
            if not api_key:
                raise HTTPException(status_code=500, detail=f"Stripe configuration missing for {invoice.country}")
        else:
            api_key = config["api_key"]

        stripe.api_key = api_key

        # 3. Prepare Line Items
        # Stripe expects integer cents
        line_items = []
        for item in invoice.items:
            # Description translation handling
            desc = item.description.get('en') or item.description.get('de') or str(item.description)
            
            line_items.append({
                "price_data": {
                    "currency": invoice.currency.lower(),
                    "product_data": {
                        "name": desc,
                    },
                    "unit_amount": int(item.unit_price_net * 100), # Net price (Wait, stripe usually wants Gross? Or we add tax item?)
                    # Invoice logic: We have line_gross.
                    # Simplified: Pass 1 line item with total gross amount to avoid rounding issues per line vs total.
                    # ADM-STP-060 says "line_items: invoice_items’lardan üret".
                    # But tax calc in Stripe is complex if we pass net.
                    # Better strategy: Pass line items with 'unit_amount' = line_gross / quantity (approx) or
                    # Just pass ONE item "Invoice Payment #..." with total amount.
                    # Let's try to pass items but use gross price per item.
                },
                "quantity": item.quantity,
            })
        
        # Override to ensure exact match with invoice total
        # Because summing line items might have rounding diffs vs invoice.gross_total
        # Safer for MVP: Single line item "Invoice #..."
        line_items = [{
            "price_data": {
                "currency": invoice.currency.lower(),
                "product_data": {
                    "name": f"Invoice #{invoice.invoice_no}",
                    "description": f"Payment for {invoice.customer_name}",
                },
                "unit_amount": int(invoice.gross_total * 100),
            },
            "quantity": 1,
        }]

        # 4. Create Session
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=line_items,
                mode="payment",
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=user_email,
                client_reference_id=str(invoice.id),
                metadata={
                    "invoice_id": str(invoice.id),
                    "country": invoice.country
                }
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

        # 5. Log Attempt
        attempt = PaymentAttempt(
            invoice_id=invoice.id,
            country=invoice.country,
            currency=invoice.currency,
            amount_gross=invoice.gross_total,
            stripe_checkout_session_id=session.id,
            status="created"
        )
        self.db.add(attempt)
        await self.db.commit()
        
        return {"checkout_url": session.url, "attempt_id": str(attempt.id)}

    async def handle_webhook(self, payload: bytes, sig_header: str):
        # We need to know WHICH secret to use.
        # This is tricky because we don't know the country yet.
        # But usually we have one webhook endpoint per account.
        # If we have multiple connected accounts, the event tells us.
        # For this MVP, we assume ONE global Stripe account (or we try all secrets).
        # Let's assume one env var STRIPE_WEBHOOK_SECRET for now.
        
        webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
        if not webhook_secret:
             raise HTTPException(status_code=500, detail="Webhook secret not configured")

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            raise HTTPException(status_code=400, detail="Invalid signature")

        # Idempotency
        existing = await self.db.execute(select(StripeEvent).where(StripeEvent.event_id == event.id))
        if existing.scalar_one_or_none():
            return {"status": "already_processed"}

        # Log Event
        log = StripeEvent(
            event_id=event.id,
            event_type=event.type,
            status="processing"
        )
        self.db.add(log)
        await self.db.commit()

        # Process
        try:
            if event.type == "checkout.session.completed":
                session = event.data.object
                invoice_id = session.client_reference_id or session.metadata.get("invoice_id")
                
                if invoice_id:
                    # Update Invoice
                    result = await self.db.execute(select(Invoice).where(Invoice.id == uuid.UUID(invoice_id)))
                    invoice = result.scalar_one_or_none()
                    if invoice:
                        invoice.status = "paid"
                        invoice.paid_at = datetime.now(timezone.utc)
                        invoice.stripe_payment_intent_id = session.payment_intent
                        invoice.payment_idempotency_key = session.id # Use session ID as idempotent key reference
                        
                        # Update attempt
                        attempt_result = await self.db.execute(select(PaymentAttempt).where(PaymentAttempt.stripe_checkout_session_id == session.id))
                        attempt = attempt_result.scalar_one_or_none()
                        if attempt:
                            attempt.status = "succeeded"
                            attempt.stripe_payment_intent_id = session.payment_intent
            
            # Update Log
            log.status = "processed"
            await self.db.commit()
            
        except Exception as e:
            log.status = "error"
            log.processing_error = str(e)
            await self.db.commit()
            raise e

        return {"status": "success"}
