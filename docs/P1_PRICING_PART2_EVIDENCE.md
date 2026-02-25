# P1 Pricing Part 2 Evidence — Launch Campaign Mode

**Tarih:** 2026-02-25

## 1) Enable/Disable + Validation (Admin)
**Enable (start_at required):**
```bash
curl -i -X PUT "https://public-site-build.preview.emergentagent.com/api/admin/pricing/campaign" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"is_enabled":true,"scope":"all"}'
```
**Response:** `400 start_at is required when enabling`

**Enable (valid):**
```bash
curl -X PUT "https://public-site-build.preview.emergentagent.com/api/admin/pricing/campaign" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"is_enabled":true,"scope":"all","start_at":"2026-02-25T07:27:51Z"}'
```
**Response:**
```json
{"ok":true,"policy":{"is_enabled":true,"scope":"all"},"active":true}
```

**Invalid Dates:**
```bash
curl -i -X PUT "https://public-site-build.preview.emergentagent.com/api/admin/pricing/campaign" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"is_enabled":false,"scope":"all","start_at":"2026-03-10T00:00:00Z","end_at":"2026-03-01T00:00:00Z"}'
```
**Response:** `400 end_at must be after start_at`

## 2) Quote Override Hook
```bash
curl -s -X POST "https://public-site-build.preview.emergentagent.com/api/pricing/quote" \
  -H "Content-Type: application/json" \
  -d '{"user_type":"individual"}'
```
**Response (campaign aktifken):**
```json
{"pricing_mode":"campaign","override_active":true,"warning":"override_active_no_rules","fallback":"default_pricing"}
```

## 3) Expire Job
- end_at geçmiş kampanya için /api/pricing/quote çağrısı sonrası `is_enabled=false` döner.

## 4) Admin UI Kanıtı
- **UI Test PASS:** `auto_frontend_testing_agent` (toggle + scope + Kaydet/Yayınla akışı)
- **Screenshot:** `/app/test_reports/admin-pricing-campaign-ui-ready.png`
