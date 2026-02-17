# Country Configuration Model v1

## 1. Schema (`countries`)
Extending the existing P19 `Country` model.

| Column | Type | Description |
| :--- | :--- | :--- |
| `code` | String(2) | PK (DE, FR, etc.) |
| `name` | JSONB | `{"en": "Germany", "de": "Deutschland"}` |
| `default_language` | String(2) | `de`, `fr` |
| `seo_locale` | String(5) | `de-DE`, `fr-FR` |
| `is_active` | Boolean | Soft launch switch |
| `legal_info` | JSONB | `{"imprint_required": true, "vat_rate": 19}` |

## 2. Initial Configuration (Seed)

### Germany (DE)
*   Language: `de`
*   SEO: `de-DE`
*   Legal: Impressum Required.

### Austria (AT)
*   Language: `de`
*   SEO: `de-AT`
*   Legal: Similar to DE.

### Switzerland (CH)
*   Language: `de` (Primary for MVP)
*   SEO: `de-CH`
*   Currency: EUR (Platform standard) - *Note: User might see CHF estimation in UI only.*

### France (FR)
*   Language: `fr`
*   SEO: `fr-FR`
*   Legal: Siren/Siret check (Future).
