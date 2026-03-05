# Admin Panel Modül Bazlı Tam Kılavuz (TR)

Üretim Tarihi: 2026-03-05 18:11 UTC

Bu doküman, admin panelindeki her modül için amaç, arayüz öğeleri, iş akışı, API uçları, veri modelleri, rol/yetki ve validasyon özetini içerir.

## Dashboard
Yönetim performansının özet izlendiği katman.

### 1. Kontrol Paneli (`/admin`)
- **Amaç:** Kontrol Paneli modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `dashboard, dashboard-activity-cta, dashboard-activity-deleted, dashboard-activity-empty, dashboard-activity-new-listings, dashboard-activity-new-users, dashboard-activity-skeleton, dashboard-activity-summary, dashboard-batch-publish-card, dashboard-batch-publish-errors`
  - Öne çıkan buton aksiyonları: {running ? 'Çalışıyor...' : 'Şimdi Çalıştır'}
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
- **API Uçları:**
  - `GET /api/admin/dashboard/country-compare` — Admin Dashboard Country Compare
  - `GET /api/admin/dashboard/country-compare/export/csv` — Admin Dashboard Country Compare Export Csv
  - `GET /api/admin/dashboard/export/pdf` — Admin Dashboard Export Pdf
  - `GET /api/admin/dashboard/summary` — Admin Dashboard Summary
  - `GET /api/admin/session/health` — Admin Session Health
- **Veri Modelleri (DB):** `(İlgili endpoint şemalarından türetilir)`
- **Rol / Yetki:** `super_admin, country_admin, admin, finance`
- **Validasyon Kuralları:**
  - period (query) | string
  - start_date (query)
  - end_date (query)
  - sort_by (query)
  - sort_dir (query)
  - countries (query)

### 2. Genel Bakış (`/admin/dashboard`)
- **Amaç:** Genel Bakış modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `dashboard, dashboard-activity-cta, dashboard-activity-deleted, dashboard-activity-empty, dashboard-activity-new-listings, dashboard-activity-new-users, dashboard-activity-skeleton, dashboard-activity-summary, dashboard-batch-publish-card, dashboard-batch-publish-errors`
  - Öne çıkan buton aksiyonları: {running ? 'Çalışıyor...' : 'Şimdi Çalıştır'}
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
- **API Uçları:**
  - `POST /api/admin/analytics/events` — Track Admin Wizard Event
  - `GET /api/admin/dashboard/country-compare` — Admin Dashboard Country Compare
  - `GET /api/admin/dashboard/country-compare/export/csv` — Admin Dashboard Country Compare Export Csv
  - `GET /api/admin/dashboard/export/pdf` — Admin Dashboard Export Pdf
  - `GET /api/admin/dashboard/summary` — Admin Dashboard Summary
  - `GET /api/admin/search/meili/contract` — Admin Search Meili Contract
  - `GET /api/admin/search/meili/health` — Admin Search Meili Health
  - `POST /api/admin/search/meili/reindex` — Admin Reindex Search Projection
  - `GET /api/admin/search/meili/stage-smoke` — Admin Search Meili Stage Smoke
  - `GET /api/admin/search/meili/sync-jobs` — Admin List Search Sync Jobs
- **Veri Modelleri (DB):** `AuditLog, Listing, User`
- **Rol / Yetki:** `super_admin, country_admin, admin, finance`
- **Validasyon Kuralları:**
  - Body şeması AdminWizardAnalyticsPayload: zorunlu alanlar -> event_name, category_id, step_id
  - period (query) | string
  - start_date (query)
  - end_date (query)
  - sort_by (query)
  - sort_dir (query)

### 3. Ülke Karşılaştırma (`/admin/country-compare`)
- **Amaç:** Ülke Karşılaştırma modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-country-compare-page, country-compare-bar-chart, country-compare-bar-empty, country-compare-bar-list, country-compare-controls, country-compare-country-list, country-compare-custom-end, country-compare-custom-range, country-compare-custom-start, country-compare-empty`
  - Öne çıkan buton aksiyonları: {exporting ? 'Hazırlanıyor' : 'CSV indir'}
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
  1) Mevcut kayıt güncellenir.
  1) Silme/iptal işlemi uygulanır.
- **API Uçları:**
  - `GET /api/admin/countries` — Admin List Countries
  - `POST /api/admin/countries` — Admin Create Country
  - `DELETE /api/admin/countries/{code}` — Admin Delete Country
  - `GET /api/admin/countries/{code}` — Admin Get Country
  - `PATCH /api/admin/countries/{code}` — Admin Update Country
  - `GET /api/admin/dashboard/country-compare` — Admin Dashboard Country Compare
  - `GET /api/admin/dashboard/country-compare/export/csv` — Admin Dashboard Country Compare Export Csv
- **Veri Modelleri (DB):** `Country, Listing, User`
- **Rol / Yetki:** `super_admin, country_admin, admin, finance`
- **Validasyon Kuralları:**
  - Body şeması CountryCreatePayload: zorunlu alanlar -> country_code, name, default_currency
  - code (path) | zorunlu | string
  - period (query) | string
  - start_date (query)
  - end_date (query)
  - sort_by (query)

## Yönetim
Admin kullanıcıları ve yetki modelinin yönetildiği katman.

### 4. Admin Kullanıcıları (`/admin/admin-users`)
- **Amaç:** Admin Kullanıcıları modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-users-bulk-actions, admin-users-bulk-deactivate, admin-users-bulk-error, admin-users-create-button, admin-users-delete-cancel, admin-users-delete-confirm, admin-users-delete-message, admin-users-delete-modal, admin-users-delete-title, admin-users-empty`
  - Öne çıkan buton aksiyonları: Ara, Kapat, Toplu Pasif Et (max 20), Vazgeç, Yeni Admin Ekle, {deleteLoading ? 'Siliniyor' : 'Onayla'}
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
  1) Mevcut kayıt güncellenir.
  1) Silme/iptal işlemi uygulanır.
- **API Uçları:**
  - `POST /api/admin/invite/accept` — Admin Invite Accept
  - `GET /api/admin/invite/preview` — Admin Invite Preview
  - `GET /api/admin/users` — List Admin Users
  - `POST /api/admin/users` — Create Admin User
  - `POST /api/admin/users/bulk-deactivate` — Bulk Deactivate Admins
  - `DELETE /api/admin/users/{user_id}` — Delete User
  - `PATCH /api/admin/users/{user_id}` — Update Admin User
  - `POST /api/admin/users/{user_id}/activate` — Activate User
  - `GET /api/admin/users/{user_id}/detail` — Admin User Detail
  - `PATCH /api/admin/users/{user_id}/risk-level` — Admin Update Risk Level
- **Veri Modelleri (DB):** `User, UserPermission, AdminInvite`
- **Rol / Yetki:** `super_admin`
- **Validasyon Kuralları:**
  - Body şeması AdminInviteAcceptPayload: zorunlu alanlar -> token, password
  - token (query) | zorunlu | string
  - search (query)
  - role (query)
  - status (query)
  - country (query)

### 5. Rol Tanımları (`/admin/roles`)
- **Amaç:** Rol Tanımları modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-roles-page, admin-roles-readonly-banner, admin-roles-title`
  - Öne çıkan aksiyonlar: filtrele, detay görüntüle, onay/reddet, kaydet/yayınla (modüle göre).
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
  1) Mevcut kayıt güncellenir.
  1) Silme/iptal işlemi uygulanır.
- **API Uçları:**
  - `GET /api/admin/permissions/flags` — Admin Permissions Flags
  - `POST /api/admin/permissions/grant` — Admin Permissions Grant
  - `GET /api/admin/permissions/me` — Admin Permissions Me
  - `POST /api/admin/permissions/migrate-from-roles` — Admin Permissions Migrate From Roles
  - `GET /api/admin/permissions/overrides` — Admin Permissions Overrides
  - `GET /api/admin/permissions/overrides/export` — Admin Permissions Overrides Export
  - `POST /api/admin/permissions/revoke` — Admin Permissions Revoke
  - `GET /api/admin/permissions/shadow-diff` — Admin Permissions Shadow Diff
  - `GET /api/admin/permissions/snapshot` — Admin Permissions Snapshot
  - `GET /api/admin/permissions/users` — Admin Permissions Users
- **Veri Modelleri (DB):** `UserPermission, User`
- **Rol / Yetki:** `super_admin`
- **Validasyon Kuralları:**
  - Body şeması AdminPermissionGrantPayload: zorunlu alanlar -> target_user_id, domain, action, reason
  - country (query)
  - page (query) | integer
  - size (query) | integer
  - q (query)
  - sort (query)

### 6. Yetki Atama (RBAC Matrix) (`/admin/rbac-matrix`)
- **Amaç:** Yetki Atama (RBAC Matrix) modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `rbac-matrix-page, rbac-matrix-readonly-banner, rbac-matrix-snapshot-card, rbac-matrix-snapshot-state, rbac-matrix-snapshot-title, rbac-matrix-title`
  - Öne çıkan aksiyonlar: filtrele, detay görüntüle, onay/reddet, kaydet/yayınla (modüle göre).
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
- **API Uçları:**
  - `GET /api/admin/permissions/flags` — Admin Permissions Flags
  - `POST /api/admin/permissions/grant` — Admin Permissions Grant
  - `GET /api/admin/permissions/me` — Admin Permissions Me
  - `POST /api/admin/permissions/migrate-from-roles` — Admin Permissions Migrate From Roles
  - `GET /api/admin/permissions/overrides` — Admin Permissions Overrides
  - `GET /api/admin/permissions/overrides/export` — Admin Permissions Overrides Export
  - `POST /api/admin/permissions/revoke` — Admin Permissions Revoke
  - `GET /api/admin/permissions/shadow-diff` — Admin Permissions Shadow Diff
  - `GET /api/admin/permissions/snapshot` — Admin Permissions Snapshot
  - `GET /api/admin/permissions/users` — Admin Permissions Users
- **Veri Modelleri (DB):** `UserPermission`
- **Rol / Yetki:** `super_admin`
- **Validasyon Kuralları:**
  - Body şeması AdminPermissionGrantPayload: zorunlu alanlar -> target_user_id, domain, action, reason
  - country (query)
  - page (query) | integer
  - size (query) | integer
  - q (query)
  - sort (query)

### 7. Permission Yönetimi (`/admin/permissions`)
- **Amaç:** Permission Yönetimi modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-permissions-content-grid, admin-permissions-draft-actions, admin-permissions-draft-card, admin-permissions-draft-close, admin-permissions-draft-country-multiselect, admin-permissions-draft-global-scope, admin-permissions-draft-global-scope-label, admin-permissions-draft-header, admin-permissions-draft-reason, admin-permissions-draft-reason-wrap`
  - Öne çıkan buton aksiyonları: Kapat
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
- **API Uçları:**
  - `GET /api/admin/permissions/flags` — Admin Permissions Flags
  - `POST /api/admin/permissions/grant` — Admin Permissions Grant
  - `GET /api/admin/permissions/me` — Admin Permissions Me
  - `POST /api/admin/permissions/migrate-from-roles` — Admin Permissions Migrate From Roles
  - `GET /api/admin/permissions/overrides` — Admin Permissions Overrides
  - `GET /api/admin/permissions/overrides/export` — Admin Permissions Overrides Export
  - `POST /api/admin/permissions/revoke` — Admin Permissions Revoke
  - `GET /api/admin/permissions/shadow-diff` — Admin Permissions Shadow Diff
  - `GET /api/admin/permissions/snapshot` — Admin Permissions Snapshot
  - `GET /api/admin/permissions/users` — Admin Permissions Users
- **Veri Modelleri (DB):** `UserPermission`
- **Rol / Yetki:** `super_admin`
- **Validasyon Kuralları:**
  - Body şeması AdminPermissionGrantPayload: zorunlu alanlar -> target_user_id, domain, action, reason
  - country (query)
  - page (query) | integer
  - size (query) | integer
  - q (query)
  - sort (query)

## Üyeler
Bireysel/kurumsal üye yaşam döngüsü yönetimi.

