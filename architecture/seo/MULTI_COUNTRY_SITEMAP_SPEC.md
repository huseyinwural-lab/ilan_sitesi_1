# Multi-Country Sitemap Spec

## 1. Index Generation
A cron job runs daily to update `sitemap-index.xml`.

## 2. Country Sitemaps
*   **Query**: `SELECT id, slug, updated_at FROM listings WHERE status='active' AND country=:code`
*   **Frequency**: Daily or Real-time (cached).

## 3. Implementation
*   Endpoint: `GET /sitemap.xml` (Router)
*   Endpoint: `GET /sitemap-{country}.xml`
