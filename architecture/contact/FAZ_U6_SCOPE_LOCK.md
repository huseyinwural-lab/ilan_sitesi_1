# FAZ-U6 Scope Lock: Contact & Privacy

## 1. Objective
To facilitate communication between buyers and sellers while protecting privacy and preventing spam.

## 2. In-Scope

### 2.1. Contact Methods
*   **Internal Messaging**: Primary method (Integrated with P26).
*   **Phone Call**: Optional (Seller can hide phone number).

### 2.2. Privacy Controls
*   **Masked Phone**: Phone number is not shown in HTML source. Fetched via API on click.
*   **Consent**: Seller explicitly opts-in to show phone number per listing.

### 2.3. Anti-Spam (Basic)
*   **Rate Limit**: Limit "Reveal Phone" requests per IP/User.
*   **Captcha**: Required for anonymous users (Future/Client-side).

## 3. Analytics
*   Track "Click to Call" events as `listing_contact_clicked` (P21).
