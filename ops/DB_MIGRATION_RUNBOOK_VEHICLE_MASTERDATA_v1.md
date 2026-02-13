# DB Migration Runbook: Vehicle Master Data

**Environment:** Staging -> Production

## 1. Pre-Migration
-   Backup Database.
-   Verify Alembic Head matches Code.

## 2. Execution
-   Run `alembic upgrade head`.
-   Verify tables `vehicle_makes`, `vehicle_models` created.
-   Verify `listings` has `make_id`, `model_id`.

## 3. Post-Migration Smoke
-   Insert a dummy Make/Model via SQL.
-   Query `listings`.
