# Healthcheck Policy v1

**Endpoint:** `/api/health/readiness`

## 1. Checks
-   **DB:** `SELECT 1` (Critical).
-   **Redis:** `PING` (Critical for Rate Limit, Fail-Open allowed but status should reflect Degraded).
-   **Migrations:** Compare `alembic_version` with `code_head`.

## 2. Response
-   **200 OK:** All Critical systems UP.
-   **503 Service Unavailable:** DB Down.
