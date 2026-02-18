## Admin Revenue Endpoint

### GET /api/admin/finance/revenue
Query:
- `country` (zorunlu)
- `start_date` (ISO8601, UTC)
- `end_date` (ISO8601, UTC)

Hesap:
- `sum(amount_gross)` where `status=paid` and `start_date <= paid_at <= end_date`
