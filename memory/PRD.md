# FAZ EU Panel — PRD

**Son güncelleme:** 2026-02-22

## Orijinal Problem Tanımı
EU uyumlu **Consumer** ve **Dealer** panellerinin tasarlanması ve geliştirilmesi.
GDPR/KVKK kapsamı gereği profil yönetimi, privacy center, 2FA ve veri minimizasyonu zorunlu.
Mongo **kullanılmayacak**; tüm yeni geliştirmeler PostgreSQL + SQLAlchemy üzerinden ilerleyecek.

## Hedefler
- Consumer ve Dealer profillerinin ayrıştırılması (consumer_profiles / dealer_profiles)
- GDPR Privacy Center (JSON export + soft delete + consent log)
- 2FA (TOTP + Backup codes)
- EU uyumlu şirket profili ve VAT doğrulama (regex)
- Preview/Prod ortamlarında DB fail-fast + migration gate
- Register anti-bot + GDPR export bildirimleri
- Ops görünürlüğü (ops_attention + last_db_error)
- EU uyumlu portal navigasyonu (TR/DE/FR)
- İlan ver sihirbazı tamamlanması (test-id kapsamı)

## Kullanıcı Personaları
- **Consumer (Bireysel)**
- **Dealer (Kurumsal)**

## Temel Gereksinimler
- Consumer Profile: full_name, display_name_mode, locale, country_code, marketing_consent
- Dealer Profile: company_name, vat_id, trade_register_no, authorized_person, address_json, logo_url
- Privacy Center: JSON export, consent logging, soft delete (30 gün grace)
- 2FA: TOTP + recovery/backup codes
- RBAC: Consumer/Dealer ayrımı

## Mimari
- **Frontend:** React (Account/Dealer portal)
- **Backend:** FastAPI (server.py monolith + SQLAlchemy)
- **Database:** PostgreSQL (DATABASE_URL)
- **Mongo:** EU panel sprintlerinde devre dışı (MONGO_ENABLED=false)

