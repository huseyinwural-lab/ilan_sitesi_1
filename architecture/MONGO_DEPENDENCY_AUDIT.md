# MONGO_DEPENDENCY_AUDIT

Tarih: 2026-02-21
Durum: Mongo devreden çıkarıldı (MONGO_ENABLED=false). Aşağıdaki endpoint’ler Mongo bağımlıdır ve SQL karşılığı tamamlanana kadar feature gate (503) altında tutulur.

## 1) Mongo Bağımlı Endpoint Envanteri

### Public / Portal
- **/api/categories** (public + admin) → Mongo: `categories` koleksiyonu
- **/api/menu/top-items** → Mongo: `menu_top_items` (şu an boş liste döner)
- **/api/v1/listings/*** → Mongo: `vehicle_listings` koleksiyonu
- **/api/v1/favorites** → Mongo: `favorites` koleksiyonu
- **/api/support/*** → Mongo: `support_tickets` koleksiyonu
- **/api/v1/messages** → Mongo: `messages` koleksiyonu

### Admin
- **/api/admin/countries** → Mongo: `countries`
- **/api/admin/menu-management** → Mongo: `menu_top_items`
- **/api/admin/audit-logs** → Mongo: `audit_logs`
- **/api/admin/dealer-applications** → Mongo: `dealer_applications`
- **/api/admin/individual-applications** → Mongo: `individual_applications`

### Kullanıcı / Dealer
- **/api/v1/listings** → Mongo: `vehicle_listings`
- **/api/v1/favorites** → Mongo: `favorites`
- **/api/v1/messages** → Mongo: `messages`

> Not: `/api/admin/users` SQL’e taşındı (Mongo bağımlılığı kaldırıldı).

## 2) Geçici Feature Gate

MONGO kapalı iken aşağıdaki prefix’ler 503 döner:
- `/api/categories`
- `/api/v1/listings`
- `/api/v1/favorites`
- `/api/v1/messages`
- `/api/support`
- `/api/admin/menu`

Not: `/api/admin/countries` Mongo kapalıyken boş liste döner (UI filtreleri kırılmasın diye).

## 3) SQL Karşılığı Taslak Plan (Migration)

### A) Kategoriler + Menü
- **Tablolar:** `categories`, `menu_top_items`
- **İş:** JSONB alanları (translations, module meta), parent-child ilişkisi
- **Adım:** Alembic migration + seed (default_categories, default_menu)

### B) Listing (vehicle_listings)
- **Tablolar:** `vehicle_listings`, `vehicle_listing_media`, `vehicle_listing_attributes`
- **İş:** draft/publish workflow, media upload, moderation status
- **Adım:** Listing modelleri + v1 endpoint’lerini SQL’e taşıma

### C) Favorites
- **Tablo:** `favorites` (user_id, listing_id, created_at)
- **İş:** unique index (user_id, listing_id)

### D) Messages / Support
- **Tablolar:** `messages`, `support_tickets`, `support_messages`
- **İş:** thread/participant modeli + read status

### E) Admin Audit + Applications
- **Tablolar:** `audit_logs`, `dealer_applications`, `individual_applications`
- **İş:** admin filtreleme + export

## 4) Önceliklendirme
1. **Categories + Listings** (wizard ve search blokajını kaldırır)
2. **Favorites + Messages** (consumer portal activation)
3. **Admin Audit + Applications** (admin operasyonları)

