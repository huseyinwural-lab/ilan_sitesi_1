# P5-007: Rate Limiting Specification (v1.0)

## 1. Scope & Endpoints
The following endpoints are strictly rate-limited to prevent abuse and ensure stability.

| Endpoint | Method | Tier | Default Limit | Rationale |
| :--- | :--- | :--- | :--- | :--- |
| `/api/commercial/dealers/{id}/listings` | POST | User (Tier 1) | 60/min | Prevent listing spam/scaping. |
| `/api/commercial/dealers/{id}/packages/{pkg}/buy` | POST | User (Tier 1) | 10/10min | Protect payment initiation. |
| `/api/auth/login` | POST | IP (Tier 2) | 20/min | Brute-force protection. |
| `/api/auth/register` | POST | IP (Tier 2) | 10/min | Account spam protection. |
| `/api/pricing/calculate` (Future) | POST | User/IP | 100/min | Protect heavy calculation logic. |

## 2. Policy: Two-Tier Keying
**Strategy:**
1.  **Tier 1 (Authenticated):**
    -   **Key:** `rate_limit:user:{user_id}:{endpoint}`
    -   **Applies to:** Requests with valid Bearer Token.
2.  **Tier 2 (Anonymous/Fallback):**
    -   **Key:** `rate_limit:ip:{ip_address}:{endpoint}`
    -   **Applies to:** Public endpoints or Failed Auth.

## 3. Configuration (Config-Driven)
Limits must be defined in `config.py` or Environment Variables, NOT hardcoded in decorators.

**Env Variables:**
```bash
RATE_LIMIT_ENABLED=True
RATE_LIMIT_STORAGE_URL=redis://localhost:6379/0 (or memory)
RL_LISTING_CREATE="60/60" # 60 req per 60 sec
RL_AUTH_LOGIN="20/60"
RL_DEFAULT="100/60"
```

## 4. HTTP 429 Contract
**Response Standard:**
- **Status:** `429 Too Many Requests`
- **Headers:**
  - `Retry-After`: Seconds until reset (e.g., "30").
  - `X-RateLimit-Limit`: Total limit.
  - `X-RateLimit-Remaining`: Remaining quota.
  - `X-RateLimit-Reset`: Unix timestamp of reset.
- **Body:**
  ```json
  {
    "code": "rate_limit_exceeded",
    "detail": "Too many requests. Please try again in 30 seconds.",
    "meta": {
        "limit_key": "user:123:listing_create",
        "retry_after_seconds": 30
    }
  }
  ```

## 5. Idempotency & Write Path Compatibility
- **Scenario:** Client sends `create_listing`. Request is blocked (429).
- **Client Action:** Client must respect `Retry-After`.
- **Idempotency Key:** If client retries with *same* Idempotency Key after waiting, the server should process it normally.
- **Burst Tolerance:** Configuration should allow slight bursts (e.g., Token Bucket algorithm) rather than strict Fixed Window if possible, to accommodate rapid retry logic from buggy clients.

## 6. Observability
- **Metrics:**
  - `rate_limit_blocked_count` (Counter, labels: endpoint, tier)
  - `rate_limit_usage` (Histogram)
- **Logs:**
  - Log `429` events as `WARNING`.
  - Include `ip_address`, `user_id` (if avail), `endpoint`.

## 7. Rollout Plan
1.  **Phase 1 (Dev/Test):** Strict Mode. Verify logic.
2.  **Phase 2 (Stage):** Enable with production-like limits.
3.  **Phase 3 (Prod - Dry Run):** (If library supports) Log usage but don't block (Soft Limit).
4.  **Phase 4 (Prod - Enforce):** Activate Blocking. Monitor `blocked_count`.
