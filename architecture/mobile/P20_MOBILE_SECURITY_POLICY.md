# P20: Mobile Security & Hardening Policy

## 1. Mobile Abuse Policy

### 1.1. Root & Jailbreak Detection
The mobile app MUST perform self-checks for:
*   **Android**: Root access, unlocked bootloader, emulator environment.
*   **iOS**: Jailbreak (Cydia, Cydia Substrate, etc.), simulator environment.

**Action**:
*   If detected, the app sends `X-App-Integrity: compromised` header or flag during Auth/Device Register.
*   **Backend**: Flags the `user_device` as high risk.
*   **Consequence**: Disable "Financial" features (Withdrawal) for this device, but allow "Read-only" access (Browsing).

### 1.2. Device Fingerprinting
*   We use `device_id` (UUID from App) + `IP Address` to create a `fingerprint_hash`.
*   **Salt Rotation**: The backend rotates the salt used for hashing every 30 days to prevent rainbow table attacks on leaked logs.

## 2. API Key & Signature Strategy

### 2.1. Request Signing (HMAC)
To prevent API replay attacks and unauthorized calls (e.g., from Postman):
1.  **Shared Secret**: Embedded in the App (Obfuscated).
2.  **Header**: `X-Signature: HMAC_SHA256(Path + Timestamp + Body, Secret)`
3.  **Backend Middleware**:
    *   Verifies `X-Signature`.
    *   Checks `X-Timestamp` (Max 60s drift allow).
    *   Rejects if invalid.

**MVP Status**: Documented for v1.1. For MVP, we rely on **HTTPS (TLS 1.2+)** and **Bearer Tokens**.

## 3. Penetration Test Checklist

| Category | Check | Status |
| :--- | :--- | :--- |
| **Data Storage** | Is `refresh_token` stored in SecureStorage/Keychain? | ✅ |
| **Data Storage** | Are cached listings excluded from system backup (iCloud)? | ⏳ (App Side) |
| **Network** | Is SSL Pinning enabled? | ⏳ (App Side) |
| **Auth** | Does `logout` invalidate the token on server? | ✅ |
| **Logic** | Can User A view User B's favorites by changing ID? | ✅ (RLS checked) |
| **Injection** | Are inputs sanitized (SQLi, XSS)? | ✅ (FastAPI/ORM default) |

## 4. Key Management Plan
*   **Google Maps Key**: Restricted by Bundle ID (Android) / App ID (iOS).
*   **FCM Key**: Stored in Server Environment (`.env`), never in App.
*   **Sentry/Analytics Key**: Public safe.
