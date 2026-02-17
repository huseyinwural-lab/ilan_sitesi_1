# P20: Mobile Attribution Policy (Deferred Deep Linking)

## 1. Objective
To track affiliate installs correctly even if the user goes through the App Store flow.

## 2. The Flow
1.  **User A** shares link: `https://platform.com/ref/123`.
2.  **User B** clicks link on Mobile.
3.  **Landing Page** detects Mobile -> Redirects to App Store with `referrer=123` (Android) or Fingerprinting (iOS).
4.  **User B** installs & opens App.
5.  **App** sends "Install Event" to Backend with device info / clipboard content.
6.  **Backend** matches `123` code and attributes User B to User A.

## 3. Implementation (MVP)
Since we don't use a paid MMP (AppsFlyer/Adjust) yet:
*   **Method**: **Clipboard Pattern** (Low tech, high reliability).
    *   Web landing page: "Copy Code & Download App".
    *   App: On first launch, check clipboard for `ref_code:...`.
*   **Alternative**: **Dynamic Links** (Firebase Dynamic Links is deprecated). Use native `Universal Links` (iOS) / `App Links` (Android) which pass data if app installed, or fallback to web if not.

## 4. Attribution Endpoint
`POST /api/v2/mobile/affiliate/attribution`
*   **Input**: `{ referral_code: "XYZ", device_id: "..." }`
*   **Action**: Store `referral_code` in `device_install_log`. When user Registers later, pull this code automatically.
