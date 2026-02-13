
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc, or_
from app.dependencies import get_db
from app.models.moderation import Listing
from app.models.attribute import ListingAttribute, Attribute, AttributeOption, CategoryAttributeMap
from app.models.category import Category
from typing import Optional, List, Dict
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v2", tags=["search"])

@router.get("/search")
async def search_listings(
    q: Optional[str] = None,
    category_slug: Optional[str] = None,
    sort: str = "date_desc",
    page: int = 1,
    limit: int = 20,
    price_min: Optional[int] = None,
    price_max: Optional[int] = None,
    attrs: Optional[str] = Query(None, description="JSON encoded attribute filters"),
    db: AsyncSession = Depends(get_db)
):
    """
    Search API v2: Typed Attribute Filtering & Faceting
    """
    # 1. Base Query
    query = select(Listing).where(Listing.status == 'active')
    
    # 2. Text Search
    if q:
        query = query.where(Listing.title.ilike(f"%{q}%"))
        
    # 3. Category Filter
    current_cat = None
    if category_slug:
        # Find category ID by slug (assuming single lang 'en' for MVP or pass lang param)
        # TODO: Proper locale handling.
        cat_res = await db.execute(select(Category).where(Category.slug['en'].astext == category_slug)) # PG syntax
        # Fallback for SQLite/Generic if astext fails (Simulated)
        # In real code we use the python lookup if seed was consistent, but here we query DB.
        # Let's use a simpler query for MVP compatibility
        cat_all = (await db.execute(select(Category))).scalars().all()
        current_cat = next((c for c in cat_all if c.slug.get('en') == category_slug), None)
        
        if current_cat:
            # TODO: Include children categories logic (recursive CTE or path match)
            # For MVP: Exact match or simple path containment
            query = query.where(Listing.category_id == current_cat.id)
    
    # 4. Standard Filters
    if price_min: query = query.where(Listing.price >= price_min)
    if price_max: query = query.where(Listing.price <= price_max)
    
    # 5. Attribute Filters (The Core Logic)
    if attrs:
        try:
            filters = json.loads(attrs)
            # filters example: {"brand": ["apple", "samsung"], "screen_size": {"min": 5}}
            
            for key, val in filters.items():
                # Find Attribute ID
                attr_res = await db.execute(select(Attribute).where(Attribute.key == key))
                attr = attr_res.scalar_one_or_none()
                if not attr: continue
                
                # Subquery for Filter
                sub_q = select(ListingAttribute.listing_id).where(
                    ListingAttribute.attribute_id == attr.id
                )
                
                if attr.attribute_type == 'select' or attr.attribute_type == 'multi_select':
                    # Value is list of slugs? Or IDs? 
                    # Contract says: slug values (e.g. "apple")
                    # Need to resolve Option IDs from Slugs
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
                    # Range
                    if isinstance(val, dict):
                        if 'min' in val: sub_q = sub_q.where(ListingAttribute.value_number >= val['min'])
                        if 'max' in val: sub_q = sub_q.where(ListingAttribute.value_number <= val['max'])
                
                query = query.where(Listing.id.in_(sub_q))
                
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid attributes format")

    # 6. Pagination & Execution (Items)
    # Total count (Separate query)
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar()
    
    # Sorting
    if sort == 'price_asc': query = query.order_by(Listing.price.asc())
    elif sort == 'price_desc': query = query.order_by(Listing.price.desc())
    else: query = query.order_by(Listing.created_at.desc())
    
    items_res = await db.execute(query.offset((page-1)*limit).limit(limit))
    items = items_res.scalars().all()
    
    # 7. Facet Generation (Aggregated from Filtered Result)
    # Strategy: We need to know which attributes are RELEVANT for the current category context.
    facets = {}
    if current_cat:
        # Fetch bound attributes
        bindings = (await db.execute(select(CategoryAttributeMap).where(CategoryAttributeMap.category_id == current_cat.id))).scalars().all()
        target_attr_ids = [b.attribute_id for b in bindings]
        
        # Fetch Attributes Defs
        target_attrs = (await db.execute(select(Attribute).where(Attribute.id.in_(target_attr_ids)))).scalars().all()
        
        # Filtered Listing IDs (for aggregation scope)
        # Note: Ideally we run aggregation on the query, but SQL complexity high. 
        # MVP: If total results < 1000, we can aggregate in Python or 
        # fetch simplified aggregation.
        # Let's do SQL Aggregation for Selects.
        
        filtered_subq = query.with_only_columns(Listing.id).subquery()
        
        for attr in target_attrs:
            if attr.attribute_type in ['select', 'multi_select']:
                # Aggregation Query
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
                        "label": label.get('en', val), # Locale handling needed
                        "count": count,
                        "selected": False # Logic to check if in current filter
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
