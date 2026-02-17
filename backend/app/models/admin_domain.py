from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, EmailStr, Field


# ===============
# Dealer (users-based)
# ===============

DealerStatus = Literal["active", "suspended"]


# ===============
# Dealer Applications
# ===============

DealerApplicationStatus = Literal["pending", "approved", "rejected"]
DealerApplicationRejectReason = Literal[
    "incomplete_info",
    "not_eligible",
    "duplicate",
    "other",
]


class DealerApplicationCreate(BaseModel):
    email: EmailStr
    company_name: str
    country_code: str = Field(min_length=2, max_length=2)


class DealerApplicationDoc(BaseModel):
    id: str
    email: EmailStr
    company_name: str
    country_code: str
    status: DealerApplicationStatus
    reason: Optional[DealerApplicationRejectReason] = None
    reason_note: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None


# ===============
# Finance: Plans / Invoices / Tax rates
# ===============

InvoiceStatus = Literal["unpaid", "paid", "cancelled"]


class InvoiceDoc(BaseModel):
    id: str
    dealer_user_id: str
    country_code: str
    status: InvoiceStatus
    amount_cents: int
    currency: str
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None


class TaxRateDoc(BaseModel):
    id: str
    country_code: str
    rate_percent: float
    effective_date: str
    created_at: str
    updated_at: Optional[str] = None


class SubscriptionPlanDoc(BaseModel):
    id: str
    name: str
    country_codes: List[str] = []  # empty => global
    price_cents: int
    currency: str
    feature_flags: Dict[str, Any] = {}
    quota: Dict[str, Any] = {}
    is_active: bool = True
    created_at: str
    updated_at: Optional[str] = None


# ===============
# Ops: Reports
# ===============

ReportStatus = Literal["open", "in_review", "resolved", "dismissed"]


class ReportDoc(BaseModel):
    id: str
    listing_id: str
    reporter_user_id: Optional[str] = None
    country_code: str
    status: ReportStatus
    reason: str
    reason_note: Optional[str] = None
    handled_by_admin_id: Optional[str] = None
    status_note: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None


# ===============
# System settings (KV)
# ===============


class SystemSettingDoc(BaseModel):
    id: str
    key: str
    value: Any
    country_code: Optional[str] = None
    is_read_only: bool = False
    created_at: str
    updated_at: Optional[str] = None
