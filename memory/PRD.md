# FAZ EU Panel — PRD

**Son güncelleme:** 2026-02-21

## Orijinal Problem Tanımı
EU uyumlu **Consumer** ve **Dealer** panellerinin tasarlanması ve geliştirilmesi. 
GDPR/KVKK kapsamı gereği profil yönetimi, privacy center, 2FA ve veri minimizasyonu zorunlu.
Mongo **kullanılmayacak**; tüm yeni geliştirmeler PostgreSQL + SQLAlchemy üzerinden ilerleyecek.

## Hedefler
- Consumer ve Dealer profillerinin ayrıştırılması (consumer_profiles / dealer_profiles)
- GDPR Privacy Center (JSON export + soft delete + consent log)
- 2FA (TOTP + Backup codes)
- EU uyumlu şirket profili ve VAT doğrulama (regex)

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
  - DELETE /api/v1/users/me/account (soft delete + 30 gün)
- Frontend (Consumer Panel): AccountProfile + PrivacyCenter artık /api/v1 endpointlerine bağlı
- Kanıt: /app/docs/PROFILE_ENDPOINT_FIX_EVIDENCE.md

## Blokajlar / Riskler
- Preview ortamında backend 520 (DATABASE_URL/SQL servis erişimi yok). Curl doğrulama ve migration apply **bloklu**.

## Öncelikli Backlog
### P0 (Hemen)
- Preview DB erişimini aç (DATABASE_URL + SQL servis)
- `alembic upgrade head` çalıştır
- Curl ile doğrulama:
  - /api/v1/users/me/profile (consumer/dealer)
  - /api/v1/users/me/dealer-profile
  - /api/v1/users/me/data-export
  - /api/v1/users/me/account

### P1 (Sprint-2)
- Dealer Panel UI (plan & kota, listing grid, accounting VAT)
- Compliance regression testleri

### P2 (Backlog)
- VIES VAT doğrulama (API)
- GDPR CSV export
- Moderation reject flow
- Verification token cleanup job
