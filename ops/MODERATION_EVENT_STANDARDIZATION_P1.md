# MODERATION_EVENT_STANDARDIZATION_P1

## Amaç
Moderation audit event isimlerini `AUDIT_EVENT_TYPES_V1` taxonomy ile tutarlı hale getirmek.

## Eski → Yeni
- approve → `MODERATION_APPROVE`
- reject → `MODERATION_REJECT`
- needs_revision → `MODERATION_NEEDS_REVISION`

## UI Uyumluluğu
- `action` alanı UI için: `APPROVE`, `REJECT`, `NEEDS_REVISION`.
- `event_type` alanı standard taxonomy’den.
