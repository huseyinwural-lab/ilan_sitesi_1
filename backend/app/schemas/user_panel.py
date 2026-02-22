from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

# --- Listing Wizard Schemas ---

class ListingDraftCreate(BaseModel):
    module: str = Field(..., description="vehicle, real_estate, etc.")
    category_id: str
    country: str = "TR"

class ListingUpdateStep1(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = "EUR"
    city: Optional[str] = None

class ListingUpdateStep2(BaseModel):
    attributes: Dict[str, str] # e.g. {"km": "50000", "year": "2020"}

class ListingUpdateStep3(BaseModel):
    images: List[str]

class ListingResponse(BaseModel):
    id: str
    title: str
    price: Optional[float]
    price_type: Optional[str] = None
    price_amount: Optional[float] = None
    hourly_rate: Optional[float] = None
    currency: Optional[str] = None
    status: str
    image_url: Optional[str]
    view_count: int
    created_at: datetime

# --- Profile Schemas ---

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    # Email change requires separate flow
