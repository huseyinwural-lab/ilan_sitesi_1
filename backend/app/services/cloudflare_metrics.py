import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)

CLOUDFLARE_GRAPHQL_ENDPOINT = "https://api.cloudflare.com/client/v4/graphql"
DEFAULT_CACHE_TTL_SECONDS = 60

CDN_TARGETS = {
    "hit_ratio_min": 85,
    "origin_fetch_ratio_max": 15,
    "warm_p95_ms": {"DE": 150, "AT": 150, "CH": 170, "FR": 170},
    "cold_p95_ms": {"DE": 450, "AT": 450, "CH": 500, "FR": 500},
}


class CloudflareMetricsError(RuntimeError):
    def __init__(self, message: str, code: str = "cloudflare_error") -> None:
        super().__init__(message)
        self.code = code


@dataclass
class CloudflareCredentials:
    api_token: str
    account_id: str
    zone_id: str


class CloudflareMetricsAdapter:
    def __init__(self, credentials: CloudflareCredentials) -> None:
        self.credentials = credentials
        self.headers = {
            "Authorization": f"Bearer {credentials.api_token}",
            "Content-Type": "application/json",
        }

    async def fetch_cache_metrics(self) -> Optional[Dict[str, Any]]:
        query = self._build_cache_query()
        return await self._execute_query(query)

    async def fetch_origin_fetch_metrics(self) -> Optional[Dict[str, Any]]:
        query = self._build_origin_fetch_query()
        return await self._execute_query(query)

    async def fetch_latency_metrics(self, cache_state: Optional[str]) -> Optional[Dict[str, Any]]:
        query = self._build_latency_query(cache_state)
        return await self._execute_query(query)

    async def _execute_query(self, query: str) -> Optional[Dict[str, Any]]:
        payload = {"query": query}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    CLOUDFLARE_GRAPHQL_ENDPOINT,
                    json=payload,
                    headers=self.headers,
                )
            if response.status_code != 200:
                logger.warning("cloudflare_graphql_error", extra={"status": response.status_code, "body": response.text})
                return None
            data = response.json()
            if data.get("errors"):
                logger.warning("cloudflare_graphql_errors", extra={"errors": data.get("errors")})
                return None
            return data.get("data")
        except httpx.RequestError as exc:
            logger.warning("cloudflare_request_error", extra={"error": str(exc)})
            return None

    def _build_cache_query(self) -> str:
        since, until = _last_hour_window()
        return f"""
        query {{
          viewer {{
            zones(filter: {{ zoneTag: "{self.credentials.zone_id}" }}) {{
              httpRequests1hGroups(limit: 1, filter: {{ datetime_geq: "{since}", datetime_lt: "{until}" }}) {{
                sum {{ requests cachedRequests cachedBytes bytes }}
              }}
            }}
          }}
        }}
        """.strip()

    def _build_origin_fetch_query(self) -> str:
        since, until = _last_hour_window()
        return f"""
        query {{
          viewer {{
            zones(filter: {{ zoneTag: "{self.credentials.zone_id}" }}) {{
              httpRequests1hGroups(limit: 1, filter: {{ datetime_geq: "{since}", datetime_lt: "{until}", responseCached: "Uncached" }}) {{
                sum {{ requests bytes }}
              }}
            }}
          }}
        }}
        """.strip()

    def _build_latency_query(self, cache_state: Optional[str]) -> str:
        since, until = _last_hour_window()
        cached_filter = f', responseCached: "{cache_state}"' if cache_state else ''
        return f"""
        query {{
          viewer {{
            zones(filter: {{ zoneTag: "{self.credentials.zone_id}" }}) {{
              httpRequests1hGroups(limit: 1, filter: {{ datetime_geq: "{since}", datetime_lt: "{until}", contentTypeMap_edgeResponseContentTypeName: "image"{cached_filter} }}) {{
                quantiles {{ edgeTimeToFirstByteMsP95 }}
                avg {{ edgeTimeToFirstByteMs }}
              }}
            }}
          }}
        }}
        """.strip()


