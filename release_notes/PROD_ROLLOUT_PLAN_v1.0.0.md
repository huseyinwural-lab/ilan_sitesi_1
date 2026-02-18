## Production Rollout Plan — v1.0.0

### 1) Versiyon Tag Stratejisi
- **Immutable tag:** `v1.0.0`
- Hotfix: `v1.0.1`, `v1.0.2` (minor patch)
- Rollback: önceki stable tag’e dönüş (örn. `v0.9.x`)

### 2) Deployment Adımları
1. **Code Freeze** (RC onayı sonrası)
2. **Smoke test** (pre-prod / staging)
3. **DB Backup** (snapshot)
4. **Backend deploy**
5. **Frontend deploy**
6. **Post-deploy smoke tests**
7. **Audit + RBAC hızlı kontrol** (admin login, /api/admin/invoices, /api/admin/listings)

### 3) Migration Sırası
- Yeni şema migration yok (Mongo schemaless).
- **Index kontrolü:** audit_logs, vehicle_listings, reports, invoices koleksiyonlarında gerekli indexler aktif mi kontrol edilir.

### 4) Seed Kontrolü
- Admin / Finance / Country Admin hesapları mevcut mu?
- Countries seed doğru mu? (DE + FR aktif)
- Default tax rate + plan seed (opsiyonel)

### 5) Feature Flag Kontrolü (Varsa)
- `moderation.auto_publish_enabled` gibi system setting flag’leri kontrol edilir.
- Bu sürümde kritik feature flag yok.

### 6) Rollback Prosedürü
1. **App rollback:** önceki stable tag’e dönüş
2. **DB rollback:** snapshot restore (data uyumsuzluğu varsa)
3. **Emergency admin erişimi:** super_admin credential doğrulama
4. **Post-rollback smoke test** (login, search, admin listing)
