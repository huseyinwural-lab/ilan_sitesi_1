from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID

from app.dependencies import get_db
from app.dependencies import get_current_user, check_permissions
from app.models.user import User
from app.models.core import Country
from app.schemas.core import CountryCreate, CountryUpdate, CountryResponse
from app.services.audit import log_action

router = APIRouter(prefix="/countries", tags=["Countries"])

@router.get("/", response_model=List[CountryResponse])
async def get_countries(
    enabled_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Country)
    
    if enabled_only:
        query = query.where(Country.is_enabled == True)
    
    query = query.order_by(Country.code)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/public", response_model=List[CountryResponse])
async def get_public_countries(db: AsyncSession = Depends(get_db)):
    """Public endpoint for enabled countries"""
    query = select(Country).where(Country.is_enabled == True).order_by(Country.code)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{country_id}", response_model=CountryResponse)
async def get_country(
    country_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Country).where(Country.id == country_id))
    country = result.scalar_one_or_none()
    
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    return country

@router.get("/code/{code}", response_model=CountryResponse)
async def get_country_by_code(
    code: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Country).where(Country.code == code.upper()))
    country = result.scalar_one_or_none()
    
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    return country

@router.post("/", response_model=CountryResponse, status_code=status.HTTP_201_CREATED)
async def create_country(
    country_data: CountryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin"]))
):
    # Check if code exists
    result = await db.execute(select(Country).where(Country.code == country_data.code.upper()))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Country code already exists"
        )
    
    country = Country(**country_data.model_dump())
    country.code = country.code.upper()
    db.add(country)
    await db.commit()
    await db.refresh(country)
    
    await log_action(
        db=db,
        action="CREATE",
        resource_type="country",
        resource_id=str(country.id),
        user_id=current_user.id,
        user_email=current_user.email,
        new_values={"code": country.code}
    )
    
    return country

@router.patch("/{country_id}", response_model=CountryResponse)
async def update_country(
    country_id: UUID,
    country_data: CountryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin"]))
):
    result = await db.execute(select(Country).where(Country.id == country_id))
    country = result.scalar_one_or_none()
    
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    old_values = {
        "is_enabled": country.is_enabled,
        "default_currency": country.default_currency
    }
    
    update_data = country_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(country, field, value)
    
    await db.commit()
    await db.refresh(country)
    
    await log_action(
        db=db,
        action="UPDATE",
        resource_type="country",
        resource_id=str(country_id),
        user_id=current_user.id,
        user_email=current_user.email,
        old_values=old_values,
        new_values=update_data,
        country_scope=country.code
    )
    
    return country

@router.delete("/{country_id}")
async def delete_country(
    country_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin"]))
):
    result = await db.execute(select(Country).where(Country.id == country_id))
    country = result.scalar_one_or_none()
    
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    await log_action(
        db=db,
        action="DELETE",
        resource_type="country",
        resource_id=str(country_id),
        user_id=current_user.id,
        user_email=current_user.email,
        old_values={"code": country.code}
    )
    
    await db.delete(country)
    await db.commit()
    
    return {"message": "Country deleted successfully"}
