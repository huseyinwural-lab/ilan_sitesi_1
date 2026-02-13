
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, desc
from sqlalchemy.exc import NoResultFound
from app.models.monetization import QuotaUsage, UserSubscription, SubscriptionPlan
from app.models.user import User
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class QuotaExceededError(Exception):
    def __init__(self, resource, limit, used):
        self.message = f"Quota exceeded for {resource}. Used: {used}, Limit: {limit}"
        super().__init__(self.message)

class QuotaService:
    # Default Limits
    FREE_LIMITS = {
        "listing_active": 3,
        "showcase_active": 0
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_active_subscription(self, user_id: str):
        """Find active subscription for user"""
        now = datetime.now(timezone.utc)
        stmt = (
            select(UserSubscription)
            .where(
                and_(
                    UserSubscription.user_id == user_id,
                    UserSubscription.status == 'active',
                    UserSubscription.end_at > now
                )
            )
            .order_by(desc(UserSubscription.end_at))
            .limit(1)
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_limits(self, user_id: str):
        """Resolve effective limits based on plan"""
        sub = await self._get_active_subscription(user_id)
        if sub:
            # Lazy load plan? Or assume joined. 
            # In async, relationship lazy load fails if not selectinload.
            # Let's fetch plan explicitly or use joinedload strategy.
            plan_res = await self.db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == sub.plan_id))
            plan = plan_res.scalar_one()
            
            # Map plan limits keys
            return {
                "listing_active": plan.limits.get("listing", 0),
                "showcase_active": plan.limits.get("showcase", 0)
            }
        
        # Fallback to Free
        return self.FREE_LIMITS

    async def get_usage(self, user_id: str, resource: str):
        """Get current usage from usage table"""
        stmt = select(QuotaUsage).where(and_(QuotaUsage.user_id == user_id, QuotaUsage.resource == resource))
        res = await self.db.execute(stmt)
        usage_rec = res.scalar_one_or_none()
        return usage_rec.used if usage_rec else 0

    async def check_quota(self, user_id: str, resource: str, needed: int = 1) -> bool:
        """Read-only check"""
        limits = await self.get_limits(user_id)
        limit = limits.get(resource, 0)
        used = await self.get_usage(user_id, resource)
        
        return (used + needed) <= limit

    async def consume_quota(self, user_id: str, resource: str, amount: int = 1):
        """Transactional consumption"""
        # Ensure row exists
        stmt = select(QuotaUsage).where(and_(QuotaUsage.user_id == user_id, QuotaUsage.resource == resource)).with_for_update()
        res = await self.db.execute(stmt)
        usage_rec = res.scalar_one_or_none()
        
        if not usage_rec:
            usage_rec = QuotaUsage(user_id=user_id, resource=resource, used=0)
            self.db.add(usage_rec)
            await self.db.flush() # Get ID and lock? Newly inserted row is locked by tx.
        
        # Re-fetch limits inside tx
        limits = await self.get_limits(user_id)
        limit = limits.get(resource, 0)
        
        if (usage_rec.used + amount) > limit:
            raise QuotaExceededError(resource, limit, usage_rec.used)
            
        usage_rec.used += amount
        # No commit here, handled by caller (Unit of Work)
        
    async def release_quota(self, user_id: str, resource: str, amount: int = 1):
        """Transactional release"""
        stmt = select(QuotaUsage).where(and_(QuotaUsage.user_id == user_id, QuotaUsage.resource == resource)).with_for_update()
        res = await self.db.execute(stmt)
        usage_rec = res.scalar_one_or_none()
        
        if usage_rec and usage_rec.used > 0:
            usage_rec.used = max(0, usage_rec.used - amount)
