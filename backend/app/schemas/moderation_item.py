from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class ModerationItemBase(BaseModel):
    listing_id: UUID
    status: str = Field(..., min_length=3, max_length=20)
    reason: Optional[str] = None
    moderator_id: Optional[UUID] = None
    audit_ref: Optional[str] = None


class ModerationItemCreate(ModerationItemBase):
    pass


class ModerationItemUpdate(BaseModel):
    status: Optional[str] = None
    reason: Optional[str] = None
    moderator_id: Optional[UUID] = None
    audit_ref: Optional[str] = None


class ModerationItemRead(ModerationItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
