# Pricing Entrypoint (Authoritative)

## Entry Point
- **Service:** `app/services/pricing_service.py`
- **Method:** `PricingService.calculate_listing_fee(dealer_id, country, listing_id, pricing_type)`

## Call Chain (target)
- Future campaigns read-path should hook into `PricingService.calculate_listing_fee` after base price is calculated and before returning `CalculationResult`.

## Notes
- Current repo references to `calculate_listing_fee` only in tests. This method is the authoritative pricing computation layer.
- Campaigns read-path will be activated once Postgres is available and `Campaign` table is migrated.
