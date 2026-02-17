# FAZ-U7 Scope Lock: Listing Display

## 1. Objective
To display a listing in a user-friendly, SEO-optimized, and secure manner.

## 2. In-Scope Components
*   **Detail Page**: `DetailPage.js` (React).
*   **Public API**: `GET /api/v1/listings/{id}`.
*   **SEO**:
    *   Canonical URLs.
    *   Meta Tags (Title, Description, OG Image).
    *   301 Redirect logic for slug changes.
*   **Interactions**:
    *   "Reveal Phone" (Already in U6 backend, needs UI).
    *   "Message Seller" (Link to P26 messaging).

## 3. Out-of-Scope
*   **Similar Listings**: Deferred (AI/Vector search needed).
*   **Map View**: Static image or simple link for now.
