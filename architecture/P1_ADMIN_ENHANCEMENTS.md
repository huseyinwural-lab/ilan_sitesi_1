## P1 — Admin Enhancements (Preview Drawer + Bulk Report Update)

### 1) Admin Listing Preview Drawer
- Trigger: `/admin/listings` satır aksiyonu
- İçerik:
  - Thumbnail galeri (max 5)
  - Başlık / fiyat / lokasyon
  - Seller badge + status
  - Hızlı aksiyonlar: Listing’e Git, Moderation’a Git, Soft Delete
- Data fetch: lazy detail fetch (listing detail endpoint)

### 2) Bulk Report Status Update
- Trigger: /admin/reports listesinde multi-select
- Flow:
  - Status seç (resolved/dismissed)
  - Not (opsiyonel)
  - Confirm modal
- Audit:
  - REPORT_STATUS_CHANGE (per report)

### RBAC
- super_admin + country_admin + moderator
