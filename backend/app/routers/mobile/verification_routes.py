from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.verification_service import VerificationService

router = APIRouter()

class PhoneRequest(BaseModel):
    phone_number: str

class OTPRequest(BaseModel):
    phone_number: str
    code: str

@router.post("/phone/send")
async def send_otp(
    data: PhoneRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = VerificationService(db)
    await service.send_phone_otp(current_user.id, data.phone_number)
    return {"message": "OTP sent"}

@router.post("/phone/verify")
async def verify_otp(
    data: OTPRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = VerificationService(db)
    await service.verify_phone_otp(current_user.id, data.phone_number, data.code)
    return {"message": "Phone verified", "verified": True}
