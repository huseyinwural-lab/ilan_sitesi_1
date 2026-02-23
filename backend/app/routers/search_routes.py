
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc, or_
from app.dependencies import get_db
from app.models.moderation import Listing
from app.models.listing_search import ListingSearch
from app.models.attribute import ListingAttribute, Attribute, AttributeOption, CategoryAttributeMap
from app.models.category import Category
from app.core.redis_rate_limit import RedisRateLimiter
from typing import Optional, List, Dict
import json
import logging
import uuid
import os
import hashlib

from app.core.redis_cache import cache_service, build_cache_key
import asyncio

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v2", tags=["search"])


def _get_search_sql_rollout() -> float:
    try:
        rollout = float(os.environ.get("SEARCH_SQL_ROLLOUT", "0"))
    except ValueError:
        rollout = 0.0
    return max(0.0, min(1.0, rollout))


def _stable_bucket_for_request(request: Request) -> float:
    key = request.headers.get("X-Request-ID")
    if not key:
        key = request.client.host if request.client else "anonymous"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    bucket_int = int(digest[:8], 16)
    return bucket_int / 0xFFFFFFFF


def _use_listings_search(request: Request) -> bool:
    rollout = _get_search_sql_rollout()
    if rollout >= 1:
        return True
    if rollout <= 0:
        return False
    return _stable_bucket_for_request(request) < rollout

@router.on_event("startup")
async def startup():
    await cache_service.connect()

@router.on_event("shutdown")
async def shutdown():
    await cache_service.close()

# Rate Limiter
# Public Search: 100 req/min (IP Based)
search_limiter = RedisRateLimiter(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))

