# Healthcheck Policy v1

**Endpoints:**
-   `/api/health/liveness`: Returns 200 OK (App is running).
-   `/api/health/readiness`: Checks Dependencies.

## 1. Readiness Checks
-   **DB:** Select 1 (Timeout 2s).
-   **Redis:** Ping (Timeout 1s).
-   **Migrations:** Check `alembic_version` matches code head.

## 2. Deployment Gate
-   Kubernetes/Render probe must pass Readiness before routing traffic.
