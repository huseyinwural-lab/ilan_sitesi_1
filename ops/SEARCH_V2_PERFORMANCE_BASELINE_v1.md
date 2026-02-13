# Search v2 Performance Baseline v1

**Dataset:** Seed v6 (~200 Listings)
**Env:** Staging

## 1. Measurements
| Scenario | Latency (p95) | DB Ops | Index Usage |
| :--- | :--- | :--- | :--- |
| **Simple Listing** | ~40ms | 1 | `ix_listings_...` |
| **Category Filter** | ~45ms | 2 | `ix_category_path` |
| **1 Facet Filter** | ~80ms | 3 | `ix_listing_attributes...` |
| **Complex Search** | ~120ms | 5+ | GIN/B-Tree Hybrid |

## 2. Thresholds
-   **p95 Goal:** < 150ms.
-   **Alert:** If > 300ms sustained.

## 3. Optimization
-   Ensure `ListingAttribute` indexes (`attribute_id`, `value_option_id`) are active.
