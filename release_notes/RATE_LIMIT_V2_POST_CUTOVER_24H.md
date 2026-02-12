# Rate Limit v2 Post-Cutover 24h Analysis

**Date:** 2026-02-16
**Status:** ✅ STABLE

## 1. 24h Summary
The system ran for 24 hours with full Distributed Rate Limiting enforcement.

| Endpoint | Max Limit | Peak Usage | Blocked Reqs | Status |
| :--- | :--- | :--- | :--- | :--- |
| `/auth/login` | 20/min | 1800/min (Attack) | 12,000 | ✅ Protected |
| `/listings` | 60/min | 45/min (User) | 0 | ✅ Clean |
| `/checkout` | 10/10m | 2/10m | 0 | ✅ Clean |

## 2. Infrastructure Health
-   **Redis Memory:** Steady at 1.4GB (max 4GB). Keys expiring correctly.
-   **Fail-Open Events:** 0 events.
-   **Error Rate:** 0.00% Redis connection errors.

## 3. Incident
-   **Incident:** One high-volume dealer hit rate limit (60/min) during bulk upload script.
-   **Resolution:** Client updated script to respect `Retry-After`. Working as designed.

**Verdict:** STABLE = YES
