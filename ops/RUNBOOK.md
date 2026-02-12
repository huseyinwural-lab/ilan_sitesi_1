# Operational Runbook (Ops)

**System:** Pricing & Scale Engine
**Version:** 1.0

## 1. Incident: Pricing Config Missing (409 Errors)
**Symptom:** Users report "Pricing configuration missing" or Alert `pricing_failures_total > 0`.
**Diagnosis:**
1.  Check Logs: Look for `PricingConfigError`. Note the `Country`, `Segment`, `Type`.
2.  Check DB:
    ```sql
    SELECT * FROM price_configs 
    WHERE country='{CODE}' AND is_active=true;
    ```
**Resolution:**
1.  **Emergency:** Insert missing config via Admin Panel or SQL seed.
2.  **Verify:** Ask user to retry (Idempotent).

## 2. Incident: Expiry Job Failure
**Symptom:** Alert "Expiry Job Failed" or Subscriptions remain active past `end_at`.
**Diagnosis:** Check logs for `expiry_worker`. Common issues: DB Timeout, Lock contention.
**Resolution:**
1.  Run manually: `./start_cron.sh` inside container.
2.  If DB lock: Kill blocking PID or wait.
3.  Verify: Check `audit_logs` for `SYSTEM_EXPIRE`.

## 3. Incident: Rate Limit False Positives
**Symptom:** Legitimate users reporting "Too many requests".
**Diagnosis:** Check `rate_limit_hits_total`. Identify if IP-based (NAT issue) or User-based.
**Resolution:**
1.  **Temporary:** Increase limit env var `RL_DEFAULT` and restart (or hot-reload if supported).
2.  **Whitelist:** Add IP/User to Whitelist (Code change required in v1).

## 4. Config Override (Emergency)
To bypass Rate Limiting completely during an incident:
1.  Set Env: `RATE_LIMIT_ENABLED=False`.
2.  Restart Service.
