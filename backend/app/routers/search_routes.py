
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc, or_
from app.dependencies import get_db
from app.models.moderation import Listing
from app.models.attribute import ListingAttribute, Attribute, AttributeOption, CategoryAttributeMap
from app.models.category import Category
from app.core.redis_rate_limit import RedisRateLimiter
from typing import Optional, List, Dict
import json
import logging
import uuid
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v2", tags=["search"])

# Rate Limiter
# Public Search: 100 req/min (IP Based)
search_limiter = RedisRateLimiter(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))

async def limit_search(request: Request):
    ip = request.client.host if request.client else "127.0.0.1"
    key = f"rl:search:{ip}"
    allowed = await search_limiter.check_limit(key, limit=100, burst=10)
    if not allowed:
        raise HTTPException(status_code=429, detail="Too Many Requests")

@router.get("/search", dependencies=[Depends(limit_search)])
async def search_listings(
    q: Optional[str] = Query(None, max_length=100),
    category_slug: Optional[str] = None,
    sort: str = "date_desc",
    page: int = Query(1, ge=1, le=1000), # Guardrail: Max Page 1000
    limit: int = Query(20, ge=1, le=100), # Guardrail: Max Page Size 100
    price_min: Optional[int] = None,
    price_max: Optional[int] = None,
    attrs: Optional[str] = Query(None, description="JSON encoded attribute filters"),
    db: AsyncSession = Depends(get_db)
):
    """
    Search API v2: Typed Attribute Filtering & Faceting
    """
    # Guardrail: Check Filter Count
    if attrs:
        try:
            filters = json.loads(attrs)
            if len(filters) > 10:
                raise HTTPException(status_code=422, detail={"code": "query_too_complex", "message": "Too many filters"})
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail={"code": "bad_request", "message": "Invalid attributes format"})
    else:
        filters = {}

    # 1. Base Query
    query = select(Listing).where(Listing.status == 'active')
    
    # 2. Text Search
    if q:
        query = query.where(Listing.title.ilike(f"%{q}%"))
        
    # 3. Category Filter
    current_cat = None
    if category_slug:
        cat_all = (await db.execute(select(Category))).scalars().all()
        current_cat = next((c for c in cat_all if c.slug.get('en') == category_slug), None)
        
        if current_cat:
            query = query.where(Listing.category_id == current_cat.id)
    
    # 4. Standard Filters
    if price_min: query = query.where(Listing.price >= price_min)
    if price_max: query = query.where(Listing.price <= price_max)
    
    # 5. Attribute Filters (The Core Logic)
    if filters:
        for key, val in filters.items():
            attr_res = await db.execute(select(Attribute).where(Attribute.key == key))
            attr = attr_res.scalar_one_or_none()
            if not attr: continue
            
            sub_q = select(ListingAttribute.listing_id).where(
                ListingAttribute.attribute_id == attr.id
            )
            
            if attr.attribute_type == 'select' or attr.attribute_type == 'multi_select':
                if isinstance(val, list):
                    opt_ids = (await db.execute(select(AttributeOption.id).where(
                        AttributeOption.attribute_id == attr.id,
                        AttributeOption.value.in_(val)
                    ))).scalars().all()
                    sub_q = sub_q.where(ListingAttribute.value_option_id.in_(opt_ids))
                
            elif attr.attribute_type == 'boolean':
                if val is True:
                    sub_q = sub_q.where(ListingAttribute.value_boolean == True)
                    
            elif attr.attribute_type == 'number':
                if isinstance(val, dict):
                    if 'min' in val: sub_q = sub_q.where(ListingAttribute.value_number >= val['min'])
                    if 'max' in val: sub_q = sub_q.where(ListingAttribute.value_number <= val['max'])
            
            query = query.where(Listing.id.in_(sub_q))

    # 6. Pagination & Execution (Items)
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar()
    
    if sort == 'price_asc': query = query.order_by(Listing.price.asc())
    elif sort == 'price_desc': query = query.order_by(Listing.price.desc())
    else: query = query.order_by(Listing.created_at.desc())
    
    items_res = await db.execute(query.offset((page-1)*limit).limit(limit))
    items = items_res.scalars().all()
    
    # 7. Facet Generation (Aggregated from Filtered Result)
    facets = {}
    if current_cat:
        # Resolve Inheritance
        # Path format: "id1.id2.id3"
        if current_cat.path:
            cat_ids = [uuid.UUID(x) for x in current_cat.path.split('.')]
        else:
            cat_ids = [current_cat.id]
            
        # Fetch bindings for current OR ancestors with inheritance
        bindings_query = select(CategoryAttributeMap).where(
            or_(
                CategoryAttributeMap.category_id == current_cat.id,
                and_(
                    CategoryAttributeMap.category_id.in_(cat_ids),
                    CategoryAttributeMap.inherit_to_children == True
                )
            )
        )
        bindings = (await db.execute(bindings_query)).scalars().all()
        target_attr_ids = [b.attribute_id for b in bindings]
        
        target_attrs = (await db.execute(select(Attribute).where(Attribute.id.in_(target_attr_ids)))).scalars().all()
        
        filtered_subq = query.with_only_columns(Listing.id).subquery()
        
        for attr in target_attrs:
            if attr.attribute_type in ['select', 'multi_select']:
                stmt = (
                    select(AttributeOption.value, AttributeOption.label, func.count(ListingAttribute.id))
                    .join(ListingAttribute, ListingAttribute.value_option_id == AttributeOption.id)
                    .where(ListingAttribute.attribute_id == attr.id)
                    .where(ListingAttribute.listing_id.in_(select(filtered_subq)))
                    .group_by(AttributeOption.id)
                )
                res = await db.execute(stmt)
                rows = res.all()
                
                options = []
                for val, label, count in rows:
                    options.append({
                        "value": val,
                        "label": label.get('en', val),
                        "count": count,
                        "selected": False
                    })
                if options:
                    facets[attr.key] = options

    return {
        "items": [{
            "id": str(i.id),
            "title": i.title,
            "price": i.price,
            "currency": i.currency,
            "image": i.images[0] if i.images else None
        } for i in items],
        "facets": facets,
        "pagination": {
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit
        }
    }
