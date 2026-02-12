# Rate Limit Governance v2

**Effective:** v1.7.0+

## 1. Tier Lifecycle
### Adding a New Tier
1.  **DB Migration:** Add ENUM to `DealerPackage`.
2.  **Config:** Update `TIER_RATE_LIMIT_MATRIX`.
3.  **Deploy:** Backend deployment required.

### Updating Limits
1.  **Request:** PR to `app/config/limits.py`.
2.  **Approval:** Ops Lead + Product Owner.
3.  **Deploy:** Config update deployment.

## 2. Override Policy
-   **Emergency:** Ops can set `rl:override:{user_id}` in Redis directly with TTL=1h.
-   **Permanent:** Change Dealer Package via Admin Panel.

## 3. Escalation
-   **Level 1:** Individual IP Block (Automated).
-   **Level 2:** User Account Suspension (Manual Admin).
-   **Level 3:** Global Fail-Open (Ops Decision during outage).
