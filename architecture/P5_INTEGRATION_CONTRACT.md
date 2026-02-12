# P5 Integration Contract: Pricing Service

## 1. Overview
This contract defines how the `PricingService` integrates with the Core Listing API (`create_dealer_listing`). The integration acts as a **Hard Gate**, meaning no listing can go "Live" or "Pending Moderation" without successfully passing through the pricing engine.

## 2. Endpoint Workflow
**Target Endpoint:** `POST /api/commercial/dealers/{dealer_id}/listings`

**Sequence:**
1.  **Validation:** Check Dealer existence and Auth.
2.  **Draft Creation:** Instantiate `Listing` object in memory (or DB with status `draft`/`pending`).
3.  **Pricing Calculation (Hard Gate):**
    - Call `PricingService.calculate_listing_fee(dealer_id, country, listing_id)`
    - **Input:** `listing_id` (generated UUID), `dealer_id`, `country`.
    - **Output:** `CalculationResult` (Free/Sub/Paid, Amounts, VAT).
4.  **Decision Point:**
    - If `PricingConfigError` -> **Abort** (Return 409 Conflict / 422 Unprocessable).
    - If `PricingIdempotencyError` -> **Abort/Recover** (Return existing result).
5.  **Commit Usage:**
    - Call `PricingService.commit_usage(...)` inside the DB transaction.
    - If `paid_extra`: Generate `Invoice` & `InvoiceItem`.
    - If `subscription`: Decrement quota (with Lock).
6.  **Finalize:**
    - Save `Listing` with status `pending` (for moderation) or `active`.
    - Return Success Response with pricing details.

## 3. Error Behavior (Fail-Fast)
| Error Type | HTTP Status | User Message | System Action |
| :--- | :--- | :--- | :--- |
| `PricingConfigError` | 409 Conflict | "Pricing configuration missing for this region. Contact Support." | Block Publish. Log Error. |
| `PricingConcurrencyError` | 429 Too Many Requests | "System busy, please retry." | Rollback. Safe to retry. |
| `PricingIdempotencyError`| 200 OK | (Return existing success) | No Action (Already done). |

## 4. Idempotency & Retry Safety
- **Key:** `listing_id`
- The `ListingConsumptionLog` table has a unique index on `listing_id`.
- If the endpoint is called twice for the same Listing ID (e.g., network timeout), the service detects existing log and prevents double billing.

## 5. Frontend Smoke Tests
**Scenario A: Free Quota Available**
- **Action:** Publish Listing.
- **UI Expectation:** "Listing Published (Free Quota Used: 1/10)".
- **Backend Verification:** `ListingConsumptionLog.source = 'free_quota'`, `charged_amount = 0`.

**Scenario B: Subscription Quota Available**
- **Action:** Publish Listing (Free exhausted).
- **UI Expectation:** "Listing Published (Package Quota Used)".
- **Backend Verification:** `ListingConsumptionLog.source = 'subscription_quota'`, `DealerSubscription.used_listing_quota` incremented.

**Scenario C: Overage (Pay-per-listing)**
- **Action:** Publish Listing (Quotas exhausted).
- **UI Expectation:** "Listing Published. Fee: 5.00 EUR (+VAT)".
- **Backend Verification:** `Invoice` created, `ListingConsumptionLog.source = 'paid_extra'`, `InvoiceItem` snapshot matches current price.

**Scenario D: Missing Config**
- **Action:** Publish Listing in new Country (e.g., 'IT') without Config.
- **UI Expectation:** Error Toast: "Configuration missing for IT. Cannot calculate price."
- **Backend Verification:** 409 Conflict response.

## 6. Security
- **Authorization:** Only the Dealer Owner or Admin can trigger this flow.
- **Anti-Tamper:** Price, Currency, and VAT are strictly derived from Server-Side Configs. User input for these values is **ignored**.
