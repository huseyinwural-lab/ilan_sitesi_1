# SQL_SCHEMA_COMPLETION_PACKAGE

**Son güncelleme:** 2026-02-24 00:25:06 UTC

## Önerilen Yeni Tablolar
### system_settings
- columns: id(UUID PK), key(varchar), value(JSONB), country_code(varchar), is_readonly(bool), description(varchar), created_at, updated_at
- index: (key, country_code) unique

### admin_invites
- columns: id(UUID PK), token_hash(varchar unique), user_id(UUID FK users), email(varchar), role(varchar), country_scope(JSON), expires_at, created_at, created_by, used_at
- index: token_hash, user_id, email+used_at

### menu_items
- columns: id(UUID PK), label(varchar), slug(varchar), url(varchar), parent_id(UUID), country_code(varchar), active_flag(bool), sort_order(int), created_at, updated_at, deleted_at
- index: slug + country_code unique

### reports
- columns: id(UUID PK), listing_id(UUID FK listings), reporter_user_id(UUID FK users), reason(varchar), reason_note(text), status(varchar), handled_by_admin_id(UUID), status_note(text), created_at, updated_at
- index: status + created_at

## FK/Index Kararları
- admin_invites.user_id → users.id (ondelete=CASCADE)
- reports.listing_id → listings.id (ondelete=CASCADE)
- reports.reporter_user_id → users.id (ondelete=SET NULL)