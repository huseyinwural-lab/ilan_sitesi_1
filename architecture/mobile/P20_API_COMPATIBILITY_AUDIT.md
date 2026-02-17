# P20: Mobile API Compatibility Audit

## 1. Overview
This audit assesses the readiness of the existing Backend API (`/api/v1`) for mobile consumption and defines the strategy for `/api/v2/mobile`.

## 2. API Versioning Strategy
**Decision**: Implement a **Mobile-Specific Facade (`/api/v2/mobile`)**.
*   **Why?**: Mobile apps require different payload structures (smaller JSONs), specific error codes, and strict versioning (forcing users to update app is hard).
*   **Implementation**: Create `app/routers/mobile/` which imports core services but exposes mobile-optimized endpoints.

## 3. Pagination Audit
*   **Current State**: Offset-based (`skip`, `limit`).
*   **Mobile Requirement**: Infinite Scroll.
*   **Gap Analysis**:
    *   Offset pagination gets slow for deep data and can cause duplicate/missing items if data changes while scrolling.
    *   *Recommendation*: Keep `skip/limit` for MVP (simplicity) but envelope the response.
    *   *Future*: Implement Cursor-based pagination (`last_id`) for Feeds.

**Standard Mobile List Response**:
```json
{
  "data": [...],
  "meta": {
    "page": 1,
    "limit": 20,
    "has_more": true,
    "next_cursor": "eyJpZCI6... (optional for future)"
  }
}
```

## 4. Error Handling Standardization
*   **Current State**: `HTTP 400` -> `{"detail": "Error message"}`.
*   **Problem**: "Error message" is localized string. Mobile app cannot toggle logic based on string text reliably.
*   **New Standard**:
    *   Return standardized Error Codes.
    *   Structure:
```json
{
  "error": {
    "code": "AUTH_INVALID_CREDENTIALS",
    "message": "E-posta veya şifre hatalı.",
    "user_message": "Giriş yapılamadı, lütfen bilgilerinizi kontrol edin.",
    "retryable": false
  }
}
```

## 5. Data Type Safety
*   **Decimal/Float**: Ensure all monetary values are sent as `String` or explicitly handled. Floating point errors in JSON parsing can be fatal in financial apps.
    *   *Rule*: Money -> String (e.g., "100.50").
*   **Date/Time**: Always ISO 8601 UTC (`YYYY-MM-DDTHH:mm:ssZ`).
*   **Null Safety**: Explicitly define nullable fields in API docs (OpenAPI/Swagger) to prevent Flutter `Null check operator used on a null value` crashes.

## 6. Action Items
1.  Setup `/api/v2/mobile` router prefix in `server.py`.
2.  Define `MobileResponse` and `MobileError` wrapper classes in backend.
3.  Audit `Listing` and `User` models to create optimized `MobileListingDTO` (exclude heavy backend fields).
