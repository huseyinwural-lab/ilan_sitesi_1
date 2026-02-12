# Load Test Spec (v1)

**Tool:** Locust or k6
**Target:** Staging Environment

## Scenario 1: Dealer Listing Burst
- **User:** 100 Concurrent Authenticated Dealers.
- **Action:** Each attempts to publish 10 listings in 1 minute.
- **Expectation:**
    - First 60 requests/min pass (per user).
    - Remaining requests receive `429 Too Many Requests`.
    - No 500 Errors.
    - Database locks hold (no negative quotas).

## Scenario 2: Login Brute Force
- **User:** 1 Attacker IP.
- **Action:** Send 1000 `POST /auth/login` requests with random creds.
- **Expectation:**
    - First 20 requests pass (200/401).
    - Request 21+ receive `429`.
    - Latency remains < 100ms for other users.

## Scenario 3: Expiry Race
- **Setup:** Create subscription expiring at `T+1 minute`.
- **Action:**
    - Run Expiry Job at `T+1:05`.
    - Simultaneously attempt `POST /listings`.
- **Expectation:**
    - Either Job wins -> Listing fails (403/409 Quota/Active Sub missing).
    - Or Listing wins -> Job expires sub afterwards.
    - **Critical:** Quota is not consumed from an expired subscription *after* the job commits.

## Scenario 4: Pricing Config Stress
- **Action:** Publish listing with Missing Config.
- **Expectation:** Immediate `409 Conflict`. Low latency (Fail-Fast).
