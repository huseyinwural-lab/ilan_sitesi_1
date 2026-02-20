# RDBMS Schema P0 (Auth + Applications)

## Hedef
Auth + Applications için Mongo bağımlılığını kaldıracak minimum Postgres şeması.

## Tablolar

### users (mevcut)
> Mevcut SQL `users` tablosu yeniden kullanılacak.

Örnek alanlar:
- id (UUID, PK)
- email (unique)
- full_name
- role (string)
- is_active, is_verified
- country_code, country_scope
- created_at, updated_at, last_login

### user_credentials (yeni)
- id (UUID, PK)
- user_id (FK → users.id)
- provider (password | google | apple | …)
- password_hash (nullable; password provider için)
- created_at

Indexes:
- user_id
- (provider, user_id)

### roles (yeni)
- id (UUID, PK)
- name (unique, e.g. super_admin, support, moderator)
- created_at

### user_roles (yeni)
- id (UUID, PK)
- user_id (FK → users.id)
- role_id (FK → roles.id)
- created_at

Index:
- (user_id, role_id)

### refresh_tokens (yeni)
- id (UUID, PK)
- user_id (FK → users.id)
- token_hash (unique)
- expires_at
- revoked_at (nullable)
- created_at

Indexes:
- token_hash
- user_id

### applications (mevcut P20)
- id (UUID, PK)
- user_id (FK → users.id, nullable?)
- application_type (individual|dealer)
- category (complaint|request)
- subject, description
- attachments (JSON / ayrı tablo opsiyonel)
- status (pending|in_review|approved|rejected|closed)
- priority (low|medium|high)
- assigned_to (FK → users.id)
- decision_reason (nullable)
- created_at, updated_at

Index:
- application_type
- status
- user_id

## Notlar
- Session invalidate cutover kabul: refresh_tokens tablosu sıfırlanabilir.
- `attachments` için P0’da JSON/array string yeterli; P1’de normalize edilebilir.
