# Fail-Open Abuse Monitoring

**Strategy:** Reliability > Strictness.
**Risk:** If Redis fails, Rate Limiter fails open (allows all). Attackers could exploit this.

## 1. Detection Mechanism
-   **Metric:** `rate_limit_redis_errors_total`
-   **Log Event:** `event_type="rate_limit_fail_open"`

## 2. Alerting Rule
-   **Condition:** `rate_limit_redis_errors_total > 10` in 1 minute.
-   **Severity:** P1 (High).
-   **Notification:** PagerDuty + Slack.

## 3. Mitigation (Escalation Path)
If Redis is confirmed down and abuse is detected:
1.  **Ops:** Enable WAF "Under Attack" mode (Cloudflare/AWS WAF).
2.  **Dev:** Hot-patch `RATE_LIMIT_BACKEND="memory"` (Revert to local limits) via Env Var update.
    -   *Note:* This requires restart/redeployment of backend pods.

## 4. Reporting
A "Fail-Open Report" will be generated automatically for post-mortem if this state persists > 5 minutes.
