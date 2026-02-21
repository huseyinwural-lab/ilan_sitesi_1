# P0_EXECUTION_LOCK

## Sıra (Kilitleme)
1) Billing audit standardı + admin endpoint
2) Wizard mapping + category NOT NULL + make/model mapping
3) Moderation SQL (approve)
4) Public Search V2 SQL
5) Email SendGrid prod switch
6) Staging smoke runbook

## Gate'ler ve Evidence
| Adım | Gate | Evidence |
|---|---|---|
| 1 | /api/admin/audit-logs?scope=billing PASS | /app/docs/BILLING_AUDIT_STANDARD_V1.md, /app/ops/BILLING_AUDIT_EVIDENCE.md |
| 2 | create→submit→detail PASS | /app/ops/FINAL01_LOCAL_E2E.md |
| 3 | submit→approve→active PASS | /app/ops/FINAL01_LOCAL_E2E.md |
| 4 | /api/v2/search SQL PASS | /app/ops/FINAL01_LOCAL_E2E.md |
| 5 | SendGrid env + prod startup guard PASS | /app/docs/EMAIL_PROVIDER_SWITCH.md |
| 6 | staging smoke runbook hazır | /app/ops/SMOKE_FINAL01_STAGING.md |
