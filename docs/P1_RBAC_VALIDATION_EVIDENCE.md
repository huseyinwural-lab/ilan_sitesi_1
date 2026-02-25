# P1 RBAC Validation Evidence

## Test Kullanıcıları
- **pricing_manager:** pricing_manager@platform.com / Rbac123!
- **ads_manager:** ads_manager@platform.com / Rbac123!
- **super_admin:** admin@platform.com / Admin123!

Seed script:
```bash
cd /app/backend
set -a && source .env && set +a
python3 scripts/seed_rbac_test_users.py --reset
```

## Endpoint RBAC Doğrulama (curl)
### pricing_manager → pricing endpoint (200)
```bash
curl -X GET "$API/admin/pricing/campaign-items?scope=individual"   -H "Authorization: Bearer $PRICING_TOKEN"
```
Response (örnek):
```json
{"items":[{"id":"7ba817be-4218-4b02-9472-8ce2587a372f"}]}
```

### pricing_manager → ads endpoint (403)
```bash
curl -X GET "$API/admin/ads/campaigns" -H "Authorization: Bearer $PRICING_TOKEN"
```
```json
{"detail":"Insufficient permissions"}
```

### ads_manager → ads endpoint (200)
```bash
curl -X GET "$API/admin/ads/campaigns" -H "Authorization: Bearer $ADS_TOKEN"
```
Response (örnek):
```json
{"items":[{"id":"7f7c711f-9efd-4224-aa10-460e7056729b"}]}
```

### ads_manager → pricing endpoint (403)
```bash
curl -X GET "$API/admin/pricing/campaign-items?scope=individual"   -H "Authorization: Bearer $ADS_TOKEN"
```
```json
{"detail":"Insufficient permissions"}
```

### super_admin → pricing endpoint (200)
```bash
curl -X GET "$API/admin/pricing/campaign-items?scope=individual"   -H "Authorization: Bearer $ADMIN_TOKEN"
```

### super_admin → ads endpoint (200)
```bash
curl -X GET "$API/admin/ads/campaigns" -H "Authorization: Bearer $ADMIN_TOKEN"
```

## Menü Görünürlüğü (UI)
- pricing_manager: sadece Fiyatlandırma menüsü
- ads_manager: sadece Reklam & Kampanya menüsü
- super_admin: tüm modüller
