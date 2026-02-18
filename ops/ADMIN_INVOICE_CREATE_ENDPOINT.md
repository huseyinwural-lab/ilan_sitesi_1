## Admin Invoice Create Endpoint

### POST /api/admin/invoices
Payload:
```json
{
  "dealer_user_id": "...",
  "country_code": "DE",
  "plan_id": "...",
  "amount_net": 1000,
  "tax_rate": 19,
  "currency": "EUR",
  "issued_at": "2026-02-17T12:00:00Z"
}
```

Kurallar:
- country-scope zorunlu
- status default: `unpaid`
- audit-first (INVOICE_STATUS_CHANGE)
