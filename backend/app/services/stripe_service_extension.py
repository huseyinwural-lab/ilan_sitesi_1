
    async def _process_revocation(self, invoice: Invoice, reason: str, refund_amount_cents: int = None, charge_amount_cents: int = None):
        """
        P16: Handles reward revocation logic for refunds/disputes.
        """
        # 1. Find Reward
        stmt = select(ReferralReward).where(
            and_(
                ReferralReward.referee_id == invoice.user_id,
                ReferralReward.status.in_(['pending', 'confirmed', 'applied']) # applied is legacy confirmed
            )
        )
        res = await self.db.execute(stmt)
        reward = res.scalar_one_or_none()
        
        if not reward:
            # No reward to revoke
            return

        # 2. Calculate Debit Amount
        debit_amount = reward.amount # Default full revoke
        
        if refund_amount_cents and charge_amount_cents and charge_amount_cents > 0:
            # Pro-rata calculation
            ratio = Decimal(refund_amount_cents) / Decimal(charge_amount_cents)
            debit_amount = reward.amount * ratio
            # Round to 2 decimals
            debit_amount = round(debit_amount, 2)
            
        if debit_amount <= 0:
            return

        # 3. Apply Revocation Logic based on Status
        previous_status = reward.status
        
        # If pending, just cancel it (no ledger debit needed as credit wasn't given yet)
        if reward.status == 'pending':
            reward.status = 'revoked'
            # Log reason? maybe in a note field or audit log.
            # We don't debit ledger because pending rewards didn't credit balance yet.
            
        # If confirmed/applied, we must debit
        elif reward.status in ['confirmed', 'applied']:
            reward.status = 'revoked' # Or 'partially_revoked'? MVP: Revoked.
            # Wait, if partial refund, do we revoke FULL reward status?
            # Policy says: "Partial refund -> debit = proportional". 
            # But status? If we keep 'confirmed', we might debit again later?
            # Let's keep it simple: If partial, we debit the amount but maybe keep status 'confirmed' if remainder exists?
            # Or simpler: Always 'revoked' implies "something bad happened".
            # For exact accounting, we should use Ledger for truth. Status is high level.
            # Let's set status to 'revoked' to prevent further automated processing (like maturity).
            
            # Create Ledger Entry (Debit)
            from app.models.ledger import RewardLedger
            ledger = RewardLedger(
                reward_id=reward.id,
                user_id=reward.referrer_id,
                type="DEBIT",
                amount=debit_amount,
                currency=reward.currency,
                reason=reason
            )
            self.db.add(ledger)
            
            # Update Stripe Balance (Add Debit = Positive Balance or Reduce Negative)
            # Stripe Balance: Negative = Credit (We owe user). Positive = Debit (User owes us).
            # To remove credit, we ADD a positive amount.
            # debit_amount is positive (e.g. 20 TRY).
            # Stripe takes integer cents.
            try:
                # Find Referrer Stripe ID
                ref_res = await self.db.execute(select(BillingCustomer).where(BillingCustomer.user_id == reward.referrer_id))
                referrer_billing = ref_res.scalar_one_or_none()
                
                if referrer_billing and referrer_billing.stripe_customer_id:
                    stripe_amount = int(debit_amount * 100)
                    stripe.Customer.create_balance_transaction(
                        referrer_billing.stripe_customer_id,
                        amount=stripe_amount, # Positive removes credit
                        currency=reward.currency.lower(),
                        description=f"Reward Revocation: {reason}"
                    )
            except Exception as e:
                # If Stripe fails, we still record ledger but log error.
                # Financial drift risk if Stripe fails but DB commits.
                # However, DB rollback will happen if this function raises.
                # So we should raise if strict.
                raise HTTPException(status_code=502, detail=f"Stripe Balance Update Failed: {e}")

        # Save changes
        self.db.add(reward)
        # Commit handled by caller
