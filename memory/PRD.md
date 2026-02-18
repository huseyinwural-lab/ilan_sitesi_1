# FAZ Admin Domain Complete — PRD

**Son güncelleme:** 2026-02-18

## Orijinal Problem Tanımı
Çok ülkeli, çok dilli bir seri ilan platformunda (Public, Dealer, Backoffice/Admin) **admin domainindeki tüm “yakında” modüllerin** gerçek veriler ve tam işlevsellikle hayata geçirilmesi. Tüm admin mutasyonları **audit-first** ve **country-scope** kurallarına uymalıdır.

## Hedefler
- Admin panelinde tüm kritik alanların (Bayiler, Başvurular, İlanlar, Finans, Sistem, Master Data) canlı veriyle yönetilebilmesi
- Country-scope ile ülke bazlı yetkilendirme
- Audit-first standartlarında denetim kayıtları

## Kullanıcı Personaları
- **Super Admin:** Global yetkili yönetici
- **Country Admin:** Ülke bazlı yetkili yönetici
- **Moderator:** Moderasyon işlemleri
- **Dealer:** Bayi hesabı

## Temel Gereksinimler
- URL tabanlı country context (`?country=XX`)
- Tüm admin mutasyonlarında audit-first kayıt zorunluluğu
- Rol tabanlı erişim (RBAC)
- Çok dilli UI (TR/DE/FR)

## Mimari
- **Frontend:** React (portal bazlı code-splitting)
- **Backend:** FastAPI
- **Database:** MongoDB (motor)
- **Portallar:** Public / Dealer / Backoffice
- **Kritik Koleksiyonlar:** `users`, `dealer_applications`, `vehicle_listings`, `audit_logs`, `categories`, `countries`

## Uygulanan Özellikler
- **Sprint 0:** Admin domain şema ve audit-first standardı
- **Sprint 1.1:** Bayi Yönetimi (listeleme + durum değiştirme)
- **Sprint 1.2:** Bayi Başvuruları (listeleme + onay/red akışı)
- **Sprint 2.1:** Admin Global Listing Yönetimi
  - Filtreler: country-scope, status, search, dealer_only, category_id
  - Aksiyonlar: soft-delete, force-unpublish
- **Sprint 2.2:** Reports Engine (Şikayet Yönetimi)
  - Report reason enum + lifecycle
  - Admin list/detail/status API + audit-first
  - Public report submit (rate limit)
  - Admin UI /admin/reports + listing detail “Şikayet Et”
- **Sprint 3:** Finance Domain
  - Invoice Engine: create/list/detail/status + revenue endpoint
  - TaxRate CRUD (audit-first)
  - Plan CRUD (audit-first)
  - Dealer plan assignment (users.plan_id) + dealer detail finance summary
  - Admin UI: /admin/invoices, /admin/tax-rates, /admin/plans
- Moderation Queue + audit log altyapısı
- Login rate-limit ve audit log (FAILED_LOGIN, RATE_LIMIT_BLOCK)

## Öncelikli Backlog
### P0 (Sıradaki)
- **Sprint 4:** System + Dashboard (Countries, Settings, KPI)

### P1
- **Sprint 5:** Master Data Engines (Categories, Attributes, Vehicle Make/Model)
- **Backlog:** Admin Listing Preview Drawer
- **Backlog:** Bulk Report Status Update

### P2
- **Sprint 6:** Final Integration Gate (RBAC + audit + country-scope E2E)
- V3 genişletmeler (gelişmiş arama, güven katmanı, bayi genişletmeleri)