### 8. Bireysel Kullanıcılar (`/admin/individual-users`)
- **Amaç:** Bireysel Kullanıcılar modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `individual-users-action-cancel, individual-users-action-confirm, individual-users-action-message, individual-users-action-modal, individual-users-action-title, individual-users-controls, individual-users-empty, individual-users-error, individual-users-export-button, individual-users-filters`
  - Öne çıkan buton aksiyonları: Ara, {actionLoading ? "İşleniyor" : "Onayla"}, {exporting ? "Dışa Aktarılıyor" : "CSV Export"}, İptal
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
  1) Mevcut kayıt güncellenir.
  1) Silme/iptal işlemi uygulanır.
- **API Uçları:**
  - `GET /api/admin/individual-users` — List Individual Users
  - `GET /api/admin/individual-users/export/csv` — Admin Individual Users Export Csv
  - `GET /api/admin/users` — List Admin Users
  - `POST /api/admin/users` — Create Admin User
  - `POST /api/admin/users/bulk-deactivate` — Bulk Deactivate Admins
  - `DELETE /api/admin/users/{user_id}` — Delete User
  - `PATCH /api/admin/users/{user_id}` — Update Admin User
  - `POST /api/admin/users/{user_id}/activate` — Activate User
  - `GET /api/admin/users/{user_id}/detail` — Admin User Detail
  - `PATCH /api/admin/users/{user_id}/risk-level` — Admin Update Risk Level
- **Veri Modelleri (DB):** `User, ConsumerProfile`
- **Rol / Yetki:** `super_admin, country_admin, support, moderator`
- **Validasyon Kuralları:**
  - search (query)
  - country (query)
  - status (query)
  - sort_by (query)
  - sort_dir (query)
  - page (query) | integer

### 9. Kurumsal Kullanıcılar (`/admin/dealers`)
- **Amaç:** Kurumsal Kullanıcılar modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `dealer-drawer, dealer-drawer-actions, dealer-drawer-audit, dealer-drawer-audit-empty, dealer-drawer-audit-error, dealer-drawer-audit-loading, dealer-drawer-close, dealer-drawer-company, dealer-drawer-contact, dealer-drawer-country`
  - Öne çıkan buton aksiyonları: Ara, Kapat, {actionLoading ? 'İşleniyor' : 'Onayla'}, İptal
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
- **API Uçları:**
  - `GET /api/admin/dealers` — Admin List Dealers
  - `GET /api/admin/dealers/{dealer_id}` — Admin Get Dealer Detail
  - `GET /api/admin/dealers/{dealer_id}/audit-logs` — Admin Get Dealer Audit Logs
  - `POST /api/admin/dealers/{dealer_id}/plan` — Admin Assign Dealer Plan
  - `POST /api/admin/dealers/{dealer_id}/status` — Admin Set Dealer Status
- **Veri Modelleri (DB):** `Dealer, DealerUser, DealerProfile`
- **Rol / Yetki:** `super_admin, country_admin, support, moderator`
- **Validasyon Kuralları:**
  - search (query)
  - country (query)
  - status (query)
  - plan_id (query)
  - sort_by (query)
  - sort_dir (query)

### 10. Bireysel Üye Başvurular (`/admin/individual-applications`)
- **Amaç:** Bireysel Üye Başvurular modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Bu modülde test-id kapsamı sınırlı; ekran temel olarak liste/form aksiyonlarına odaklanır.
  - Öne çıkan buton aksiyonları: Ara
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
  1) Mevcut kayıt güncellenir.
- **API Uçları:**
  - `GET /api/admin/applications/assignees` — List Support Application Assignees
  - `PATCH /api/admin/applications/{application_id}/status` — Update Support Application Status
  - `GET /api/admin/individual-applications` — Admin List Individual Applications
  - `POST /api/admin/individual-applications/{app_id}/approve` — Admin Approve Individual Application
  - `POST /api/admin/individual-applications/{app_id}/reject` — Admin Reject Individual Application
- **Veri Modelleri (DB):** `Application`
- **Rol / Yetki:** `super_admin, country_admin, support, moderator`
- **Validasyon Kuralları:**
  - application_id (path) | zorunlu | string
  - Body şeması SupportApplicationStatusPayload: zorunlu alanlar -> status
  - skip (query) | integer
  - limit (query) | integer
  - status (query)
  - search (query)

### 11. Kurumsal Üye Başvurular (`/admin/dealer-applications`)
- **Amaç:** Kurumsal Üye Başvurular modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Bu modülde test-id kapsamı sınırlı; ekran temel olarak liste/form aksiyonlarına odaklanır.
  - Öne çıkan buton aksiyonları: Ara
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
  1) Mevcut kayıt güncellenir.
- **API Uçları:**
  - `GET /api/admin/applications/assignees` — List Support Application Assignees
  - `PATCH /api/admin/applications/{application_id}/status` — Update Support Application Status
  - `GET /api/admin/dealer-applications` — Admin List Dealer Applications
  - `POST /api/admin/dealer-applications/{app_id}/approve` — Admin Approve Dealer Application
  - `POST /api/admin/dealer-applications/{app_id}/reject` — Admin Reject Dealer Application
- **Veri Modelleri (DB):** `Application, DealerApplication`
- **Rol / Yetki:** `super_admin, country_admin, support, moderator`
- **Validasyon Kuralları:**
  - application_id (path) | zorunlu | string
  - Body şeması SupportApplicationStatusPayload: zorunlu alanlar -> status
  - skip (query) | integer
  - limit (query) | integer
  - status (query)
  - search (query)

## İlan & Moderasyon
İlan onayı, rapor inceleme ve aksiyon operasyonu.

### 12. Moderation Queue (`/admin/moderation`)
- **Amaç:** Moderation Queue modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `moderation-action-cancel, moderation-action-dialog, moderation-action-reason, moderation-action-reason-note, moderation-action-submit, moderation-bulk-approve, moderation-bulk-bar, moderation-bulk-cancel, moderation-bulk-dialog, moderation-bulk-reason`
  - Öne çıkan buton aksiyonları: Onayla, Submit
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
- **API Uçları:**
  - `GET /api/admin/listings` — Admin Listings
  - `POST /api/admin/listings/batch-publish/run` — Admin Run Batch Publish Scheduler Once
  - `GET /api/admin/listings/batch-publish/stats` — Admin Get Batch Publish Stats
  - `POST /api/admin/listings/{listing_id}/approve` — Admin Approve Listing
  - `POST /api/admin/listings/{listing_id}/doping` — Admin Update Listing Doping
  - `POST /api/admin/listings/{listing_id}/force-unpublish` — Admin Force Unpublish Listing
  - `POST /api/admin/listings/{listing_id}/needs_revision` — Admin Needs Revision Listing
  - `POST /api/admin/listings/{listing_id}/reject` — Admin Reject Listing
  - `POST /api/admin/listings/{listing_id}/soft-delete` — Admin Soft Delete Listing
  - `POST /api/admin/moderation/bulk-approve` — Admin Bulk Approve Listings
- **Veri Modelleri (DB):** `ModerationItem, ModerationAction, Listing`
- **Rol / Yetki:** `super_admin, country_admin, moderator`
- **Validasyon Kuralları:**
  - skip (query) | integer
  - limit (query) | integer
  - status (query)
  - q (query)
  - dealer_only (query)
  - category_id (query)

### 13. Rapor Paneli (`/admin/reports`)
- **Amaç:** Rapor Paneli modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-reports-context, admin-reports-page, admin-reports-title, report-detail-close, report-detail-conversation-id, report-detail-empty, report-detail-id, report-detail-listing-price, report-detail-listing-status, report-detail-listing-title`
  - Öne çıkan buton aksiyonları: Filtreleri Temizle, Kapat, Soft Delete Listing, Status Güncelle, Suspend Seller
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
- **API Uçları:**
  - `GET /api/admin/reports` — Admin Reports
  - `GET /api/admin/reports/messages` — Admin Message Reports
  - `POST /api/admin/reports/messages/{report_id}/status` — Admin Message Report Status Change
  - `GET /api/admin/reports/{report_id}` — Admin Report Detail
  - `POST /api/admin/reports/{report_id}/status` — Admin Report Status Change
  - `POST /api/reports` — Create Report
  - `POST /api/reports/messages` — Create Message Report
- **Veri Modelleri (DB):** `Report, MessageReport`
- **Rol / Yetki:** `super_admin, country_admin, moderator`
- **Validasyon Kuralları:**
  - status (query)
  - reason (query)
  - listing_id (query)
  - skip (query) | integer
  - limit (query) | integer
  - message_id (query)

### 14. Tüm İlanlar (`/admin/listings`)
- **Amaç:** Tüm İlanlar modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-listings-context, admin-listings-title, listing-action-cancel-button, listing-action-confirm-button, listing-action-modal, listing-action-note-input, listing-action-reason-input, listing-action-subtitle, listing-action-title, listings-category-option-all`
  - Öne çıkan buton aksiyonları: Confirm, Filtreleri Temizle
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
- **API Uçları:**
  - `GET /api/admin/listings` — Admin Listings
  - `POST /api/admin/listings/batch-publish/run` — Admin Run Batch Publish Scheduler Once
  - `GET /api/admin/listings/batch-publish/stats` — Admin Get Batch Publish Stats
  - `POST /api/admin/listings/{listing_id}/approve` — Admin Approve Listing
  - `POST /api/admin/listings/{listing_id}/doping` — Admin Update Listing Doping
  - `POST /api/admin/listings/{listing_id}/force-unpublish` — Admin Force Unpublish Listing
  - `POST /api/admin/listings/{listing_id}/needs_revision` — Admin Needs Revision Listing
  - `POST /api/admin/listings/{listing_id}/reject` — Admin Reject Listing
  - `POST /api/admin/listings/{listing_id}/soft-delete` — Admin Soft Delete Listing
  - `POST /api/admin/moderation/bulk-approve` — Admin Bulk Approve Listings
- **Veri Modelleri (DB):** `Listing, DopingRequest, ListingSearch`
- **Rol / Yetki:** `super_admin, country_admin, moderator`
- **Validasyon Kuralları:**
  - skip (query) | integer
  - limit (query) | integer
  - status (query)
  - q (query)
  - dealer_only (query)
  - category_id (query)

### 15. Ücretli İlanlar (`/admin/listings/paid`)
- **Amaç:** Ücretli İlanlar modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-listings-context, admin-listings-title, listing-action-cancel-button, listing-action-confirm-button, listing-action-modal, listing-action-note-input, listing-action-reason-input, listing-action-subtitle, listing-action-title, listings-category-option-all`
  - Öne çıkan buton aksiyonları: Confirm, Filtreleri Temizle
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
- **API Uçları:**
  - `GET /api/admin/doping/requests` — List Doping Requests
  - `POST /api/admin/doping/requests/{request_id}/approve` — Approve Doping Request
  - `POST /api/admin/doping/requests/{request_id}/mark-paid` — Mark Doping Paid
  - `POST /api/admin/doping/requests/{request_id}/publish` — Publish Doping Request
  - `GET /api/admin/listings` — Admin Listings
  - `POST /api/admin/listings/batch-publish/run` — Admin Run Batch Publish Scheduler Once
  - `GET /api/admin/listings/batch-publish/stats` — Admin Get Batch Publish Stats
  - `POST /api/admin/listings/{listing_id}/approve` — Admin Approve Listing
  - `POST /api/admin/listings/{listing_id}/doping` — Admin Update Listing Doping
  - `POST /api/admin/listings/{listing_id}/force-unpublish` — Admin Force Unpublish Listing
- **Veri Modelleri (DB):** `Listing, DopingRequest, ListingSearch`
- **Rol / Yetki:** `super_admin, country_admin, moderator`
- **Validasyon Kuralları:**
  - status (query)
  - request_id (path) | zorunlu | string
  - Body şeması DopingApprovalPayload: zorunlu alanlar -> request_id
  - skip (query) | integer
  - limit (query) | integer
  - q (query)

### 16. Vitrin İlanlar (`/admin/listings/featured`)
- **Amaç:** Vitrin İlanlar modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-listings-context, admin-listings-title, listing-action-cancel-button, listing-action-confirm-button, listing-action-modal, listing-action-note-input, listing-action-reason-input, listing-action-subtitle, listing-action-title, listings-category-option-all`
  - Öne çıkan buton aksiyonları: Confirm, Filtreleri Temizle
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
- **API Uçları:**
  - `GET /api/admin/doping/requests` — List Doping Requests
  - `POST /api/admin/doping/requests/{request_id}/approve` — Approve Doping Request
  - `POST /api/admin/doping/requests/{request_id}/mark-paid` — Mark Doping Paid
  - `POST /api/admin/doping/requests/{request_id}/publish` — Publish Doping Request
  - `GET /api/admin/listings` — Admin Listings
  - `POST /api/admin/listings/batch-publish/run` — Admin Run Batch Publish Scheduler Once
  - `GET /api/admin/listings/batch-publish/stats` — Admin Get Batch Publish Stats
  - `POST /api/admin/listings/{listing_id}/approve` — Admin Approve Listing
  - `POST /api/admin/listings/{listing_id}/doping` — Admin Update Listing Doping
  - `POST /api/admin/listings/{listing_id}/force-unpublish` — Admin Force Unpublish Listing
