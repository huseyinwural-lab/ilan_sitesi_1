from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.dependencies import get_current_user, check_permissions
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate, UserRole
from app.services.audit import log_action

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    role: Optional[UserRole] = None,
    country: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))
):
    query = select(User)
    
    if role:
        query = query.where(User.role == role)
    
    if country:
        query = query.where(User.country_scope.contains([country]))
    
    if search:
        query = query.where(
            (User.email.ilike(f"%{search}%")) | 
            (User.full_name.ilike(f"%{search}%"))
        )
    
    query = query.offset(skip).limit(limit).order_by(User.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/count")
async def get_users_count(
    role: Optional[UserRole] = None,
    country: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))
):
    query = select(func.count(User.id))
    
    if role:
        query = query.where(User.role == role)
    
    if country:
        query = query.where(User.country_scope.contains([country]))
    
    result = await db.execute(query)
    return {"count": result.scalar()}

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin"]))
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    old_values = {
        "role": user.role,
        "is_active": user.is_active,
        "country_scope": user.country_scope
    }
    
    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    
    await log_action(
        db=db,
        action="UPDATE",
        resource_type="user",
        resource_id=str(user_id),
        user_id=current_user.id,
        user_email=current_user.email,
        old_values=old_values,
        new_values=update_data
    )
    
    return user

@router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin"]))
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await log_action(
        db=db,
        action="DELETE",
        resource_type="user",
        resource_id=str(user_id),
        user_id=current_user.id,
        user_email=current_user.email,
        old_values={"email": user.email, "role": user.role}
    )
    
    await db.delete(user)
    await db.commit()
    
    return {"message": "User deleted successfully"}

@router.post("/{user_id}/suspend")
async def suspend_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot suspend yourself")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = False
    await db.commit()
    
    await log_action(
        db=db,
        action="SUSPEND",
        resource_type="user",
        resource_id=str(user_id),
        user_id=current_user.id,
        user_email=current_user.email
    )
    
    return {"message": "User suspended successfully"}

@router.post("/{user_id}/activate")
async def activate_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = True
    await db.commit()
    
    await log_action(
        db=db,
        action="ACTIVATE",
        resource_type="user",
        resource_id=str(user_id),
        user_id=current_user.id,
        user_email=current_user.email
    )
    
    return {"message": "User activated successfully"}
