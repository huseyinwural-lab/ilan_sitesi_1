# Real Estate SEO & Breadcrumb Standard v1

## 1. Breadcrumb Logic
Breadcrumbs must reflect the *localized* path hierarchy.

**Example (DE):**
`Home > Immobilien > Gewerbeimmobilien > Zu Verkaufen > Tankstelle`

**Example (TR):**
`Anasayfa > Emlak > Ticari İşletme > Satılık > Akaryakıt İstasyonu`

## 2. Canonical URLs
-   Each language version has its own canonical URL.
-   Use `hreflang` tags in `<head>` to link them:
    ```html
    <link rel="alternate" hreflang="tr" href=".../satilik/daire" />
    <link rel="alternate" hreflang="de" href=".../zu-verkaufen/wohnung" />
    ```

## 3. Sitemap Strategy
-   Generate `sitemap-tr.xml`, `sitemap-de.xml`, `sitemap-fr.xml`.
-   Include all leaf category pages.
