# P5-007: Rate Limiting Specification

## 1. Ticket Set (Implementation Plan)

### 🎫 Ticket 1: Rate Limit Infrastructure
- **Task:** Install and configure rate limiting library.
- **Library:** `fastapi-limiter` (Redis) or custom memory-based middleware (if Redis not available).
- **Config:** Add rate limit values to `.env` or `config.py`.
  - `RATE_LIMIT_LISTING_CREATE=60/minute`
  - `RATE_LIMIT_CHECKOUT=10/10minute`
- **Acceptance:** Redis connection established (or memory fallback active).

### 🎫 Ticket 2: Endpoint Protection (Guards)
- **Task:** Apply decorators/dependencies to critical endpoints.
- **Targets:**
  - `POST /api/commercial/dealers/{id}/listings` (User ID based)
  - `POST /api/commercial/.../buy` (User ID based)
  - `POST /api/auth/login` (IP based - stricter)
- **Acceptance:** Headers `X-RateLimit-Remaining` present in responses.

### 🎫 Ticket 3: Observability & Handling
- **Task:** Standardize 429 responses and logging.
- **Details:**
  - Custom Exception Handler for `RateLimitExceeded`.
  - Return JSON: `{"code": "rate_limit_exceeded", "detail": "...", "retry_after": 30}`.
  - Log 429 events for security monitoring.

## 2. Rate Limit Policy v1
| Scope | Key | Limit | Window | Action |
| :--- | :--- | :--- | :--- | :--- |
| **Listing Publish** | `user_id` | 60 | 1 min | Block |
| **Pricing Calc** | `user_id` | 100 | 1 min | Block |
| **Checkout Init** | `user_id` | 10 | 10 min | Block |
| **Public/Auth** | `ip_address`| 20 | 1 min | Block |

## 3. Response Standard
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 45
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
Content-Type: application/json

{
  "code": "rate_limit_exceeded",
  "detail": "Too many requests. Please try again in 45 seconds."
}
```
