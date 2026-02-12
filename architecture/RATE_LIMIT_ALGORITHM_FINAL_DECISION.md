# Rate Limit Algorithm Final Decision

**Algorithm:** **Fixed Window (with Tier buckets)**
**Rejection:** Sliding Window Log was rejected due to high memory cost (storing timestamps) vs benefit for current scale.

## 1. Selected Model: Fixed Window + Burst Token
-   **Primary:** Redis `INCR` + `EXPIRE` (Simple Counter).
-   **Burst:** We implicitly allow burst up to the limit within the minute window.
-   *Wait, scope said "Burst Control"*.
-   **Correction:** To support Burst Control properly without high cost, we use **Token Bucket (Lua)**.
    -   Bucket Size = Burst Capacity.
    -   Refill Rate = Limit / 60 seconds.

## 2. Redis Data Model (Token Bucket)
-   **Key:** `rl:{scope}:{tier}:{id}` (Hash)
    -   `tokens`: Current count.
    -   `last_refill`: Timestamp.
-   **Atomic:** Lua script performs calc and update.

## 3. Performance & Cost
-   **Latency:** < 1ms (Single Lua call).
-   **Memory:** Small Hash (2 fields). No list of timestamps.
-   **TTL:** Expire key after `window_size` of inactivity to save space.

## 4. Cleanup
-   Redis `volatile-lru` handles cleanup if maxmemory reached.
