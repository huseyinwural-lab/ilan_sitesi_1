from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.notification_service import NotificationService

router = APIRouter()

class DeviceRegisterRequest(BaseModel):
    token: str
    platform: str # ios, android
    device_id: str
    is_rooted: bool = False # Security check from App

@router.post("/device/register")
async def register_device(
    data: DeviceRegisterRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = NotificationService(db)
    await service.register_device(
        user_id=current_user.id, 
        token=data.token, 
        platform=data.platform, 
        device_id=data.device_id,
        is_rooted=data.is_rooted
    )
    
    if data.is_rooted:
        # Log security warning
        # In real app: Flag user account for review
        print(f"⚠️ SECURITY WARNING: Rooted device registered for User {current_user.id}")
        
    return {"status": "registered"}

@router.post("/device/unregister")
async def unregister_device(
    data: DeviceRegisterRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = NotificationService(db)
    await service.unregister_device(data.token)
    return {"status": "unregistered"}

@router.post("/test-push")
async def test_push_self(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Debug endpoint to trigger a push to self"""
    service = NotificationService(db)
    await service.send_push(
        user_id=current_user.id,
        title="Test Bildirim 🔔",
        body="Bu bir test bildirimidir.",
        data={"type": "test"}
    )
    return {"status": "sent"}
