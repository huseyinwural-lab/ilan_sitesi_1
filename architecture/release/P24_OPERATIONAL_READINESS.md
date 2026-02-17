# P24: Operational Readiness Handbook

## 1. Release Strategy
*   **Versioning**: Semantic Versioning (`v1.0.0`, `v1.1.0`).
*   **Tagging**: Git tags trigger CI/CD pipeline.
*   **Cadence**: Bi-weekly releases on Tuesday.

## 2. Incident Response Plan

### 2.1. Severity Matrix
| Sev | Impact | Response Time | Example |
| :--- | :--- | :--- | :--- |
| **SEV-1** | System Down | 15 mins | Database crash, API 500s > 10% |
| **SEV-2** | Feature Broken | 1 hour | Search down, Recommendations stuck |
| **SEV-3** | Minor Bug | 24 hours | UI glitch, Typo |

### 2.2. Escalation Path
1.  **Level 1**: On-Call Engineer (Check Logs, Restart Services).
2.  **Level 2**: Tech Lead (Rollback, DB Restore).
3.  **Level 3**: CTO/VP (Customer Communication).

## 3. Monitoring Checklist (Soft Launch)
*   **Infrastructure**: CPU, RAM, Disk Usage (Supervisor/Docker).
*   **Application**:
    *   `backend.err.log`: Watch for `Traceback`.
    *   `ml_prediction_logs`: Watch for `avg_score` drift.
*   **Business**:
    *   `user_interactions`: Is traffic arriving?
    *   `audit_logs`: Are admins active?

## 4. Soft Launch Config (Country: TR)
*   **Traffic**: 100% of TR users.
*   **Features**:
    *   ML Ranking: **ON** (Group B).
    *   Experiment: `revenue_boost_v1` **ACTIVE**.
*   **Limits**:
    *   Rate Limit: 60/min.
    *   DB Pool: 20 conns.
