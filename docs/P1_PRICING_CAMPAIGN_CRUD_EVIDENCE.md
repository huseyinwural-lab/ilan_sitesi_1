# P1 Pricing Campaign CRUD Evidence

## Migration Gate
- `python3 /app/scripts/migration_dry_run.py` → **PASS** (2026-02-25)
- `alembic upgrade heads` → **OK** (p51_drop_campaign_idx)
- `/api/health/db` → **ok**

## Test User Seed (Ops)
- Doc: `/app/docs/PRICING_TEST_USER_SEED.md`
- Script: `/app/backend/scripts/seed_pricing_test_user.py --reset`

## Admin CRUD (curl)
### Create (Individual)
```bash
curl -X POST "$API/admin/pricing/campaign-items" -H "Authorization: Bearer $ADMIN"   -H "Content-Type: application/json"   -d '{"scope":"individual","listing_quota":1,"price_amount":50,"currency":"EUR","publish_days":90,"is_active":true}'
```
Response (örnek):
```json
{"item":{"id":"648ef6c2-fb0f-41f9-b369-d32087dcd84d","scope":"individual","listing_quota":1,"price_amount":50.0,"currency":"EUR","publish_days":90,"is_active":true}}
```

### Create (Corporate)
```bash
curl -X POST "$API/admin/pricing/campaign-items" -H "Authorization: Bearer $ADMIN"   -H "Content-Type: application/json"   -d '{"scope":"corporate","listing_quota":10,"price_amount":200,"currency":"EUR","publish_days":90,"is_active":true}'
```
Response (örnek):
```json
{"item":{"id":"0d509897-8ac3-40e4-93bb-18780b12198f","scope":"corporate","listing_quota":10,"price_amount":200.0,"currency":"EUR","publish_days":90,"is_active":true}}
```

### List
```bash
curl -X GET "$API/admin/pricing/campaign-items?scope=individual" -H "Authorization: Bearer $ADMIN"
curl -X GET "$API/admin/pricing/campaign-items?scope=corporate" -H "Authorization: Bearer $ADMIN"
```

### Update
```bash
curl -X PUT "$API/admin/pricing/campaign-items/$ID" -H "Authorization: Bearer $ADMIN"   -H "Content-Type: application/json" -d '{"price_amount":60}'
```

### Activate / Deactivate
```bash
curl -X PATCH "$API/admin/pricing/campaign-items/$ID/status" -H "Authorization: Bearer $ADMIN"   -H "Content-Type: application/json" -d '{"is_active":false}'
```

### Soft Delete
```bash
curl -X DELETE "$API/admin/pricing/campaign-items/$ID" -H "Authorization: Bearer $ADMIN"
```

## Quote (Individual)
```bash
curl -X POST "$API/pricing/quote" -H "Authorization: Bearer $USER" -H "Content-Type: application/json" -d '{}'
```
Response (örnek):
```json
{"quote":{"type":"campaign_item","campaign_item_id":"648ef6c2-fb0f-41f9-b369-d32087dcd84d","listing_quota":1,"amount":60.0,"currency":"EUR","publish_days":90,"requires_payment":true}}
```

## Checkout Session + Snapshot
```bash
curl -X POST "$API/pricing/checkout-session" -H "Authorization: Bearer $USER"   -H "Content-Type: application/json"   -d '{"listing_id":"01624f22-dc83-4fa4-b38e-af181ee60dbd","origin_url":"https://config-telemetry.preview.emergentagent.com","campaign_item_id":"648ef6c2-fb0f-41f9-b369-d32087dcd84d"}'
```
Response (örnek):
```json
{"checkout_url":"https://checkout.stripe.com/...","snapshot_id":"01cb4fed-a4dc-452c-80c6-51668174d6df","payment_required":true}
```

Snapshot doğrulama (DB):
```json
{"id":"01cb4fed-a4dc-452c-80c6-51668174d6df","listing_id":"01624f22-dc83-4fa4-b38e-af181ee60dbd","campaign_item_id":"648ef6c2-fb0f-41f9-b369-d32087dcd84d","listing_quota":1,"amount":"60.00","currency":"EUR","publish_days":90,"campaign_override_active":false}
```

## UI Evidence
- `admin-pricing-individual-page.png`
- `admin-pricing-individual-modal.png`
- `admin-pricing-corporate-page.png`
- `admin-pricing-tiers-page.png`
- `admin-pricing-individual-modal-fields.png`
- `admin-pricing-individual-validation-error.png`
- `admin-pricing-packages-page.png`
- `admin-pricing-corporate-modal-fields.png`
- `admin-pricing-corporate-validation-error.png`
- **Auto frontend testing:** PASS (minor hydration warnings only)


## Kampanya Tarih/Saat Zorunluluğu (2026-02-25)

### UI Screenshot
- **Modal date-time alanları:** admin pricing modal ekranında Başlangıç/Bitiş alanları + timezone etiketi.

### API Validasyonları (curl)
**Geçmiş başlangıç (400):**
```bash
curl -X POST "$API/admin/pricing/campaign-items" -H "Authorization: Bearer $ADMIN"   -H "Content-Type: application/json"   -d '{"scope":"individual","listing_quota":5,"price_amount":120,"currency":"EUR","publish_days":90,"start_at":"2026-02-25T09:50:32Z","end_at":"2026-03-07T11:50:32Z","is_active":true}'
```
Response (örnek):
```json
{"detail":"start_at must be in the future"}
```

**Overlap (409):**
```bash
curl -X POST "$API/admin/pricing/campaign-items" -H "Authorization: Bearer $ADMIN"   -H "Content-Type: application/json"   -d '{"scope":"individual","listing_quota":6,"price_amount":140,"currency":"EUR","publish_days":90,"start_at":"2026-03-02T11:50:32Z","end_at":"2026-03-12T11:50:32Z","is_active":true}'
```
Response (örnek):
```json
{"detail":"Active campaign overlaps with existing time range"}
```

### Quote Zaman Aralığı Kontrolü
**Şimdi aralığında:** (Bireysel kampanya aktif)
```json
{"quote":{"type":"campaign_item","campaign_item_id":"7ba817be-4218-4b02-9472-8ce2587a372f","listing_quota":5,"amount":120.0}}
```

**Aralık dışında (Planlı kampanya):** (Kurumsal sadece gelecekte)
```json
{"quote":{"type":"campaign_none","reason":"no_active_campaign"}}
```
