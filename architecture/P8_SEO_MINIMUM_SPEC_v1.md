# P8 SEO Minimum Specification

**Document ID:** P8_SEO_MINIMUM_SPEC_v1  
**Date:** 2026-02-13  
**Status:** 📝 DRAFT  

---

## 1. Meta Tags (React Helmet)

### 1.1. Title
Format: `{Listing Title} - {Price} {Currency} | {SiteName}`
*Example:* `Sahibinden Temiz BMW 320i - 1.250.000 TL | AdminPanel`

### 1.2. Description
Source: First 160 characters of Listing Description.
Fallback: "{City} {Category} ilanı. Fiyat: {Price}. Detaylar için tıklayın."

### 1.3. Canonical
URL: `https://{domain}/ilan/{slug}-{id}`
*Purpose:* Prevent duplicate content issues if accessed via different query params.

### 1.4. Robots
- Active Listings: `index, follow`
- Inactive/Sold: `noindex, follow` (Eventually 410)

---

## 2. Open Graph (Social Sharing)
- `og:title`: Same as Page Title
- `og:description`: Same as Meta Description
- `og:image`: First listing image (800x600 recommended)
- `og:type`: `website` (or `product` if applicable)
- `og:url`: Canonical URL
- `og:price:amount`: Price
- `og:price:currency`: Currency

---

## 3. Structured Data (JSON-LD)

### 3.1. Product Schema (General)
```json
{
  "@context": "https://schema.org/",
  "@type": "Product",
  "name": "Listing Title",
  "image": ["url1", "url2"],
  "description": "...",
  "offers": {
    "@type": "Offer",
    "priceCurrency": "TRY",
    "price": "1250000",
    "itemCondition": "https://schema.org/UsedCondition",
    "availability": "https://schema.org/InStock"
  }
}
```

### 3.2. BreadcrumbList
To enhance search result snippets.

---

## 4. Implementation Strategy
- Library: `react-helmet-async`
- Component: `<SEOHelmet data={...} />` inside Detail Page.
- Validation: Use Google Rich Results Test (Manual check).
