# Cache Invalidation Strategy v1

**Goal:** Ensure Tier changes are immediate.

## 1. Triggers
Invalidation MUST happen when:
-   Dealer Tier is updated via Admin API.
-   Dealer Package is changed via Admin API.
-   Subscription status changes (e.g. Expired -> Active).

## 2. Target Keys
| Key Pattern | Description | Action |
| :--- | :--- | :--- |
| `rl:context:{user_id}` | Cached Tier & Limits | **DELETE** |
| `rl:listings:{old_tier}:{user_id}` | Rate Limit Counters | **DELETE** (Optional but recommended to reset burst) |

## 3. Implementation Logic
```python
async def invalidate_user_context(user_id: str, redis: Redis):
    # 1. Delete Context
    await redis.delete(f"rl:context:{user_id}")
    
    # 2. (Optional) Scan & Delete old counters?
    # Better: Just delete context. New context will generate new key 
    # `rl:listings:PREMIUM:{id}` which starts fresh.
    # The old key `rl:listings:STANDARD:{id}` will expire naturally.
```

## 4. Sync vs Async
-   **Decision:** **Synchronous**.
-   **Reason:** The Admin UI should only show "Success" when the limit is actually active.
-   **Rollback:** If Redis fails, log Error but do not revert DB transaction (Soft fail). Use "Best Effort" with alerting.
