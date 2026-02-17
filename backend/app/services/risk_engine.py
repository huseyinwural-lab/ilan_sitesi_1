from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta, timezone
from app.models.user import User
from app.models.messaging import Message
from app.models.analytics import UserInteraction

class RiskEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_risk_score(self, user_id: str) -> int:
        score = 0
        user = await self.db.get(User, user_id)
        if not user:
            return 0
            
        # 1. Account Age
        age_days = (datetime.now(timezone.utc) - user.created_at).days
        if age_days < 7:
            score += 20
            
        # 2. Verification
        if not user.is_phone_verified:
            score += 30
            
        # 3. Spam Check (Last 1h)
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        msg_count = (await self.db.execute(select(func.count(Message.id)).where(
            Message.sender_id == user_id,
            Message.created_at >= one_hour_ago
        ))).scalar()
        
        if msg_count > 20:
            score += 40
        elif msg_count > 10:
            score += 10
            
        # 4. Rating Check
        if user.rating_count > 0 and user.rating_avg < 3.0:
            score += 20
            
        # Cap at 100
        return min(100, score)

    async def enforce_policy(self, user_id: str) -> str:
        """
        Returns: 'allow', 'restrict', 'ban'
        """
        score = await self.calculate_risk_score(user_id)
        
        if score > 80:
            return "ban"
        if score > 60:
            return "restrict"
        return "allow"
