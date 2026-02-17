# i18n Core Architecture v1

## 1. Strategy
*   **Backend**: Returns localized strings for Categories, Attributes, and Errors based on `Accept-Language` header.
*   **Frontend**: Uses `react-i18next` for UI strings (Buttons, Labels).

## 2. Database Localization (JSONB)
Models like `Category`, `Attribute` use JSONB columns: `name = {"en": "House", "de": "Haus"}`.

### 2.1. Fallback Logic
If `de` is requested but missing:
1.  Check `en` (Global default).
2.  Check key itself.

## 3. SEO Localization
*   **Meta Tags**: Dynamically generated based on URL locale (`/de/...` -> German Title).
*   **URL Slugs**: `slug` field in DB is also JSONB or stored per locale. *Correction*: Current schema uses single slug. For V1, slugs are English or Localized once. V2 will have `slug_tr`, `slug_de`.
