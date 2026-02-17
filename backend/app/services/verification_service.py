import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from fastapi import HTTPException

class VerificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def send_phone_otp(self, user_id: str, phone_number: str) -> str:
        """
        Sends OTP. In Prod: Call Twilio.
        In Dev: Return '123456' and log.
        """
        # Check uniqueness
        exists = (await self.db.execute(select(User).where(User.phone_number == phone_number))).scalar_one_or_none()
        if exists and str(exists.id) != str(user_id):
            raise HTTPException(status_code=400, detail="Phone number already in use")
            
        # Save temp code in Redis (Mocking here)
        print(f"📲 OTP for {phone_number}: 123456")
        return "123456"

    async def verify_phone_otp(self, user_id: str, phone_number: str, code: str) -> bool:
        if code != "123456":
            raise HTTPException(status_code=400, detail="Invalid OTP")
            
        user = await self.db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        user.phone_number = phone_number
        user.is_phone_verified = True
        user.trust_score += 20 # Boost trust
        
        await self.db.commit()
        return True

    async def mock_kyc_callback(self, user_id: str, status: str = "verified"):
        """
        Simulates Stripe Identity Webhook
        """
        user = await self.db.get(User, user_id)
        if not user:
            return
            
        if status == "verified":
            user.is_identity_verified = True
            user.trust_score += 50
            await self.db.commit()
