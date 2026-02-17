from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from typing import List

from app.dependencies import get_db
from app.models.attribute import Attribute, CategoryAttributeMap
from pydantic import BaseModel

router = APIRouter()

class AttributeFormSchema(BaseModel):
    key: str
    label: str
    type: str
    required: bool
    unit: str | None
    options: List[dict]

from app.middleware.locale_middleware import get_locale

@router.get("/form-schema/{category_id}", response_model=List[AttributeFormSchema])
async def get_attribute_schema(
    category_id: str,
    db: AsyncSession = Depends(get_db)
):
    lang = get_locale()
    
    # ... query ...
    
    # 2. Map to Schema with Localization
    schema = []
    for attr in attributes:
        options = []
        if attr.options:
            # Localize Options
            options = [{"label": opt.label.get(lang, opt.label.get("en", opt.value)), "value": opt.value} for opt in attr.options]
            
        schema.append(AttributeFormSchema(
            key=attr.key,
            # Localize Label
            label=attr.name.get(lang, attr.name.get("en", attr.key)),
            type=attr.attribute_type,
            required=attr.is_required,
            unit=attr.unit,
            options=options
        ))
        
    return schema
