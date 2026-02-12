# Real Estate Listings Seed Scope v1

**Goal:** Populate DB with high-fidelity Real Estate Listings using the new Attribute structure.
**Target Env:** Local / Staging

## 1. Volume & Distribution
**Total Target:** 90 Listings

| Category | Count | Status Distribution | Countries |
| :--- | :--- | :--- | :--- |
| **Housing (Konut)** | 60 | 60% Active, 20% Pending, 20% Rejected | DE (30), TR (20), FR (10) |
| **Commercial (Ticari)**| 30 | 70% Active, 20% Pending, 10% Expired | DE (15), TR (10), FR (5) |

## 2. Status Rules
-   **Active:** Published < 30 days ago.
-   **Pending:** Created < 2 days ago.
-   **Rejected:** Created < 5 days ago, rejected reason filled.
-   **Expired:** Published > 90 days ago.

## 3. Ownership
-   Listings will be linked to the existing 10 Dealers and 20 Individual Users created in `seed_dummy_users.py`.
-   **Logic:** 80% Dealer owned, 20% Individual owned.
