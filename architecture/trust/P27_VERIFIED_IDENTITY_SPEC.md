# P27: Verified Identity Layer (KYC-Lite)

## 1. Objective
To reduce fraud and increase trust by verifying user identities.

## 2. Verification Methods

### 2.1. Phone Verification (OTP)
*   **Mandatory** for: Posting listings, Sending messages.
*   **Provider**: Twilio / AWS SNS (Mock for MVP).
*   **Flow**:
    1.  User inputs phone.
    2.  System sends 6-digit code.
    3.  User inputs code -> `is_phone_verified = True`.

### 2.2. Identity Verification (Optional)
*   **Optional** for: "Trusted Seller" badge.
*   **Provider**: Stripe Identity / Onfido (Mock for MVP).
*   **Flow**: Upload ID photo -> webhook callback -> `is_identity_verified = True`.

## 3. Badge Logic
*   **Phone Badge**: 📱 (Automatic upon OTP)
*   **Identity Badge**: 🛡️ (Automatic upon KYC)
*   **Blue Checkmark**: Phone + Identity + Rating > 4.5.

## 4. Database Schema Update
Add to `users`:
*   `phone_number`: String (Unique)
*   `is_phone_verified`: Boolean
*   `is_identity_verified`: Boolean
*   `verification_data`: JSONB (Provider metadata)
