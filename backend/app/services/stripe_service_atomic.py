
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
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid payload")

        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid signature")

        # P5-001: Atomic Webhook Processing
        # Start Transaction
        # Check idempotency inside transaction with lock if possible, or unique constraint handling.
        # Since we use async session, we rely on commit to fail if duplicate.
        
        # Log Event
        log = StripeEvent(
            event_id=event.id,
            event_type=event.type,
            status="processing"
        )
        self.db.add(log)
        
        # Try to commit log first to check uniqueness? 
        # If we commit now, and fail later, we have a processed log but failed logic.
        # Requirement: "Tek transaction içinde commit"
        # So we add log to session, do logic, then commit all.
        # If event_id exists, commit will fail with IntegrityError.
        # We need to handle that gracefully.
        
        try:
            # We flush here to catch event duplicate early without committing
            await self.db.flush()
        except Exception as e:
            await self.db.rollback()
            # If duplicate key error, return success (idempotent)
            if "ix_stripe_events_event_id" in str(e) or "unique constraint" in str(e).lower():
                return {"status": "already_processed"}
            raise e

        # Process Logic
        try:
            if event.type == "checkout.session.completed":
                session = event.data.object
                invoice_id = session.client_reference_id or session.metadata.get("invoice_id")
                
                if invoice_id:
                    # P5-001: Lock Invoice Row
                    result = await self.db.execute(select(Invoice).where(Invoice.id == uuid.UUID(invoice_id)).with_for_update())
                    invoice = result.scalar_one_or_none()
                    
                    if invoice and invoice.status != 'paid':
                        invoice.status = "paid"
                        invoice.paid_at = datetime.now(timezone.utc)
                        invoice.stripe_payment_intent_id = session.payment_intent
                        invoice.payment_idempotency_key = session.id 
                        
                        # Update attempt
                        attempt_result = await self.db.execute(select(PaymentAttempt).where(PaymentAttempt.stripe_checkout_session_id == session.id))
                        attempt = attempt_result.scalar_one_or_none()
                        if attempt:
                            attempt.status = "succeeded"
                            attempt.stripe_payment_intent_id = session.payment_intent
                        
                        # P4: Check for Subscription Activation
                        await self._activate_subscription_if_needed(invoice)
            
            elif event.type == "charge.refunded":
                charge = event.data.object
                payment_intent_id = charge.payment_intent
                amount_refunded = Decimal(charge.amount_refunded) / 100
                
                # Find Invoice & Lock
                result = await self.db.execute(select(Invoice).where(Invoice.stripe_payment_intent_id == payment_intent_id).with_for_update())
                invoice = result.scalar_one_or_none()
                
                if invoice:
                    invoice.refunded_total = amount_refunded
                    
                    if invoice.refunded_total >= invoice.gross_total:
                        invoice.status = "refunded"
                        invoice.refund_status = "full"
                        invoice.refunded_at = datetime.now(timezone.utc)
                    elif invoice.refunded_total > 0:
                        invoice.status = "partially_refunded"
                        invoice.refund_status = "partial"
                        invoice.last_refund_at = datetime.now(timezone.utc)
                    
                    if hasattr(charge, 'refunds'):
                        for ref_data in charge.refunds.data:
                            ref_res = await self.db.execute(select(Refund).where(Refund.stripe_refund_id == ref_data.id))
                            local_ref = ref_res.scalar_one_or_none()
                            if local_ref and local_ref.status != "succeeded":
                                local_ref.status = "succeeded"
            
            # Update Log status
            log.status = "processed"
            await self.db.commit()
            
        except Exception as e:
            await self.db.rollback()
            # Log error separately if possible, but for now re-raise to Stripe triggers retry
            # Or swallow if it's logical error?
            # Stripe expects 200 to stop retrying. 
            # If we fail, Stripe retries. 
            # If it's a permanent error, we should probably log and return 200?
            # But let's raise for visibility in MVP.
            raise e

        return {"status": "success"}
