import os
import time
from collections import deque
from typing import Any, Dict, List, Tuple

SLOW_QUERY_WINDOW_SECONDS = 24 * 60 * 60
SLOW_QUERY_BUFFER_SIZE = 5000

_latency_events_by_endpoint: Dict[str, deque] = {}
_slow_query_events_by_endpoint: Dict[str, deque] = {}


def get_slow_query_threshold_ms() -> int:
    value = os.environ.get("SLOW_QUERY_THRESHOLD_MS", "800")
    try:
        return max(0, int(value))
    except ValueError:
        return 800


def classify_endpoint(path: str) -> str | None:
    normalized = path or ""
    if normalized.startswith("/api/"):
        normalized = normalized[4:]
        if not normalized.startswith("/"):
            normalized = f"/{normalized}"

    if normalized.startswith("/v2/search") or normalized.startswith("/search") or normalized.startswith("/real-estate"):
        return "/api/search"
    if normalized.startswith("/v1/listings") or normalized.startswith("/listings"):
        return "/api/listings"
    if normalized.startswith("/admin/"):
        return "/api/admin/*"
    return None


def _get_endpoint_bucket(store: Dict[str, deque], endpoint: str) -> deque:
    if endpoint not in store:
        store[endpoint] = deque(maxlen=SLOW_QUERY_BUFFER_SIZE)
    return store[endpoint]


def _prune_events(events: deque, window_seconds: int) -> None:
    now_ts = time.time()
    while events and (now_ts - events[0]["ts"]) > window_seconds:
        events.popleft()


def record_request_latency(endpoint: str, duration_ms: float) -> None:
    bucket = _get_endpoint_bucket(_latency_events_by_endpoint, endpoint)
    bucket.append({"ts": time.time(), "duration_ms": round(duration_ms, 2)})

    threshold = get_slow_query_threshold_ms()
    if duration_ms >= threshold:
        slow_bucket = _get_endpoint_bucket(_slow_query_events_by_endpoint, endpoint)
        slow_bucket.append({"ts": time.time(), "duration_ms": round(duration_ms, 2)})


def _percentile(values: List[float], percentile: float) -> float | None:
    if not values:
        return None
    values_sorted = sorted(values)
    idx = int((percentile / 100) * (len(values_sorted) - 1))
    return values_sorted[idx]


def get_slow_query_summary(window_seconds: int = SLOW_QUERY_WINDOW_SECONDS) -> Tuple[int, int]:
    total = 0
    for bucket in _slow_query_events_by_endpoint.values():
        _prune_events(bucket, window_seconds)
        total += len(bucket)
    return total, get_slow_query_threshold_ms()


def get_endpoint_stats(window_seconds: int = SLOW_QUERY_WINDOW_SECONDS) -> List[Dict[str, Any]]:
    stats = []
    for endpoint, bucket in _latency_events_by_endpoint.items():
        _prune_events(bucket, window_seconds)
        durations = [item["duration_ms"] for item in bucket]
        p95 = _percentile(durations, 95)
        slow_bucket = _slow_query_events_by_endpoint.get(endpoint, deque())
        _prune_events(slow_bucket, window_seconds)
        stats.append(
            {
                "endpoint": endpoint,
                "p95_latency_ms": round(p95, 2) if p95 is not None else None,
                "slow_query_count": len(slow_bucket),
            }
        )
    return stats


def get_slow_query_events(window_seconds: int = SLOW_QUERY_WINDOW_SECONDS, limit: int = 50) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    for endpoint, bucket in _slow_query_events_by_endpoint.items():
        _prune_events(bucket, window_seconds)
        for event in bucket:
            events.append({**event, "endpoint": endpoint})
    events = sorted(events, key=lambda item: item["ts"], reverse=True)
    return events[:limit]
