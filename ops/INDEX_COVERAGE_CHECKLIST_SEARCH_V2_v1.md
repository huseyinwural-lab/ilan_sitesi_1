# Index Coverage Checklist Search v2 v1

**Status:** PENDING

## 1. Listings Table
- [ ] `category_id` (B-Tree) -> For filtering by category.
- [ ] `(price, id)` (B-Tree) -> For sorting/filtering by price.
- [ ] `(created_at, id)` (B-Tree) -> For default sort.

## 2. Listing Attributes Table
- [ ] `listing_id` (B-Tree) -> For joining back to listings.
- [ ] `(attribute_id, value_option_id)` (B-Tree) -> For Select Filters.
- [ ] `(attribute_id, value_number)` (B-Tree) -> For Range Filters.
-   *Note:* Boolean filters are low cardinality, index usage depends on distribution.

## 3. Findings
*(To be filled after Audit Script)*
