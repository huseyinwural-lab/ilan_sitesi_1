# Seed Execution Guardrails

**Policy:** Strict Environment Control

## 1. Environment Checks
-   **Local:** Allowed.
-   **Staging:** Allowed.
-   **Production:** **BLOCKED** by default.
    -   *Override:* Requires argument `--allow-prod` AND env var `SEED_CONFIRM_PROD=true`.

## 2. Execution Logic
-   **Dry Run:** Default mode if not specified. Shows what *would* happen.
-   **Idempotency:** Uses `SELECT` check before `INSERT`. Updates if exists (Upsert).
-   **Batch ID:** Logs execution UUID to `audit_logs` (System Action).

## 3. Rollback
-   Script does NOT provide auto-rollback.
-   **Manual Rollback:** Restore from DB Snapshot taken before execution.
