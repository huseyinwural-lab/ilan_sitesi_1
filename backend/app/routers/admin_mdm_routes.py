
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from app.dependencies import get_db, check_permissions
from app.models.user import User
from app.models.attribute import Attribute, AttributeOption, CategoryAttributeMap
from app.models.vehicle_mdm import VehicleMake, VehicleModel
from app.models.core import AuditLog
from typing import List, Optional, Dict
from pydantic import BaseModel
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/master-data", tags=["admin-master-data"])

# Pydantic Models for Requests
class AttributeUpdate(BaseModel):
    name: Optional[Dict[str, str]] = None
    is_active: Optional[bool] = None
    is_filterable: Optional[bool] = None
    display_order: Optional[int] = None

class OptionUpdate(BaseModel):
    label: Optional[Dict[str, str]] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

class BindingCreate(BaseModel):
    attribute_id: str
    is_required_override: Optional[bool] = None
    inherit_to_children: bool = True

class VehicleMakeUpdate(BaseModel):
    label_tr: Optional[str] = None
    label_de: Optional[str] = None
    label_fr: Optional[str] = None
    is_active: Optional[bool] = None

class VehicleModelUpdate(BaseModel):
    label_tr: Optional[str] = None
    label_de: Optional[str] = None
    label_fr: Optional[str] = None
    is_active: Optional[bool] = None

async def log_md_action(db, action, res_type, res_id, user, old, new):
    db.add(AuditLog(
        action=action, resource_type=res_type, resource_id=str(res_id),
        user_id=user.id, user_email=user.email,
        old_values=old, new_values=new
    ))

# 1. Attributes
@router.get("/attributes")
async def list_attributes(
    q: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))
):
    query = select(Attribute).order_by(Attribute.key)
    if q: query = query.where(Attribute.key.ilike(f"%{q}%")) # Simple key search
    if is_active is not None: query = query.where(Attribute.is_active == is_active)
    
    res = await db.execute(query)
    return res.scalars().all()

@router.patch("/attributes/{id}")
async def update_attribute(
    id: str,
    data: AttributeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))
):
    res = await db.execute(select(Attribute).where(Attribute.id == uuid.UUID(id)))
    attr = res.scalar_one_or_none()
    if not attr: raise HTTPException(404, "Attribute not found")

    # RBAC: Country Admin can only update Labels (name)
    if current_user.role != "super_admin":
        if data.is_active is not None or data.is_filterable is not None:
            raise HTTPException(403, "Only Super Admin can change configuration")

    old_vals = {"name": attr.name, "is_active": attr.is_active, "is_filterable": attr.is_filterable}
    
    if data.name: attr.name = data.name
    if data.is_active is not None: attr.is_active = data.is_active
    if data.is_filterable is not None: attr.is_filterable = data.is_filterable
    if data.display_order is not None: attr.display_order = data.display_order
    
    await log_md_action(db, "ADMIN_UPDATE_MASTERDATA", "attribute", id, current_user, old_vals, data.model_dump(exclude_unset=True))
    await db.commit()
    return attr

# 2. Options
@router.get("/attributes/{id}/options")
async def list_options(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))
):
    res = await db.execute(select(AttributeOption).where(AttributeOption.attribute_id == uuid.UUID(id)).order_by(AttributeOption.sort_order))
    return res.scalars().all()

@router.patch("/options/{id}")
async def update_option(
    id: str,
    data: OptionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))
):
    res = await db.execute(select(AttributeOption).where(AttributeOption.id == uuid.UUID(id)))
    opt = res.scalar_one_or_none()
    if not opt: raise HTTPException(404, "Option not found")

    # RBAC: Country Admin can only update Labels
    if current_user.role != "super_admin":
        if data.is_active is not None:
             raise HTTPException(403, "Only Super Admin can deactivate options")

    old_vals = {"label": opt.label, "is_active": opt.is_active}
    
    if data.label: opt.label = data.label
    if data.is_active is not None: opt.is_active = data.is_active
    if data.sort_order is not None: opt.sort_order = data.sort_order
    
    await log_md_action(db, "ADMIN_UPDATE_MASTERDATA", "option", id, current_user, old_vals, data.model_dump(exclude_unset=True))
    await db.commit()
    return opt

# 3. Category Binding
@router.get("/categories/{id}/attributes")
async def list_bindings(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))
):
    # Fetch direct bindings
    stmt = select(CategoryAttributeMap).where(CategoryAttributeMap.category_id == uuid.UUID(id))
    # Ideally we join with Attribute to show details, but frontend can fetch attr list separately or we expand.
    # For MVP, return binding objects.
    res = await db.execute(stmt)
    return res.scalars().all()

@router.post("/categories/{id}/bind")
async def bind_attribute(
    id: str,
    data: BindingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin"]))
):
    # Check if exists
    exists = await db.execute(select(CategoryAttributeMap).where(
        CategoryAttributeMap.category_id == uuid.UUID(id),
        CategoryAttributeMap.attribute_id == uuid.UUID(data.attribute_id)
    ))
    if exists.scalar_one_or_none():
        raise HTTPException(400, "Attribute already bound")
        
    binding = CategoryAttributeMap(
        category_id=uuid.UUID(id),
        attribute_id=uuid.UUID(data.attribute_id),
        is_required_override=data.is_required_override,
        inherit_to_children=data.inherit_to_children
    )
    db.add(binding)
    await log_md_action(db, "ADMIN_BIND_ATTRIBUTE", "category", id, current_user, None, data.model_dump())
    await db.commit()
    return binding

