
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.dependencies import get_db
from app.models.moderation import Listing
from app.models.user import User
from app.models.dealer import Dealer
from app.models.attribute import ListingAttribute, Attribute, AttributeOption
from app.models.category import Category
from app.models.vehicle_mdm import VehicleMake, VehicleModel
from typing import Optional, List, Dict, Any
import uuid
import logging

router = APIRouter(prefix="/v2/listings", tags=["listings"])
logger = logging.getLogger(__name__)

# --- Models (Pydantic) ---
# Keeping it inline for speed, usually goes to schemas/
from pydantic import BaseModel

class MediaItem(BaseModel):
    url: str
    type: str = "image"

class AttributeItem(BaseModel):
    key: str
    label: str
    value: Any
    unit: Optional[str] = None

class AttributeGroup(BaseModel):
    group: str
    items: List[AttributeItem]

class BreadcrumbItem(BaseModel):
    label: str
    slug: str

class SellerInfo(BaseModel):
    id: str
    name: str
    type: str # individual, dealer
    dealer_name: Optional[str] = None
    phones: List[str] = []

class SeoInfo(BaseModel):
    title: str
    description: str

class ListingDetail(BaseModel):
    id: str
    title: str
    slug: str
    price: Optional[int]
    currency: str
    description: Optional[str]
    status: str
    created_at: str
    updated_at: str
    
    location: Dict[str, Any]
    media: List[MediaItem]
    
    attributes: List[AttributeGroup]
    breadcrumbs: List[BreadcrumbItem]
    seller: SellerInfo
    
    seo: SeoInfo

class RelatedListing(BaseModel):
    id: str
    title: str
    price: int
    currency: str
    image: Optional[str]

class ListingResponse(BaseModel):
    listing: ListingDetail
    related: List[RelatedListing]

# --- Helper ---
def normalize_slug(text: str) -> str:
    # Basic slugify
    import re
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    return text.strip('-')

@router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing_detail(listing_id: str, db: AsyncSession = Depends(get_db)):
    try:
        uuid_id = uuid.UUID(listing_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Invalid ID format")

    # 1. Fetch Listing
    stmt = select(Listing).where(Listing.id == uuid_id)
    result = await db.execute(stmt)
    listing = result.scalar_one_or_none()

    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
        
    # Check Status (Guardrail)
    if listing.status != 'active':
        # In a real app, we might return 410 or a specific schema for sold items
        # For now, if it's not active, we might restricted it unless admin (omitted for public API)
        pass # Allow fetching for now to show "Sold" state in UI, usually handled by UI

    # 2. Fetch Seller
    seller_info = {"id": str(listing.user_id), "name": "Unknown", "type": "individual", "phones": []}
    
    user_res = await db.execute(select(User).where(User.id == listing.user_id))
    user = user_res.scalar_one_or_none()
    
    if user:
        if listing.is_dealer_listing and listing.dealer_id:
            dealer_res = await db.execute(select(Dealer).where(Dealer.id == listing.dealer_id))
            dealer = dealer_res.scalar_one_or_none()
            if dealer:
                seller_info["name"] = user.full_name
                seller_info["type"] = "dealer"
                seller_info["dealer_name"] = dealer.company_name
                seller_info["phones"] = [dealer.contact_phone] if dealer.contact_phone else []
        else:
            # Mask Name
            name_parts = user.full_name.split()
            masked_name = f"{name_parts[0]} {name_parts[-1][0]}." if len(name_parts) > 1 else user.full_name
            seller_info["name"] = masked_name

    # 3. Fetch Category & Breadcrumbs
    breadcrumbs = []
    cat_group = "General"
    if listing.category_id:
        cat_res = await db.execute(select(Category).where(Category.id == listing.category_id))
        category = cat_res.scalar_one_or_none()
        if category:
            cat_group = category.slug.get('en', 'General')
            # Resolve path
            path_ids = category.path.split('.') if category.path else [str(category.id)]
            # We would need to fetch all parents to build breadcrumbs. 
            # For speed, let's just add Home > Category
            breadcrumbs.append({"label": "Ana Sayfa", "slug": ""})
            breadcrumbs.append({"label": category.translations[0].name if category.translations else category.slug.get('en'), "slug": category.slug.get('en')})

    # 4. Fetch Attributes (EAV)
    # Get all definitions first to map keys
    attr_stmt = select(Attribute)
    all_attrs = (await db.execute(attr_stmt)).scalars().all()
    attr_def_map = {a.id: a for a in all_attrs}
    
    # Get values
    val_stmt = (
        select(ListingAttribute, AttributeOption)
        .outerjoin(AttributeOption, ListingAttribute.value_option_id == AttributeOption.id)
        .where(ListingAttribute.listing_id == listing.id)
    )
    val_res = await db.execute(val_stmt)
    vals = val_res.all()
    
    formatted_attrs = []
    
    for la, opt in vals:
        if la.attribute_id not in attr_def_map: continue
        definition = attr_def_map[la.attribute_id]
        
        # Determine value
        val_display = None
        if definition.attribute_type in ['select', 'multi_select']:
            if opt:
                val_display = opt.label.get('tr', opt.label.get('en', opt.value))
            else:
                val_display = la.value_text
        elif definition.attribute_type == 'boolean':
            val_display = "Evet" if la.value_boolean else "Hayır"
        elif definition.attribute_type == 'number':
            val_display = la.value_number
        else:
            val_display = la.value_text
            
        if val_display is not None:
            formatted_attrs.append(AttributeItem(
                key=definition.key,
                label=definition.name.get('tr', definition.key),
                value=str(val_display),
                unit=definition.unit
            ))

    # Add Make/Model if exists
    if listing.make_id:
        m_res = await db.execute(select(VehicleMake).where(VehicleMake.id == listing.make_id))
        make = m_res.scalar_one_or_none()
        if make:
            formatted_attrs.insert(0, AttributeItem(key="brand", label="Marka", value=make.name))
            
    if listing.model_id:
        m_res = await db.execute(select(VehicleModel).where(VehicleModel.id == listing.model_id))
        model = m_res.scalar_one_or_none()
        if model:
            formatted_attrs.insert(1, AttributeItem(key="model", label="Model", value=model.name))

    # 5. Media
    media_list = [MediaItem(url=url) for url in (listing.images or [])]

    # 6. Related (Simple: Same category, random 4)
    related_stmt = (
        select(Listing)
        .where(Listing.category_id == listing.category_id, Listing.id != listing.id, Listing.status == 'active')
        .limit(4)
    )
    related_res = await db.execute(related_stmt)
    related_items = [
        RelatedListing(
            id=str(r.id),
            title=r.title,
            price=r.price or 0,
            currency=r.currency,
            image=r.images[0] if r.images else None
        ) for r in related_res.scalars().all()
    ]

    # 7. Construct Response
    detail = ListingDetail(
        id=str(listing.id),
        title=listing.title,
        slug=normalize_slug(listing.title),
        price=listing.price,
        currency=listing.currency,
        description=listing.description,
        status=listing.status,
        created_at=listing.created_at.isoformat(),
        updated_at=listing.updated_at.isoformat(),
        location={"country": listing.country, "city": listing.city},
        media=media_list,
        attributes=[AttributeGroup(group="Özellikler", items=formatted_attrs)],
        breadcrumbs=breadcrumbs,
        seller=SellerInfo(**seller_info),
        seo=SeoInfo(
            title=f"{listing.title} - {listing.price} {listing.currency}",
            description=listing.description[:160] if listing.description else listing.title
        )
    )

    return ListingResponse(listing=detail, related=related_items)
