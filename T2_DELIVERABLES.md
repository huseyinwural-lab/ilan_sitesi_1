# Phase T2 Deliverables & Definition of Done Report

## 1. Pricing Service Contract
**Service:** `PricingService`
**Method:** `calculate_listing_fee`

### Input
- `dealer_id` (UUID str): The dealer attempting to publish.
- `country` (str): Country code (e.g., "DE").
- `listing_id` (UUID str): Unique ID of the listing (must exist).
- `pricing_type` (str, default="pay_per_listing"): The type of charge to check for overage.

### Output (`CalculationResult`)
- `is_free` (bool): True if covered by Free Quota.
- `is_covered_by_package` (bool): True if covered by Subscription.
- `source` (str): One of `free_quota`, `subscription_quota`, `paid_extra`.
- `charge_amount` (Decimal): Net amount to charge (0 for free/sub).
- `currency` (str): Currency code.
- `vat_rate` (Decimal): Applicable VAT rate.
- `gross_amount` (Decimal): Total amount including VAT.
- `base_unit_price` (Decimal): Snapshot of the unit price from config.
- `price_config_version` (int): Version of the config used.

### Error Codes (Exceptions)
- `PricingIdempotencyError`: Listing already consumed (Idempotency check failed).
- `PricingConfigError`:
  - "No active VAT configuration found..."
  - "No active price configuration found..."
- `PricingConcurrencyError`: "Subscription quota exhausted during transaction" (Race condition).

---

## 2. Config Preconditions Checklist
The following configurations **MUST** exist in the database for the service to function:

1.  **CountryCurrencyMap**: Entry for the target country (e.g., `DE` -> `EUR`).
2.  **VatRate**: Active record for the target country (e.g., `DE` -> `19.00`).
3.  **PriceConfig**: Active record for `segment='dealer'`, `pricing_type='pay_per_listing'`, `country='DE'` (Required for Overage).
4.  **FreeQuotaConfig** (Optional but recommended): Active record for `segment='dealer'`, `country='DE'`. If missing, Free Quota is skipped (0).

**Fail-Fast Rule:** If VAT or Overage Price Config is missing when needed, the service raises `PricingConfigError` and blocks the transaction.

---

## 3. Pricing Waterfall Scenario Matrix
| Scenario | User Type | Free Quota | Sub Quota | Overage Config | Expected Source | Charge |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Dealer | Available | N/A | N/A | `free_quota` | 0 |
| 2 | Dealer | Exhausted | Available | N/A | `subscription_quota` | 0 |
| 3 | Dealer | Exhausted | Exhausted | Available | `paid_extra` | Price |
| 4 | Dealer | Exhausted | None | Available | `paid_extra` | Price |
| 5 | Dealer | None | Available | N/A | `subscription_quota` | 0 |
| 6 | Dealer | None | None | Available | `paid_extra` | Price |
| 7 | Dealer | Exhausted | Exhausted | **Missing** | **ERROR** | N/A |
| 8 | Dealer | N/A | N/A | N/A | **ERROR (VAT)** | N/A |
| 9 | Individual | Available | N/A | N/A | `free_quota` | 0 |
| 10| Individual | Exhausted | N/A | Available | `paid_extra` | Price |
| 11| Edge | Available | N/A | N/A | `free_quota` | 0 |
| 12| Edge (Race)| Exhausted | **Taken** | Available | **ERROR/Retry** | N/A |

---

## 4. Concurrency & Idempotency Rules
1.  **Strict Idempotency:**
    - Before calculation, `check_idempotency` queries `ListingConsumptionLog`.
    - If a log exists for `listing_id`, it raises `PricingIdempotencyError`.
    - Unique constraint on `listing_id` in logs is enforced via application logic (and should be backed by DB index).

2.  **Atomic Transactions:**
    - `commit_usage` executes within a database transaction.
    - **Row-Level Locking:** `SELECT ... FOR UPDATE` is used on `DealerSubscription` to prevent double-spending of quota.
    - If quota is exhausted between check and commit, `PricingConcurrencyError` is raised.

3.  **Immutable Snapshots:**
    - `InvoiceItem` stores `base_unit_price`, `applied_vat_rate`, `price_config_version` at the time of creation.
    - Future changes to `PriceConfig` do NOT affect existing Invoice Items.

---

## 5. Post-T2 Priority Queue
1.  **Cron Job (P5-005):** Daily worker to expire subscriptions (`status -> Expired`).
2.  **Rate Limiting (P5-007):** Protect checkout and pricing endpoints.
3.  **Observability (P5-008):** Dashboard metrics for active subs, refund ratios.
4.  **Audit Logs:** Track who changed `PriceConfig` or `FreeQuotaConfig`.

