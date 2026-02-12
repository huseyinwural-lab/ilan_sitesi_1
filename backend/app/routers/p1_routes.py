"""
P1 API Routes: Dealer, Premium, Moderation, Billing
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import uuid

from app.models.dealer import DealerApplication, Dealer, DealerUser
from app.models.premium import PremiumProduct, ListingPromotion, PremiumRankingRule
from app.models.moderation import Listing, ModerationAction, ModerationRule
from app.models.billing import VatRate, Invoice, InvoiceItem
from app.models.core import AuditLog

router = APIRouter()

# ==================== PYDANTIC MODELS ====================

# Dealer
class DealerApplicationCreate(BaseModel):
    country: str
    dealer_type: str
    company_name: str
    vat_tax_no: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    website: Optional[str] = None
    contact_name: str
    contact_email: str
    contact_phone: Optional[str] = None

class DealerApplicationReview(BaseModel):
    action: str  # approve, reject
    reject_reason: Optional[str] = None

class DealerUpdate(BaseModel):
    is_active: Optional[bool] = None
    can_publish: Optional[bool] = None
    listing_limit: Optional[int] = None
    premium_limit: Optional[int] = None

# Premium
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

# Moderation
class ModerationActionCreate(BaseModel):
    action_type: str  # approve, reject, suspend
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

# Billing
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

# ==================== HELPER FUNCTIONS ====================

async def log_action(db: AsyncSession, action: str, resource_type: str, resource_id: Optional[str] = None,
                    user_id: Optional[uuid.UUID] = None, user_email: Optional[str] = None,
                    old_values: Optional[dict] = None, new_values: Optional[dict] = None,
                    country_scope: Optional[str] = None):
    audit = AuditLog(action=action, resource_type=resource_type, resource_id=resource_id,
                     user_id=user_id, user_email=user_email, old_values=old_values,
                     new_values=new_values, country_scope=country_scope)
    db.add(audit)
    await db.commit()

# ==================== DEALER ROUTES ====================

@router.get("/dealer-applications")
async def get_dealer_applications(
    country: Optional[str] = None,
    dealer_type: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = None,
    current_user = None
):
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

@router.get("/dealer-applications/{app_id}")
async def get_dealer_application(app_id: str, db: AsyncSession = None, current_user = None):
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

@router.post("/dealer-applications/{app_id}/review")
async def review_dealer_application(app_id: str, review: DealerApplicationReview, db: AsyncSession = None, current_user = None):
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
        
        # Create Dealer entity
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

@router.get("/dealers")
async def get_dealers(
    country: Optional[str] = None,
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = None,
    current_user = None
):
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

@router.patch("/dealers/{dealer_id}")
async def update_dealer(dealer_id: str, data: DealerUpdate, db: AsyncSession = None, current_user = None):
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

# ==================== PREMIUM ROUTES ====================

@router.get("/premium-products")
async def get_premium_products(
    country: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = None,
    current_user = None
):
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

@router.post("/premium-products", status_code=201)
async def create_premium_product(data: PremiumProductCreate, db: AsyncSession = None, current_user = None):
    # Enforce CH = CHF
    if data.country.upper() == "CH" and data.currency != "CHF":
        raise HTTPException(status_code=400, detail="Switzerland requires CHF currency")
    if data.country.upper() in ["DE", "FR", "AT"] and data.currency != "EUR":
        raise HTTPException(status_code=400, detail="This country requires EUR currency")
    
    # Check unique key per country
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

@router.patch("/premium-products/{product_id}")
async def update_premium_product(product_id: str, data: PremiumProductUpdate, db: AsyncSession = None, current_user = None):
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

@router.get("/listing-promotions")
async def get_listing_promotions(
    listing_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = None,
    current_user = None
):
    query = select(ListingPromotion)
    if listing_id:
        query = query.where(ListingPromotion.listing_id == listing_id)
    if is_active is not None:
        query = query.where(ListingPromotion.is_active == is_active)
    
    query = query.order_by(desc(ListingPromotion.created_at)).offset(skip).limit(limit)
    result = await db.execute(query)
    promos = result.scalars().all()
    
    return [{
        "id": str(p.id),
        "listing_id": p.listing_id,
        "product_id": str(p.product_id),
        "start_at": p.start_at.isoformat() if p.start_at else None,
        "end_at": p.end_at.isoformat() if p.end_at else None,
        "priority_score": p.priority_score,
        "is_active": p.is_active
    } for p in promos]

@router.post("/listing-promotions", status_code=201)
async def create_listing_promotion(data: ListingPromotionCreate, db: AsyncSession = None, current_user = None):
    # Check for overlapping promotions
    result = await db.execute(select(ListingPromotion).where(
        and_(
            ListingPromotion.listing_id == data.listing_id,
            ListingPromotion.product_id == uuid.UUID(data.product_id),
            ListingPromotion.is_active == True,
            or_(
                and_(ListingPromotion.start_at <= data.start_at, ListingPromotion.end_at >= data.start_at),
                and_(ListingPromotion.start_at <= data.end_at, ListingPromotion.end_at >= data.end_at)
            )
        )
    ))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Overlapping promotion exists for this listing and product")
    
    promo = ListingPromotion(
        listing_id=data.listing_id,
        product_id=uuid.UUID(data.product_id),
        start_at=data.start_at,
        end_at=data.end_at,
        priority_score=data.priority_score,
        created_by_admin_id=current_user.id
    )
    db.add(promo)
    await db.commit()
    await db.refresh(promo)
    
    await log_action(db, "CREATE", "listing_promotion", str(promo.id),
                    user_id=current_user.id, user_email=current_user.email,
                    new_values={"listing_id": promo.listing_id})
    
    return {"id": str(promo.id)}

@router.post("/listing-promotions/{promo_id}/deactivate")
async def deactivate_promotion(promo_id: str, db: AsyncSession = None, current_user = None):
    result = await db.execute(select(ListingPromotion).where(ListingPromotion.id == uuid.UUID(promo_id)))
    promo = result.scalar_one_or_none()
    if not promo:
        raise HTTPException(status_code=404, detail="Promotion not found")
    
    promo.is_active = False
    promo.end_at = datetime.now(timezone.utc)
    await db.commit()
    
    await log_action(db, "DEACTIVATE", "listing_promotion", promo_id,
                    user_id=current_user.id, user_email=current_user.email)
    
    return {"message": "Promotion deactivated"}

@router.get("/premium-ranking-rules")
async def get_ranking_rules(db: AsyncSession = None, current_user = None):
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

@router.patch("/premium-ranking-rules/{country}")
async def update_ranking_rule(country: str, data: RankingRuleUpdate, db: AsyncSession = None, current_user = None):
    result = await db.execute(select(PremiumRankingRule).where(PremiumRankingRule.country == country.upper()))
    rule = result.scalar_one_or_none()
    
    if not rule:
        # Create if not exists
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

# ==================== MODERATION ROUTES ====================

@router.get("/moderation/queue")
async def get_moderation_queue(
    country: Optional[str] = None,
    module: Optional[str] = None,
    status: str = "pending",
    is_dealer: Optional[bool] = None,
    is_premium: Optional[bool] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = None,
    current_user = None
):
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

@router.get("/moderation/queue/count")
async def get_moderation_queue_count(
    country: Optional[str] = None,
    db: AsyncSession = None,
    current_user = None
):
    query = select(func.count(Listing.id)).where(Listing.status == "pending")
    if country:
        query = query.where(Listing.country == country.upper())
    
    result = await db.execute(query)
    return {"count": result.scalar()}

@router.get("/moderation/listings/{listing_id}")
async def get_listing_detail(listing_id: str, db: AsyncSession = None, current_user = None):
    result = await db.execute(select(Listing).where(Listing.id == uuid.UUID(listing_id)))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    # Get moderation history
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

@router.post("/moderation/listings/{listing_id}/action")
async def moderate_listing(listing_id: str, action: ModerationActionCreate, db: AsyncSession = None, current_user = None):
    result = await db.execute(select(Listing).where(Listing.id == uuid.UUID(listing_id)))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    # Validate reject requires reason
    if action.action_type == "reject" and not action.reason:
        raise HTTPException(status_code=400, detail="Reject reason is required")
    
    old_status = listing.status
    
    # Update listing status
    if action.action_type == "approve":
        listing.status = "active"
        listing.published_at = datetime.now(timezone.utc)
    elif action.action_type == "reject":
        listing.status = "rejected"
    elif action.action_type == "suspend":
        listing.status = "suspended"
    
    listing.updated_at = datetime.now(timezone.utc)
    
    # Create moderation action record
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

@router.get("/moderation/rules")
async def get_moderation_rules(db: AsyncSession = None, current_user = None):
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

@router.patch("/moderation/rules/{country}")
async def update_moderation_rule(country: str, data: ModerationRuleUpdate, db: AsyncSession = None, current_user = None):
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

# ==================== BILLING ROUTES ====================

@router.get("/vat-rates")
async def get_vat_rates(country: Optional[str] = None, is_active: Optional[bool] = None, db: AsyncSession = None, current_user = None):
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

@router.post("/vat-rates", status_code=201)
async def create_vat_rate(data: VatRateCreate, db: AsyncSession = None, current_user = None):
    # Check for overlapping rates
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

@router.patch("/vat-rates/{rate_id}")
async def update_vat_rate(rate_id: str, data: VatRateUpdate, db: AsyncSession = None, current_user = None):
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

@router.get("/invoices")
async def get_invoices(
    country: Optional[str] = None,
    status: Optional[str] = None,
    customer_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = None,
    current_user = None
):
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

@router.get("/invoices/{invoice_id}")
async def get_invoice_detail(invoice_id: str, db: AsyncSession = None, current_user = None):
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

@router.get("/invoices/export")
async def export_invoices(
    country: Optional[str] = None,
    status: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    db: AsyncSession = None,
    current_user = None
):
    query = select(Invoice)
    if country:
        query = query.where(Invoice.country == country.upper())
    if status:
        query = query.where(Invoice.status == status)
    if from_date:
        query = query.where(Invoice.issued_at >= from_date)
    if to_date:
        query = query.where(Invoice.issued_at <= to_date)
    
    query = query.order_by(Invoice.issued_at)
    result = await db.execute(query)
    invoices = result.scalars().all()
    
    # Return JSON export (CSV/PDF in V2)
    return {
        "export_type": "json",
        "count": len(invoices),
        "data": [{
            "invoice_no": i.invoice_no,
            "country": i.country,
            "currency": i.currency,
            "customer_name": i.customer_name,
            "customer_vat_no": i.customer_vat_no,
            "status": i.status,
            "net_total": float(i.net_total),
            "tax_total": float(i.tax_total),
            "gross_total": float(i.gross_total),
            "tax_rate": float(i.tax_rate_snapshot),
            "issued_at": i.issued_at.isoformat() if i.issued_at else None
        } for i in invoices]
    }
