# Technical Debt Inventory (P6)

## 1. Rate Limiting
- **Item:** In-Memory Storage (`_rate_limit_store`).
- **Impact:** Limits reset on restart; limits are per-pod (not global).
- **Plan:** Migrate to Redis (P6).

## 2. Observability
- **Item:** Logs are unstructured text/print statements in some places.
- **Impact:** Hard to parse in Datadog/ELK.
- **Plan:** Adopt `structlog` or standard JSON formatter globally.

## 3. Audit Logs
- **Item:** `AuditLog` table grows indefinitely.
- **Impact:** DB Bloat/Performance.
- **Plan:** Implement Partitioning or Archival Job (Move >1yr logs to S3).

## 4. Pricing Logic
- **Item:** "Hardcoded" fallback checks in legacy tests.
- **Impact:** Confusion during maintenance.
- **Plan:** Refactor legacy tests to strictly mock DB state.
