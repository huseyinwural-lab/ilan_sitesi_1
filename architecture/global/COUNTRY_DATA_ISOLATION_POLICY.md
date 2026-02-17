# Country Data Isolation Policy

## 1. API Level Isolation
*   **Middleware**: `CountryMiddleware` (P19) already extracts country from URL path.
*   **Dependency**: `get_current_country` injects the scope into Services.

## 2. Database Level Isolation
*   **Listings**: `WHERE country = :current_country` is mandatory for Search/Feed.
*   **Dealers**: `WHERE country = :current_country`.
*   **Users**: Users are *Global* (can login anywhere), but their "Home Country" is set.

## 3. SEO Isolation
*   `sitemap-de.xml` contains ONLY `country='DE'` listings.
*   `robots.txt` points to index sitemap.
