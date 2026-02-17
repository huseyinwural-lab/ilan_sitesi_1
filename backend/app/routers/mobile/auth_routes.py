from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid
from datetime import datetime, timezone

from app.dependencies import get_db, get_current_user
from app.core.security import create_access_token, create_refresh_token, verify_password
from app.models.user import User

router = APIRouter()

# --- DTOs ---
class MobileLoginRequest(BaseModel):
    email: EmailStr
    password: str
    device_name: str  # e.g., "iPhone 13"
    device_id: str    # Unique ID for tracking

class MobileTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    user: dict

class MobileError(BaseModel):
    code: str
    message: str

# --- Endpoints ---
@router.post("/login", response_model=MobileTokenResponse)
async def mobile_login(credentials: MobileLoginRequest, db: AsyncSession = Depends(get_db)):
    # 1. Verify User
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        # Standardized Mobile Error
        raise HTTPException(
            status_code=401,
            detail={"code": "AUTH_INVALID_CREDENTIALS", "message": "E-posta veya şifre hatalı."}
        )
    
    if not user.is_active:
         raise HTTPException(
            status_code=403,
            detail={"code": "AUTH_ACCOUNT_DISABLED", "message": "Hesabınız askıya alınmıştır."}
        )
        
    # 2. Generate Tokens
    token_data = {"sub": str(user.id), "email": user.email, "role": user.role, "scope": "mobile"}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    # 3. Log Device (Simplified for MVP)
    # In real implementation, store refresh token hash in DB to allow revocation
    user.last_login = datetime.now(timezone.utc)
    await db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": 900, # 15 mins
        "user": {
            "id": str(user.id),
            "full_name": user.full_name,
            "email": user.email,
            "avatar": None # Placeholder
        }
    }
