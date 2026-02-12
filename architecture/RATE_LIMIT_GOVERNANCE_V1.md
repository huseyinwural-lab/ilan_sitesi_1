# Rate Limit Governance Policy (v1)

**Effective Date:** 2026-02-16

## 1. Default Policy
Every NEW public or authenticated write endpoint MUST have a rate limit defined.

| Type | Default Limit | Key Strategy |
| :--- | :--- | :--- |
| **Read (Public)** | 100/min | IP-Based |
| **Write (Auth)** | 60/min | User-Based |
| **Critical (Auth)**| 10/min | User-Based (Login, Pay) |

## 2. Change Management
-   **Request:** Submit PR modifying `app/core/config.py` (Limit constants).
-   **Review:** Required from 1 Backend Lead + 1 DevOps.
-   **Rollout:** Config change requires deployment (ENV update).

## 3. Escalation
-   **DDoS:** If Global 429 > 20%, Ops triggers "Under Attack" WAF rules.
-   **VIP Bypass:** Specific Dealer limits can be overridden in `redis` directly (Manual Op) or future Admin UI.

## 4. Key Lifecycle
-   Keys MUST include `v1` versioning if logic changes drastically.
-   Current Pattern: `rl:{scope}:{tier}:{id}`.
