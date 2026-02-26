import hashlib
import asyncio
import re
import unicodedata
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Tuple
from urllib.parse import quote

import httpx
from sqlalchemy import and_, asc, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.meilisearch_config import MeiliSearchConfig
from app.models.moderation import Listing
from app.services.meilisearch_config import decrypt_meili_master_key, normalize_meili_url


def _normalize_text(value: str) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    lowered = ascii_text.lower()
    lowered = re.sub(r"[^a-z0-9\s]", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def stable_numeric_id(value: Any) -> int | None:
    if value in (None, ""):
        return None
    text = str(value)
    if text.isdigit():
        try:
            return int(text)
        except ValueError:
            return None
    try:
        as_uuid = uuid.UUID(text)
        return as_uuid.int % 9_007_199_254_740_991
    except ValueError:
        digest = hashlib.sha1(text.encode("utf-8")).hexdigest()
        return int(digest[:12], 16)


def _flatten_attributes(data: Any, prefix: str = "") -> Dict[str, Any]:
    if not isinstance(data, dict):
        return {}
    flat: Dict[str, Any] = {}
    for key, value in data.items():
        safe_key = re.sub(r"[^a-zA-Z0-9_]+", "_", str(key).strip().lower())
        if not safe_key:
            continue
        next_key = f"{prefix}_{safe_key}" if prefix else safe_key
        if isinstance(value, dict):
            flat.update(_flatten_attributes(value, next_key))
        elif isinstance(value, list):
            sanitized = []
            for item in value:
                if isinstance(item, (str, int, float, bool)) or item is None:
                    sanitized.append(item)
                else:
                    sanitized.append(str(item))
            flat[next_key] = sanitized
        elif isinstance(value, (str, int, float, bool)) or value is None:
            flat[next_key] = value
        else:
            flat[next_key] = str(value)
    return flat


def is_listing_searchable(listing: Listing) -> bool:
    return listing.status in {"published", "active"} and listing.deleted_at is None


def build_listing_document(listing: Listing) -> Dict[str, Any]:
    attrs = listing.attributes or {}
    vehicle = attrs.get("vehicle") or {}
    attribute_map = attrs.get("attributes") or {}
    attribute_flat_map = _flatten_attributes(attribute_map)

    category_path_ids = attrs.get("category_path_ids")
    if isinstance(category_path_ids, list):
        normalized_category_path = [str(item) for item in category_path_ids if item not in (None, "")]
    else:
        normalized_category_path = []
    if not normalized_category_path and listing.category_id:
        normalized_category_path = [str(listing.category_id)]

    trim_value = vehicle.get("vehicle_trim_id") or vehicle.get("trim_id")
    city_value = attrs.get("city_id") or listing.city

    searchable_text = _normalize_text(f"{listing.title or ''} {listing.description or ''}")
    premium_score = 0
    if listing.is_premium:
        premium_score += 1000
    if listing.is_showcase:
        premium_score += 400
    if listing.premium_until and listing.premium_until > datetime.now(timezone.utc):
        premium_score += 200

    doc: Dict[str, Any] = {
        "listing_id": str(listing.id),
        "category_path_ids": normalized_category_path,
        "make_id": stable_numeric_id(listing.make_id),
        "model_id": stable_numeric_id(listing.model_id),
        "trim_id": stable_numeric_id(trim_value),
        "city_id": stable_numeric_id(city_value),
        "attribute_flat_map": attribute_flat_map,
        "price": float(listing.price or listing.hourly_rate or 0),
        "price_amount": float(listing.price or 0),
        "hourly_rate": float(listing.hourly_rate or 0),
        "price_type": listing.price_type or "FIXED",
        "currency": listing.currency or "EUR",
        "premium_score": premium_score,
        "published_at": listing.published_at.isoformat() if listing.published_at else None,
        "searchable_text": searchable_text,
        "title": listing.title or "",
        "description": listing.description or "",
        "city": listing.city or "",
        "image": (listing.images[0] if listing.images else None),
        "status": listing.status,
    }

    for key, value in attribute_flat_map.items():
        doc[f"attribute_{key}"] = value
    return doc


async def get_active_meili_runtime(session: AsyncSession) -> Dict[str, str]:
    row = (
        (
            await session.execute(
                select(MeiliSearchConfig)
                .where(MeiliSearchConfig.status == "active")
                .order_by(desc(MeiliSearchConfig.updated_at), desc(MeiliSearchConfig.created_at))
                .limit(1)
            )
        )
        .scalars()
        .first()
    )
    if not row:
        raise RuntimeError("no_active_meili_config")

    return {
        "url": normalize_meili_url(row.meili_url),
        "index_name": row.meili_index_name or "listings_index",
        "master_key": decrypt_meili_master_key(row.meili_master_key_ciphertext),
    }


async def _meili_client(runtime: Dict[str, str]) -> httpx.AsyncClient:
    headers = {
        "Authorization": f"Bearer {runtime['master_key']}",
        "Content-Type": "application/json",
    }
    return httpx.AsyncClient(base_url=runtime["url"], headers=headers, timeout=12.0)


async def meili_delete_document(runtime: Dict[str, str], listing_id: str) -> Dict[str, Any]:
    index_path = quote(runtime["index_name"], safe="")
    async with await _meili_client(runtime) as client:
        response = await client.delete(f"/indexes/{index_path}/documents/{quote(listing_id, safe='')}")
        if response.status_code not in (200, 202, 404):
            raise RuntimeError(f"meili_delete_failed_{response.status_code}")
    return {"ok": True}


async def meili_upsert_documents(runtime: Dict[str, str], docs: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    payload = list(docs)
    index_path = quote(runtime["index_name"], safe="")
    async with await _meili_client(runtime) as client:
        response = await client.post(f"/indexes/{index_path}/documents", json=payload)
        if response.status_code not in (200, 202):
            raise RuntimeError(f"meili_upsert_failed_{response.status_code}")
    return {"ok": True, "count": len(payload)}


async def meili_clear_documents(runtime: Dict[str, str]) -> Dict[str, Any]:
    index_path = quote(runtime["index_name"], safe="")
    async with await _meili_client(runtime) as client:
        response = await client.delete(f"/indexes/{index_path}/documents")
        if response.status_code not in (200, 202):
            raise RuntimeError(f"meili_clear_failed_{response.status_code}")
    return {"ok": True}


async def meili_search_documents(
    runtime: Dict[str, str],
    *,
    query: str,
    limit: int = 20,
    offset: int = 0,
    sort: List[str] | None = None,
    filter_query: str | None = None,
    facets: List[str] | None = None,
) -> Dict[str, Any]:
    index_path = quote(runtime["index_name"], safe="")
    payload: Dict[str, Any] = {
        "q": query,
        "limit": limit,
        "offset": offset,
    }
    if sort:
        payload["sort"] = sort
    if filter_query:
        payload["filter"] = filter_query
    if facets:
        payload["facets"] = facets

    async with await _meili_client(runtime) as client:
        response = await client.post(f"/indexes/{index_path}/search", json=payload)
        if response.status_code != 200:
            body = response.text[:300]
            raise RuntimeError(f"meili_search_failed_{response.status_code}: {body}")
        return response.json()


async def meili_update_filterable_attributes(runtime: Dict[str, str], filterable_attributes: List[str]) -> Dict[str, Any]:
    index_path = quote(runtime["index_name"], safe="")
    async with await _meili_client(runtime) as client:
        response = await client.patch(
            f"/indexes/{index_path}/settings/filterable-attributes",
            json=filterable_attributes,
        )
        if response.status_code == 405:
            response = await client.put(
                f"/indexes/{index_path}/settings/filterable-attributes",
                json=filterable_attributes,
            )
        if response.status_code not in (200, 202):
            raise RuntimeError(f"meili_filterable_update_failed_{response.status_code}")
        task_uid = None
        try:
            payload = response.json()
            task_uid = payload.get("taskUid") or payload.get("uid")
        except Exception:
            task_uid = None

        if task_uid is not None:
            for _ in range(20):
                task_resp = await client.get(f"/tasks/{task_uid}")
                if task_resp.status_code != 200:
                    await asyncio.sleep(0.25)
                    continue
                task_payload = task_resp.json()
                status = task_payload.get("status")
                if status == "succeeded":
                    break
                if status in {"failed", "canceled"}:
                    raise RuntimeError(f"meili_filterable_task_{status}")
                await asyncio.sleep(0.25)
    return {"ok": True}


async def meili_index_stats(runtime: Dict[str, str]) -> Dict[str, Any]:
    index_path = quote(runtime["index_name"], safe="")
    async with await _meili_client(runtime) as client:
        response = await client.get(f"/indexes/{index_path}/stats")
        if response.status_code != 200:
            raise RuntimeError(f"meili_stats_failed_{response.status_code}")
        return response.json()


async def sync_listing_to_meili(session: AsyncSession, listing_id: uuid.UUID, operation: str) -> Dict[str, Any]:
    runtime = await get_active_meili_runtime(session)

    if operation == "delete":
        await meili_delete_document(runtime, str(listing_id))
        return {"ok": True, "mode": "delete"}

    listing = await session.get(Listing, listing_id)
    if not listing:
        await meili_delete_document(runtime, str(listing_id))
        return {"ok": True, "mode": "delete_missing"}

    if not is_listing_searchable(listing):
        await meili_delete_document(runtime, str(listing.id))
        return {"ok": True, "mode": "delete_not_searchable"}

    document = build_listing_document(listing)
    await meili_upsert_documents(runtime, [document])
    return {"ok": True, "mode": "upsert"}


async def bulk_reindex_search_projection(
    session: AsyncSession,
    chunk_size: int = 200,
    max_docs: int | None = None,
) -> Tuple[int, float]:
    runtime = await get_active_meili_runtime(session)

    total_indexed = 0
    offset = 0
    start = datetime.now(timezone.utc)

    while True:
        query = (
            select(Listing)
            .where(and_(Listing.status.in_(["published", "active"]), Listing.deleted_at.is_(None)))
            .order_by(asc(Listing.created_at), asc(Listing.id))
            .offset(offset)
            .limit(chunk_size)
        )
        rows = (await session.execute(query)).scalars().all()
        if not rows:
            break

        docs = [build_listing_document(item) for item in rows]
        if max_docs is not None:
            remaining = max_docs - total_indexed
            if remaining <= 0:
                break
            docs = docs[:remaining]
            rows = rows[:remaining]

        await meili_upsert_documents(runtime, docs)
        total_indexed += len(docs)
        offset += len(rows)

        if max_docs and total_indexed >= max_docs:
            break

    elapsed = (datetime.now(timezone.utc) - start).total_seconds()
    return total_indexed, elapsed
