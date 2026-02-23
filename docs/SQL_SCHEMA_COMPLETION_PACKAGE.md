# SQL_SCHEMA_COMPLETION_PACKAGE

**Son güncelleme:** 2026-02-23 23:44:57 UTC

## Önerilen Yeni Tablolar
### system_settings
- columns: id(UUID PK), key(varchar), value(JSONB), country_code(varchar), is_readonly(bool), description(varchar), created_at, updated_at
- index: (key, country_code) unique

### admin_invites
- columns: id(UUID PK), token_hash(varchar unique), user_id(UUID FK users), email(varchar), role(varchar), country_scope(JSON), expires_at, created_at, created_by, used_at
- index: token_hash, user_id, email+used_at

### reports (opsiyonel)
- Eğer support_messages yeterli değilse: reports tablosu (listing_id, reason, status, handled_by, created_at)

## FK/Index Kararları
- admin_invites.user_id → users.id (ondelete=CASCADE)
- system_settings.country_code → countries.code (opsiyonel FK)
