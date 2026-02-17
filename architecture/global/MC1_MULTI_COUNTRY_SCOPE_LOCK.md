# FAZ-MC1 Scope Lock: Multi-Country Hardening

## 1. Objective
To prepare the platform for simultaneous operation in 4 countries (DE, AT, CH, FR) under a single domain (`.com/{country}`).

## 2. In-Scope

### 2.1. Country Configuration
*   **Active Countries**: Germany (DE), Austria (AT), Switzerland (CH), France (FR).
*   **Currency**: Fixed EUR (CHF for Switzerland displayed as ~EUR for MVP/MC1 or handled as display only). *Correction: Decision 2 says Fixed EUR.*
*   **Language**:
    *   DE, AT, CH -> German (de)
    *   FR -> French (fr)
    *   TR -> Turkish (tr) - *Existing*

### 2.2. Data Isolation
*   **Strict Rule**: API requests MUST have `?country=XX` or path param `/{country}/...`.
*   **Cross-Border**: Users can view listings from other countries, but default view is scoped.

### 2.3. SEO Architecture
*   **Structure**: `platform.com/{country}/emlak/...`
*   **Hreflang**: Automated generation for cross-country pages.

## 3. Out-of-Scope
*   **Multi-Currency Payment**: We stick to EUR stripe accounts for now.
*   **Separate Legal Entities**: One global entity operates the platform.
