import asyncio
import math
import os
import time
import uuid
from typing import Any, Dict, List, Tuple

import httpx

BASE_URL = os.environ.get("BASE_URL") or os.environ.get("REACT_APP_BACKEND_URL")
if not BASE_URL:
    raise RuntimeError("CONFIG_MISSING: BASE_URL")

TEST_EMAIL = os.environ.get("TEST_EMAIL")
TEST_PASSWORD = os.environ.get("TEST_PASSWORD")
if not TEST_EMAIL or not TEST_PASSWORD:
    raise RuntimeError("CONFIG_MISSING: TEST_EMAIL or TEST_PASSWORD")

BASE_URL = BASE_URL.rstrip("/")
LOGIN_URL = f"{BASE_URL}/api/auth/login"
ME_URL = f"{BASE_URL}/api/auth/me"

REQUEST_TIMEOUT = httpx.Timeout(30.0)


def _percentile(values: List[float], percentile: float) -> float | None:
    if not values:
        return None
    values_sorted = sorted(values)
    idx = int(math.ceil((percentile / 100) * len(values_sorted))) - 1
    idx = min(max(idx, 0), len(values_sorted) - 1)
    return values_sorted[idx]


def _summarize_errors(errors: List[Dict[str, Any]], label: str) -> None:
    if not errors:
        print(f"{label}: 0 hata")
        return
    print(f"{label}: {len(errors)} hata")
    print("Ilk 10 hata ornegi:")
    for error in errors[:10]:
        print(error)


def _build_error_detail(
    phase: str,
    step: str,
    status_code: int | None,
    request_id: str,
    response_request_id: str | None,
    body: str | None,
) -> Dict[str, Any]:
    return {
        "phase": phase,
        "step": step,
        "status_code": status_code,
        "request_id": request_id,
        "response_request_id": response_request_id,
        "body": body,
    }


async def _login_and_me(
    client: httpx.AsyncClient,
    phase: str,
    iteration: int,
) -> Tuple[bool, Dict[str, Any] | None]:
    request_id = str(uuid.uuid4())
    headers = {"X-Request-ID": request_id}
    payload = {"email": TEST_EMAIL, "password": TEST_PASSWORD}

    try:
        login_response = await client.post(LOGIN_URL, json=payload, headers=headers)
    except Exception as exc:
        return False, _build_error_detail(phase, "login_exception", None, request_id, None, str(exc))

    response_request_id = login_response.headers.get("X-Request-ID") or login_response.headers.get("X-Correlation-ID")
    if login_response.status_code != 200:
        return False, _build_error_detail(
            phase,
            "login",
            login_response.status_code,
            request_id,
            response_request_id,
            login_response.text,
        )

    token = login_response.json().get("access_token")
    if not token:
        return False, _build_error_detail(phase, "login_no_token", login_response.status_code, request_id, response_request_id, login_response.text)

    headers["Authorization"] = f"Bearer {token}"
    try:
        me_response = await client.get(ME_URL, headers=headers)
    except Exception as exc:
        return False, _build_error_detail(phase, "me_exception", None, request_id, response_request_id, str(exc))

    me_response_request_id = me_response.headers.get("X-Request-ID") or me_response.headers.get("X-Correlation-ID")
    if me_response.status_code != 200:
        return False, _build_error_detail(
            phase,
            "me",
            me_response.status_code,
            request_id,
            me_response_request_id,
            me_response.text,
        )

    return True, None


async def run_sequential(total: int) -> Tuple[List[float], List[Dict[str, Any]]]:
    latencies: List[float] = []
    errors: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        for i in range(total):
            start = time.perf_counter()
            ok, error = await _login_and_me(client, "sequential", i)
            latencies.append(time.perf_counter() - start)
            if not ok and error:
                errors.append(error)
    return latencies, errors


async def run_parallel(total: int, concurrency: int) -> Tuple[List[float], List[Dict[str, Any]]]:
    latencies: List[float] = []
    errors: List[Dict[str, Any]] = []
    semaphore = asyncio.Semaphore(concurrency)

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        async def worker(idx: int):
            async with semaphore:
                start = time.perf_counter()
                ok, error = await _login_and_me(client, "parallel", idx)
                latency = time.perf_counter() - start
                return ok, error, latency

        results = await asyncio.gather(*[worker(i) for i in range(total)])
        for ok, error, latency in results:
            latencies.append(latency)
            if not ok and error:
                errors.append(error)

    return latencies, errors


async def main():
    print("Phase 1: 1000 sequential login+me")
    seq_latencies, seq_errors = await run_sequential(1000)
    p95_seq = _percentile(seq_latencies, 95)
    print(f"Phase 1 p95 latency: {p95_seq * 1000:.2f} ms" if p95_seq else "Phase 1 p95 latency: n/a")
    _summarize_errors(seq_errors, "Phase 1")

    print("
Phase 2: 10 parallel users, total 1000 login+me")
    par_latencies, par_errors = await run_parallel(1000, 10)
    p95_par = _percentile(par_latencies, 95)
    print(f"Phase 2 p95 latency: {p95_par * 1000:.2f} ms" if p95_par else "Phase 2 p95 latency: n/a")
    _summarize_errors(par_errors, "Phase 2")

    total_errors = len(seq_errors) + len(par_errors)
    if total_errors:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
