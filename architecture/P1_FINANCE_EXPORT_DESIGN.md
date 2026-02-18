## P1 — Finance CSV Export + Revenue Chart Tasarımı

### CSV Export (Invoices)
- Endpoint:
  - `GET /api/admin/invoices/export?country=DE&status=paid&from=...&to=...`
- Kolonlar:
  - invoice_id, dealer_user_id, plan_id, amount_net, tax_rate, tax_amount, amount_gross, currency, status, issued_at, paid_at

### Revenue Chart
- Endpoint:
  - `GET /api/admin/finance/revenue-series?country=DE&granularity=day|week|month&from=...&to=...`
- Output:
  - [{ date, amount_gross_sum }]

### RBAC
- Sadece `finance` + `super_admin`

### Performans
- Summary querylerde index: paid_at, status, country_code
