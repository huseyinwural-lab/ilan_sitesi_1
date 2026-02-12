# Changelog

## [v1.5.0-P5-HARDENING] - 2026-02-12

**Phase:** P5 Scale Hardening
**Status:** PROD-READY

### Added
- **Pricing Engine Hard Gate:** Listings cannot be published without valid pricing calculation. Missing configuration triggers `409 Conflict`.
- **Subscription Expiry Job:** Daily cron worker (`expiry_worker.py`) automates `active` -> `expired` state transitions based on UTC time.
- **Rate Limiting (Tier 1 & 2):** 
  - Tier 1: Token-based limits for authenticated users (e.g., Listing Creation: 60/min).
  - Tier 2: IP-based limits for public endpoints (e.g., Login: 20/min).
- **Concurrency Protection:** Implemented `SELECT FOR UPDATE` row-level locking for critical quota consumption.
- **Fail-Fast Logic:** Explicit `PricingConfigError` prevents zero-price listings due to misconfiguration.

### Changed
- **Commercial API:** `create_dealer_listing` now strictly integrates with `PricingService`.
- **Database:** Added `ix_dealer_subscriptions_status_end_at` index for performance.

### Security
- **Abuse Prevention:** Rate limiting middleware mitigates brute-force and spam attacks.
- **Financial Integrity:** Idempotency checks prevent double-charging.