- **Veri Modelleri (DB):** `Listing, DopingRequest, ListingSearch`
- **Rol / Yetki:** `super_admin, country_admin, moderator`
- **Validasyon Kuralları:**
  - status (query)
  - request_id (path) | zorunlu | string
  - Body şeması DopingApprovalPayload: zorunlu alanlar -> request_id
  - skip (query) | integer
  - limit (query) | integer
  - q (query)

### 17. Acil İlanlar (`/admin/listings/urgent`)
- **Amaç:** Acil İlanlar modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-listings-context, admin-listings-title, listing-action-cancel-button, listing-action-confirm-button, listing-action-modal, listing-action-note-input, listing-action-reason-input, listing-action-subtitle, listing-action-title, listings-category-option-all`
  - Öne çıkan buton aksiyonları: Confirm, Filtreleri Temizle
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
- **API Uçları:**
  - `GET /api/admin/doping/requests` — List Doping Requests
  - `POST /api/admin/doping/requests/{request_id}/approve` — Approve Doping Request
  - `POST /api/admin/doping/requests/{request_id}/mark-paid` — Mark Doping Paid
  - `POST /api/admin/doping/requests/{request_id}/publish` — Publish Doping Request
  - `GET /api/admin/listings` — Admin Listings
  - `POST /api/admin/listings/batch-publish/run` — Admin Run Batch Publish Scheduler Once
  - `GET /api/admin/listings/batch-publish/stats` — Admin Get Batch Publish Stats
  - `POST /api/admin/listings/{listing_id}/approve` — Admin Approve Listing
  - `POST /api/admin/listings/{listing_id}/doping` — Admin Update Listing Doping
  - `POST /api/admin/listings/{listing_id}/force-unpublish` — Admin Force Unpublish Listing
- **Veri Modelleri (DB):** `Listing, DopingRequest, ListingSearch`
- **Rol / Yetki:** `super_admin, country_admin, moderator`
- **Validasyon Kuralları:**
  - status (query)
  - request_id (path) | zorunlu | string
  - Body şeması DopingApprovalPayload: zorunlu alanlar -> request_id
  - skip (query) | integer
  - limit (query) | integer
  - q (query)

### 18. Bireysel İlan Başvuruları (`/admin/individual-listing-applications`)
- **Amaç:** Bireysel İlan Başvuruları modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Bu modülde test-id kapsamı sınırlı; ekran temel olarak liste/form aksiyonlarına odaklanır.
  - Öne çıkan aksiyonlar: filtrele, detay görüntüle, onay/reddet, kaydet/yayınla (modüle göre).
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
- **API Uçları:**
  - `GET /api/admin/individual-applications` — Admin List Individual Applications
  - `POST /api/admin/individual-applications/{app_id}/approve` — Admin Approve Individual Application
  - `POST /api/admin/individual-applications/{app_id}/reject` — Admin Reject Individual Application
  - `GET /api/admin/listings` — Admin Listings
  - `POST /api/admin/listings/batch-publish/run` — Admin Run Batch Publish Scheduler Once
  - `GET /api/admin/listings/batch-publish/stats` — Admin Get Batch Publish Stats
  - `POST /api/admin/listings/{listing_id}/approve` — Admin Approve Listing
  - `POST /api/admin/listings/{listing_id}/doping` — Admin Update Listing Doping
  - `POST /api/admin/listings/{listing_id}/force-unpublish` — Admin Force Unpublish Listing
  - `POST /api/admin/listings/{listing_id}/needs_revision` — Admin Needs Revision Listing
- **Veri Modelleri (DB):** `ListingDesignConfig`
- **Rol / Yetki:** `super_admin, country_admin, moderator`
- **Validasyon Kuralları:**
  - skip (query) | integer
  - limit (query) | integer
  - status (query)
  - search (query)
  - app_id (path) | zorunlu | string
  - Body şeması IndividualApplicationRejectPayload: zorunlu alanlar -> reason

### 19. Bireysel Ücretli İlan (`/admin/individual-listing-applications/paid`)
- **Amaç:** Bireysel Ücretli İlan modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-listings-context, admin-listings-title, listing-action-cancel-button, listing-action-confirm-button, listing-action-modal, listing-action-note-input, listing-action-reason-input, listing-action-subtitle, listing-action-title, listings-category-option-all`
  - Öne çıkan buton aksiyonları: Confirm, Filtreleri Temizle
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
- **API Uçları:**
  - `GET /api/admin/individual-applications` — Admin List Individual Applications
  - `POST /api/admin/individual-applications/{app_id}/approve` — Admin Approve Individual Application
  - `POST /api/admin/individual-applications/{app_id}/reject` — Admin Reject Individual Application
  - `GET /api/admin/listings` — Admin Listings
  - `POST /api/admin/listings/batch-publish/run` — Admin Run Batch Publish Scheduler Once
  - `GET /api/admin/listings/batch-publish/stats` — Admin Get Batch Publish Stats
  - `POST /api/admin/listings/{listing_id}/approve` — Admin Approve Listing
  - `POST /api/admin/listings/{listing_id}/doping` — Admin Update Listing Doping
  - `POST /api/admin/listings/{listing_id}/force-unpublish` — Admin Force Unpublish Listing
  - `POST /api/admin/listings/{listing_id}/needs_revision` — Admin Needs Revision Listing
- **Veri Modelleri (DB):** `ListingDesignConfig`
- **Rol / Yetki:** `super_admin, country_admin, moderator`
- **Validasyon Kuralları:**
  - skip (query) | integer
  - limit (query) | integer
  - status (query)
  - search (query)
  - app_id (path) | zorunlu | string
  - Body şeması IndividualApplicationRejectPayload: zorunlu alanlar -> reason

### 20. Bireysel Vitrin İlan (`/admin/individual-listing-applications/featured`)
- **Amaç:** Bireysel Vitrin İlan modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-listings-context, admin-listings-title, listing-action-cancel-button, listing-action-confirm-button, listing-action-modal, listing-action-note-input, listing-action-reason-input, listing-action-subtitle, listing-action-title, listings-category-option-all`
  - Öne çıkan buton aksiyonları: Confirm, Filtreleri Temizle
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
- **API Uçları:**
  - `GET /api/admin/individual-applications` — Admin List Individual Applications
  - `POST /api/admin/individual-applications/{app_id}/approve` — Admin Approve Individual Application
  - `POST /api/admin/individual-applications/{app_id}/reject` — Admin Reject Individual Application
  - `GET /api/admin/listings` — Admin Listings
  - `POST /api/admin/listings/batch-publish/run` — Admin Run Batch Publish Scheduler Once
  - `GET /api/admin/listings/batch-publish/stats` — Admin Get Batch Publish Stats
  - `POST /api/admin/listings/{listing_id}/approve` — Admin Approve Listing
  - `POST /api/admin/listings/{listing_id}/doping` — Admin Update Listing Doping
  - `POST /api/admin/listings/{listing_id}/force-unpublish` — Admin Force Unpublish Listing
  - `POST /api/admin/listings/{listing_id}/needs_revision` — Admin Needs Revision Listing
- **Veri Modelleri (DB):** `ListingDesignConfig`
- **Rol / Yetki:** `super_admin, country_admin, moderator`
- **Validasyon Kuralları:**
  - skip (query) | integer
  - limit (query) | integer
  - status (query)
  - search (query)
  - app_id (path) | zorunlu | string
  - Body şeması IndividualApplicationRejectPayload: zorunlu alanlar -> reason

### 21. Bireysel Acil İlan (`/admin/individual-listing-applications/urgent`)
- **Amaç:** Bireysel Acil İlan modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-listings-context, admin-listings-title, listing-action-cancel-button, listing-action-confirm-button, listing-action-modal, listing-action-note-input, listing-action-reason-input, listing-action-subtitle, listing-action-title, listings-category-option-all`
  - Öne çıkan buton aksiyonları: Confirm, Filtreleri Temizle
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
- **API Uçları:**
  - `GET /api/admin/individual-applications` — Admin List Individual Applications
  - `POST /api/admin/individual-applications/{app_id}/approve` — Admin Approve Individual Application
  - `POST /api/admin/individual-applications/{app_id}/reject` — Admin Reject Individual Application
  - `GET /api/admin/listings` — Admin Listings
  - `POST /api/admin/listings/batch-publish/run` — Admin Run Batch Publish Scheduler Once
  - `GET /api/admin/listings/batch-publish/stats` — Admin Get Batch Publish Stats
  - `POST /api/admin/listings/{listing_id}/approve` — Admin Approve Listing
  - `POST /api/admin/listings/{listing_id}/doping` — Admin Update Listing Doping
  - `POST /api/admin/listings/{listing_id}/force-unpublish` — Admin Force Unpublish Listing
  - `POST /api/admin/listings/{listing_id}/needs_revision` — Admin Needs Revision Listing
- **Veri Modelleri (DB):** `ListingDesignConfig`
- **Rol / Yetki:** `super_admin, country_admin, moderator`
- **Validasyon Kuralları:**
  - skip (query) | integer
  - limit (query) | integer
  - status (query)
  - search (query)
  - app_id (path) | zorunlu | string
  - Body şeması IndividualApplicationRejectPayload: zorunlu alanlar -> reason

### 22. Kurumsal İlan Başvuruları (`/admin/corporate-listing-applications`)
- **Amaç:** Kurumsal İlan Başvuruları modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Bu modülde test-id kapsamı sınırlı; ekran temel olarak liste/form aksiyonlarına odaklanır.
  - Öne çıkan aksiyonlar: filtrele, detay görüntüle, onay/reddet, kaydet/yayınla (modüle göre).
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
- **API Uçları:**
  - `GET /api/admin/dealer-applications` — Admin List Dealer Applications
  - `POST /api/admin/dealer-applications/{app_id}/approve` — Admin Approve Dealer Application
  - `POST /api/admin/dealer-applications/{app_id}/reject` — Admin Reject Dealer Application
  - `GET /api/admin/listings` — Admin Listings
  - `POST /api/admin/listings/batch-publish/run` — Admin Run Batch Publish Scheduler Once
  - `GET /api/admin/listings/batch-publish/stats` — Admin Get Batch Publish Stats
  - `POST /api/admin/listings/{listing_id}/approve` — Admin Approve Listing
  - `POST /api/admin/listings/{listing_id}/doping` — Admin Update Listing Doping
  - `POST /api/admin/listings/{listing_id}/force-unpublish` — Admin Force Unpublish Listing
  - `POST /api/admin/listings/{listing_id}/needs_revision` — Admin Needs Revision Listing
- **Veri Modelleri (DB):** `ListingDesignConfig`
- **Rol / Yetki:** `super_admin, country_admin, moderator`
- **Validasyon Kuralları:**
  - skip (query) | integer
  - limit (query) | integer
  - status (query)
  - search (query)
  - app_id (path) | zorunlu | string
  - Body şeması DealerApplicationRejectPayload: zorunlu alanlar -> reason

