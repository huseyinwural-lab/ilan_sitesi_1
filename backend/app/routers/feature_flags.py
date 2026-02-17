from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID

from app.dependencies import get_db
from app.dependencies import get_current_user, check_permissions
from app.models.user import User
from app.models.core import FeatureFlag
from app.schemas.core import (
    FeatureFlagCreate, FeatureFlagUpdate, FeatureFlagResponse, FeatureScope
)
from app.services.audit import log_action

router = APIRouter(prefix="/feature-flags", tags=["Feature Flags"])

@router.get("/", response_model=List[FeatureFlagResponse])
async def get_feature_flags(
    scope: Optional[FeatureScope] = None,
    country: Optional[str] = None,
    enabled_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(FeatureFlag)
    
    if scope:
        query = query.where(FeatureFlag.scope == scope)
    
    if country:
        query = query.where(FeatureFlag.enabled_countries.contains([country]))
    
    if enabled_only:
        query = query.where(FeatureFlag.is_enabled == True)
    
    query = query.order_by(FeatureFlag.scope, FeatureFlag.key)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/check/{key}")
async def check_feature_flag(
    key: str,
    country: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Public endpoint to check if a feature is enabled"""
    result = await db.execute(select(FeatureFlag).where(FeatureFlag.key == key))
    flag = result.scalar_one_or_none()
    
    if not flag:
        return {"key": key, "enabled": False, "exists": False}
    
    is_enabled = flag.is_enabled
    if country and is_enabled:
        is_enabled = country in flag.enabled_countries or '*' in flag.enabled_countries
    
    return {"key": key, "enabled": is_enabled, "exists": True}

@router.get("/{flag_id}", response_model=FeatureFlagResponse)
async def get_feature_flag(
    flag_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(FeatureFlag).where(FeatureFlag.id == flag_id))
    flag = result.scalar_one_or_none()
    
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    
    return flag

@router.post("/", response_model=FeatureFlagResponse, status_code=status.HTTP_201_CREATED)
async def create_feature_flag(
    flag_data: FeatureFlagCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin"]))
):
    # Check if key exists
    result = await db.execute(select(FeatureFlag).where(FeatureFlag.key == flag_data.key))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feature flag key already exists"
        )
    
    flag = FeatureFlag(**flag_data.model_dump())
    db.add(flag)
    await db.commit()
    await db.refresh(flag)
    
    await log_action(
        db=db,
        action="CREATE",
        resource_type="feature_flag",
        resource_id=str(flag.id),
        user_id=current_user.id,
        user_email=current_user.email,
        new_values={"key": flag.key, "is_enabled": flag.is_enabled}
    )
    
    return flag

@router.patch("/{flag_id}", response_model=FeatureFlagResponse)
async def update_feature_flag(
    flag_id: UUID,
    flag_data: FeatureFlagUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))
):
    result = await db.execute(select(FeatureFlag).where(FeatureFlag.id == flag_id))
    flag = result.scalar_one_or_none()
    
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    
    old_values = {
        "is_enabled": flag.is_enabled,
        "enabled_countries": flag.enabled_countries
    }
    
    update_data = flag_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(flag, field, value)
    
    flag.version += 1
    await db.commit()
    await db.refresh(flag)
    
    await log_action(
        db=db,
        action="UPDATE",
        resource_type="feature_flag",
        resource_id=str(flag_id),
        user_id=current_user.id,
        user_email=current_user.email,
        old_values=old_values,
        new_values=update_data
    )
    
    return flag

@router.delete("/{flag_id}")
async def delete_feature_flag(
    flag_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin"]))
):
    result = await db.execute(select(FeatureFlag).where(FeatureFlag.id == flag_id))
    flag = result.scalar_one_or_none()
    
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    
    await log_action(
        db=db,
        action="DELETE",
        resource_type="feature_flag",
        resource_id=str(flag_id),
        user_id=current_user.id,
        user_email=current_user.email,
        old_values={"key": flag.key}
    )
    
    await db.delete(flag)
    await db.commit()
    
    return {"message": "Feature flag deleted successfully"}

@router.post("/{flag_id}/toggle")
async def toggle_feature_flag(
    flag_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))
):
    result = await db.execute(select(FeatureFlag).where(FeatureFlag.id == flag_id))
    flag = result.scalar_one_or_none()
    
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    
    old_state = flag.is_enabled
    flag.is_enabled = not flag.is_enabled
    flag.version += 1
    await db.commit()
    
    await log_action(
        db=db,
        action="TOGGLE",
        resource_type="feature_flag",
        resource_id=str(flag_id),
        user_id=current_user.id,
        user_email=current_user.email,
        old_values={"is_enabled": old_state},
        new_values={"is_enabled": flag.is_enabled}
    )
    
    return {"message": f"Feature flag {'enabled' if flag.is_enabled else 'disabled'}", "is_enabled": flag.is_enabled}
