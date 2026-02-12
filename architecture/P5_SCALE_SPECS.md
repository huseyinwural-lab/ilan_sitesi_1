# P5 Scale Specifications

## 1. P5-005: Subscription Expiry Job (Cron)

**Objective:** Automatically mark expired subscriptions as `expired` to prevent unauthorized usage and keep data clean.

### Specification
- **Schedule:** Daily at **00:00 UTC**.
- **Target Data:** `DealerSubscription` table.
- **Logic:**
  ```sql
  UPDATE dealer_subscriptions
  SET status = 'expired', updated_at = NOW()
  WHERE status = 'active' AND end_at < NOW();
  ```
- **State Machine:** `active` -> `expired`.
- **Idempotency:** The query is naturally idempotent (running it twice changes nothing if already expired).
- **Audit:**
  - System User (`system@platform.com`) logs the action.
  - Log summary: "Expired X subscriptions."
- **Performance:**
  - Use batch updates (SQL `UPDATE` is efficient).
  - Expected volume: < 10k rows/day. No pagination needed for MVP.

### Implementation Guide
- Create `app/jobs/expiry_job.py`.
- Use a simple script invokable via `cron` or `Celery` (if available).
- For Render: Add a "Cron Job" service running `./start_expiry_job.sh`.

---

## 2. P5-007: Rate Limiting Policy

**Objective:** Protect pricing and checkout endpoints from abuse and brute-force scanning.

### Specification
- **Scope:**
  1.  **Pricing Calculation:** `POST /api/pricing/calculate` (if public).
  2.  **Listing Creation:** `POST /api/commercial/dealers/.../listings` (Authenticated).
  3.  **Checkout:** `POST /api/commercial/.../buy` (Authenticated).

### Policy Limits (Config-Driven)
| Route Scope | Target | Limit | Window | Action |
| :--- | :--- | :--- | :--- | :--- |
| `listing_create` | `user_id` | 60 | 1 min | 429 Retry-After |
| `checkout_init` | `user_id` | 10 | 10 min | 429 Retry-After |
| `public_read` | `ip_address`| 100 | 1 min | 429 Retry-After |

### Technical Approach
- **Backend:** `FastAPI-Limiter` (Redis) or In-Memory (if Redis unavailable).
- **Standard:** Return `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After` headers.
- **Config:** Limits defined in `config.py` or `.env`.

### 429 Response Format
```json
{
  "detail": "Too many requests. Try again in 45 seconds.",
  "code": "rate_limit_exceeded"
}
```
