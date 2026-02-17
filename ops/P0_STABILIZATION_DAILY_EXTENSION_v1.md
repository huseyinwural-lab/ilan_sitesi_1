# P0 Stabilization Daily Extension (v1)

**Ana Doküman:** `/app/ops/P0_STABILIZATION_DAILY_CHECKS.md` (Varsayımsal)
**Eklenen Metrikler:** P13 Listing Lifecycle & Search

## Günlük Kontrol Listesi (Daily Checklist)

### 1. Lifecycle Metrikleri
*   [ ] **Expired Count:** Son 24 saatte kaç ilan `expired` statüsüne düştü? (Beklenen: < Toplam İlanların %5'i)
*   [ ] **Renew Count:** Son 24 saatte kaç ilan yenilendi? (Revenue sinyali)
*   [ ] **Job Success:** `process_expirations.py` son çalışma durumu (Log: `Checking logs for 'process_expirations'`).

### 2. Search Tutarlılığı
*   [ ] **Stale Check:** Rastgele 5 `expired` ilan ID'si alınıp Search API'da sorgulanacak. Sonuç boş dönmeli.
    *   `curl /api/v2/listings/{expired_id}` -> 200 OK (Detay sayfası açık olabilir)
    *   `curl /api/v2/search?q={title}` -> Listede o ilan OLMAMALI.

### 3. Invite-Only Güvenliği
*   [ ] **Allowlist Bypass:** `users` tablosunda `created_at` son 24 saat olan kullanıcıların e-postaları, `signup_allowlist` tablosunda var mı? (Audit query).

### 4. Sistem Sağlığı
*   [ ] **Redis Memory:** `info memory` (Fragmentation < 1.5).
*   [ ] **DB Connections:** `pg_stat_activity` (Idle connection şişmesi var mı?).
