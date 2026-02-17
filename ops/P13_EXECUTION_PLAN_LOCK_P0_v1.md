# P13 Execution Plan Lock (P0)

**Durum:** KİLİTLENDİ (LOCKED)
**Tarih:** 14 Şubat 2026
**Öncelik:** P0 (Highest)

Bu doküman, Listing Lifecycle (P13) validasyonu, Soft Launch aktivasyonu ve Production Readiness süreçlerinin kesin icra sırasını ve başarı kriterlerini (gates) tanımlar.

## İcra Sırası (Execution Order)

### 1. Adım: P13 Validasyon + Search Self-Cleaning (TEKNİK)
*   **Hedef:** İlan yaşam döngüsünün (Expiration) veritabanı, search indeksi ve önbellek (cache) üzerinde deterministik olarak çalıştığını doğrulamak.
*   **Aksiyonlar:**
    *   `process_expirations.py` job'ına Redis Cache Invalidation adımı eklenecek.
    *   Expiration Job'ın "Expire -> Quota Release -> Cache Clear" zinciri test edilecek.
*   **Çıktılar:**
    *   `/app/ops/P13_PRODUCTION_VALIDATION_REPORT_v1.md`
    *   `/app/architecture/P13_SEARCH_STALE_DATA_POLICY_v1.md`
*   **Gate:** Search sonuçlarında stale (süresi dolmuş) veri yok.

### 2. Adım: Invite-Only Soft Launch Aktivasyonu (GELİŞTİRME)
*   **Hedef:** Kontrolsüz kullanıcı girişini engellemek ve sadece onaylı (Allowlist) kullanıcıların kayıt olmasını sağlamak.
*   **Politika:** C - Allowlist (İzinli E-posta).
*   **Aksiyonlar:**
    *   DB: `signup_allowlist` tablosu oluşturulacak.
    *   Backend: `/auth/register` endpoint'i allowlist kontrolü yapacak şekilde güncellenecek.
    *   Admin: Allowlist'e e-posta ekleme/çıkarma için API/Logic eklenecek.
*   **Çıktılar:**
    *   `/app/ops/SOFT_LAUNCH_ACTIVATION_CONFIRMATION_v1.md`
*   **Gate:** DB'de kayıtlı olmayan bir e-posta ile kayıt işlemi başarısız olmalı.

### 3. Adım: Audit, Retention ve Stabilizasyon (DOKÜMANTASYON & POLİTİKA)
*   **Hedef:** Üretim ortamına hazır oluşu (Production Readiness) sertifikalandırmak ve veri politikalarını netleştirmek.
*   **Aksiyonlar:**
    *   Production Readiness Audit kontrol listesi tamamlanacak.
    *   Veri saklama (Retention) politikası yazılacak.
    *   Günlük stabilizasyon kontrollerine P13 metrikleri eklenecek.
*   **Çıktılar:**
    *   `/app/release_notes/PRODUCTION_READINESS_AUDIT_v1.md`
    *   `/app/architecture/P13_DATA_RETENTION_POLICY_v1.md`
    *   `/app/ops/P0_STABILIZATION_DAILY_EXTENSION_v1.md`
*   **Gate:** Tüm kritik akışlar imzalı ve operasyonel prosedürler hazır.

---
**Onaylayan:** User & Agent E1
**Statü:** YÜRÜTÜLÜYOR
