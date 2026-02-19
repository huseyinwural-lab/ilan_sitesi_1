## Sprint 2.2 E2E Evidence

### Zorunlu Testler
1) **Public report create → admin report listte görünür**
- Listing: `14e4ae50-973e-4b99-b8bb-c8b8f0e2ecb2`
- Report ID: `c02ab575-52fa-4129-b5df-4470ce133088`
- Sonuç: `/api/admin/reports?listing_id=...` listesinde görünür

2) **Country-scope ihlali → 403**
- `GET /api/admin/reports/{id}?country=FR` → `403 Country scope forbidden`

3) **Status change → audit log kaydı**
- `POST /api/admin/reports/{id}/status` → `in_review`
- `GET /api/audit-logs?event_type=REPORT_STATUS_CHANGE&resource_type=report` kaydı oluştu

4) **Report → listing/moderation linkleri çalışır**
- Admin UI’da `/admin/reports` satır aksiyonları link verir

### Komutlar (özet)
```bash
curl -X POST $REACT_APP_BACKEND_URL/api/reports \
  -H "Content-Type: application/json" \
  -d '{"listing_id":"14e4ae50-973e-4b99-b8bb-c8b8f0e2ecb2","reason":"spam"}'

curl -X GET "$REACT_APP_BACKEND_URL/api/admin/reports?listing_id=kategori-form-v2" \
  -H "Authorization: Bearer <TOKEN>"

curl -X POST $REACT_APP_BACKEND_URL/api/admin/reports/c02ab575-52fa-4129-b5df-4470ce133088/status \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"target_status":"in_review","note":"İnceleme başlatıldı"}'

curl -X GET "$REACT_APP_BACKEND_URL/api/audit-logs?event_type=REPORT_STATUS_CHANGE&resource_type=report" \
  -H "Authorization: Bearer <TOKEN>"
```
