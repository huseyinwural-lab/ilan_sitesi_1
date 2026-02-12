# Hypercare Completion Criteria (T+24h)

**Target Date:** 2026-02-13 17:00 UTC
**Status:** PENDING

To officially exit Hypercare and return to Standard Operations, the following must be true:

## 1. Stability
- [ ] **Zero Critical Incidents:** No P0 (System Down) or P1 (Revenue Blocked) incidents.
- [ ] **Error Rates:**
    -   Global 5xx rate < 0.1%.
    -   Pricing 409 rate (Config Missing) = 0%.

## 2. Feature Verification
- [ ] **Expiry Job:** Successfully ran at least once (Exit Code 0).
- [ ] **Rate Limiting:** Confirmed `429` responses for abusive traffic, no reports of legitimate user blocking.
- [ ] **Publishing:** `listing_publish_success_rate` > 98%.

## 3. Data
- [ ] **Pricing Snapshots:** Random sampling of `invoice_items` shows populated `price_config_version`.
