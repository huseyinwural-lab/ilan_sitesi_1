# Listing Detail SEO Spec

## 1. Canonical URL
*   Format: `https://platform.com/ilan/{id}-{slug}`
*   Rule: The ID is the source of truth. The slug is for humans/bots.

## 2. Meta Tags
*   `<title>`: `{Listing Title} | {City} | {Platform Name}`
*   `<meta name="description">`: `{Category} for sale in {City}. {Price}. {Short Description}.`
*   `<meta property="og:image">`: First image URL (Full size).
*   `<meta property="og:type">`: `product` (or `website`).
*   `<meta property="og:price:amount">`: `{Price}`.
*   `<meta property="og:price:currency">`: `{Currency}`.

## 3. Structured Data (JSON-LD)
*   Type: `Product` or `RealEstateListing` (Schema.org).
*   Fields: name, description, image, offers.price.