### 23. Kurumsal Ücretli İlan (`/admin/corporate-listing-applications/paid`)
- **Amaç:** Kurumsal Ücretli İlan modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-listings-context, admin-listings-title, listing-action-cancel-button, listing-action-confirm-button, listing-action-modal, listing-action-note-input, listing-action-reason-input, listing-action-subtitle, listing-action-title, listings-category-option-all`
  - Öne çıkan buton aksiyonları: Confirm, Filtreleri Temizle
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
- **API Uçları:**
  - `GET /api/admin/dealer-applications` — Admin List Dealer Applications
  - `POST /api/admin/dealer-applications/{app_id}/approve` — Admin Approve Dealer Application
  - `POST /api/admin/dealer-applications/{app_id}/reject` — Admin Reject Dealer Application
  - `GET /api/admin/listings` — Admin Listings
  - `POST /api/admin/listings/batch-publish/run` — Admin Run Batch Publish Scheduler Once
  - `GET /api/admin/listings/batch-publish/stats` — Admin Get Batch Publish Stats
  - `POST /api/admin/listings/{listing_id}/approve` — Admin Approve Listing
  - `POST /api/admin/listings/{listing_id}/doping` — Admin Update Listing Doping
  - `POST /api/admin/listings/{listing_id}/force-unpublish` — Admin Force Unpublish Listing
  - `POST /api/admin/listings/{listing_id}/needs_revision` — Admin Needs Revision Listing
- **Veri Modelleri (DB):** `ListingDesignConfig`
- **Rol / Yetki:** `super_admin, country_admin, moderator`
- **Validasyon Kuralları:**
  - skip (query) | integer
  - limit (query) | integer
  - status (query)
  - search (query)
  - app_id (path) | zorunlu | string
  - Body şeması DealerApplicationRejectPayload: zorunlu alanlar -> reason

### 24. Kurumsal Vitrin İlan (`/admin/corporate-listing-applications/featured`)
- **Amaç:** Kurumsal Vitrin İlan modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-listings-context, admin-listings-title, listing-action-cancel-button, listing-action-confirm-button, listing-action-modal, listing-action-note-input, listing-action-reason-input, listing-action-subtitle, listing-action-title, listings-category-option-all`
  - Öne çıkan buton aksiyonları: Confirm, Filtreleri Temizle
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
- **API Uçları:**
  - `GET /api/admin/dealer-applications` — Admin List Dealer Applications
  - `POST /api/admin/dealer-applications/{app_id}/approve` — Admin Approve Dealer Application
  - `POST /api/admin/dealer-applications/{app_id}/reject` — Admin Reject Dealer Application
  - `GET /api/admin/listings` — Admin Listings
  - `POST /api/admin/listings/batch-publish/run` — Admin Run Batch Publish Scheduler Once
  - `GET /api/admin/listings/batch-publish/stats` — Admin Get Batch Publish Stats
  - `POST /api/admin/listings/{listing_id}/approve` — Admin Approve Listing
  - `POST /api/admin/listings/{listing_id}/doping` — Admin Update Listing Doping
  - `POST /api/admin/listings/{listing_id}/force-unpublish` — Admin Force Unpublish Listing
  - `POST /api/admin/listings/{listing_id}/needs_revision` — Admin Needs Revision Listing
- **Veri Modelleri (DB):** `ListingDesignConfig`
- **Rol / Yetki:** `super_admin, country_admin, moderator`
- **Validasyon Kuralları:**
  - skip (query) | integer
  - limit (query) | integer
  - status (query)
  - search (query)
  - app_id (path) | zorunlu | string
  - Body şeması DealerApplicationRejectPayload: zorunlu alanlar -> reason

### 25. Kurumsal Acil İlan (`/admin/corporate-listing-applications/urgent`)
- **Amaç:** Kurumsal Acil İlan modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-listings-context, admin-listings-title, listing-action-cancel-button, listing-action-confirm-button, listing-action-modal, listing-action-note-input, listing-action-reason-input, listing-action-subtitle, listing-action-title, listings-category-option-all`
  - Öne çıkan buton aksiyonları: Confirm, Filtreleri Temizle
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
- **API Uçları:**
  - `GET /api/admin/dealer-applications` — Admin List Dealer Applications
  - `POST /api/admin/dealer-applications/{app_id}/approve` — Admin Approve Dealer Application
  - `POST /api/admin/dealer-applications/{app_id}/reject` — Admin Reject Dealer Application
  - `GET /api/admin/listings` — Admin Listings
  - `POST /api/admin/listings/batch-publish/run` — Admin Run Batch Publish Scheduler Once
  - `GET /api/admin/listings/batch-publish/stats` — Admin Get Batch Publish Stats
  - `POST /api/admin/listings/{listing_id}/approve` — Admin Approve Listing
  - `POST /api/admin/listings/{listing_id}/doping` — Admin Update Listing Doping
  - `POST /api/admin/listings/{listing_id}/force-unpublish` — Admin Force Unpublish Listing
  - `POST /api/admin/listings/{listing_id}/needs_revision` — Admin Needs Revision Listing
- **Veri Modelleri (DB):** `ListingDesignConfig`
- **Rol / Yetki:** `super_admin, country_admin, moderator`
- **Validasyon Kuralları:**
  - skip (query) | integer
  - limit (query) | integer
  - status (query)
  - search (query)
  - app_id (path) | zorunlu | string
  - Body şeması DealerApplicationRejectPayload: zorunlu alanlar -> reason

## Reklamlar
Reklam envanteri ve kampanya yönetimi.

### 26. Reklam Yönetimi (`/admin/ads`)
- **Amaç:** Reklam Yönetimi modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-ads-active, admin-ads-active-conflict, admin-ads-analytics-apply, admin-ads-analytics-breakdown, admin-ads-analytics-breakdown-title, admin-ads-analytics-content, admin-ads-analytics-empty, admin-ads-analytics-end, admin-ads-analytics-error, admin-ads-analytics-filters`
  - Öne çıkan buton aksiyonları: Reklam Oluştur, {deleteLoading ? 'Siliniyor...' : 'Sil'}
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
  1) Mevcut kayıt güncellenir.
  1) Silme/iptal işlemi uygulanır.
- **API Uçları:**
  - `GET /api/admin/ads` — List Ads Admin
  - `POST /api/admin/ads` — Create Ad
  - `GET /api/admin/ads/analytics` — Get Ads Analytics
  - `GET /api/admin/ads/campaigns` — List Ad Campaigns
  - `POST /api/admin/ads/campaigns` — Create Ad Campaign
  - `GET /api/admin/ads/campaigns/{campaign_id}` — Get Ad Campaign
  - `PATCH /api/admin/ads/campaigns/{campaign_id}` — Update Ad Campaign
  - `DELETE /api/admin/ads/campaigns/{campaign_id}/ads/{ad_id}` — Unlink Ad From Campaign
  - `POST /api/admin/ads/campaigns/{campaign_id}/ads/{ad_id}` — Link Ad To Campaign
  - `DELETE /api/admin/ads/{ad_id}` — Delete Ad
- **Veri Modelleri (DB):** `Advertisement, AdCampaign, AdImpression, AdClick`
- **Rol / Yetki:** `super_admin, ads_manager`
- **Validasyon Kuralları:**
  - placement (query)
  - Body şeması AdCreatePayload: zorunlu alanlar -> placement
  - range (query) | string
  - start_at (query)
  - end_at (query)
  - group_by (query) | string

### 27. Kampanyalar (`/admin/ads/campaigns`)
- **Amaç:** Kampanyalar modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-ads-campaigns, admin-campaigns-ads-empty, admin-campaigns-ads-link, admin-campaigns-ads-select, admin-campaigns-ads-tab, admin-campaigns-create, admin-campaigns-create-advertiser, admin-campaigns-create-budget, admin-campaigns-create-button, admin-campaigns-create-currency`
  - Öne çıkan buton aksiyonları: Kampanya Oluştur, Kaydet, Reklam Ekle
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
  1) Mevcut kayıt güncellenir.
  1) Silme/iptal işlemi uygulanır.
- **API Uçları:**
  - `GET /api/admin/ads` — List Ads Admin
  - `POST /api/admin/ads` — Create Ad
  - `GET /api/admin/ads/analytics` — Get Ads Analytics
  - `GET /api/admin/ads/campaigns` — List Ad Campaigns
  - `POST /api/admin/ads/campaigns` — Create Ad Campaign
  - `GET /api/admin/ads/campaigns/{campaign_id}` — Get Ad Campaign
  - `PATCH /api/admin/ads/campaigns/{campaign_id}` — Update Ad Campaign
  - `DELETE /api/admin/ads/campaigns/{campaign_id}/ads/{ad_id}` — Unlink Ad From Campaign
  - `POST /api/admin/ads/campaigns/{campaign_id}/ads/{ad_id}` — Link Ad To Campaign
  - `DELETE /api/admin/ads/{ad_id}` — Delete Ad
- **Veri Modelleri (DB):** `Advertisement, AdCampaign, AdImpression, AdClick`
- **Rol / Yetki:** `super_admin, ads_manager`
- **Validasyon Kuralları:**
  - placement (query)
  - Body şeması AdCreatePayload: zorunlu alanlar -> placement
  - range (query) | string
  - start_at (query)
  - end_at (query)
  - group_by (query) | string

## Fiyatlandırma
Kampanya/katman/paket fiyat konfigürasyonları.

### 28. Kampanya Modu (`/admin/pricing/campaign`)
- **Amaç:** Kampanya Modu modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-pricing-campaign-card, admin-pricing-campaign-dates, admin-pricing-campaign-end, admin-pricing-campaign-error, admin-pricing-campaign-form, admin-pricing-campaign-page, admin-pricing-campaign-publish, admin-pricing-campaign-save, admin-pricing-campaign-scope, admin-pricing-campaign-start`
  - Öne çıkan aksiyonlar: filtrele, detay görüntüle, onay/reddet, kaydet/yayınla (modüle göre).
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
  1) Mevcut kayıt güncellenir.
  1) Silme/iptal işlemi uygulanır.
- **API Uçları:**
  - `GET /api/admin/campaigns` — List Campaigns
  - `POST /api/admin/campaigns` — Create Campaign
  - `DELETE /api/admin/campaigns/{campaign_id}` — Archive Campaign
  - `GET /api/admin/campaigns/{campaign_id}` — Get Campaign Detail
  - `PUT /api/admin/campaigns/{campaign_id}` — Update Campaign
  - `POST /api/admin/campaigns/{campaign_id}/activate` — Activate Campaign
  - `POST /api/admin/campaigns/{campaign_id}/archive` — Archive Campaign Action
  - `POST /api/admin/campaigns/{campaign_id}/pause` — Pause Campaign
  - `GET /api/admin/pricing/campaign` — Get Pricing Campaign
  - `PUT /api/admin/pricing/campaign` — Update Pricing Campaign
- **Veri Modelleri (DB):** `PricingCampaign, PricingTierRule, PricingPackage, PricingCampaignItem, PricingPriceSnapshot`
- **Rol / Yetki:** `super_admin, pricing_manager`
- **Validasyon Kuralları:**
  - type (query)
  - status (query)
  - country (query)
  - q (query)
  - date_range (query)
  - page (query) | integer

