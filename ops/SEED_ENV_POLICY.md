# Seed Environment Policy

**Strict Rule:** Seed scripts are strictly prohibited in Production.

## 1. Safety Guards
-   **Code Guard:** Script must check `os.environ.get("APP_ENV") != "production"`.
-   **DB Guard:** Script checks if table `users` count > 100 (If huge data exists, abort to prevent messing up prod-like staging).

## 2. Usage
-   **Local:** `make seed` or `python scripts/seed_dummy_users.py`.
-   **Staging:** Trigger via CI/CD pipeline "Reset & Seed" job.

## 3. Reset Procedure
-   Before seeding, optional `--clean` flag can wipe data.
-   **Warning:** Cleaning wipes `users`, `dealers`, `listings`. Does not wipe `countries`, `categories` (Static Configs).
