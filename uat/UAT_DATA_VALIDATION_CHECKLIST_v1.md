# UAT Data Validation Checklist (v1.0)

**Target:** Seeded Data Integrity

## 1. Individual Users
- [ ] **Count:** Exactly 20 records (plus admin/demo users).
- [ ] **Distribution:**
    -   DE (Germany) ~10
    -   TR (Turkey) ~6
    -   FR (France) ~4
- [ ] **Verification:** ~70% have `is_verified=True`.

## 2. Commercial Members (Dealers)
- [ ] **Count:** Exactly 10 records.
- [ ] **Tier Distribution:**
    -   STANDARD: ~6
    -   PREMIUM: ~3
    -   ENTERPRISE: ~1
- [ ] **Subscriptions:** 100% have an active subscription linked to a valid Invoice.

## 3. Listings
-   **Count:** Exactly 40 records.
-   **Status:** Mixed (Active, Pending, Rejected).
-   **Localization:** Titles match Category Language (e.g. "Test Listing... - Apartments for Sale").

## 4. Configs
-   [ ] **Currencies:** DE->EUR, TR->TRY (if supp), FR->EUR.
-   [ ] **Packages:** 3 Types exist (Basic, Pro, Enterprise).