### 29. Bireysel Kampanyalar (`/admin/pricing/tiers`)
- **Amaç:** Bireysel Kampanyalar modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-pricing-individual-create, admin-pricing-individual-empty, admin-pricing-individual-error, admin-pricing-individual-modal, admin-pricing-individual-modal-active, admin-pricing-individual-modal-active-toggle, admin-pricing-individual-modal-cancel, admin-pricing-individual-modal-card, admin-pricing-individual-modal-close, admin-pricing-individual-modal-currency`
  - Öne çıkan buton aksiyonları: Kampanya Yap, Kaydet
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
  1) Mevcut kayıt güncellenir.
  1) Silme/iptal işlemi uygulanır.
- **API Uçları:**
  - `GET /api/admin/pricing/campaign` — Get Pricing Campaign
  - `PUT /api/admin/pricing/campaign` — Update Pricing Campaign
  - `GET /api/admin/pricing/campaign-items` — List Pricing Campaign Items
  - `POST /api/admin/pricing/campaign-items` — Create Pricing Campaign Item
  - `DELETE /api/admin/pricing/campaign-items/{item_id}` — Delete Pricing Campaign Item
  - `PUT /api/admin/pricing/campaign-items/{item_id}` — Update Pricing Campaign Item
  - `PATCH /api/admin/pricing/campaign-items/{item_id}/status` — Update Pricing Campaign Item Status
  - `GET /api/admin/pricing/packages` — List Pricing Packages Admin
  - `PUT /api/admin/pricing/packages` — Update Pricing Packages
  - `GET /api/admin/pricing/tiers` — List Pricing Tiers
- **Veri Modelleri (DB):** `PricingCampaign, PricingTierRule, PricingPackage, PricingCampaignItem, PricingPriceSnapshot`
- **Rol / Yetki:** `super_admin, pricing_manager`
- **Validasyon Kuralları:**
  - Body şeması PricingCampaignPolicyPayload: zorunlu alanlar -> is_enabled
  - scope (query) | zorunlu | string
  - listing_type (query)
  - include_deleted (query) | boolean
  - Body şeması PricingCampaignItemCreatePayload: zorunlu alanlar -> scope, listing_quota, price_amount, publish_days, start_at, end_at
  - item_id (path) | zorunlu | string

### 30. Kurumsal Kampanyalar (`/admin/pricing/packages`)
- **Amaç:** Kurumsal Kampanyalar modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-pricing-corporate-create, admin-pricing-corporate-empty, admin-pricing-corporate-error, admin-pricing-corporate-modal, admin-pricing-corporate-modal-active, admin-pricing-corporate-modal-active-toggle, admin-pricing-corporate-modal-cancel, admin-pricing-corporate-modal-card, admin-pricing-corporate-modal-close, admin-pricing-corporate-modal-currency`
  - Öne çıkan buton aksiyonları: Kampanya Yap, Kaydet
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
  1) Mevcut kayıt güncellenir.
  1) Silme/iptal işlemi uygulanır.
- **API Uçları:**
  - `GET /api/admin/pricing/campaign` — Get Pricing Campaign
  - `PUT /api/admin/pricing/campaign` — Update Pricing Campaign
  - `GET /api/admin/pricing/campaign-items` — List Pricing Campaign Items
  - `POST /api/admin/pricing/campaign-items` — Create Pricing Campaign Item
  - `DELETE /api/admin/pricing/campaign-items/{item_id}` — Delete Pricing Campaign Item
  - `PUT /api/admin/pricing/campaign-items/{item_id}` — Update Pricing Campaign Item
  - `PATCH /api/admin/pricing/campaign-items/{item_id}/status` — Update Pricing Campaign Item Status
  - `GET /api/admin/pricing/packages` — List Pricing Packages Admin
  - `PUT /api/admin/pricing/packages` — Update Pricing Packages
  - `GET /api/admin/pricing/tiers` — List Pricing Tiers
- **Veri Modelleri (DB):** `PricingCampaign, PricingTierRule, PricingPackage, PricingCampaignItem, PricingPriceSnapshot`
- **Rol / Yetki:** `super_admin, pricing_manager`
- **Validasyon Kuralları:**
  - Body şeması PricingCampaignPolicyPayload: zorunlu alanlar -> is_enabled
  - scope (query) | zorunlu | string
  - listing_type (query)
  - include_deleted (query) | boolean
  - Body şeması PricingCampaignItemCreatePayload: zorunlu alanlar -> scope, listing_quota, price_amount, publish_days, start_at, end_at
  - item_id (path) | zorunlu | string

## Site İç Tasarımı
Header/footer/tema/vitrin ve içerik düzenleyicileri.

### 31. Header Yönetimi (`/admin/site-design/header`)
- **Amaç:** Header Yönetimi modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-header-add-link-button, admin-header-current-mode-title, admin-header-error, admin-header-file-input, admin-header-links-editor, admin-header-links-empty, admin-header-links-list, admin-header-links-title, admin-header-management, admin-header-mode-tabs`
  - Öne çıkan buton aksiyonları: {t('admin_header_add_link')}, {t('admin_header_upload_button')}, {t('header_logout')}
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
  1) Mevcut kayıt güncellenir.
- **API Uçları:**
  - `GET /api/admin/site/header` — Admin Get Site Header
  - `PUT /api/admin/site/header` — Admin Update Site Header
  - `POST /api/admin/site/header/logo` — Upload Site Header Logo
  - `GET /api/site/header` — Get Site Header
- **Veri Modelleri (DB):** `SiteHeaderConfig, SiteHeaderSetting`
- **Rol / Yetki:** `super_admin`
- **Validasyon Kuralları:**
  - mode (query) | string
  - Body şeması Body_upload_site_header_logo_api_admin_site_header_logo_post: zorunlu alanlar -> file

### 32. Footer Yönetimi (`/admin/site-design/footer`)
- **Amaç:** Footer Yönetimi modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-footer-actions, admin-footer-add-row, admin-footer-builder, admin-footer-empty, admin-footer-error, admin-footer-management, admin-footer-preview, admin-footer-publish, admin-footer-rows, admin-footer-save-draft`
  - Öne çıkan buton aksiyonları: Satır Ekle, Yayınla
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
  1) Mevcut kayıt güncellenir.
- **API Uçları:**
  - `GET /api/admin/footer/layout` — Get Footer Layout Admin
  - `PUT /api/admin/footer/layout` — Save Footer Layout
  - `POST /api/admin/footer/layout/publish` — Publish Footer Layout
  - `GET /api/admin/footer/layout/{layout_id}` — Get Footer Layout Version
  - `POST /api/admin/footer/layout/{layout_id}/publish` — Publish Footer Layout Version
  - `GET /api/admin/footer/layouts` — List Footer Layouts
  - `GET /api/site/footer` — Get Footer Layout
- **Veri Modelleri (DB):** `FooterLayout`
- **Rol / Yetki:** `super_admin`
- **Validasyon Kuralları:**
  - Body şeması FooterLayoutPayload: zorunlu alanlar -> layout
  - layout_id (path) | zorunlu | string

### 33. Tema Yönetimi (`/admin/site-design/theme`)
- **Amaç:** Tema Yönetimi modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-theme-actions, admin-theme-active-version, admin-theme-editor, admin-theme-error, admin-theme-header, admin-theme-layout, admin-theme-loading, admin-theme-management, admin-theme-meta, admin-theme-mode-tabs`
  - Öne çıkan buton aksiyonları: Kaydet (Draft), Primary CTA, Publish, Secondary, Varsayılanlara Dön, İlan Ver
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
  1) Mevcut kayıt güncellenir.
- **API Uçları:**
  - `GET /api/admin/site/theme` — Get Site Theme Admin
  - `PUT /api/admin/site/theme/config` — Save Site Theme Config
  - `GET /api/admin/site/theme/config/{theme_id}` — Get Site Theme Config
  - `POST /api/admin/site/theme/config/{theme_id}/publish` — Publish Site Theme Config
  - `GET /api/admin/site/theme/configs` — List Site Theme Configs
  - `GET /api/site/theme` — Get Site Theme
- **Veri Modelleri (DB):** `SiteThemeConfig, UITheme, UIThemeAssignment`
- **Rol / Yetki:** `super_admin`
- **Validasyon Kuralları:**
  - Body şeması ThemeConfigPayload: zorunlu alanlar -> config
  - theme_id (path) | zorunlu | string

### 34. Vitrin Yönetimi (`/admin/site-design/showcase`)
- **Amaç:** Vitrin Yönetimi modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-showcase-category-add, admin-showcase-category-block, admin-showcase-category-default-columns, admin-showcase-category-default-grid, admin-showcase-category-default-listing-count, admin-showcase-category-default-rows, admin-showcase-category-empty, admin-showcase-category-enabled, admin-showcase-category-enabled-wrap, admin-showcase-category-list`
  - Öne çıkan buton aksiyonları: Ana Kategori Ekle, Sil, Taslağı Kaydet, Yayınla
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
  1) Mevcut kayıt güncellenir.
  1) Silme/iptal işlemi uygulanır.
- **API Uçları:**
  - `GET /api/admin/site/showcase-layout` — Get Showcase Layout Admin
  - `PUT /api/admin/site/showcase-layout/config` — Save Showcase Layout Config
  - `DELETE /api/admin/site/showcase-layout/config/{layout_id}` — Delete Showcase Layout Config
  - `GET /api/admin/site/showcase-layout/config/{layout_id}` — Get Showcase Layout Config
  - `POST /api/admin/site/showcase-layout/config/{layout_id}/publish` — Publish Showcase Layout Config
  - `GET /api/admin/site/showcase-layout/configs` — List Showcase Layout Configs
  - `GET /api/site/showcase-layout` — Get Site Showcase Layout
- **Veri Modelleri (DB):** `SiteShowcaseLayout`
- **Rol / Yetki:** `super_admin`
- **Validasyon Kuralları:**
  - Body şeması ShowcaseLayoutConfigPayload: zorunlu alanlar -> config
  - layout_id (path) | zorunlu | string

### 35. Ana Site Kategorisi (`/admin/site-design/home-category`)
- **Amaç:** Ana Site Kategorisi modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `home-category-crud-add-root, home-category-crud-card, home-category-crud-empty, home-category-crud-error, home-category-crud-field-active, home-category-crud-field-active-wrap, home-category-crud-field-icon, home-category-crud-field-icon-upload, home-category-crud-field-icon-upload-error, home-category-crud-field-icon-upload-help`
  - Öne çıkan buton aksiyonları: Kapat, Yenile, {categorySaving ? 'Kaydediliyor...' : 'Kaydet'}, {saving ? 'Kaydediliyor...' : 'Layout Kaydet'}, İptal
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Mevcut kayıt güncellenir.
- **API Uçları:**
  - `GET /api/admin/site/home-category-layout` — Get Home Category Layout Admin
  - `PUT /api/admin/site/home-category-layout` — Save Home Category Layout Admin
  - `GET /api/site/home-category-layout` — Get Site Home Category Layout
- **Veri Modelleri (DB):** `Category`
- **Rol / Yetki:** `super_admin`
- **Validasyon Kuralları:**
  - country (query)
  - Body şeması HomeCategoryLayoutPayload: zorunlu alanlar -> config

### 36. İlan Tasarım (`/admin/site-design/listing`)
- **Amaç:** İlan Tasarım modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-listing-design-actions, admin-listing-design-address-country-mode, admin-listing-design-address-module-apply, admin-listing-design-address-requirements, admin-listing-design-contact-message-toggle, admin-listing-design-contact-message-toggle-wrap, admin-listing-design-contact-phone-toggle, admin-listing-design-contact-phone-toggle-wrap, admin-listing-design-duration-discount-toggle, admin-listing-design-duration-discount-wrap`
  - Öne çıkan buton aksiyonları: Key’i Temizle, Modül Kutusu Ekle, Yenile, {saving ? 'Kaydediliyor…' : 'Tümünü Kaydet'}
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
  1) Mevcut kayıt güncellenir.
- **API Uçları:**
  - `GET /api/admin/site/listing-design` — Get Admin Listing Design
  - `PUT /api/admin/site/listing-design` — Save Admin Listing Design
  - `POST /api/admin/site/listing-design/publish` — Publish Admin Listing Design
  - `POST /api/admin/site/listing-design/rollback` — Rollback Admin Listing Design
  - `GET /api/site/listing-design` — Get Site Listing Design
- **Veri Modelleri (DB):** `ListingDesignConfig`
- **Rol / Yetki:** `super_admin`
- **Validasyon Kuralları:**
  - Body şeması ListingSiteDesignPayload: zorunlu alanlar -> config

### 37. İlan Ver Akış Ayarları (`/admin/site-design/listing-flow-settings?focus=listing-create`)
- **Amaç:** İlan Ver Akış Ayarları modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Bu modülde test-id kapsamı sınırlı; ekran temel olarak liste/form aksiyonlarına odaklanır.
  - Öne çıkan aksiyonlar: filtrele, detay görüntüle, onay/reddet, kaydet/yayınla (modüle göre).
- **İş Akışı:**
  1) Ekran üzerinden filtreleme, aksiyon ve detay inceleme akışı yürütülür.
- **API Uçları:**
  - Ekran, ortak servis katmanı üzerinden veri alır (endpoint çağrısı ilgili hook/servis dosyasında).
- **Veri Modelleri (DB):** `ListingDesignConfig`
- **Rol / Yetki:** `super_admin`
- **Validasyon Kuralları:**
  - Parametreler route seviyesinde tip ve zorunluluk kurallarıyla doğrulanır.

### 38. Content Builder (`/admin/site-design/content-builder`)
- **Amaç:** Content Builder modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-content-builder-add-row-button, admin-content-builder-apply-preset-button, admin-content-builder-binding-action-grid, admin-content-builder-binding-active-empty, admin-content-builder-binding-active-page-id, admin-content-builder-binding-active-summary, admin-content-builder-binding-bind-button, admin-content-builder-binding-category-input, admin-content-builder-binding-category-search-input, admin-content-builder-binding-category-search-wrap`
  - Öne çıkan buton aksiyonları: Aktifi Getir, Auto-Fix Uygula, Binding Kaldır, Bu Page'i Bağla, Draft Kaydet, Formları Aç
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
  1) Mevcut kayıt güncellenir.
