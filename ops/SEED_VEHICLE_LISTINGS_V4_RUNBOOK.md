# Seed Vehicle Listings v4 Runbook

**Script:** `app/backend/scripts/seed_vehicle_listings.py`

## 1. Logic
1.  **Fetch Context:** Users, Dealers, Vehicle Categories.
2.  **Clean Old:** Delete existing vehicle listings (v1 seeds).
3.  **Generate:** Loop through templates.
    -   Use `faker` or predefined lists for Titles ("BMW 320d M Sport", "Ford Transit Van").
4.  **Insert:** Bulk insert.

## 2. Safety
-   `--allow-prod` required for Production.
