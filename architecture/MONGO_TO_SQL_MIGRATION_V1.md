# MONGO_TO_SQL_MIGRATION_V1

Tarih: 2026-02-21
Durum: **Plan + Draft Migration** (Local hazır, Preview/Prod için Ops bekleniyor)

## 0) Amaç
Mongo tamamen kaldırılarak tek veri kaynağı Postgres olacak. Bu doküman; kategoriler, ilanlar, favoriler, mesajlar ve destek modüllerinin SQL tasarımını, endpoint eşlemesini ve geçiş adımlarını tanımlar.

## 1) Mevcut Durum (SQL Envanteri)

### Zaten SQL’de Olanlar
- **categories / category_translations** (P0-1) — `app/models/category.py`
- **listings** (moderation için minimum model + indeksler) — `app/models/moderation.py`
- **applications** (support başvuruları) — `app/models/application.py` + `applications_repository.py`
- **users, invoices, plans, payments** gibi çekirdek tablolar

### SQL’de Eksik Olanlar (Mongo bağımlı)
- **favorites** (SQL tablosu draft ile ekleniyor)
- **messages** (SQL tabloları mevcut: `conversations`, `messages`; endpoint refactor gerekiyor)
- **support_messages** (applications için mesajlaşma; draft ile ekleniyor)

## 2) Migrasyon Önceliği (Deterministik)
1. **Categories (master data)**
2. **Listings (consumer side)**
3. **Favorites**
4. **Messages**
5. **Support (messages + full SQL mode)**

> Not: Categories ve Listings tabloları mevcut; bu adımda asıl iş endpoint refactor + seed.

## 3) Alembic Draft (Local için hazır)
- **Draft migration:** `/app/backend/migrations/versions/d2f4c9c4c7ab_mongo_to_sql_phase1_draft.py`
- **Eklenen tablolar:** favorites, support_messages

> Draft migration **head** olarak oluşur. Preview/Prod’da Ops’dan gelen DB üzerinde uygulanmadan önce merge/sequence netleştirilmelidir.

## 4) Şema Tasarımı (Özet)

### 4.1 Favorites
- `favorites(id, user_id, listing_id, created_at)`
- Unique: `(user_id, listing_id)`

### 4.2 Messages
- **Mevcut SQL tabloları:** `conversations`, `messages` (migrations: `1c2ba5052ea4`, `9f9e9c1bb40d`)
- **Eksik alanlar:** unread_count, client_message_id idempotency, thread summary alanları
- **Plan:**
  - `/api/v1/messages` endpointleri `conversations` + `messages` üzerinden yeniden yazılır
  - Gerekirse `conversation_participants` tablosu eklenir (unread_count, last_read_at)

### 4.3 Support Messages
- `support_messages(id, application_id, sender_id, body, attachments, is_internal, created_at)`
- `applications` zaten SQL’de (support başvuru ana kaydı)

## 5) Endpoint → SQL Refactor Haritası

### Categories
- **/api/categories** (public list) → SQL `Category` + `CategoryTranslation`
- **/api/admin/categories** → SQL zaten kısmi (MDM routes) → public endpoint adaptasyonu

### Listings (v1)
- **/api/v1/listings/*** → SQL `Listing` (+ listing extensions)
- `vehicle_listings` Mongo koleksiyonu kaldırılır

### Favorites
- **/api/v1/favorites** → SQL `favorites` tablosu

### Messages
- **/api/v1/messages/*** → SQL `conversations` + `messages`
- **/ws/messages** → SQL read/write + last_message_at güncellemesi
- Gerekirse `conversation_participants` ile unread_count yönetimi

### Support
- **/api/applications** → SQL `applications` (aktif)
- **/api/support/*** (varsa) → SQL `applications` + `support_messages`

## 6) Feature Gate Temizliği (Hedef)
- `MONGO_ENABLED` bayrağı ve mongo fallback kaldırılacak.
- Mongo koleksiyonları tamamen devre dışı.
- Health endpoint `database: postgres` olarak sabitlenir.

## 7) Veri Taşıma Stratejisi (Backfill)
1. **Snapshot export** (Mongo → JSON)
2. **Mapping & normalization** (UUID cast, country codes, timestamps)
3. **Bulk insert** (COPY / batch)
4. **Validation** (row count + spot-check)

## 8) Risk & Önlem
- **Migration drift** → Preview/Prod’da `alembic current = head` zorunlu.
- **Partial SQL state** → Feature gate ile yalnızca SQL tamamlanan modüller açılır.
- **ID format uyuşmazlığı** → UUID normalize scripti (listing_id/user_id).

## 9) Sonraki Aksiyonlar (Local)
- Categories public endpoint SQL’e taşınacak (seed + /api/categories 200)
- Listings v1 SQL refactor backlog’a alınacak
- Favorites + Messages endpointleri SQL’e taşınacak
- Support messages endpointleri SQL’e taşınacak

