from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime, timezone
from app.models.notification import UserDevice
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_device(self, user_id, token: str, platform: str, device_id: str = None, is_rooted: bool = False):
        # 1. Remove token if it exists for another user (Device handover)
        await self.db.execute(delete(UserDevice).where(UserDevice.token == token, UserDevice.user_id != user_id))
        
        # 2. Check if device exists for this user
        result = await self.db.execute(select(UserDevice).where(UserDevice.token == token))
        device = result.scalar_one_or_none()
        
        if device:
            device.user_id = user_id # Update user owner
            device.last_active_at = datetime.now(timezone.utc)
            device.is_active = True
            device.is_rooted = is_rooted
        else:
            device = UserDevice(
                user_id=user_id,
                token=token,
                platform=platform,
                device_id=device_id,
                is_rooted=is_rooted,
                last_active_at=datetime.now(timezone.utc)
            )
            self.db.add(device)
            
        await self.db.commit()
        return device

    async def unregister_device(self, token: str):
        await self.db.execute(delete(UserDevice).where(UserDevice.token == token))
        await self.db.commit()

    async def send_push(self, user_id, title: str, body: str, data: dict = None):
        """
        Sends push notification to all active devices of a user.
        MOCKED for MVP (Logs to stdout)
        """
        result = await self.db.execute(select(UserDevice).where(UserDevice.user_id == user_id, UserDevice.is_active == True))
        devices = result.scalars().all()
        
        if not devices:
            logger.info(f"PUSH_SKIP: User {user_id} has no devices.")
            return

        for dev in devices:
            # Here we would call FCM API
            logger.info(f"🚀 PUSH_SEND [User: {user_id}] [Platform: {dev.platform}]")
            logger.info(f"   Title: {title}")
            logger.info(f"   Body: {body}")
            logger.info(f"   Data: {data}")
            # In real impl: try/except and handle 'NotRegistered' (delete from DB)