@router.delete("/categories/{id}/bind/{attr_id}")
async def unbind_attribute(
    id: str,
    attr_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin"]))
):
    res = await db.execute(select(CategoryAttributeMap).where(
        CategoryAttributeMap.category_id == uuid.UUID(id),
        CategoryAttributeMap.attribute_id == uuid.UUID(attr_id)
    ))
    binding = res.scalar_one_or_none()
    if not binding: raise HTTPException(404, "Binding not found")
    
    await db.delete(binding)
    await log_md_action(db, "ADMIN_UNBIND_ATTRIBUTE", "category", id, current_user, {"attr_id": attr_id}, None)


# ============================================
# 4. VEHICLE MAKES
# ============================================

@router.get("/vehicle-makes")
async def list_vehicle_makes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))
):
    query = select(VehicleMake).order_by(VehicleMake.name)
    res = await db.execute(query)
    makes = res.scalars().all()
    
    # Transform to include label_tr, label_de, label_fr from name field
    result = []
    for make in makes:
        result.append({
            "id": str(make.id),
            "slug": make.slug,
            "label_tr": make.name,  # Using name as TR label for now
            "label_de": make.name,
            "label_fr": make.name,
            "is_active": make.is_active,
            "created_at": make.created_at.isoformat() if make.created_at else None
        })
    return result

@router.get("/vehicle-makes/{id}")
async def get_vehicle_make(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))
):
    res = await db.execute(select(VehicleMake).where(VehicleMake.id == uuid.UUID(id)))
    make = res.scalar_one_or_none()
    if not make:
        raise HTTPException(404, "Make not found")
    
    return {
        "id": str(make.id),
        "slug": make.slug,
        "label_tr": make.name,
        "label_de": make.name,
        "label_fr": make.name,
        "is_active": make.is_active,
        "created_at": make.created_at.isoformat() if make.created_at else None
    }

@router.patch("/vehicle-makes/{id}")
async def update_vehicle_make(
    id: str,
    data: VehicleMakeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))
):
    res = await db.execute(select(VehicleMake).where(VehicleMake.id == uuid.UUID(id)))
    make = res.scalar_one_or_none()
    if not make:
        raise HTTPException(404, "Make not found")

    # RBAC: Country Admin can only update Labels
    if current_user.role != "super_admin":
        if data.is_active is not None:
            raise HTTPException(403, "Only Super Admin can change activation status")

    old_vals = {"name": make.name, "is_active": make.is_active}
    
    # Update name if any label provided (using TR as primary)
    if data.label_tr:
        make.name = data.label_tr
    if data.is_active is not None:
        make.is_active = data.is_active
    
    await log_md_action(db, "ADMIN_UPDATE_MASTERDATA", "vehicle_make", id, current_user, old_vals, data.model_dump(exclude_unset=True))
    await db.commit()
    
    return {
        "id": str(make.id),
        "slug": make.slug,
        "label_tr": make.name,
        "label_de": make.name,
        "label_fr": make.name,
        "is_active": make.is_active
    }

# ============================================
# 5. VEHICLE MODELS
# ============================================

@router.get("/vehicle-makes/{make_id}/models")
async def list_vehicle_models(
    make_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))
):
    # Verify make exists
    make_res = await db.execute(select(VehicleMake).where(VehicleMake.id == uuid.UUID(make_id)))
    if not make_res.scalar_one_or_none():
        raise HTTPException(404, "Make not found")
    
    query = select(VehicleModel).where(VehicleModel.make_id == uuid.UUID(make_id)).order_by(VehicleModel.name)
    res = await db.execute(query)
    models = res.scalars().all()
    
    result = []
    for model in models:
        result.append({
            "id": str(model.id),
            "make_id": str(model.make_id),
            "slug": model.slug,
            "label_tr": model.name,
            "label_de": model.name,
            "label_fr": model.name,
            "vehicle_type": model.vehicle_type,
            "is_active": model.is_active,
            "created_at": model.created_at.isoformat() if model.created_at else None
        })
    return result

@router.patch("/vehicle-models/{id}")
async def update_vehicle_model(
    id: str,
    data: VehicleModelUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))
):
    res = await db.execute(select(VehicleModel).where(VehicleModel.id == uuid.UUID(id)))
    model = res.scalar_one_or_none()
    if not model:
        raise HTTPException(404, "Model not found")

    # RBAC: Country Admin can only update Labels
    if current_user.role != "super_admin":
        if data.is_active is not None:
            raise HTTPException(403, "Only Super Admin can change activation status")

    old_vals = {"name": model.name, "is_active": model.is_active}
    
    if data.label_tr:
        model.name = data.label_tr
    if data.is_active is not None:
        model.is_active = data.is_active
    
    await log_md_action(db, "ADMIN_UPDATE_MASTERDATA", "vehicle_model", id, current_user, old_vals, data.model_dump(exclude_unset=True))
    await db.commit()
    
    return {
        "id": str(model.id),
        "make_id": str(model.make_id),
        "slug": model.slug,
        "label_tr": model.name,
        "label_de": model.name,
        "label_fr": model.name,
        "is_active": model.is_active
    }

    await db.commit()
    return {"status": "deleted"}
