# FAZ-U5 Scope Lock: EU Legal & Trust

## 1. Objective
To ensure the platform complies with EU Digital Services Act (DSA) and Consumer Rights Directives, specifically for "Commercial" sellers.

## 2. In-Scope

### 2.1. Dealer Profile (Commercial Identity)
*   **Mandatory Fields**: Company Name, Business Address, VAT ID / Tax Number.
*   **Legal Texts**: Imprint (Impressum), Terms & Conditions, Withdrawal Policy.
*   **Validation**: VIES (VAT Information Exchange System) check (Mock for MVP).

### 2.2. Consumer Protection (Listing View)
*   **Badges**: "Private Seller" vs "Commercial Seller" explicitly labeled.
*   **Disclaimers**: "Prices include VAT" (for B2C).

### 2.3. Listing Submission Guard
*   **Rule**: A user with `user_type='commercial'` CANNOT publish a listing if their Dealer Profile is incomplete.

## 3. Out-of-Scope
*   **Digital Contracts**: Automated PDF contract generation.
*   **Complex Tax Calculation**: Dynamic VAT rates per item (We assume standard rate).