- **API Uçları:**
  - `GET /api/admin/site/content-layout/audit-logs` — List Layout Audit Logs
  - `POST /api/admin/site/content-layout/bindings` — Bind Layout Page To Category
  - `GET /api/admin/site/content-layout/bindings/active` — Get Active Binding
  - `POST /api/admin/site/content-layout/bindings/unbind` — Unbind Layout Page From Category
  - `GET /api/admin/site/content-layout/components` — List Layout Components
  - `POST /api/admin/site/content-layout/components` — Create Layout Component
  - `PATCH /api/admin/site/content-layout/components/{component_id}` — Patch Layout Component
  - `GET /api/admin/site/content-layout/metrics` — Get Layout Builder Metrics
  - `GET /api/admin/site/content-layout/pages` — List Layout Pages
  - `POST /api/admin/site/content-layout/pages` — Create Layout Page Admin
- **Veri Modelleri (DB):** `LayoutPage, LayoutRevision, LayoutBinding, LayoutComponentDefinition, LayoutAuditLog`
- **Rol / Yetki:** `super_admin`
- **Validasyon Kuralları:**
  - entity_type (query)
  - entity_id (query)
  - actor_user_id (query)
  - action (query)
  - start_at (query)
  - end_at (query)

### 39. Kullanıcı Tasarım (`/admin/user-interface-design`)
- **Amaç:** Kullanıcı Tasarım modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-user-interface-design-header, admin-user-interface-design-page, admin-user-interface-design-subtitle, admin-user-interface-design-tab-content, admin-user-interface-design-tab-corporate-header, admin-user-interface-design-tab-dashboard, admin-user-interface-design-tab-theme, admin-user-interface-design-tabs, admin-user-interface-design-title, ui-designer-corporate-actions`
  - Öne çıkan buton aksiyonları: Atamayı Kaydet, Canlı Render Oku, Effective Getir, Effective Oku, Forma Yükle, Latest Draft’ı Çek + Diff’i Yeniden Aç
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
- **API Uçları:**
  - `POST /api/admin/ui/configs/header/logo` — Admin Upload Header Logo
  - `GET /api/admin/ui/configs/{config_type}` — Admin Get Ui Config
  - `POST /api/admin/ui/configs/{config_type}` — Admin Save Ui Config
  - `POST /api/admin/ui/configs/{config_type}/conflict-sync` — Admin Ui Config Conflict Sync
  - `GET /api/admin/ui/configs/{config_type}/diff` — Admin Ui Config Diff
  - `GET /api/admin/ui/configs/{config_type}/ops-alerts/delivery-audit` — Admin Ui Publish Alert Delivery Audit
  - `GET /api/admin/ui/configs/{config_type}/ops-alerts/html-report` — Admin Ui Publish Alerts Html Report
  - `GET /api/admin/ui/configs/{config_type}/ops-alerts/secret-checklist` — Admin Ui Publish Alerts Secret Checklist
  - `GET /api/admin/ui/configs/{config_type}/ops-alerts/secret-presence` — Admin Ui Publish Alerts Secret Presence
  - `POST /api/admin/ui/configs/{config_type}/ops-alerts/simulate` — Admin Ui Publish Alerts Simulate
- **Veri Modelleri (DB):** `UIConfig, UILogoAsset`
- **Rol / Yetki:** `super_admin, country_admin`
- **Validasyon Kuralları:**
  - Body şeması Body_admin_upload_header_logo_api_admin_ui_configs_header_logo_post: zorunlu alanlar -> file
  - config_type (path) | zorunlu | string
  - segment (query) | string
  - scope (query) | string
  - scope_id (query)
  - status (query) | string

## Operasyon
Yayın sağlığı, güvenilirlik ve canlılık kontrolü.

### 40. Publish Health (`/admin/ops/publish-health`)
- **Amaç:** Publish Health modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `ops-alert-channel-breakdown-grid, ops-alert-last-failure-timestamp, ops-alert-metrics-refresh-button, ops-alert-open-html-report-button, ops-alert-reliability-grid, ops-alert-rerun-actions, ops-alert-rerun-button, ops-alert-rerun-card, ops-alert-rerun-channel-results, ops-alert-rerun-channel-results-empty`
  - Öne çıkan buton aksiyonları: HTML Rapor Aç, KPI Yenile, Publish KPI Yenile
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
- **API Uçları:**
  - `GET /api/admin/ops/alert-delivery-metrics` — Admin Ops Alert Delivery Metrics
  - `POST /api/admin/ops/alert-delivery/rerun-simulation` — Admin Ops Alert Delivery Rerun Simulation
  - `GET /api/admin/system/health-detail` — Ops Health Detail Route
  - `GET /api/admin/system/health-summary` — Ops Health Summary Route
- **Veri Modelleri (DB):** `AuditLog, WebhookEventLog`
- **Rol / Yetki:** `super_admin, country_admin, ops`
- **Validasyon Kuralları:**
  - window (query) | string

## İçerik Yönetimi
Statik bilgi sayfalarının yönetimi.

### 41. Bilgi Sayfaları (`/admin/info-pages`)
- **Amaç:** Bilgi Sayfaları modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-info-pages, admin-info-pages-cancel, admin-info-pages-content-de, admin-info-pages-content-fr, admin-info-pages-content-tr, admin-info-pages-create, admin-info-pages-empty, admin-info-pages-error, admin-info-pages-modal, admin-info-pages-modal-card`
  - Öne çıkan buton aksiyonları: Kaydet, Yeni Sayfa
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
  1) Mevcut kayıt güncellenir.
- **API Uçları:**
  - `GET /api/admin/info-pages` — List Info Pages
  - `POST /api/admin/info-pages` — Create Info Page
  - `GET /api/admin/info-pages/{page_id}` — Get Info Page Admin
  - `PATCH /api/admin/info-pages/{page_id}` — Update Info Page
- **Veri Modelleri (DB):** `InfoPage`
- **Rol / Yetki:** `super_admin, country_admin`
- **Validasyon Kuralları:**
  - Body şeması InfoPagePayload: zorunlu alanlar -> slug, title_tr, title_de, title_fr, content_tr, content_de, content_fr
  - page_id (path) | zorunlu | string

## Katalog & İçerik
Kategori, özellik ve içerik ağacının yönetimi.

### 42. Kategoriler (`/admin/categories`)
- **Amaç:** Kategoriler modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-categories-page, categories-active-checkbox, categories-active-wrapper, categories-bulk-actions-bar, categories-bulk-actions-buttons, categories-bulk-actions-summary, categories-bulk-activate, categories-bulk-deactivate, categories-bulk-delete, categories-bulk-delete-actions`
  - Öne çıkan buton aksiyonları: Bir üst seviyeye dön, Düzenle, Ekle, Kaldır, Kopyala, Seçilenleri Sil
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
  1) Mevcut kayıt güncellenir.
  1) Silme/iptal işlemi uygulanır.
- **API Uçları:**
  - `GET /api/admin/categories` — Admin List Categories
  - `POST /api/admin/categories` — Admin Create Category
  - `POST /api/admin/categories/bulk-actions` — Admin Categories Bulk Actions
  - `GET /api/admin/categories/bulk-actions/jobs/{job_id}` — Admin Categories Bulk Action Job Status
  - `POST /api/admin/categories/image-upload` — Admin Upload Category Image
  - `GET /api/admin/categories/import-export/export/csv` — Admin Export Categories Csv
  - `GET /api/admin/categories/import-export/export/json` — Admin Export Categories Json
  - `GET /api/admin/categories/import-export/export/xlsx` — Admin Export Categories Xlsx
  - `POST /api/admin/categories/import-export/import/commit` — Admin Import Categories Commit
  - `POST /api/admin/categories/import-export/import/dry-run` — Admin Import Categories Dry Run
- **Veri Modelleri (DB):** `Category, CategoryTranslation, CategorySchemaVersion, CategoryBulkJob`
- **Rol / Yetki:** `super_admin, country_admin, moderator`
- **Validasyon Kuralları:**
  - country (query)
  - module (query)
  - active_flag (query)
  - Body şeması CategoryCreatePayload: zorunlu alanlar -> name, slug, sort_order
  - Body şeması CategoryBulkActionPayload: zorunlu alanlar -> action
  - Body enum kuralları (CategoryBulkActionPayload): action=['delete', 'activate', 'deactivate']; scope=['ids', 'filter']

### 43. Kategori Import/Export (`/admin/categories/import-export`)
- **Amaç:** Kategori Import/Export modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-categories-import-export-page, categories-apply-result, categories-export-actions, categories-export-country, categories-export-csv, categories-export-desc, categories-export-filters, categories-export-module, categories-export-title, categories-import-apply`
  - Öne çıkan buton aksiyonları: CSV Export, Dry-run Yap, Uygula, Örnek CSV indir
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
  1) Mevcut kayıt güncellenir.
  1) Silme/iptal işlemi uygulanır.
- **API Uçları:**
  - `GET /api/admin/categories` — Admin List Categories
  - `POST /api/admin/categories` — Admin Create Category
  - `POST /api/admin/categories/bulk-actions` — Admin Categories Bulk Actions
  - `GET /api/admin/categories/bulk-actions/jobs/{job_id}` — Admin Categories Bulk Action Job Status
  - `POST /api/admin/categories/image-upload` — Admin Upload Category Image
  - `GET /api/admin/categories/import-export/export/csv` — Admin Export Categories Csv
  - `GET /api/admin/categories/import-export/export/json` — Admin Export Categories Json
  - `GET /api/admin/categories/import-export/export/xlsx` — Admin Export Categories Xlsx
  - `POST /api/admin/categories/import-export/import/commit` — Admin Import Categories Commit
  - `POST /api/admin/categories/import-export/import/dry-run` — Admin Import Categories Dry Run
- **Veri Modelleri (DB):** `Category, CategoryTranslation, CategorySchemaVersion, CategoryBulkJob`
- **Rol / Yetki:** `super_admin, country_admin`
- **Validasyon Kuralları:**
  - country (query)
  - module (query)
  - active_flag (query)
  - Body şeması CategoryCreatePayload: zorunlu alanlar -> name, slug, sort_order
  - Body şeması CategoryBulkActionPayload: zorunlu alanlar -> action
  - Body enum kuralları (CategoryBulkActionPayload): action=['delete', 'activate', 'deactivate']; scope=['ids', 'filter']

