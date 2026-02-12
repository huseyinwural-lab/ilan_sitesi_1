# Seed Entity Mapping v1

## 1. Individual User
| Field | Source/Logic |
| :--- | :--- |
| `email` | `user_{i}@example.com` |
| `role` | `individual` |
| `is_verified` | 70% `True` |
| `country_scope` | `['DE']` (or TR/FR) |

## 2. Dealer (Commercial)
| Field | Source/Logic |
| :--- | :--- |
| `company_name` | Fake Company (e.g. "Berlin Auto GmbH") |
| `dealer_type` | `auto_dealer` or `real_estate_agency` |
| `application_id`| Generate dummy `DealerApplication` |
| **Tier** | Derived from `DealerPackage` link |
| `subscription` | Active `DealerSubscription` record |

## 3. Listing
| Field | Source/Logic |
| :--- | :--- |
| `title` | Generated "VW Golf 2020" / "Apartment in Munich" |
| `price` | Random(10k, 500k) |
| `category_id` | Fetch from existing `categories` table |
| `attributes` | Valid JSON matching category rules |
