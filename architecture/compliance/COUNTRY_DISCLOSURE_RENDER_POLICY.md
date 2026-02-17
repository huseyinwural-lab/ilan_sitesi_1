# Country Disclosure Render Policy

## 1. Impressum (Germany/Austria/Switzerland)
*   **Rule**: Mandatory for "Commercial" (Geweblich) sellers.
*   **Location**: Listing Detail Page (Seller Section) and Dealer Profile.
*   **Fields**: Company Name, Address, Contact, VAT ID, Register Court/Number, Managing Director.

## 2. Siret/Siren (France)
*   **Rule**: Mandatory for professionals.
*   **Location**: Seller Profile.

## 3. Implementation
*   The `DealerProfile` model (FAZ-U5) already has `impressum_text`.
*   **Frontend**: If `country in ['DE', 'AT', 'CH']` AND `seller_type == 'commercial'`, render the "Rechtliche Angaben" (Legal Info) link/accordion.
