import os
import time
from collections import deque
from typing import Any, Dict, List, Tuple

SLOW_QUERY_WINDOW_SECONDS = 24 * 60 * 60
SLOW_QUERY_BUFFER_SIZE = 5000

_slow_query_events: deque = deque(maxlen=SLOW_QUERY_BUFFER_SIZE)


def get_slow_query_threshold_ms() -> int:
    value = os.environ.get("SLOW_QUERY_THRESHOLD_MS", "800")
    try:
        return max(0, int(value))
    except ValueError:
        return 800


def record_slow_query(duration_ms: float, endpoint: str, meta: Dict[str, Any] | None = None) -> bool:
    threshold = get_slow_query_threshold_ms()
    if duration_ms < threshold:
        return False
    _slow_query_events.append(
        {
            "ts": time.time(),
            "duration_ms": round(duration_ms, 2),
            "endpoint": endpoint,
            "meta": meta or {},
        }
    )
    return True


def _prune_events(window_seconds: int) -> None:
    now_ts = time.time()
    while _slow_query_events and (now_ts - _slow_query_events[0]["ts"]) > window_seconds:
        _slow_query_events.popleft()


def get_slow_query_summary(window_seconds: int = SLOW_QUERY_WINDOW_SECONDS) -> Tuple[int, int]:
    _prune_events(window_seconds)
    return len(_slow_query_events), get_slow_query_threshold_ms()


def get_slow_query_events(window_seconds: int = SLOW_QUERY_WINDOW_SECONDS, limit: int = 50) -> List[Dict[str, Any]]:
    _prune_events(window_seconds)
    return list(_slow_query_events)[-limit:]
