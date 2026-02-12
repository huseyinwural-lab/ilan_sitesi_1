"""
P1 API Functions: Dealer, Premium, Moderation, Billing
These are called from server.py with proper dependency injection
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime, timezone
from decimal import Decimal
import uuid

from app.models.dealer import DealerApplication, Dealer, DealerUser
from app.models.premium import PremiumProduct, ListingPromotion, PremiumRankingRule
from app.models.moderation import Listing, ModerationAction, ModerationRule
from app.models.billing import VatRate, Invoice, InvoiceItem
from app.models.core import AuditLog

# ==================== PYDANTIC MODELS ====================

class DealerApplicationReview(BaseModel):
    action: str
    reject_reason: Optional[str] = None

class DealerUpdate(BaseModel):
    is_active: Optional[bool] = None
    can_publish: Optional[bool] = None
    listing_limit: Optional[int] = None
    premium_limit: Optional[int] = None

class PremiumProductCreate(BaseModel):
    key: str
    name: Dict[str, str]
    description: Optional[Dict[str, str]] = None
    country: str
    currency: str
    price_net: float
    duration_days: int
    tax_category: str = "digital_service"

class PremiumProductUpdate(BaseModel):
    name: Optional[Dict[str, str]] = None
    price_net: Optional[float] = None
    duration_days: Optional[int] = None
    is_active: Optional[bool] = None

class ListingPromotionCreate(BaseModel):
    listing_id: str
    product_id: str
    start_at: datetime
    end_at: datetime
    priority_score: int = 0

class RankingRuleUpdate(BaseModel):
    premium_first: Optional[bool] = None
    weight_priority: Optional[int] = None
    weight_recency: Optional[int] = None
    is_active: Optional[bool] = None

class ModerationActionCreate(BaseModel):
    action_type: str
    reason: Optional[str] = None
    note: Optional[str] = None

class ModerationRuleUpdate(BaseModel):
    bad_words_enabled: Optional[bool] = None
    bad_words_list: Optional[List[str]] = None
    bad_words_mode: Optional[str] = None
    min_images_enabled: Optional[bool] = None
    min_images_count: Optional[int] = None
    price_sanity_enabled: Optional[bool] = None
    price_min: Optional[int] = None
    price_max: Optional[int] = None
    auto_approve_dealers: Optional[bool] = None
    is_active: Optional[bool] = None

class VatRateCreate(BaseModel):
    country: str
    rate: float
    valid_from: datetime
    valid_to: Optional[datetime] = None
    tax_type: str = "standard"
    description: Optional[str] = None

class VatRateUpdate(BaseModel):
    rate: Optional[float] = None
    valid_to: Optional[datetime] = None
    is_active: Optional[bool] = None

# ==================== HELPER ====================

async def log_action(db, action, resource_type, resource_id=None, user_id=None, user_email=None,
                    old_values=None, new_values=None, country_scope=None):
    audit = AuditLog(action=action, resource_type=resource_type, resource_id=resource_id,
                     user_id=user_id, user_email=user_email, old_values=old_values,
                     new_values=new_values, country_scope=country_scope)
    db.add(audit)
    await db.commit()

# ==================== DEALER FUNCTIONS ====================

async def get_dealer_applications(country, dealer_type, status, skip, limit, db, current_user):
    from fastapi import HTTPException
    query = select(DealerApplication)
    if country:
        query = query.where(DealerApplication.country == country.upper())
    if dealer_type:
        query = query.where(DealerApplication.dealer_type == dealer_type)
    if status:
        query = query.where(DealerApplication.status == status)
    
    query = query.order_by(desc(DealerApplication.created_at)).offset(skip).limit(limit)
    result = await db.execute(query)
    apps = result.scalars().all()
    
    return [{
        "id": str(a.id),
        "country": a.country,
        "dealer_type": a.dealer_type,
        "company_name": a.company_name,
        "contact_name": a.contact_name,
        "contact_email": a.contact_email,
        "status": a.status,
        "created_at": a.created_at.isoformat() if a.created_at else None
    } for a in apps]

async def get_dealer_application(app_id, db, current_user):
    from fastapi import HTTPException
    result = await db.execute(select(DealerApplication).where(DealerApplication.id == uuid.UUID(app_id)))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return {
        "id": str(app.id),
        "country": app.country,
        "dealer_type": app.dealer_type,
        "company_name": app.company_name,
        "vat_tax_no": app.vat_tax_no,
        "address": app.address,
        "city": app.city,
        "website": app.website,
        "logo_url": app.logo_url,
        "contact_name": app.contact_name,
        "contact_email": app.contact_email,
        "contact_phone": app.contact_phone,
        "status": app.status,
        "reject_reason": app.reject_reason,
        "created_at": app.created_at.isoformat() if app.created_at else None
    }

async def review_dealer_application(app_id, review: DealerApplicationReview, db, current_user):
    from fastapi import HTTPException
    result = await db.execute(select(DealerApplication).where(DealerApplication.id == uuid.UUID(app_id)))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if app.status != "pending":
        raise HTTPException(status_code=400, detail="Application already reviewed")
    
    if review.action == "reject" and not review.reject_reason:
        raise HTTPException(status_code=400, detail="Reject reason is required")
    
    if review.action == "approve":
        app.status = "approved"
        app.reviewed_by_id = current_user.id
        app.reviewed_at = datetime.now(timezone.utc)
        
        dealer = Dealer(
            application_id=app.id,
            country=app.country,
            dealer_type=app.dealer_type,
            company_name=app.company_name,
            vat_tax_no=app.vat_tax_no,
            logo_url=app.logo_url
        )
        db.add(dealer)
        
    elif review.action == "reject":
        app.status = "rejected"
        app.reject_reason = review.reject_reason
        app.reviewed_by_id = current_user.id
        app.reviewed_at = datetime.now(timezone.utc)
    
    await db.commit()
    await log_action(db, review.action.upper(), "dealer_application", app_id,
                    user_id=current_user.id, user_email=current_user.email,
                    new_values={"status": app.status}, country_scope=app.country)
    
    return {"message": f"Application {review.action}d", "status": app.status}

async def get_dealers(country, is_active, skip, limit, db, current_user):
    query = select(Dealer)
    if country:
        query = query.where(Dealer.country == country.upper())
    if is_active is not None:
        query = query.where(Dealer.is_active == is_active)
    
    query = query.order_by(desc(Dealer.created_at)).offset(skip).limit(limit)
    result = await db.execute(query)
    dealers = result.scalars().all()
    
    return [{
        "id": str(d.id),
        "country": d.country,
        "dealer_type": d.dealer_type,
        "company_name": d.company_name,
        "is_active": d.is_active,
        "can_publish": d.can_publish,
        "listing_limit": d.listing_limit,
        "active_listing_count": d.active_listing_count,
        "created_at": d.created_at.isoformat() if d.created_at else None
    } for d in dealers]

async def update_dealer(dealer_id, data: DealerUpdate, db, current_user):
    from fastapi import HTTPException
    result = await db.execute(select(Dealer).where(Dealer.id == uuid.UUID(dealer_id)))
    dealer = result.scalar_one_or_none()
    if not dealer:
        raise HTTPException(status_code=404, detail="Dealer not found")
    
    old_values = {"is_active": dealer.is_active, "can_publish": dealer.can_publish}
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(dealer, field, value)
    dealer.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    await log_action(db, "UPDATE", "dealer", dealer_id, user_id=current_user.id,
                    user_email=current_user.email, old_values=old_values,
                    new_values=data.model_dump(exclude_unset=True), country_scope=dealer.country)
    
    return {"id": str(dealer.id), "is_active": dealer.is_active, "can_publish": dealer.can_publish}

# ==================== PREMIUM FUNCTIONS ====================

async def get_premium_products(country, is_active, db, current_user):
    query = select(PremiumProduct)
    if country:
        query = query.where(PremiumProduct.country == country.upper())
    if is_active is not None:
        query = query.where(PremiumProduct.is_active == is_active)
    
    query = query.order_by(PremiumProduct.country, PremiumProduct.sort_order)
    result = await db.execute(query)
    products = result.scalars().all()
    
    return [{
        "id": str(p.id),
        "key": p.key,
        "name": p.name,
        "description": p.description,
        "country": p.country,
        "currency": p.currency,
        "price_net": float(p.price_net),
        "duration_days": p.duration_days,
        "tax_category": p.tax_category,
        "is_active": p.is_active
    } for p in products]

async def create_premium_product(data: PremiumProductCreate, db, current_user):
    from fastapi import HTTPException
    if data.country.upper() == "CH" and data.currency != "CHF":
        raise HTTPException(status_code=400, detail="Switzerland requires CHF currency")
    if data.country.upper() in ["DE", "FR", "AT"] and data.currency != "EUR":
        raise HTTPException(status_code=400, detail="This country requires EUR currency")
    
    result = await db.execute(select(PremiumProduct).where(
        and_(PremiumProduct.country == data.country.upper(), PremiumProduct.key == data.key)
    ))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Product key already exists for this country")
    
    product = PremiumProduct(
        key=data.key,
        name=data.name,
        description=data.description,
        country=data.country.upper(),
        currency=data.currency,
        price_net=Decimal(str(data.price_net)),
        duration_days=data.duration_days,
        tax_category=data.tax_category
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    
    await log_action(db, "CREATE", "premium_product", str(product.id),
                    user_id=current_user.id, user_email=current_user.email,
                    new_values={"key": product.key, "country": product.country})
    
    return {"id": str(product.id), "key": product.key}

async def update_premium_product(product_id, data: PremiumProductUpdate, db, current_user):
    from fastapi import HTTPException
    result = await db.execute(select(PremiumProduct).where(PremiumProduct.id == uuid.UUID(product_id)))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "price_net" and value is not None:
            setattr(product, field, Decimal(str(value)))
        else:
            setattr(product, field, value)
    product.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    await log_action(db, "UPDATE", "premium_product", product_id,
                    user_id=current_user.id, user_email=current_user.email,
                    new_values=data.model_dump(exclude_unset=True))
    
    return {"id": str(product.id), "is_active": product.is_active}

async def get_ranking_rules(db, current_user):
    result = await db.execute(select(PremiumRankingRule).order_by(PremiumRankingRule.country))
    rules = result.scalars().all()
    
    return [{
        "id": str(r.id),
        "country": r.country,
        "premium_first": r.premium_first,
        "weight_priority": r.weight_priority,
        "weight_recency": r.weight_recency,
        "is_active": r.is_active,
        "version": r.version
    } for r in rules]

async def update_ranking_rule(country, data: RankingRuleUpdate, db, current_user):
    result = await db.execute(select(PremiumRankingRule).where(PremiumRankingRule.country == country.upper()))
    rule = result.scalar_one_or_none()
    
    if not rule:
        rule = PremiumRankingRule(country=country.upper())
        db.add(rule)
    
    old_values = {"premium_first": rule.premium_first, "weight_priority": rule.weight_priority}
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    rule.version += 1
    rule.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    await log_action(db, "UPDATE", "premium_ranking_rule", country.upper(),
                    user_id=current_user.id, user_email=current_user.email,
                    old_values=old_values, new_values=data.model_dump(exclude_unset=True),
                    country_scope=country.upper())
    
    return {"country": rule.country, "version": rule.version}

class ListingPromotionCreate(BaseModel):
    listing_id: str
    product_id: str
    start_at: datetime
    end_at: datetime
    priority_score: int = 0

async def create_listing_promotion(data: ListingPromotionCreate, db, current_user):
    from fastapi import HTTPException
    # Check if listing exists
    listing_result = await db.execute(select(Listing).where(Listing.id == uuid.UUID(data.listing_id)))
    listing = listing_result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    # Check for overlap
    overlap_result = await db.execute(select(ListingPromotion).where(
        and_(
            ListingPromotion.listing_id == uuid.UUID(data.listing_id),
            ListingPromotion.is_active == True,
            or_(
                and_(ListingPromotion.start_at <= data.start_at, ListingPromotion.end_at >= data.start_at),
                and_(ListingPromotion.start_at <= data.end_at, ListingPromotion.end_at >= data.end_at)
            )
        )
    ))
    if overlap_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Active promotion already exists for this period")

    promotion = ListingPromotion(
        listing_id=uuid.UUID(data.listing_id),
        product_id=uuid.UUID(data.product_id),
        start_at=data.start_at,
        end_at=data.end_at,
        priority_score=data.priority_score,
        is_active=True
    )
    db.add(promotion)
    listing.is_premium = True
    
    await db.commit()
    await log_action(db, "CREATE", "listing_promotion", str(promotion.id),
                    user_id=current_user.id, user_email=current_user.email,
                    new_values={"listing_id": str(listing.id), "product_id": str(data.product_id)})
    
    return {"id": str(promotion.id), "status": "active"}


# ==================== MODERATION FUNCTIONS ====================

async def get_moderation_queue(country, module, status, is_dealer, is_premium, skip, limit, db, current_user):
    query = select(Listing).where(Listing.status == status)
    
    if country:
        query = query.where(Listing.country == country.upper())
    if module:
        query = query.where(Listing.module == module)
    if is_dealer is not None:
        query = query.where(Listing.is_dealer_listing == is_dealer)
    if is_premium is not None:
        query = query.where(Listing.is_premium == is_premium)
    
    query = query.order_by(Listing.created_at).offset(skip).limit(limit)
    result = await db.execute(query)
    listings = result.scalars().all()
    
    return [{
        "id": str(l.id),
        "title": l.title,
        "module": l.module,
        "country": l.country,
        "city": l.city,
        "price": l.price,
        "currency": l.currency,
        "is_dealer_listing": l.is_dealer_listing,
        "is_premium": l.is_premium,
        "image_count": l.image_count,
        "status": l.status,
        "created_at": l.created_at.isoformat() if l.created_at else None
    } for l in listings]

async def get_moderation_queue_count(country, db, current_user):
    query = select(func.count(Listing.id)).where(Listing.status == "pending")
    if country:
        query = query.where(Listing.country == country.upper())
    
    result = await db.execute(query)
    return {"count": result.scalar()}

async def get_listing_detail(listing_id, db, current_user):
    from fastapi import HTTPException
    result = await db.execute(select(Listing).where(Listing.id == uuid.UUID(listing_id)))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    actions_result = await db.execute(
        select(ModerationAction)
        .where(ModerationAction.listing_id == listing.id)
        .order_by(desc(ModerationAction.created_at))
    )
    actions = actions_result.scalars().all()
    
    return {
        "id": str(listing.id),
        "title": listing.title,
        "description": listing.description,
        "module": listing.module,
        "category_id": str(listing.category_id) if listing.category_id else None,
        "country": listing.country,
        "city": listing.city,
        "price": listing.price,
        "currency": listing.currency,
        "user_id": str(listing.user_id),
        "dealer_id": str(listing.dealer_id) if listing.dealer_id else None,
        "is_dealer_listing": listing.is_dealer_listing,
        "images": listing.images,
        "attributes": listing.attributes,
        "status": listing.status,
        "is_premium": listing.is_premium,
        "created_at": listing.created_at.isoformat() if listing.created_at else None,
        "moderation_history": [{
            "id": str(a.id),
            "action_type": a.action_type,
            "reason": a.reason,
            "note": a.note,
            "actor_email": a.actor_email,
            "created_at": a.created_at.isoformat() if a.created_at else None
        } for a in actions]
    }

async def moderate_listing(listing_id, action: ModerationActionCreate, db, current_user):
    from fastapi import HTTPException
    result = await db.execute(select(Listing).where(Listing.id == uuid.UUID(listing_id)))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    if action.action_type == "reject" and not action.reason:
        raise HTTPException(status_code=400, detail="Reject reason is required")
    
    old_status = listing.status
    
    if action.action_type == "approve":
        listing.status = "active"
        listing.published_at = datetime.now(timezone.utc)
    elif action.action_type == "reject":
        listing.status = "rejected"
    elif action.action_type == "suspend":
        listing.status = "suspended"
    
    listing.updated_at = datetime.now(timezone.utc)
    
    mod_action = ModerationAction(
        listing_id=listing.id,
        action_type=action.action_type,
        reason=action.reason,
        note=action.note,
        actor_admin_id=current_user.id,
        actor_email=current_user.email
    )
    db.add(mod_action)
    
    await db.commit()
    await log_action(db, action.action_type.upper(), "listing", listing_id,
                    user_id=current_user.id, user_email=current_user.email,
                    old_values={"status": old_status}, new_values={"status": listing.status},
                    country_scope=listing.country)
    
    return {"message": f"Listing {action.action_type}d", "status": listing.status}

async def get_moderation_rules(db, current_user):
    result = await db.execute(select(ModerationRule).order_by(ModerationRule.country))
    rules = result.scalars().all()
    
    return [{
        "id": str(r.id),
        "country": r.country,
        "bad_words_enabled": r.bad_words_enabled,
        "bad_words_list": r.bad_words_list,
        "bad_words_mode": r.bad_words_mode,
        "min_images_enabled": r.min_images_enabled,
        "min_images_count": r.min_images_count,
        "price_sanity_enabled": r.price_sanity_enabled,
        "price_min": r.price_min,
        "price_max": r.price_max,
        "auto_approve_dealers": r.auto_approve_dealers,
        "is_active": r.is_active
    } for r in rules]

async def update_moderation_rule(country, data: ModerationRuleUpdate, db, current_user):
    result = await db.execute(select(ModerationRule).where(ModerationRule.country == country.upper()))
    rule = result.scalar_one_or_none()
    
    if not rule:
        rule = ModerationRule(country=country.upper())
        db.add(rule)
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    rule.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    await log_action(db, "UPDATE", "moderation_rule", country.upper(),
                    user_id=current_user.id, user_email=current_user.email,
                    new_values=data.model_dump(exclude_unset=True), country_scope=country.upper())
    
    return {"country": rule.country, "is_active": rule.is_active}

# ==================== BILLING FUNCTIONS ====================

async def get_vat_rates(country, is_active, db, current_user):
    query = select(VatRate)
    if country:
        query = query.where(VatRate.country == country.upper())
    if is_active is not None:
        query = query.where(VatRate.is_active == is_active)
    
    query = query.order_by(VatRate.country, desc(VatRate.valid_from))
    result = await db.execute(query)
    rates = result.scalars().all()
    
    return [{
        "id": str(r.id),
        "country": r.country,
        "rate": float(r.rate),
        "valid_from": r.valid_from.isoformat() if r.valid_from else None,
        "valid_to": r.valid_to.isoformat() if r.valid_to else None,
        "tax_type": r.tax_type,
        "description": r.description,
        "is_active": r.is_active
    } for r in rates]

async def create_vat_rate(data: VatRateCreate, db, current_user):
    from fastapi import HTTPException
    result = await db.execute(select(VatRate).where(
        and_(
            VatRate.country == data.country.upper(),
            VatRate.is_active == True,
            or_(
                VatRate.valid_to == None,
                VatRate.valid_to >= data.valid_from
            )
        )
    ))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Overlapping VAT rate exists for this country")
    
    rate = VatRate(
        country=data.country.upper(),
        rate=Decimal(str(data.rate)),
        valid_from=data.valid_from,
        valid_to=data.valid_to,
        tax_type=data.tax_type,
        description=data.description
    )
    db.add(rate)
    await db.commit()
    await db.refresh(rate)
    
    await log_action(db, "CREATE", "vat_rate", str(rate.id),
                    user_id=current_user.id, user_email=current_user.email,
                    new_values={"country": rate.country, "rate": float(rate.rate)},
                    country_scope=rate.country)
    
    return {"id": str(rate.id), "country": rate.country, "rate": float(rate.rate)}

async def update_vat_rate(rate_id, data: VatRateUpdate, db, current_user):
    from fastapi import HTTPException
    result = await db.execute(select(VatRate).where(VatRate.id == uuid.UUID(rate_id)))
    rate = result.scalar_one_or_none()
    if not rate:
        raise HTTPException(status_code=404, detail="VAT rate not found")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "rate" and value is not None:
            setattr(rate, field, Decimal(str(value)))
        else:
            setattr(rate, field, value)
    rate.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    await log_action(db, "UPDATE", "vat_rate", rate_id,
                    user_id=current_user.id, user_email=current_user.email,
                    new_values=data.model_dump(exclude_unset=True), country_scope=rate.country)
    
    return {"id": str(rate.id), "is_active": rate.is_active}

async def get_invoices(country, status, customer_type, skip, limit, db, current_user):
    query = select(Invoice)
    if country:
        query = query.where(Invoice.country == country.upper())
    if status:
        query = query.where(Invoice.status == status)
    if customer_type:
        query = query.where(Invoice.customer_type == customer_type)
    
    query = query.order_by(desc(Invoice.issued_at)).offset(skip).limit(limit)
    result = await db.execute(query)
    invoices = result.scalars().all()
    
    return [{
        "id": str(i.id),
        "invoice_no": i.invoice_no,
        "country": i.country,
        "currency": i.currency,
        "customer_type": i.customer_type,
        "customer_name": i.customer_name,
        "status": i.status,
        "net_total": float(i.net_total),
        "tax_total": float(i.tax_total),
        "gross_total": float(i.gross_total),
        "issued_at": i.issued_at.isoformat() if i.issued_at else None
    } for i in invoices]

async def get_invoice_detail(invoice_id, db, current_user):
    from fastapi import HTTPException
    result = await db.execute(select(Invoice).where(Invoice.id == uuid.UUID(invoice_id)))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return {
        "id": str(invoice.id),
        "invoice_no": invoice.invoice_no,
        "country": invoice.country,
        "currency": invoice.currency,
        "customer_type": invoice.customer_type,
        "customer_ref_id": str(invoice.customer_ref_id),
        "customer_name": invoice.customer_name,
        "customer_email": invoice.customer_email,
        "customer_address": invoice.customer_address,
        "customer_vat_no": invoice.customer_vat_no,
        "status": invoice.status,
        "net_total": float(invoice.net_total),
        "tax_total": float(invoice.tax_total),
        "gross_total": float(invoice.gross_total),
        "tax_rate_snapshot": float(invoice.tax_rate_snapshot),
        "issued_at": invoice.issued_at.isoformat() if invoice.issued_at else None,
        "due_at": invoice.due_at.isoformat() if invoice.due_at else None,
        "paid_at": invoice.paid_at.isoformat() if invoice.paid_at else None,
        "notes": invoice.notes,
        "items": [{
            "id": str(item.id),
            "item_type": item.item_type,
            "description": item.description,
            "quantity": item.quantity,
            "unit_price_net": float(item.unit_price_net),
            "line_net": float(item.line_net),
            "line_tax": float(item.line_tax),
            "line_gross": float(item.line_gross)
        } for item in invoice.items]
    }


class InvoiceCreate(BaseModel):
    country: str
    customer_type: str  # 'B2C' or 'B2B'
    customer_name: str
    customer_email: str
    items: List[dict]

async def create_invoice(data: InvoiceCreate, db, current_user):
    from fastapi import HTTPException
    
    year = datetime.now().year
    prefix = f"INV-{data.country}-{year}-"
    
    query = select(Invoice.invoice_no).where(Invoice.invoice_no.like(f"{prefix}%")).order_by(desc(Invoice.invoice_no)).limit(1)
    result = await db.execute(query)
    last_no = result.scalar_one_or_none()
    
    if last_no:
        seq = int(last_no.split('-')[-1]) + 1
    else:
        seq = 1
        
    invoice_no = f"{prefix}{seq:06d}"
    
    exists = await db.execute(select(Invoice).where(Invoice.invoice_no == invoice_no))
    if exists.scalar_one_or_none():
         raise HTTPException(status_code=409, detail="Invoice number collision, please retry")

    net_total = 0
    tax_total = 0
    
    vat_query = select(VatRate).where(and_(VatRate.country == data.country, VatRate.is_active == True))
    vat_result = await db.execute(vat_query)
    vat = vat_result.scalars().first()
    tax_rate = vat.rate if vat else Decimal(0)
    
    invoice = Invoice(
        invoice_no=invoice_no,
        country=data.country,
        currency="EUR",
        customer_type=data.customer_type,
        customer_name=data.customer_name,
        customer_email=data.customer_email,
        status="issued",
        issued_at=datetime.now(timezone.utc),
        tax_rate_snapshot=tax_rate
    )
    db.add(invoice)
    await db.flush()
    
    for item in data.items:
        line_net = Decimal(str(item['unit_price'])) * item['quantity']
        line_tax = line_net * (tax_rate / 100)
        inv_item = InvoiceItem(
            invoice_id=invoice.id,
            item_type="custom",
            description=item['description'],
            quantity=item['quantity'],
            unit_price_net=item['unit_price'],
            line_net=line_net,
            line_tax=line_tax,
            line_gross=line_net + line_tax
        )
        db.add(inv_item)
        net_total += line_net
        tax_total += line_tax
        
    invoice.net_total = net_total
    invoice.tax_total = tax_total
    invoice.gross_total = net_total + tax_total
    
    await db.commit()
    return {"id": str(invoice.id), "invoice_no": invoice_no}
