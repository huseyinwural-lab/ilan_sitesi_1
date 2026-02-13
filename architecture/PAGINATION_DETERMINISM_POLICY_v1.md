# Pagination Determinism Policy v1

**Rule:** Sort stability is mandatory.

## 1. Implementation
-   **API Layer:** `search_routes.py` MUST append `, Listing.id` to every `order_by`.
-   **DB Layer:** Ensure ID is unique/primary key (Already true).

## 2. Test Case
-   Fetch Page 1 (Limit 10). Note IDs.
-   Fetch Page 2 (Limit 10). Note IDs.
-   **Pass:** Intersection is Empty.
