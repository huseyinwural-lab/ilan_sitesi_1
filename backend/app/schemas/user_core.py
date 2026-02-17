from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str
    user_type: str
    kyc_status: str
    default_country: str
    is_phone_verified: bool
    email_verified: bool
    trust_score: float
    # badges: List[str] = [] # Calculated field

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2)
    default_country: Optional[str] = Field(None, min_length=2, max_length=2)

class SecurityStatusResponse(BaseModel):
    email_verified: bool
    phone_verified: bool
    kyc_status: str
    # last_password_change: datetime
