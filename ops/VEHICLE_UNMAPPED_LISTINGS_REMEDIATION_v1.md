# Vehicle Unmapped Listings Remediation v1

**Goal:** Resolve 34 Unmapped Listings to reach 0 Unmatched.
**Status:** BLOCKED until resolved.

## 1. Analysis of Unmapped Data
Most unmapped items stem from `seed_vehicle_listings.py` generating random strings like "Model 123" which do not exist in the real-world Master Data seed.

| Count | Issue | Remediation Strategy |
| :--- | :--- | :--- |
| ~30 | Random "Model X" strings | **Map to 'Other'** or **Random Valid Model** of same Make. |
| ~4 | Mismatched Make Strings | **Fuzzy Match** or **Delete**. |

## 2. Decision Logic (Script)
1.  Identify Listing with `make_id=NULL` or `model_id=NULL`.
2.  Parse `attributes->>'brand'`.
3.  If Brand matches a Master Make:
    -   Pick a random valid Model from that Make (since original data "Model 123" is garbage).
    -   *Why:* Preserves the listing structure for UI testing without polluting Master Data with "Model 123".
4.  If Brand is unknown:
    -   Delete Listing (It's garbage seed data).

## 3. Success Criteria
-   `SELECT count(*) FROM listings WHERE module='vehicle' AND (make_id IS NULL OR model_id IS NULL)` **MUST BE 0**.
