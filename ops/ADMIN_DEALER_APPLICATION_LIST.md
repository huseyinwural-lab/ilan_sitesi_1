# ADMIN_DEALER_APPLICATION_LIST

## Endpoint
`GET /api/admin/dealer-applications`

## Amaç
Dealer onboarding başvurularını admin panelde listelenebilir hale getirmek.

## Kurallar
- Country-scope enforced (`?country=XX` context)
- Status filtre: `pending | approved | rejected`
- Pagination: `skip`, `limit`
- Search: `email` veya `company_name` üzerinde case-insensitive regex

## Response
```json
{
  "items": [ ...application docs... ],
  "pagination": {"total": 0, "skip": 0, "limit": 50}
}
```
