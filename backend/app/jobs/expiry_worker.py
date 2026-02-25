
import asyncio
import logging
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from app.database import AsyncSessionLocal
from app.models.commercial import DealerSubscription
from app.models.core import AuditLog
from app.models.user import User
from app.models.pricing_campaign import PricingCampaign
from app.models.pricing_tier_rule import PricingTierRule
from app.models.pricing_package import UserPackageSubscription

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("expiry_worker")

async def run_expiry_job():
    logger.info("Starting Expiry Job...")
    async with AsyncSessionLocal() as session:
        try:
            now = datetime.now(timezone.utc)
            
            # 1. Find Expired Subscriptions
            # We fetch IDs first to log them, or just do a bulk update returning IDs.
            # SQLAlchemy 2.0 supports UPDATE...RETURNING
            stmt = (
                update(DealerSubscription)
                .where(and_(
                    DealerSubscription.status == 'active',
                    DealerSubscription.end_at < now
                ))
                .values(status='expired', updated_at=now)
                .returning(DealerSubscription.id, DealerSubscription.dealer_id)
            )
            
            result = await session.execute(stmt)
            expired_subs = result.all()
            
            count = len(expired_subs)
            
            if count > 0:
                logger.info(f"Expired {count} subscriptions.")
                
                # 2. Create Audit Log
                # We log one summary entry to avoid spamming 10k logs
                # Or detailed? Spec says "Audit Trail: Every expiration action".
                # P5_005_EXPIRY_SPEC.md says: "Audit log: subscription_id..."
                # But Ticket 2 says: "Log summary: 'Expired X subscriptions'".
                # Let's do a system audit log summary + maybe individual notes if critical.
                # For scalability (<10k), a single log is better.
                
                # Find system user
                sys_user_res = await session.execute(select(User).where(User.email == "admin@platform.com"))
                sys_user = sys_user_res.scalar_one_or_none()
                sys_user_id = sys_user.id if sys_user else None
                
                audit = AuditLog(
                    action="SYSTEM_EXPIRE",
                    resource_type="dealer_subscription",
                    user_id=sys_user_id,
                    user_email="system@platform.com",
                    new_values={"count": count, "ids": [str(s.id) for s in expired_subs]},
                    ip_address="127.0.0.1"
                )
                session.add(audit)
                
                await session.commit()
            else:
                logger.info("No subscriptions to expire.")
                
        except Exception as e:
            logger.error(f"Expiry Job Failed: {e}")
            await session.rollback()
            raise e

if __name__ == "__main__":
    asyncio.run(run_expiry_job())
