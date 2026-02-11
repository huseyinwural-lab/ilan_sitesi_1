from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict
from datetime import datetime
from uuid import UUID
from enum import Enum

# Translation helper type
TranslatedText = Dict[str, str]  # {"tr": "...", "de": "...", "fr": "..."}

class FeatureScope(str, Enum):
    MODULE = "module"
    FEATURE = "feature"

class FeatureFlagBase(BaseModel):
    key: str = Field(..., pattern=r'^[a-z_]+$', min_length=2, max_length=100)
    name: TranslatedText
    description: Optional[TranslatedText] = None
    scope: FeatureScope = FeatureScope.FEATURE
    enabled_countries: List[str] = Field(default_factory=list)
    is_enabled: bool = False
    depends_on: List[str] = Field(default_factory=list)

class FeatureFlagCreate(FeatureFlagBase):
    pass

class FeatureFlagUpdate(BaseModel):
    name: Optional[TranslatedText] = None
    description: Optional[TranslatedText] = None
    enabled_countries: Optional[List[str]] = None
    is_enabled: Optional[bool] = None
    depends_on: Optional[List[str]] = None

class FeatureFlagResponse(FeatureFlagBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    version: int
    created_at: datetime
    updated_at: datetime

class CountryBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=5)
    name: TranslatedText
    default_currency: str = Field(..., min_length=3, max_length=5)
    default_language: str = "de"
    area_unit: str = "m²"
    distance_unit: str = "km"
    weight_unit: str = "kg"
    date_format: str = "DD.MM.YYYY"
    number_format: str = "1.234,56"
    support_email: Optional[str] = None
    support_phone: Optional[str] = None
    is_enabled: bool = True

class CountryCreate(CountryBase):
    pass

class CountryUpdate(BaseModel):
    name: Optional[TranslatedText] = None
    default_currency: Optional[str] = None
    default_language: Optional[str] = None
    area_unit: Optional[str] = None
    distance_unit: Optional[str] = None
    weight_unit: Optional[str] = None
    date_format: Optional[str] = None
    number_format: Optional[str] = None
    support_email: Optional[str] = None
    support_phone: Optional[str] = None
    is_enabled: Optional[bool] = None

class CountryResponse(CountryBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    created_at: datetime
    updated_at: datetime

class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_id: Optional[UUID] = None
    user_email: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    old_values: Optional[dict] = None
    new_values: Optional[dict] = None
    metadata: Optional[dict] = None
    ip_address: Optional[str] = None
    country_scope: Optional[str] = None
    is_pii_scrubbed: bool
    created_at: datetime
