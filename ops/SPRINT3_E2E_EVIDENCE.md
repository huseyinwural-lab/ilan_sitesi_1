## Sprint 3 E2E Evidence

### Zorunlu Testler
1) **Invoice create → list görünür**
- Dealer: `40a9aec7-0ce0-4c0c-8624-d33a6b51bafa`
- Invoice ID: `d3de6d59-b639-4023-a70f-8def72381a36`
- List endpoint: `/api/admin/invoices?country=DE&dealer_user_id=...`

2) **Status change → audit yazılır**
- POST `/api/admin/invoices/{id}/status` → `paid`
- Audit: `/api/audit-logs?event_type=INVOICE_STATUS_CHANGE&resource_type=invoice`

3) **Revenue endpoint doğru hesaplar**
- `/api/admin/finance/revenue?country=DE&start_date=...&end_date=...`
- `total_gross` döner

4) **Country-scope ihlal → 403**
- Country admin (`countryadmin@platform.com`) ile `country=FR` → `403 Country scope forbidden`

5) **Plan değişimi → audit**
- PATCH `/api/admin/plans/{id}` → price update
- Audit: `/api/audit-logs?event_type=PLAN_CHANGE&resource_type=plan`

### Komutlar (özet)
```bash
curl -X POST $REACT_APP_BACKEND_URL/api/admin/invoices \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"dealer_user_id":"40a9aec7-0ce0-4c0c-8624-d33a6b51bafa","country_code":"DE","plan_id":"<PLAN_ID>","amount_net":1000,"tax_rate":19,"currency":"EUR"}'

curl -X POST $REACT_APP_BACKEND_URL/api/admin/invoices/d3de6d59-b639-4023-a70f-8def72381a36/status \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"target_status":"paid","note":"ödeme alındı"}'

curl -X GET "$REACT_APP_BACKEND_URL/api/admin/finance/revenue?country=DE&start_date=<ISO>&end_date=<ISO>" \
  -H "Authorization: Bearer <TOKEN>"
```