class CloudflareMetricsService:
    def __init__(self) -> None:
        self._cache: Dict[str, Any] = {"checked_at": 0, "payload": None}

    def is_enabled(self) -> bool:
        return (os.environ.get("CLOUDFLARE_ANALYTICS_ENABLED") or "").lower() == "true"

    def _load_credentials(self) -> CloudflareCredentials:
        token = os.environ.get("CLOUDFLARE_API_TOKEN")
        account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
        zone_id = os.environ.get("CLOUDFLARE_ZONE_ID")
        if not token or not account_id or not zone_id:
            raise CloudflareMetricsError("Cloudflare credentials missing", code="credentials_missing")
        return CloudflareCredentials(api_token=token, account_id=account_id, zone_id=zone_id)

    def _get_cache_ttl(self) -> int:
        raw = os.environ.get("CLOUDFLARE_METRICS_CACHE_TTL")
        if not raw:
            return DEFAULT_CACHE_TTL_SECONDS
        try:
            return max(10, int(raw))
        except ValueError:
            return DEFAULT_CACHE_TTL_SECONDS

    async def get_metrics(self) -> Dict[str, Any]:
        if not self.is_enabled():
            return {"enabled": False, "status": "disabled"}

        ttl = self._get_cache_ttl()
        now_ts = time.time()
        cached = self._cache.get("payload")
        if cached and (now_ts - (self._cache.get("checked_at") or 0)) < ttl:
            return cached

        credentials = self._load_credentials()
        adapter = CloudflareMetricsAdapter(credentials)

        cache_payload = await adapter.fetch_cache_metrics()
        origin_payload = await adapter.fetch_origin_fetch_metrics()
        warm_payload = await adapter.fetch_latency_metrics("Cached")
        cold_payload = await adapter.fetch_latency_metrics("Uncached")

        cache_metrics = _extract_cache_metrics(cache_payload)
        origin_metrics = _extract_origin_metrics(origin_payload)
        warm_metrics = _extract_latency_metrics(warm_payload)
        cold_metrics = _extract_latency_metrics(cold_payload)

        total_requests = cache_metrics.get("total_requests") or 0
        cached_requests = cache_metrics.get("cached_requests") or 0
        cache_hit_ratio = round((cached_requests / total_requests) * 100, 2) if total_requests else None
        origin_fetch_count = origin_metrics.get("origin_fetch_count")
        origin_fetch_ratio = (
            round((origin_fetch_count / total_requests) * 100, 2)
            if total_requests and origin_fetch_count is not None
            else None
        )

        warm_p95 = warm_metrics.get("p95_ms")
        cold_p95 = cold_metrics.get("p95_ms")

        payload = {
            "enabled": True,
            "status": "ok" if any([cache_metrics, origin_metrics, warm_metrics, cold_metrics]) else "degraded",
            "last_updated_at": datetime.now(timezone.utc).isoformat(),
            "cache_hit_ratio": cache_hit_ratio,
            "cached_requests": cached_requests,
            "total_requests": total_requests,
            "origin_fetch_count": origin_fetch_count,
            "origin_fetch_ratio": origin_fetch_ratio,
            "image_latency_p95_ms": {
                "warm": warm_p95,
                "cold": cold_p95,
            },
            "targets": CDN_TARGETS,
        }

        payload["alerts"] = _evaluate_alerts(payload)
        self._cache.update({"checked_at": now_ts, "payload": payload})
        return payload


def _last_hour_window() -> tuple[str, str]:
    until = datetime.now(timezone.utc)
    since = until - timedelta(hours=1)
    return since.isoformat(), until.isoformat()


def _extract_cache_metrics(raw: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    zones = raw.get("viewer", {}).get("zones", []) if raw else []
    if not zones:
        return {}
    groups = zones[0].get("httpRequests1hGroups", [])
    if not groups:
        return {}
    summary = groups[0].get("sum", {})
    return {
        "total_requests": summary.get("requests", 0),
        "cached_requests": summary.get("cachedRequests", 0),
        "cached_bytes": summary.get("cachedBytes", 0),
        "total_bytes": summary.get("bytes", 0),
    }


def _extract_origin_metrics(raw: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    zones = raw.get("viewer", {}).get("zones", []) if raw else []
    if not zones:
        return {}
    groups = zones[0].get("httpRequests1hGroups", [])
    if not groups:
        return {}
    summary = groups[0].get("sum", {})
    return {
        "origin_fetch_count": summary.get("requests", 0),
        "origin_fetch_bytes": summary.get("bytes", 0),
    }


def _extract_latency_metrics(raw: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    zones = raw.get("viewer", {}).get("zones", []) if raw else []
    if not zones:
        return {}
    groups = zones[0].get("httpRequests1hGroups", [])
    if not groups:
        return {}
    quantiles = groups[0].get("quantiles", {})
    avg = groups[0].get("avg", {})
    return {
        "p95_ms": quantiles.get("edgeTimeToFirstByteMsP95"),
        "avg_ms": avg.get("edgeTimeToFirstByteMs"),
    }


def _evaluate_alerts(payload: Dict[str, Any]) -> Dict[str, Any]:
    targets = payload.get("targets") or {}
    hit_ratio_min = targets.get("hit_ratio_min", 85)
    origin_ratio_max = targets.get("origin_fetch_ratio_max", 15)
    warm_targets = targets.get("warm_p95_ms", {})
    cold_targets = targets.get("cold_p95_ms", {})

    hit_ratio = payload.get("cache_hit_ratio")
    origin_ratio = payload.get("origin_fetch_ratio")
    warm_p95 = (payload.get("image_latency_p95_ms") or {}).get("warm")
    cold_p95 = (payload.get("image_latency_p95_ms") or {}).get("cold")

    hit_ok = hit_ratio is None or hit_ratio >= hit_ratio_min
    origin_ok = origin_ratio is None or origin_ratio <= origin_ratio_max

    warm_breaches = [country for country, target in warm_targets.items() if warm_p95 is not None and warm_p95 > target]
    cold_breaches = [country for country, target in cold_targets.items() if cold_p95 is not None and cold_p95 > target]

    warm_ok = warm_p95 is None or len(warm_breaches) == 0
    cold_ok = cold_p95 is None or len(cold_breaches) == 0

    return {
        "hit_ratio_ok": hit_ok,
        "origin_fetch_ok": origin_ok,
        "warm_p95_ok": warm_ok,
        "cold_p95_ok": cold_ok,
        "warm_breaches": warm_breaches,
        "cold_breaches": cold_breaches,
        "has_alert": not (hit_ok and origin_ok and warm_ok and cold_ok),
    }
