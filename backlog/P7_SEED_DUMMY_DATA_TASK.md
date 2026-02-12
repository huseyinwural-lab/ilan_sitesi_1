# Task: Seed Dummy Data Script

**Script:** `app/backend/scripts/seed_dummy_users.py`

## Requirements
1.  **Arguments:**
    -   `--count-individual`: Default 20
    -   `--count-dealer`: Default 10
    -   `--clean`: Optional (Wipe users/dealers before start)
2.  **Safety:**
    -   Abort if `APP_ENV=production`.
3.  **Logic:**
    -   Create Users first.
    -   Create Dealers (linked to random users).
    -   Create Packages (if missing) & Subscriptions for Dealers.
    -   Create Listings (linked to Users/Dealers).
4.  **Output:**
    -   Print summary: "Created 20 users, 10 dealers, 40 listings."
