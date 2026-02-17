# Multi-Country SEO Strategy v1

## 1. Domain Architecture
**Subdirectory Strategy** (`platform.com/de`) is chosen over ccTLD (`platform.de`) for centralized domain authority and easier management.

### 1.1. URL Structure
*   **Root**: `/` (Smart Redirect or Global Splash)
*   **Germany**: `/de/emlak/...`
*   **France**: `/fr/immobilier/...`
*   **Turkey**: `/tr/emlak/...`

## 2. Hreflang Logic
Every page MUST link to its alternates.

### Example: Search Result (Berlin)
On `platform.com/de/emlak/konut/satilik/berlin`:
```html
<link rel="alternate" hreflang="de-DE" href="https://platform.com/de/emlak/konut/satilik/berlin" />
<link rel="alternate" hreflang="de-AT" href="https://platform.com/at/emlak/konut/satilik/berlin" />
<link rel="alternate" hreflang="tr" href="https://platform.com/tr/emlak/konut/satilik/berlin" />
```

## 3. Sitemap Structure
*   `sitemap.xml` -> Index
    *   `sitemap-de.xml` -> Listings where country=DE
    *   `sitemap-fr.xml` -> Listings where country=FR
    *   `sitemap-static.xml` -> /about, /contact
