# EU Compliance Spec

## 1. Data Model: `dealer_profiles`
*   `user_id` (FK)
*   `company_name`: Official registered name.
*   `vat_number`: e.g., "DE123456789".
*   `address_street`, `address_zip`, `address_city`, `address_country`.
*   `contact_email`, `contact_phone`.
*   `impressum_text`: Custom text required by German law (Telemediengesetz).
*   `terms_text`: AGB.
*   `withdrawal_policy_text`: Widerrufsbelehrung.

## 2. Listing Display Logic
If `listing.user_type_snapshot == 'commercial'`:
1.  Show "Commercial Seller" badge.
2.  Display "Legal Information" section in accordion (Impressum, Terms).
3.  Show "14-Day Right of Withdrawal" notice.

If `listing.user_type_snapshot == 'individual'`:
1.  Show "Private Seller" badge.
2.  Show disclaimer: "Consumer protection laws does not apply to this private sale."
