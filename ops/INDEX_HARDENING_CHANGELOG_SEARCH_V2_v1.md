# Index Hardening Changelog Search v2 v1

**Status:** DRAFT

## 1. Existing Indexes
-   `ix_listings_...` (Standard columns).
-   `ix_listing_attributes_attr_val_opt` (Attribute filtering).

## 2. Proposed Hardening
-   If sorting by `price` is slow -> `CREATE INDEX ix_listings_price_id ON listings (price, id DESC)`.
-   If facet aggregation is slow -> Consider covering index or materialized view (Deferred to P7.3).
