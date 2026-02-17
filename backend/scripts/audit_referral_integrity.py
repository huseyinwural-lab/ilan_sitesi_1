
import asyncio
import os
import sys
import uuid
import stripe
from sqlalchemy import text, select
from datetime import datetime, timedelta, timezone

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal
from app.models.referral import ReferralReward
from app.models.billing import Invoice

# Config
stripe.api_key = os.environ.get("STRIPE_API_KEY")

async def audit_referral_integrity():
    print("🔍 Starting Referral Financial Integrity Audit...")
    
    issues_found = []
    
    async with AsyncSessionLocal() as session:
        # 1. Fetch recent rewards
        # Limit to last 30 days for performance in production
        stmt = select(ReferralReward).order_by(ReferralReward.created_at.desc()).limit(100)
        result = await session.execute(stmt)
        rewards = result.scalars().all()
        
        print(f"📋 Checking {len(rewards)} recent rewards...")
        
        for reward in rewards:
            try:
                # 2. Get Referee's Invoice (The source of truth for payment)
                # Note: MVP implementation didn't explicitly link reward to invoice_id, 
                # but we can find the referee's first paid invoice.
                inv_stmt = select(Invoice).where(
                    Invoice.user_id == reward.referee_id,
                    Invoice.status.in_(['paid', 'refunded', 'partially_refunded'])
                ).order_by(Invoice.paid_at.asc()).limit(1)
                
                inv_res = await session.execute(inv_stmt)
                invoice = inv_res.scalar_one_or_none()
                
                if not invoice:
                    # Weird state: Reward exists but no paid invoice found?
                    # Could be manual reward or data inconsistency.
                    issues_found.append({
                        "reward_id": str(reward.id),
                        "issue": "NO_PAID_INVOICE",
                        "detail": f"Referee {reward.referee_id} has no paid invoice record."
                    })
                    continue
                
                # 3. Check Stripe Status (The Real Truth)
                if not invoice.stripe_payment_intent_id:
                    # Mock/Manual invoice?
                    # If live mode, this is a risk if not found.
                    if "sk_live" in (stripe.api_key or ""):
                         issues_found.append({
                            "reward_id": str(reward.id),
                            "issue": "NO_STRIPE_ID",
                            "detail": "Invoice has no stripe_payment_intent_id in Live Mode."
                        })
                    continue
                    
                # Safe Stripe Call
                try:
                    payment_intent = stripe.PaymentIntent.retrieve(invoice.stripe_payment_intent_id)
                except Exception as e:
                    print(f"   ⚠️ Stripe API Error for {invoice.stripe_payment_intent_id}: {e}")
                    continue

                # Check Charges
                if not payment_intent.charges.data:
                    continue
                    
                charge = payment_intent.charges.data[0] # Get latest charge
                
                # 4. Risk Analysis
                risk_level = "NONE"
                details = []
                
                # Check Refunds
                if charge.refunded:
                    risk_level = "HIGH"
                    details.append(f"Charge fully refunded ({charge.amount_refunded/100} {charge.currency})")
                elif charge.amount_refunded > 0:
                    risk_level = "MEDIUM"
                    details.append(f"Charge partially refunded ({charge.amount_refunded/100} {charge.currency})")
                    
                # Check Disputes
                if charge.dispute:
                    risk_level = "CRITICAL"
                    details.append(f"Charge disputed (Status: {charge.dispute.status})")
                
                # 5. Report if Issue
                # Logic: If risk detected AND reward is NOT revoked/cancelled
                if risk_level != "NONE" and reward.status not in ['revoked', 'cancelled']:
                    issues_found.append({
                        "reward_id": str(reward.id),
                        "referrer_id": str(reward.referrer_id),
                        "referee_id": str(reward.referee_id),
                        "risk_level": risk_level,
                        "issue": "REWARD_ACTIVE_BUT_PAYMENT_REVERSED",
                        "details": ", ".join(details),
                        "reward_amount": float(reward.amount),
                        "reward_status": reward.status
                    })
                    
            except Exception as e:
                print(f"⚠️ Error checking reward {reward.id}: {e}")

    # 6. Output Report
    print("\n" + "="*60)
    print("🚩 REFERRAL INTEGRITY AUDIT REPORT")
    print("="*60)
    
    if not issues_found:
        print("✅ No financial risks detected in scanned records.")
    else:
        print(f"⚠️ FOUND {len(issues_found)} RISKY RECORDS:")
        for issue in issues_found:
            print(f"\n[Risk: {issue.get('risk_level', 'UNKNOWN')}] Reward ID: {issue['reward_id']}")
            print(f"  - Issue: {issue.get('issue', 'Unknown')}")
            print(f"  - Details: {issue.get('details', issue.get('detail'))}")
            print(f"  - Status: {issue.get('reward_status', 'N/A')} | Amount: {issue.get('reward_amount', 0)}")
            
    print("="*60)

if __name__ == "__main__":
    asyncio.run(audit_referral_integrity())
