# P20: Mobile Authentication Flow (Auth Contract v2)

## 1. Overview
Mobile authentication differs from Web. We cannot rely on `HttpOnly` cookies easily for cross-platform apps (especially in generic http clients). We need a robust **Token-Based Auth** with secure storage.

## 2. Token Lifecycle
*   **Access Token (JWT)**:
    *   Short-lived (15 minutes).
    *   Sent in Header: `Authorization: Bearer <token>`.
    *   Stored in **Memory** (Variable in Riverpod state). *Never* persisted to disk to minimize theft risk if device is compromised (though sandboxed).
*   **Refresh Token (Opaque/JWT)**:
    *   Long-lived (30 days).
    *   Used ONLY to get new Access Tokens.
    *   Stored in **Secure Storage** (Keychain on iOS, Keystore on Android).

## 3. The "Silent Refresh" Flow
The user should never be logged out unless they explicitly click "Logout" or the Refresh Token expires/is revoked.

1.  **App Start**:
    *   Check Secure Storage for `refresh_token`.
    *   If missing -> Show Login Screen.
    *   If present -> Call `/api/v2/mobile/auth/refresh`.
        *   *Success*: Get new Access Token -> Go to Home.
        *   *Fail (401)*: Delete `refresh_token` -> Show Login Screen.

2.  **During Usage (Interceptor)**:
    *   User performs action (e.g., Like Listing).
    *   API returns `401 Unauthorized`.
    *   **Dio Interceptor** catches 401.
    *   **Lock** all other outgoing requests.
    *   Call `/api/v2/mobile/auth/refresh` using stored Refresh Token.
        *   *Success*: Update Access Token in Memory -> **Retry** the failed request -> Unlock queue.
        *   *Fail*: Clear Storage -> Force Redirect to Login.

## 4. Security Specifics
*   **Logout**: Must call API `/auth/logout` to blacklist/revoke the Refresh Token on server side, then clear local storage.
*   **Biometrics (FaceID/TouchID)**:
    *   Optional layer *before* accessing the Refresh Token for sensitive actions (e.g., Withdraw Funds).

## 5. Endpoints Required
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v2/mobile/auth/login` | Returns `{ access_token, refresh_token }` |
| `POST` | `/api/v2/mobile/auth/refresh` | Input: `{ refresh_token }`. Returns `{ access_token, refresh_token (rotated) }` |
| `POST` | `/api/v2/mobile/auth/logout` | Revokes Refresh Token. |
