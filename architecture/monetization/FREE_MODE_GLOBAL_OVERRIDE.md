# Free Mode Global Override Policy

## 1. Strategy
To gain rapid traction in new markets (DE, FR, CH, AT), we override the default monetization rules.

## 2. Implementation
*   **Feature Flag**: `MONETIZATION_FREE_MODE` (Global or Per-Country).
*   **Effect**:
    *   Listing Quota Check -> Always Returns `True`.
    *   Dealer Plan Check -> Always Returns `True`.
    *   Premium Products -> Price = €0.00 (or hidden from UI).

## 3. Exit Strategy (Future)
1.  **Monitor**: When Active Listings > 10,000 in a country.
2.  **Action**: Disable Flag for that country.
3.  **Communication**: Email users 30 days prior.
