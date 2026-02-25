
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
from app.models.pricing_campaign_item import PricingCampaignItem
from app.models.pricing_tier_rule import PricingTierRule
from app.models.pricing_package import UserPackageSubscription

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("expiry_worker")

async def run_expiry_job():
    logger.info("Starting Expiry Job...")
    async with AsyncSessionLocal() as session:
        try:
            now = datetime.now(timezone.utc)

            dealer_stmt = (
                update(DealerSubscription)
                .where(and_(
                    DealerSubscription.status == 'active',
                    DealerSubscription.end_at < now
                ))
                .values(status='expired', updated_at=now)
                .returning(DealerSubscription.id, DealerSubscription.dealer_id)
            )
            dealer_result = await session.execute(dealer_stmt)
            expired_subs = dealer_result.all()

            campaign_stmt = (
                update(PricingCampaign)
                .where(and_(
                    PricingCampaign.is_enabled.is_(True),
                    PricingCampaign.end_at.isnot(None),
                    PricingCampaign.end_at < now
                ))
                .values(is_enabled=False, updated_at=now)
                .returning(PricingCampaign.id)
            )
            campaign_result = await session.execute(campaign_stmt)
            expired_campaigns = campaign_result.all()

            campaign_item_stmt = (
                update(PricingCampaignItem)
                .where(and_(
                    PricingCampaignItem.is_active.is_(True),
                    PricingCampaignItem.is_deleted.is_(False),
                    PricingCampaignItem.end_at.isnot(None),
                    PricingCampaignItem.end_at < now
                ))
                .values(is_active=False, updated_at=now)
                .returning(PricingCampaignItem.id)
            )
            campaign_item_result = await session.execute(campaign_item_stmt)
            expired_campaign_items = campaign_item_result.all()

            tier_stmt = (
                update(PricingTierRule)
                .where(and_(
                    PricingTierRule.is_active.is_(True),
                    PricingTierRule.effective_end_at.isnot(None),
                    PricingTierRule.effective_end_at < now
                ))
                .values(is_active=False, updated_at=now)
                .returning(PricingTierRule.id)
            )
            tier_result = await session.execute(tier_stmt)
            expired_tiers = tier_result.all()

            package_stmt = (
                update(UserPackageSubscription)
                .where(and_(
                    UserPackageSubscription.status == 'active',
                    UserPackageSubscription.ends_at.isnot(None),
                    UserPackageSubscription.ends_at < now
                ))
                .values(status='expired', remaining_quota=0, updated_at=now)
                .returning(UserPackageSubscription.id, UserPackageSubscription.package_id)
            )
            package_result = await session.execute(package_stmt)
            expired_package_subs = package_result.all()

            total_updates = len(expired_subs) + len(expired_campaigns) + len(expired_tiers) + len(expired_package_subs)

            if total_updates > 0:
                logger.info(
                    "Expired: dealer_subs=%s campaigns=%s tier_rules=%s package_subs=%s",
                    len(expired_subs),
                    len(expired_campaigns),
                    len(expired_tiers),
                    len(expired_package_subs),
                )

                sys_user_res = await session.execute(select(User).where(User.email == "admin@platform.com"))
                sys_user = sys_user_res.scalar_one_or_none()
                sys_user_id = sys_user.id if sys_user else None

                if expired_subs:
                    session.add(
                        AuditLog(
                            action="SYSTEM_EXPIRE",
                            resource_type="dealer_subscription",
                            user_id=sys_user_id,
                            user_email="system@platform.com",
                            new_values={"count": len(expired_subs), "ids": [str(s.id) for s in expired_subs]},
                            ip_address="127.0.0.1",
                        )
                    )
                if expired_campaigns:
                    session.add(
                        AuditLog(
                            action="SYSTEM_EXPIRE",
                            resource_type="pricing_campaign",
                            user_id=sys_user_id,
                            user_email="system@platform.com",
                            new_values={"count": len(expired_campaigns), "ids": [str(c.id) for c in expired_campaigns]},
                            ip_address="127.0.0.1",
                        )
                    )
                if expired_tiers:
                    session.add(
                        AuditLog(
                            action="SYSTEM_EXPIRE",
                            resource_type="pricing_tier_rule",
                            user_id=sys_user_id,
                            user_email="system@platform.com",
                            new_values={"count": len(expired_tiers), "ids": [str(t.id) for t in expired_tiers]},
                            ip_address="127.0.0.1",
                        )
                    )
                if expired_package_subs:
                    session.add(
                        AuditLog(
                            action="SYSTEM_EXPIRE",
                            resource_type="pricing_package_subscription",
                            user_id=sys_user_id,
                            user_email="system@platform.com",
                            new_values={"count": len(expired_package_subs), "ids": [str(s.id) for s in expired_package_subs]},
                            ip_address="127.0.0.1",
                        )
                    )

                await session.commit()
            else:
                logger.info("No expirations to process.")
                
        except Exception as e:
            logger.error(f"Expiry Job Failed: {e}")
            await session.rollback()
            raise e

if __name__ == "__main__":
    asyncio.run(run_expiry_job())
