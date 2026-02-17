
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, text
from app.models.growth import GrowthEvent
from app.models.user import User
from app.models.affiliate import Affiliate
from datetime import datetime, timedelta, timezone
import uuid

logger = logging.getLogger(__name__)

class GrowthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_event(self, event_type: str, user_id: str = None, affiliate_id: str = None, data: dict = None, country_code: str = None):
        """
        Fire-and-forget style logging with country segmentation.
        """
        try:
            # Auto-detect country if user_id provided and country missing
            if user_id and not country_code:
                user_res = await self.db.execute(select(User.country_code).where(User.id == uuid.UUID(user_id)))
                country_code = user_res.scalar_one_or_none() or "TR"

            event = GrowthEvent(
                event_type=event_type,
                user_id=uuid.UUID(user_id) if user_id else None,
                affiliate_id=uuid.UUID(affiliate_id) if affiliate_id else None,
                event_data=data or {},
                country_code=country_code or "TR"
            )
            self.db.add(event)
            # Caller handles commit
        except Exception as e:
            logger.error(f"Growth Event Log Error: {e}")

    async def get_overview_stats(self, country_code: str = None):
        """Dashboard Overview Stats with Country Filter"""
        # 1. Total Users
        q_users = select(func.count(User.id))
        if country_code:
            q_users = q_users.where(User.country_code == country_code)
        total_users = (await self.db.execute(q_users)).scalar()
        
        # 2. New Users (Last 7 Days)
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        q_new = select(func.count(User.id)).where(User.created_at >= seven_days_ago)
        if country_code:
            q_new = q_new.where(User.country_code == country_code)
        new_users = (await self.db.execute(q_new)).scalar()
        
        # 3. Revenue Events (Subscription Confirmed)
        q_sales = select(func.count(GrowthEvent.id)).where(GrowthEvent.event_type == 'subscription_confirmed')
        if country_code:
            q_sales = q_sales.where(GrowthEvent.country_code == country_code)
        total_sales = (await self.db.execute(q_sales)).scalar()
        
        # 4. Viral Coefficient
        q_referred = select(func.count(User.id)).where(User.referred_by.isnot(None))
        if country_code:
            q_referred = q_referred.where(User.country_code == country_code)
        referred_users = (await self.db.execute(q_referred)).scalar()
        
        k_factor = round(referred_users / total_users, 2) if total_users and total_users > 0 else 0
        
        return {
            "country_filter": country_code or "GLOBAL",
            "total_users": total_users,
            "new_users_7d": new_users,
            "total_sales_count": total_sales,
            "viral_k_factor": k_factor
        }
