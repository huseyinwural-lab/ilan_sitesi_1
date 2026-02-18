## Admin Tax Rate Engine (Complete)

### Endpoints
- GET `/api/admin/tax-rates`
- POST `/api/admin/tax-rates`
- PATCH `/api/admin/tax-rates/{id}`
- DELETE `/api/admin/tax-rates/{id}` (soft delete)

Kurallar:
- rate 0–100 validation
- audit-first: `TAX_RATE_CHANGE`