### 44. Özellikler (`/admin/attributes`)
- **Amaç:** Özellikler modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-attributes-page, attributes-active-checkbox, attributes-cancel, attributes-category-select, attributes-country-input, attributes-create-open, attributes-error, attributes-filter-category, attributes-filterable-checkbox, attributes-key-input`
  - Öne çıkan buton aksiyonları: Kaydet, Yeni Attribute
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
  1) Mevcut kayıt güncellenir.
  1) Silme/iptal işlemi uygulanır.
- **API Uçları:**
  - `GET /api/admin/attributes` — Admin List Attributes
  - `POST /api/admin/attributes` — Admin Create Attribute
  - `DELETE /api/admin/attributes/{attribute_id}` — Admin Delete Attribute
  - `PATCH /api/admin/attributes/{attribute_id}` — Admin Update Attribute
  - `GET /api/attributes` — Public Attributes
- **Veri Modelleri (DB):** `Attribute, AttributeOption, CategoryAttributeMap`
- **Rol / Yetki:** `super_admin, country_admin`
- **Validasyon Kuralları:**
  - category_id (query)
  - country (query)
  - Body şeması AttributeCreatePayload: zorunlu alanlar -> category_id, name, key, type
  - attribute_id (path) | zorunlu | string
  - category_id (query) | zorunlu | string

### 45. Kurumsal Menü Yönetimi (`/admin/dealer-portal-config`)
- **Amaç:** Kurumsal Menü Yönetimi modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-dealer-config-actions, admin-dealer-config-diff-panel, admin-dealer-config-diff-title, admin-dealer-config-diff-total, admin-dealer-config-draft-meta, admin-dealer-config-error, admin-dealer-config-header, admin-dealer-config-header-card, admin-dealer-config-header-list, admin-dealer-config-header-title-quick`
  - Öne çıkan buton aksiyonları: Son işlemi geri al, Sürükle, Yenile, {publishing ? 'Yayınlanıyor...' : 'Yayınla'}, {saving ? 'Kaydediliyor...' : 'Taslağı Kaydet'}
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
  1) Mevcut kayıt güncellenir.
- **API Uçları:**
  - `GET /api/admin/dealer-portal/config` — Admin Dealer Portal Config
  - `POST /api/admin/dealer-portal/config/draft/publish` — Admin Dealer Portal Draft Publish
  - `POST /api/admin/dealer-portal/config/draft/save` — Admin Dealer Portal Draft Save
  - `GET /api/admin/dealer-portal/config/preview` — Admin Dealer Portal Config Preview
  - `GET /api/admin/dealer-portal/config/revisions` — Admin Dealer Portal Revisions
  - `POST /api/admin/dealer-portal/config/rollback` — Admin Dealer Portal Rollback
  - `POST /api/admin/dealer-portal/modules/reorder` — Admin Dealer Portal Module Reorder
  - `PATCH /api/admin/dealer-portal/modules/{module_id}` — Admin Dealer Portal Module Update
  - `POST /api/admin/dealer-portal/nav/reorder` — Admin Dealer Portal Nav Reorder
  - `PATCH /api/admin/dealer-portal/nav/{item_id}` — Admin Dealer Portal Nav Update
- **Veri Modelleri (DB):** `DealerModule, DealerNavItem, DealerConfigRevision`
- **Rol / Yetki:** `super_admin`
- **Validasyon Kuralları:**
  - mode (query) | string
  - Body şeması DealerDraftRollbackPayload: zorunlu alanlar -> revision_id
  - Body şeması DealerModuleReorderPayload: zorunlu alanlar -> ordered_ids
  - module_id (path) | zorunlu | string
  - Body şeması DealerVisibilityPayload: zorunlu alanlar -> visible

## Araç Verisi
Araç marka/model master data operasyonları.

### 46. Araç Markaları (`/admin/vehicle-makes`)
- **Amaç:** Araç Markaları modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-vehicle-makes-page, vehicle-makes-active-checkbox, vehicle-makes-bulk-delete, vehicle-makes-cancel, vehicle-makes-country, vehicle-makes-country-input, vehicle-makes-create-open, vehicle-makes-error, vehicle-makes-filter-type, vehicle-makes-filters`
  - Öne çıkan buton aksiyonları: Kaydet, Seçili ({selectedIds.size}) Pasifleştir, Yeni Marka
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
  1) Mevcut kayıt güncellenir.
  1) Silme/iptal işlemi uygulanır.
- **API Uçları:**
  - `GET /api/admin/vehicle-makes` — Admin List Vehicle Makes
  - `POST /api/admin/vehicle-makes` — Admin Create Vehicle Make
  - `POST /api/admin/vehicle-makes/bulk-delete` — Admin Bulk Delete Vehicle Makes
  - `DELETE /api/admin/vehicle-makes/{make_id}` — Admin Delete Vehicle Make
  - `PATCH /api/admin/vehicle-makes/{make_id}` — Admin Update Vehicle Make
- **Veri Modelleri (DB):** `VehicleMake`
- **Rol / Yetki:** `super_admin, country_admin`
- **Validasyon Kuralları:**
  - country (query)
  - vehicle_type (query)
  - Body şeması VehicleMakeCreatePayload: zorunlu alanlar -> name, slug, country_code
  - Body şeması VehicleBulkDeletePayload: zorunlu alanlar -> ids
  - make_id (path) | zorunlu | string

### 47. Araç Modelleri (`/admin/vehicle-models`)
- **Amaç:** Araç Modelleri modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-vehicle-models-page, vehicle-models-active-checkbox, vehicle-models-bulk-delete, vehicle-models-cancel, vehicle-models-country, vehicle-models-create-open, vehicle-models-error, vehicle-models-filter-make, vehicle-models-filter-type, vehicle-models-filters`
  - Öne çıkan buton aksiyonları: Kaydet, Seçili ({selectedIds.size}) Pasifleştir, Yeni Model
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
  1) Mevcut kayıt güncellenir.
  1) Silme/iptal işlemi uygulanır.
- **API Uçları:**
  - `GET /api/admin/vehicle-models` — Admin List Vehicle Models
  - `POST /api/admin/vehicle-models` — Admin Create Vehicle Model
  - `POST /api/admin/vehicle-models/bulk-delete` — Admin Bulk Delete Vehicle Models
  - `DELETE /api/admin/vehicle-models/{model_id}` — Admin Delete Vehicle Model
  - `PATCH /api/admin/vehicle-models/{model_id}` — Admin Update Vehicle Model
- **Veri Modelleri (DB):** `VehicleModel, VehicleTrim`
- **Rol / Yetki:** `super_admin, country_admin`
- **Validasyon Kuralları:**
  - make_id (query)
  - country (query)
  - vehicle_type (query)
  - Body şeması VehicleModelCreatePayload: zorunlu alanlar -> make_id, name, slug, vehicle_type
  - Body şeması VehicleBulkDeletePayload: zorunlu alanlar -> ids
  - model_id (path) | zorunlu | string

### 48. Araç Master Data Import (`/admin/vehicle-master-import`)
- **Amaç:** Araç Master Data Import modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `vehicle-import-api-dry-run, vehicle-import-api-dry-run-toggle, vehicle-import-api-error, vehicle-import-api-flags, vehicle-import-api-full-results, vehicle-import-api-preview-button, vehicle-import-api-preview-output, vehicle-import-api-sold-in-us, vehicle-import-api-status, vehicle-import-api-submit`
  - Öne çıkan buton aksiyonları: Yenile, {apiLoading ? 'İşleniyor...' : 'Çek ve Import Et'}, Örnek JSON indir, İsteği Önizle
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
- **API Uçları:**
  - `POST /api/admin/vehicle-import/apply` — Admin Vehicle Import Apply
  - `POST /api/admin/vehicle-import/dry-run` — Admin Vehicle Import Dry Run
  - `GET /api/admin/vehicle-master-import/jobs` — List Vehicle Import Jobs
  - `POST /api/admin/vehicle-master-import/jobs/api` — Create Vehicle Import Job From Api
  - `POST /api/admin/vehicle-master-import/jobs/upload` — Create Vehicle Import Job From Upload
  - `GET /api/admin/vehicle-master-import/jobs/{job_id}` — Get Vehicle Import Job
- **Veri Modelleri (DB):** `VehicleImportJob, VehicleMake, VehicleModel`
- **Rol / Yetki:** `super_admin, country_admin`
- **Validasyon Kuralları:**
  - Body şeması Body_create_vehicle_import_job_from_upload_api_admin_vehicle_master_import_jobs_upload_post: zorunlu alanlar -> file
  - job_id (path) | zorunlu | string

## Finans
Fatura, ödeme, abonelik ve muhasebe modülleri.

### 49. Finans Overview (`/admin/finance-overview`)
- **Amaç:** Finans Overview modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-finance-card-active-subscriptions, admin-finance-card-failed-rate, admin-finance-card-failed-rate-value, admin-finance-card-mrr, admin-finance-card-mrr-empty, admin-finance-card-refund-rate, admin-finance-card-refund-rate-value, admin-finance-card-revenue, admin-finance-card-revenue-empty, admin-finance-export-invoices`
  - Öne çıkan buton aksiyonları: Uygula, navigate('/admin/invoices')}>Invoices, navigate('/admin/ledger')}>Ledger, navigate('/admin/payments')}>Payments, navigate('/admin/subscriptions')}>Subscriptions
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
  1) Mevcut kayıt güncellenir.
- **API Uçları:**
  - `GET /api/admin/finance/export` — Admin Finance Export
  - `GET /api/admin/finance/ledger` — Admin Finance Ledger List
  - `POST /api/admin/finance/ledger/{entry_id}/reverse` — Admin Finance Reverse Ledger Entry
  - `GET /api/admin/finance/overview` — Admin Finance Overview
  - `GET /api/admin/finance/product-prices` — Admin Finance Product Prices
  - `GET /api/admin/finance/products` — Admin Finance Products
  - `POST /api/admin/finance/products` — Admin Finance Create Product
  - `POST /api/admin/finance/products/{product_id}/prices` — Admin Finance Create Product Price
  - `GET /api/admin/finance/revenue` — Admin Revenue
  - `GET /api/admin/finance/subscriptions` — Admin Finance Subscriptions
- **Veri Modelleri (DB):** `FinanceProduct, FinanceProductPrice, TaxProfile, LedgerEntry`
- **Rol / Yetki:** `super_admin, country_admin, admin, finance`
- **Validasyon Kuralları:**
  - type (query) | zorunlu | string
  - status (query)
  - country (query)
  - start_date (query)
  - end_date (query)
  - currency (query)

### 50. Planlar (`/admin/plans`)
- **Amaç:** Planlar modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `plans-create-button, plans-db-banner, plans-error, plans-filter-chip-country, plans-filter-chip-global, plans-filter-chips, plans-filter-country, plans-filter-country-label, plans-filter-scope, plans-filter-scope-label`
  - Öne çıkan buton aksiyonları: Kapat, Vazgeç, Yeni Plan
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
  1) Mevcut kayıt güncellenir.
- **API Uçları:**
  - `GET /api/admin/plans` — Admin List Plans
  - `POST /api/admin/plans` — Admin Create Plan
  - `GET /api/admin/plans/{plan_id}` — Admin Get Plan
  - `PUT /api/admin/plans/{plan_id}` — Admin Update Plan
  - `POST /api/admin/plans/{plan_id}/archive` — Admin Archive Plan
  - `POST /api/admin/plans/{plan_id}/toggle-active` — Admin Toggle Plan Active
- **Veri Modelleri (DB):** `Plan`
- **Rol / Yetki:** `super_admin, country_admin, admin, finance`
- **Validasyon Kuralları:**
  - scope (query)
  - country_code (query)
  - status (query)
  - period (query)
  - q (query)
  - Body şeması PlanCreatePayload: zorunlu alanlar -> name, country_scope, price_amount, listing_quota, showcase_quota

### 51. Faturalar (`/admin/invoices`)
- **Amaç:** Faturalar modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-invoices-context, admin-invoices-page, admin-invoices-scope-badge, admin-invoices-title, invoice-amount-max, invoice-amount-min, invoice-country-required, invoice-create-amount, invoice-create-close, invoice-create-country`
  - Öne çıkan buton aksiyonları: Kapat, PDF, Temizle, Yeni Invoice, {createLoading ? 'Oluşturuluyor…' : 'Oluştur'}
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
- **API Uçları:**
  - `GET /api/admin/invoices` — Admin List Invoices
  - `POST /api/admin/invoices` — Admin Create Invoice
  - `GET /api/admin/invoices/export/csv` — Admin Export Invoices Csv
  - `GET /api/admin/invoices/{invoice_id}` — Admin Invoice Detail
  - `POST /api/admin/invoices/{invoice_id}/cancel` — Admin Invoice Cancel
  - `GET /api/admin/invoices/{invoice_id}/download-pdf` — Admin Invoice Download Pdf
  - `POST /api/admin/invoices/{invoice_id}/generate-pdf` — Admin Invoice Generate Pdf
  - `POST /api/admin/invoices/{invoice_id}/mark-paid` — Admin Invoice Mark Paid
  - `POST /api/admin/invoices/{invoice_id}/refund` — Admin Invoice Refund
  - `POST /api/admin/invoices/{invoice_id}/regenerate-pdf` — Admin Invoice Regenerate Pdf
