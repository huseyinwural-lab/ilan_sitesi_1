# Programmatic SEO Strategy v1

## 1. Concept
Generate thousands of static-like landing pages based on our taxonomy and location data.

## 2. URL Structure
`/{country}/emlak/{segment}/{transaction}/{type}/{city}/{district?}`

### Examples
*   `/de/emlak/konut/satilik/daire/berlin`
*   `/de/emlak/konut/kiralik/daire/berlin/mitte`
*   `/tr/emlak/ticari/kiralik/ofis/istanbul/kadikoy`

## 3. Page Template (Content)
*   **H1**: `{City} {District} Satılık {Type} İlanları`
*   **Description**: `{City} bölgesinde {Count} adet satılık {type} ilanı. Fiyatlar {MinPrice} ile {MaxPrice} arasında değişmektedir.`
*   **Listing Grid**: First 20 items (Sorted by Premium).
*   **FAQ Section**: Generated from aggregate data ("What is avg price in {City}?").
*   **Internal Links**: Nearby districts, similar categories.

## 4. Technical Implementation
*   **Router**: `GET /api/v1/search/landing/{path_params}`.
*   **Parsing**: Extract filters from URL path.
*   **Response**: Metadata + Search Results (reusing Search API logic).
*   **Sitemap**: Background job to generate `sitemap-landing.xml` covering top 1000 combinations.
