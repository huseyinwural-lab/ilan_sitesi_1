## Admin Invoice API (Complete)

### GET /api/admin/invoices
- Zorunlu: `country`
- Filtreler: `dealer_user_id`, `status`, `skip`, `limit`

### GET /api/admin/invoices/{id}
- Dealer + plan summary ile döner

### POST /api/admin/invoices/{id}/status
- `target_status`: paid | cancelled
- Audit-first: `INVOICE_STATUS_CHANGE`

### POST /api/admin/invoices
- Manuel invoice create
- Audit-first
