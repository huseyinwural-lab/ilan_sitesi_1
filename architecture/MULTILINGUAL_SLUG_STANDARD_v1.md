# Multilingual Slug Standard v1

**Goal:** SEO-friendly, localized URLs for each country/language.

## 1. Structure
`/{language}/{module-slug}/{section-slug}/{transaction-slug}/{category-slug}`

## 2. Rules
1.  **Localization:** Every segment is translated.
    -   *TR:* `/tr/emlak/konut/satilik/daire`
    -   *DE:* `/de/immobilien/wohnen/zu-verkaufen/wohnung`
    -   *FR:* `/fr/immobilier/residentiel/a-vendre/appartement`
2.  **Normalization:**
    -   Lowercase (küçük harf).
    -   Spaces -> Hyphens (` ` -> `-`).
    -   Special chars replaced:
        -   `ü`->`u`, `ö`->`o`, `ş`->`s`, `ç`->`c`, `ğ`->`g`, `ı`->`i`.
        -   `&` -> `-`.
        -   `ß` -> `ss`.
3.  **Immutability:** Slugs should not change often to preserve SEO ranking.

## 3. Examples
| TR | DE | FR |
| :--- | :--- | :--- |
| `ticari-isletme` | `gewerbeimmobilien` | `immobilier-commercial` |
| `akaryakit-istasyonu` | `tankstelle` | `station-service` |
| `is-hani-kati-ve-ofisi`| `zentrum-etage-und-buro` | `etage-de-bureau-commercial` |
