# Disaster Recovery Plan (v1)

**Scope:** Backend, DB, Redis
**RTO (Recovery Time Obj):** 1 Hour
**RPO (Recovery Point Obj):** 15 Minutes

## 1. Redis Recovery (Rate Limits)
-   **Scenario:** Cache Cluster Data Corruption.
-   **Action:**
    1.  FlushAll (Clear bad state).
    2.  System defaults to "Empty Counters" (Users get fresh limits).
    3.  **Impact:** Minor abuse risk for 1 hour. Acceptable.

## 2. Database Recovery (Core Data)
-   **Scenario:** Accidental Table Drop or Corruption.
-   **Action:**
    1.  Point-in-Time Recovery (PITR) via Cloud Provider Console to T-5 mins.
    2.  Redeploy Backend.
    3.  Re-run Expiry Job (Idempotent) to catch up status.

## 3. Configuration Disaster
-   **Scenario:** Env Vars deleted / Secrets lost.
-   **Action:** Restore from Terraform/Ansible State or Secret Manager History.

## 4. Drills
-   **Schedule:** Bi-Annual (Every 6 months).
-   **Next Drill:** June 2026.
-   **Test:** "Redis Failure & Fail-Open Behavior".