## Uygulanan Özellikler
- EU panel dokümantasyon paketi (/app/docs/CONSUMER_IA_V1.md, DEALER_IA_V1.md, PRIVACY_CENTER_EU.md, DATA_MODEL_SPEC_EU_PROFILES_V1.md)
- ConsumerProfile ve DealerProfile modelleri
- DealerProfile için gdpr_deleted_at alanı (model + migration: p34_dealer_gdpr_deleted_at)
- Helper: lazy create + VAT regex doğrulama + profile response builder
- **Yeni v1 endpointler:**
  - GET/PUT /api/v1/users/me/profile (consumer)
  - GET/PUT /api/v1/users/me/dealer-profile (dealer)
  - GET/PUT /api/v1/dealers/me/profile (alias)
  - GET/POST /api/v1/users/me/2fa/* (status/setup/verify/disable)
  - GET /api/v1/users/me/data-export (JSON)
  - DELETE /api/v1/users/me/account (soft delete + 30 gün + is_active=false)
- Frontend (Consumer Panel): AccountProfile + PrivacyCenter yeni v1 endpointlerine bağlı
- **Portal yeniden tasarımı (EU uyumlu):**
  - Turuncu zemin + üst yatay menü + sol alt menü
  - Bireysel/Ticari menü farkları uygulandı
  - TR/DE/FR menü dili toggle
- Dealer portal ek sayfalar: Şirket Profili + Gizlilik Merkezi
- **Admin kategori modalı:**
  - Hiyerarşi adı → Kategori
  - Alt kategoriler çok seviyeli (alt kategori içinde alt kategori) yapı ile oluşturulabiliyor
  - Alt kategori listesi Accordion düzeninde (Aç/Kapat) gösteriliyor
  - "Tamam" ile alt kategori kilitlenir, üst seviye tamamlanınca yeni alt kategori eklenir
- **Admin kategori parametre alanları:**
  - Parametre alanlarında seçenekleri tek tek ekleme/çıkarma arayüzü
  - Parametre listesinde seçenek ve zorunluluk özetleri
- **İlan Ver (Emlak) yeni akış:**
  - /ilan-ver/kategori-secimi sütunlu drill-down + breadcrumb + arama kutusu
  - /ilan-ver/detaylar placeholder (detay formu daha sonra)
  - /api/categories/children + /api/categories/search endpointleri

- **İlan ver sihirbazı (create listing):**
  - Başlıklar/boş durumlar/section alanları için data-testid eklendi
  - Dropzone + cover etiketleri test-id ile tamamlandı
- Preview/Prod DB fail-fast: CONFIG_MISSING hatası + localhost yasak + DB_SSL_MODE=require
- .env override kapatıldı (server.py, core/config.py, app/database.py)
- **P0 Sertleştirmeler:**
  - /api/health/db → migration_state gate + 60sn cache + last_migration_check_at
  - /api/health → config_state + last_migration_check_at + ops_attention + last_db_error
  - Register honeypot (company_website) + server-side reject + audit log (register_honeypot_hit)
  - GDPR export completion notification (in-app, warning) + audit trail
- **Mongo temizliği (moderasyon):**
  - Moderation queue/count/detail SQL’e taşındı
  - Approve/Reject/Needs‑revision SQL akışı + ModerationAction + audit log
- **Local Infra:**
  - PostgreSQL kuruldu, app_local DB oluşturuldu
  - Alembic upgrade heads PASS
  - Stripe CLI kuruldu (auth/test key invalid → idempotency BLOCKED)
- **Preview E2E:**
  - Admin login + Moderation Queue PASS
  - Consumer/Dealer login + profil endpointleri PASS

## Kanıtlar
- /app/docs/LOCAL_DB_READY_EVIDENCE.md
- /app/docs/MIGRATION_DRIFT_SIMULATION_EVIDENCE.md
- /app/docs/STRIPE_CLI_INSTALL_EVIDENCE.md
- /app/docs/STRIPE_IDEMPOTENCY_LOCAL_EVIDENCE.md
- /app/docs/AUTH_SECURITY_STRESS_EVIDENCE.md
- /app/docs/AUDIT_CHAIN_PARITY_EVIDENCE.md
- /app/docs/HEALTH_OPS_VISIBILITY_SPEC.md
- /app/docs/PROFILE_ENDPOINT_FIX_EVIDENCE.md
- /app/docs/PREVIEW_DB_FIX_EVIDENCE.md
- /app/docs/PREVIEW_MIGRATION_EVIDENCE.md
- /app/docs/HEALTH_MIGRATION_GATE_SPEC.md
- /app/docs/HEALTH_MIGRATION_GATE_EVIDENCE.md
- /app/docs/HEALTH_MIGRATION_GATE_PREVIEW_EVIDENCE.md
- /app/docs/PREVIEW_MIGRATION_PARITY_EVIDENCE.md
- /app/docs/SPRINT1_PREVIEW_API_EVIDENCE.md
- /app/docs/SPRINT1_PREVIEW_E2E_EVIDENCE.md
- /app/docs/SPRINT_PREVIEW_ADMIN_E2E_EVIDENCE.md
- /app/docs/SPRINT1_CLOSEOUT.md
- /app/docs/REGISTER_ANTIBOT_HONEYPOT_SPEC.md
- /app/docs/REGISTER_ANTIBOT_HONEYPOT_EVIDENCE.md
- /app/docs/GDPR_EXPORT_NOTIFICATION_SPEC.md
- /app/docs/GDPR_EXPORT_NOTIFICATION_EVIDENCE.md
- /app/docs/OPS_ESCALATION_TICKET.md
- /app/docs/PREVIEW_UNBLOCK_TRACKER.md
- /app/docs/LOCAL_PREVIEW_SIMULATION_EVIDENCE.md
- /app/docs/PREVIEW_ACTIVATION_RUNBOOK.md

## Blokajlar / Riskler
- Stripe API key geçersiz (idempotency testi BLOCKED)

## Öncelikli Backlog
### P0 (Hemen)
- Preview GDPR export + soft delete E2E kanıtları (/api/v1/users/me/data-export, /api/v1/users/me/account)
- Honeypot 400 + register_honeypot_hit audit doğrulaması (preview)
- GDPR export completion notification + audit doğrulaması (preview)
- Stripe idempotency testi (geçerli test API key sağlanınca)

### P0.1 (Güvenlik Doğrulama)
- Login rate limit tetikleme testi (preview)
- 2FA challenge + backup code tek kullanımlık testi (preview)
- Soft delete → login blocked testi (preview)
- GDPR export sonrası notification severity=warning UI doğrulaması

### P1 (Sprint‑1 closeout)
- Sprint‑1 E2E kanıt paketi

### P1.5 / P2 (Enhancement)
- Privacy Center export geçmişi (gdpr_exports tablosu + UI) → /app/docs/PRIVACY_EXPORT_HISTORY_SPEC.md

### P2
- VIES VAT doğrulama (API)
- GDPR CSV export
- Public search + admin listings Mongo bağımlılıklarının SQL’e taşınması
- Verification token cleanup job