- **Veri Modelleri (DB):** `AdminInvoice`
- **Rol / Yetki:** `super_admin, country_admin, admin, finance`
- **Validasyon Kuralları:**
  - status (query)
  - country (query)
  - dealer (query)
  - plan_id (query)
  - date_from (query)
  - date_to (query)

### 52. Transactions Log (`/admin/payments`)
- **Amaç:** Transactions Log modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-transactions-apply-filters, admin-transactions-export-csv, admin-transactions-filter-end-date, admin-transactions-filter-listing-id, admin-transactions-filter-query, admin-transactions-filter-start-date, admin-transactions-filter-status, admin-transactions-filter-user-id, admin-transactions-filters, admin-transactions-header`
  - Öne çıkan buton aksiyonları: CSV Export, Uygula
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
- **API Uçları:**
  - `GET /api/admin/payments` — Admin List Payments
  - `GET /api/admin/payments/export/csv` — Admin Export Payments Csv
  - `GET /api/admin/payments/runtime-health` — Get Admin Payments Runtime Health
  - `GET /api/payments/checkout/status/{session_id}` — Get Checkout Status
  - `POST /api/payments/create-checkout-session` — Create Checkout Session
  - `POST /api/payments/create-intent` — Create Listing Payment Intent
  - `GET /api/payments/runtime-config` — Get Payments Runtime Config
  - `POST /api/payments/stripe/webhook` — Stripe Payment Intent Webhook
  - `POST /api/payments/webhook` — Stripe Payment Intent Webhook
  - `POST /api/payments/{payment_id}/reconcile` — Reconcile Listing Payment
- **Veri Modelleri (DB):** `Payment, PaymentTransaction, ListingPayment, ProcessedWebhookEvent`
- **Rol / Yetki:** `super_admin, country_admin, admin, finance`
- **Validasyon Kuralları:**
  - status (query)
  - start_date (query)
  - end_date (query)
  - q (query)
  - user_id (query)
  - listing_id (query)

### 53. Subscriptions (`/admin/subscriptions`)
- **Amaç:** Subscriptions modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-subscriptions-detail-close, admin-subscriptions-detail-invoice-count, admin-subscriptions-detail-panel, admin-subscriptions-detail-plan, admin-subscriptions-detail-provider, admin-subscriptions-detail-status, admin-subscriptions-detail-title, admin-subscriptions-detail-user, admin-subscriptions-header, admin-subscriptions-page`
  - Öne çıkan aksiyonlar: filtrele, detay görüntüle, onay/reddet, kaydet/yayınla (modüle göre).
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Mevcut kayıt güncellenir.
- **API Uçları:**
  - `GET /api/admin/finance/subscriptions` — Admin Finance Subscriptions
  - `GET /api/admin/finance/subscriptions/{subscription_id}` — Admin Finance Subscription Detail
  - `PATCH /api/admin/finance/subscriptions/{subscription_id}/status` — Admin Finance Update Subscription Status
- **Veri Modelleri (DB):** `UserSubscription, UserPackageSubscription`
- **Rol / Yetki:** `super_admin, country_admin, admin, finance`
- **Validasyon Kuralları:**
  - status (query)
  - skip (query) | integer
  - limit (query) | integer
  - subscription_id (path) | zorunlu | string
  - Body şeması FinanceSubscriptionStatusUpdatePayload: zorunlu alanlar -> target_status

### 54. Ledger (`/admin/ledger`)
- **Amaç:** Ledger modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-ledger-empty, admin-ledger-error, admin-ledger-filter-apply, admin-ledger-filter-reference-id, admin-ledger-filter-reference-type, admin-ledger-filters, admin-ledger-header, admin-ledger-loading, admin-ledger-page, admin-ledger-scope-badge`
  - Öne çıkan buton aksiyonları: Uygula
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
- **API Uçları:**
  - `GET /api/admin/finance/ledger` — Admin Finance Ledger List
  - `POST /api/admin/finance/ledger/{entry_id}/reverse` — Admin Finance Reverse Ledger Entry
  - `GET /api/admin/ledger/export/csv` — Admin Export Ledger Csv
- **Veri Modelleri (DB):** `LedgerAccount, LedgerEntry`
- **Rol / Yetki:** `super_admin, country_admin, admin, finance`
- **Validasyon Kuralları:**
  - reference_type (query)
  - reference_id (query)
  - skip (query) | integer
  - limit (query) | integer
  - entry_id (path) | zorunlu | string
  - currency (query)

### 55. Vergi Oranları (`/admin/tax-rates`)
- **Amaç:** Vergi Oranları modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-tax-context, admin-tax-rates-page, admin-tax-title, tax-create-open, tax-empty, tax-form-active, tax-form-country, tax-form-effective, tax-form-error, tax-form-rate`
  - Öne çıkan buton aksiyonları: Yeni Tax Rate, {editing ? 'Güncelle' : 'Oluştur'}
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
  1) Mevcut kayıt güncellenir.
  1) Silme/iptal işlemi uygulanır.
- **API Uçları:**
  - `GET /api/admin/tax-rates` — Admin List Tax Rates
  - `POST /api/admin/tax-rates` — Admin Create Tax Rate
  - `DELETE /api/admin/tax-rates/{tax_id}` — Admin Delete Tax Rate
  - `PATCH /api/admin/tax-rates/{tax_id}` — Admin Update Tax Rate
- **Veri Modelleri (DB):** `VatRate`
- **Rol / Yetki:** `super_admin, country_admin, admin, finance`
- **Validasyon Kuralları:**
  - country (query)
  - Body şeması TaxRateCreatePayload: zorunlu alanlar -> country_code, rate, effective_date
  - tax_id (path) | zorunlu | string

## Sistem
Ülke, sistem ayarları ve audit süreçleri.

### 56. Ülkeler (`/admin/countries`)
- **Amaç:** Ülkeler modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-countries-page, admin-countries-title, countries-create-open, countries-empty, countries-form-active, countries-form-code, countries-form-currency, countries-form-error, countries-form-language, countries-form-name`
  - Öne çıkan buton aksiyonları: Yeni Ülke, {editing ? 'Güncelle' : 'Oluştur'}
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
  1) Mevcut kayıt güncellenir.
  1) Silme/iptal işlemi uygulanır.
- **API Uçları:**
  - `GET /api/admin/countries` — Admin List Countries
  - `POST /api/admin/countries` — Admin Create Country
  - `DELETE /api/admin/countries/{code}` — Admin Delete Country
  - `GET /api/admin/countries/{code}` — Admin Get Country
  - `PATCH /api/admin/countries/{code}` — Admin Update Country
- **Veri Modelleri (DB):** `Country`
- **Rol / Yetki:** `super_admin, country_admin`
- **Validasyon Kuralları:**
  - Body şeması CountryCreatePayload: zorunlu alanlar -> country_code, name, default_currency
  - code (path) | zorunlu | string

### 57. Audit Dashboard (`/admin/audit`)
- **Amaç:** Audit Dashboard modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-audit-anomalies-card, admin-audit-anomalies-empty-wrap, admin-audit-anomalies-list, admin-audit-anomalies-title, admin-audit-apply-filters, admin-audit-clear-filters, admin-audit-dashboard-header, admin-audit-dashboard-page, admin-audit-dashboard-subtitle, admin-audit-dashboard-title`
  - Öne çıkan buton aksiyonları: Temizle, Uygula, Yenile
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
- **API Uçları:**
  - `GET /api/admin/audit-logs` — Admin List Audit Logs
  - `GET /api/admin/audit-logs/actions` — Admin Audit Actions
  - `GET /api/admin/audit-logs/event-types` — Admin Audit Event Types
  - `GET /api/admin/audit-logs/export` — Admin Export Audit Logs
  - `GET /api/admin/audit-logs/resources` — Admin Audit Resources
  - `GET /api/admin/audit-logs/{log_id}` — Admin Audit Log Detail
  - `GET /api/admin/audit/dashboard/anomalies` — Admin Audit Dashboard Anomalies
  - `GET /api/admin/audit/dashboard/events` — Admin Audit Dashboard Events
  - `GET /api/admin/audit/dashboard/schema` — Admin Audit Dashboard Schema
  - `GET /api/admin/audit/dashboard/stats` — Admin Audit Dashboard Stats
- **Veri Modelleri (DB):** `AuditLog`
- **Rol / Yetki:** `super_admin`
- **Validasyon Kuralları:**
  - page (query) | integer
  - size (query) | integer
  - q (query)
  - actor (query)
  - role (query)
  - country (query)

### 58. Sistem Ayarları (`/admin/system-settings`)
- **Amaç:** Sistem Ayarları modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Kritik öğe test-id örnekleri: `admin-system-settings-page, system-settings-apple-signin-actions, system-settings-apple-signin-card, system-settings-apple-signin-clear-private-key, system-settings-apple-signin-client-id-input, system-settings-apple-signin-client-id-wrap, system-settings-apple-signin-error, system-settings-apple-signin-hint, system-settings-apple-signin-input-grid, system-settings-apple-signin-key-id-input`
  - Öne çıkan buton aksiyonları: Key’i Temizle, Private Key Temizle, Yeni Setting, Yenile, {cloudflareSaving ? 'Kaydediliyor…' : 'Kaydet'}, {editing ? 'Güncelle' : 'Oluştur'}
- **İş Akışı:**
  1) Listeleme/özet görüntüleme yapılır.
  1) Yeni kayıt/aksiyon oluşturulur veya toplu işlem tetiklenir.
  1) Mevcut kayıt güncellenir.
- **API Uçları:**
  - `GET /api/admin/system-settings` — Admin List System Settings
  - `POST /api/admin/system-settings` — Admin Create System Setting
  - `GET /api/admin/system-settings/apple-signin` — Admin Get Apple Signin Settings
  - `POST /api/admin/system-settings/apple-signin` — Admin Save Apple Signin Settings
  - `GET /api/admin/system-settings/cloudflare` — Admin Get Cloudflare Config
  - `POST /api/admin/system-settings/cloudflare` — Admin Update Cloudflare Config
  - `POST /api/admin/system-settings/cloudflare/canary` — Admin Cloudflare Canary
  - `GET /api/admin/system-settings/google-maps` — Admin Get Google Maps Settings
  - `POST /api/admin/system-settings/google-maps` — Admin Save Google Maps Settings
  - `GET /api/admin/system-settings/listing-create` — Admin Get Listing Create Config
- **Veri Modelleri (DB):** `SystemSetting, CloudflareConfig, MeiliSearchConfig`
- **Rol / Yetki:** `super_admin, country_admin`
- **Validasyon Kuralları:**
  - country (query)
  - Body şeması SystemSettingCreatePayload: zorunlu alanlar -> key, value

### 59. Google Maps Ayarları (`/admin/system-settings?focus=google-maps`)
- **Amaç:** Google Maps Ayarları modülünün operasyonel yönetimini sağlamak.
- **Arayüz (UI):**
  - Bu modülde test-id kapsamı sınırlı; ekran temel olarak liste/form aksiyonlarına odaklanır.
  - Öne çıkan aksiyonlar: filtrele, detay görüntüle, onay/reddet, kaydet/yayınla (modüle göre).
- **İş Akışı:**
  1) Ekran üzerinden filtreleme, aksiyon ve detay inceleme akışı yürütülür.
- **API Uçları:**
  - Ekran, ortak servis katmanı üzerinden veri alır (endpoint çağrısı ilgili hook/servis dosyasında).
- **Veri Modelleri (DB):** `SystemSetting, CloudflareConfig, MeiliSearchConfig`
- **Rol / Yetki:** `super_admin, country_admin`
- **Validasyon Kuralları:**
  - Parametreler route seviyesinde tip ve zorunluluk kurallarıyla doğrulanır.

## Notlar
- Bu kılavuz canlı OpenAPI sözleşmesi + admin frontend route haritası üzerinden türetilmiştir.
- Route bazlı aynı bileşeni kullanan ekranlarda (ör. paid/featured/urgent) UI yapısı aynı, filtre/başlık bağlamı farklıdır.
