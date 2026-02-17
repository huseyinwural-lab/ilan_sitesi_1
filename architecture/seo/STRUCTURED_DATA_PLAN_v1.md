# Structured Data (JSON-LD) Plan

## 1. Schema Type
**Product** (Generic) or **RealEstateListing** (Specific).
We will use `Product` for broader compatibility initially, or `RealEstateListing` if Google supports it well in target region. Let's stick to `Product` with `category` specification.

## 2. Mapping
| Schema Field | Listing Attribute |
| :--- | :--- |
| `@type` | `Product` |
| `name` | `title` |
| `description` | `description` |
| `image` | `media[0].url` |
| `offers.price` | `price` |
| `offers.priceCurrency` | `currency` |
| `offers.availability` | `InStock` (if active) |
| `brand.name` | `seller.name` |

## 3. Implementation
*   **Backend**: `GET /api/v1/listings/{id}` already returns SEO fields.
*   **Frontend**: `DetailPage.js` injects `<script type="application/ld+json">` into `<head>`.
