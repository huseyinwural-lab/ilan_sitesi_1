# SEO URL Specification (Real Estate)

## 1. Listing Page (SERP)
Format: `/{country-code}/emlak/{segment-slug}/{transaction-slug}/{type-slug}/{city-slug}`

### Examples
*   `/de/emlak/konut/satilik/daire/berlin`
*   `/tr/emlak/ticari/kiralik/ofis/istanbul`

### Rules
*   **Slug Normalization**: Lowercase, ASCII only, hyphens.
*   **Fallback**: `/de/emlak/konut/satilik` (City seçilmediyse).

## 2. Detail Page
Format: `/ilan/{id}-{slug}`

### Example
*   `/ilan/123e4567-e89b-12d3-a456-426614174000-satilik-lüks-daire-berlin`

### Canonical
*   Listing ID unique identifier'dır. Slug değişse bile ID ile bulunur, ama canonical URL her zaman güncel slug olmalıdır.
