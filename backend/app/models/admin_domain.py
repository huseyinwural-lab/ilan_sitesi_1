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
    plan_id: str
    amount_net: float
    tax_rate: float
    tax_amount: float
    amount_gross: float
    currency: str
    status: InvoiceStatus
    issued_at: str
    paid_at: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None


class TaxRateDoc(BaseModel):
    id: str
    country_code: str
    rate: float
    effective_date: str
    active_flag: bool = True
    created_at: str
    updated_at: Optional[str] = None


class SubscriptionPlanDoc(BaseModel):
    id: str
    name: str
    country_code: str
    price: float
    currency: str
    listing_quota: int
    showcase_quota: int
    active_flag: bool = True
    created_at: str
    updated_at: Optional[str] = None


class CountryDoc(BaseModel):
    country_code: str
    name: str
    active_flag: bool = True
    default_currency: str
    default_language: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None


class SystemSettingDoc(BaseModel):
    id: str
    key: str
    value: Any
    country_code: Optional[str] = None
    is_readonly: bool = False
    description: Optional[str] = None
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


# ===============
# Master Data (Categories / Attributes / Vehicle)
# ===============


class CategoryDoc(BaseModel):
    id: str
    parent_id: Optional[str] = None
    name: str
    slug: str
    country_code: Optional[str] = None
    active_flag: bool = True
    sort_order: int = 0
    created_at: str
    updated_at: Optional[str] = None


class AttributeDoc(BaseModel):
    id: str
    category_id: str
    name: str
    key: str
    type: str
    required_flag: bool = False
    filterable_flag: bool = False
    options: Optional[List[str]] = None
    country_code: Optional[str] = None
    active_flag: bool = True
    created_at: str
    updated_at: Optional[str] = None


class VehicleMakeDoc(BaseModel):
    id: str
    name: str
    slug: str
    country_code: str
    active_flag: bool = True
    created_at: str
    updated_at: Optional[str] = None


class VehicleModelDoc(BaseModel):
    id: str
    make_id: str
    name: str
    slug: str
    active_flag: bool = True
    created_at: str
    updated_at: Optional[str] = None


class CategoryCreatePayload(BaseModel):
    name: str
    slug: str
    parent_id: Optional[str] = None
    country_code: Optional[str] = None
    active_flag: Optional[bool] = True
    sort_order: Optional[int] = 0


class CategoryUpdatePayload(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    parent_id: Optional[str] = None
    country_code: Optional[str] = None
    active_flag: Optional[bool] = None
    sort_order: Optional[int] = None


class AttributeCreatePayload(BaseModel):
    category_id: str
    name: str
    key: str
    type: Literal["text", "number", "select", "boolean"]
    required_flag: Optional[bool] = False
    filterable_flag: Optional[bool] = False
    options: Optional[List[str]] = None
    country_code: Optional[str] = None
    active_flag: Optional[bool] = True


class AttributeUpdatePayload(BaseModel):
    category_id: Optional[str] = None
    name: Optional[str] = None
    key: Optional[str] = None
    type: Optional[Literal["text", "number", "select", "boolean"]] = None
    required_flag: Optional[bool] = None
    filterable_flag: Optional[bool] = None
    options: Optional[List[str]] = None
    country_code: Optional[str] = None
    active_flag: Optional[bool] = None


class VehicleMakeCreatePayload(BaseModel):
    name: str
    slug: str
    country_code: str
    active_flag: Optional[bool] = True


class VehicleMakeUpdatePayload(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    country_code: Optional[str] = None
    active_flag: Optional[bool] = None


class VehicleModelCreatePayload(BaseModel):
    make_id: str
    name: str
    slug: str
    active_flag: Optional[bool] = True


class VehicleModelUpdatePayload(BaseModel):
    make_id: Optional[str] = None
    name: Optional[str] = None
    slug: Optional[str] = None
    active_flag: Optional[bool] = None
