# Production Deployment Checklist

**Version:** v1.8.0
**Executor:** DevOps

## 1. Pre-Flight
- [ ] **Backup:** DB Snapshot taken.
- [ ] **Maintenance:** Window announced (10 mins).
- [ ] **Redis:** Connection verified via Bastion.

## 2. Deployment
- [ ] **Migration:** `alembic upgrade head` (Adds tier column - already done in P6 S2, verifying no drift).
- [ ] **Backend:** Deploy `v1.8.0` image.
- [ ] **Frontend:** Deploy Admin Build to CDN.

## 3. Configuration
- [ ] **Feature Flags:**
    -   `TIER_LIMIT_ENABLED=True`
    -   `RATE_LIMIT_ENFORCE=True`
-   **Limits:** Verify `TIER_RATE_LIMIT_MATRIX` matches spec.

## 4. Rollback
-   **Trigger:** 5xx > 1% or Admin Login fails.
-   **Action:** Revert Container Image to `v1.7.0`.
