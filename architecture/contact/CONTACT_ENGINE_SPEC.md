# Contact Engine Spec

## 1. Data Model Extension (`listings`)
*   `contact_option_phone`: Boolean (Default: True). Allows users to see phone number.
*   `contact_option_message`: Boolean (Default: True). Allows internal messaging.

## 2. API: Reveal Phone
`GET /api/v1/listings/{id}/contact/phone`

### Logic
1.  Check if `listing.contact_option_phone` is True.
2.  Check if `listing.user.phone_number` exists and is verified (P27 requirement).
3.  **Log Event**: Record `listing_contact_clicked` in `user_interactions`.
4.  Return Phone Number.

## 3. API: Initiate Message
`POST /api/v2/mobile/messages/send` (Existing P26)
*   **Guard**: Check `listing.contact_option_message`.
