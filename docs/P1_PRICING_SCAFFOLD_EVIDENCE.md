# P1 Pricing Scaffold Evidence (Part 1)

**Tarih:** 2026-02-25

## 1) Admin Pricing Campaign (GET)
**Komut:**
```bash
curl -s -X GET "https://corporate-ui-build.preview.emergentagent.com/api/admin/pricing/campaign" \
  -H "Authorization: Bearer <TOKEN>"
```
**Çıktı:**
```json
{"status":"not_implemented","pricing_campaign_mode":{"is_active":false,"start_at":null,"end_at":null,"scope":"both"}}
```

## 2) Admin Pricing Campaign (PUT)
**Komut:**
```bash
curl -s -X PUT "https://corporate-ui-build.preview.emergentagent.com/api/admin/pricing/campaign" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"is_active":false,"scope":"both"}'
```
**Çıktı:**
```json
{"status":"not_implemented","message":"Pricing campaign policy scaffold","payload":{"is_active":false,"start_at":null,"end_at":null,"scope":"both"}}
```

## 3) Public Pricing Quote (POST)
**Komut:**
```bash
curl -s -X POST "https://corporate-ui-build.preview.emergentagent.com/api/pricing/quote" \
  -H "Content-Type: application/json" \
  -d '{"user_type":"individual","listing_count_year":1,"listing_type":"listing"}'
```
**Çıktı:**
```json
{"status":"not_implemented","message":"Pricing quote scaffold","payload":{"user_type":"individual","listing_count_year":1,"listing_type":"listing"}}
```

## 4) Public Pricing Packages (GET)
**Komut:**
```bash
curl -s -X GET "https://corporate-ui-build.preview.emergentagent.com/api/pricing/packages"
```
**Çıktı:**
```json
{"status":"not_implemented","packages":[]}
```

## 5) Admin UI Kanıtı
- **Screenshot:** `/app/test_reports/admin-pricing-campaign.png`
- **UI Test PASS:** `auto_frontend_testing_agent` (Fiyatlandırma menüsü + 3 placeholder sayfa)