async def limit_search(request: Request):
    ip = request.client.host if request.client else "127.0.0.1"
    key = f"rl:search:{ip}"
    allowed = await search_limiter.check_limit(key, limit=60, burst=5)
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
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Search API v2: Typed Attribute Filtering & Faceting
    """
    use_listings_search = _use_listings_search(request)
    backend_label = "sql" if use_listings_search else "legacy"
    # 0. Check Cache
    cache_key = build_cache_key("search:v2", 
        q=q, category_slug=category_slug, sort=sort, page=page, limit=limit,
        price_min=price_min, price_max=price_max, attrs=attrs, backend=backend_label
    )
    
    cached = await cache_service.get(cache_key)
    if cached:
        return cached

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

    ListingModel = ListingSearch if use_listings_search else Listing
    id_col = ListingSearch.listing_id if use_listings_search else Listing.id
    price_col = ListingSearch.price_amount if use_listings_search else Listing.price
    price_type_col = ListingSearch.price_type if use_listings_search else Listing.price_type
    created_col = ListingSearch.published_at if use_listings_search else Listing.created_at

    # 1. Base Query
    query = select(ListingModel).where(ListingModel.status == 'active')

    # 2. Text Search
    if q:
        if use_listings_search:
            ts_query_tr = func.plainto_tsquery('turkish', q)
            ts_query_de = func.plainto_tsquery('german', q)
            query = query.where(
                or_(
                    ListingSearch.tsv_tr.op('@@')(ts_query_tr),
                    ListingSearch.tsv_de.op('@@')(ts_query_de),
                    ListingSearch.title.ilike(f"%{q}%"),
                    ListingSearch.description.ilike(f"%{q}%"),
                )
            )
        else:
            query = query.where(Listing.title.ilike(f"%{q}%"))

    # 3. Category Filter
    current_cat = None
    if category_slug:
        cat_all = (await db.execute(select(Category))).scalars().all()
        current_cat = next((c for c in cat_all if c.slug.get('en') == category_slug), None)

        if current_cat:
            query = query.where(ListingModel.category_id == current_cat.id)

    # 4. Standard Filters
    if price_min:
        query = query.where(price_col >= price_min)
    if price_max:
        query = query.where(price_col <= price_max)
    if price_min or price_max:
        query = query.where(or_(price_type_col == "FIXED", price_type_col.is_(None)))

    # 5. Attribute Filters (The Core Logic)
    if filters:
        for key, val in filters.items():
            attr_res = await db.execute(select(Attribute).where(Attribute.key == key))
            attr = attr_res.scalar_one_or_none()
            if not attr:
                continue

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
                    sub_q = sub_q.where(ListingAttribute.value_boolean.is_(True))

            elif attr.attribute_type == 'number':
                if isinstance(val, dict):
                    if 'min' in val:
                        sub_q = sub_q.where(ListingAttribute.value_number >= val['min'])
                    if 'max' in val:
                        sub_q = sub_q.where(ListingAttribute.value_number <= val['max'])

            query = query.where(id_col.in_(sub_q))

    # 6. Pagination & Execution (Items)
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar()

    if sort == 'price_asc':
        query = query.order_by(price_col.asc())
    elif sort == 'price_desc':
        query = query.order_by(price_col.desc())
    else:
        query = query.order_by(created_col.desc())

    items_res = await db.execute(query.offset((page-1)*limit).limit(limit))
    items = items_res.scalars().all()
    
    # 7. Facet Generation (Aggregated from Filtered Result)
    facets = {}
    facet_meta = {}
    
    if current_cat:
        # Resolve Inheritance
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
                    CategoryAttributeMap.inherit_to_children.is_(True)
                )
            )
        )
        bindings = (await db.execute(bindings_query)).scalars().all()
        target_attr_ids = [b.attribute_id for b in bindings]
        
        target_attrs = (await db.execute(select(Attribute).where(Attribute.id.in_(target_attr_ids)))).scalars().all()
        
        # Populate Meta
        for attr in target_attrs:
            facet_meta[attr.key] = {
                "type": attr.attribute_type,
                "label": attr.name.get('tr', attr.name.get('en', attr.key)),
                "unit": attr.unit,
                "min": 0,
                "max": 1000000 
            }
        
        # P9 Optimization: Parallel Facet Aggregation using asyncio.gather
        filtered_subq = query.with_only_columns(id_col).subquery()
        
        async def fetch_facet(attr):
            if attr.attribute_type in ['select', 'multi_select']:
                stmt = (
                    select(AttributeOption.value, AttributeOption.label, func.count(ListingAttribute.id))
                    .join(ListingAttribute, ListingAttribute.value_option_id == AttributeOption.id)
                    .where(ListingAttribute.attribute_id == attr.id)
                    .where(ListingAttribute.listing_id.in_(select(filtered_subq)))
                    .group_by(AttributeOption.id)
                )
                res = await db.execute(stmt)
                return attr.key, res.all()
            return attr.key, []

        # Run all facet queries in parallel
        tasks = [fetch_facet(attr) for attr in target_attrs]
        results = await asyncio.gather(*tasks)
        
        for key, rows in results:
            if not rows:
                continue
            options = []
            for val, label, count in rows:
                options.append({
                    "value": val,
                    "label": label.get('en', val),
                    "count": count,
                    "selected": False
                })
            if options:
                facets[key] = options

    items_payload = []
    for item in items:
        listing_id = item.listing_id if use_listings_search else item.id
        price_value = item.price_amount if use_listings_search else item.price
        price_type_value = item.price_type or "FIXED"
        hourly_rate_value = item.hourly_rate
        currency_value = item.currency or "EUR"
        image_value = item.images[0] if item.images else None
        items_payload.append(
            {
                "id": str(listing_id),
                "title": item.title,
                "price": price_value,
                "price_type": price_type_value,
                "price_amount": price_value,
                "hourly_rate": hourly_rate_value,
                "currency": currency_value,
                "image": image_value,
            }
        )

    response = {
        "items": items_payload,
        "facets": facets,
        "facet_meta": facet_meta,
        "pagination": {
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit
        }
    }

    duration_ms = (time.perf_counter() - start_ts) * 1000
    record_slow_query(
        duration_ms,
        "search:v2",
        {
            "backend": backend_label,
            "q": q,
            "category": category_slug,
            "sort": sort,
        },
    )
    
    # Store in Cache (Background task usually, but here await is fine for now)
    await cache_service.set(cache_key, response, ttl=60)
    
    return response
