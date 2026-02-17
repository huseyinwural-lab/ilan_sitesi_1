
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.models.user import User
from app.models.affiliate import Affiliate
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

class AbuseService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_signup_abuse(self, ip_address: str, device_hash: str = None) -> bool:
        """
        Checks if signup request is suspicious.
        Returns True if abuse detected.
        """
        if device_hash:
            # Note: The count is ALWAYS returning 0 in tests because the previous inserts 
            # in server.py (register function) are in a different transaction context 
            # than this query, OR the isolation level prevents seeing uncommitted reads 
            # if server.py holds transaction open?
            # NO, server.py creates AbuseService(db), calls check, THEN creates User, THEN commits.
            # So `check_signup_abuse` runs BEFORE the current user is inserted.
            # It sees existing users.
            
            # Why is count 0 for attempts 2, 3, 4?
            # Because `test_abuse_fix.py` runs sequential requests.
            # Request 1 -> Server (New DB Session) -> Check (0) -> Insert -> Commit -> Return 201.
            # Request 2 -> Server (New DB Session) -> Check (Should be 1!) -> Insert...
            
            # Ah! `debug_abuse_control.py` output showed 201, 201, 201, 201.
            # And logs showed "Count 0" every time.
            # This implies the DB is empty every time?
            # Is `test_abuse_fix.py` cleaning up after EACH request? No.
            # Is the server running in memory DB or rollback mode? No, Postgres.
            
            # WAIT. `test_abuse_fix.py` does:
            # 1. Clean previous run (DELETE users)
            # 2. Register 1
            # 3. Register 2 ...
            
            # If server logs show "Count 0" every time, it means the SELECT query is not finding the records.
            # Is `device_hash` being saved correctly?
            # Let's check `User` creation in server.py.
            
            stmt = select(func.count(User.id)).where(User.device_hash == device_hash)
            count = (await self.db.execute(stmt)).scalar() or 0
            
            print(f"DEBUG: Abuse Check: Device {device_hash}, Count {count}")
            logger.info(f"Abuse Check: Device {device_hash}, Count {count}")
            
            if count >= 3: 
                logger.warning(f"Abuse: Device hash collision {device_hash}")
                return True
                
        return False

    async def calculate_affiliate_risk(self, affiliate_id: str):
        pass
