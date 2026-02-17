# AUDIT_EVENT_TYPES_V1

## Amaç
Bu doküman **v1.0.0 / FAZ-FINAL-02 (P1)** kapsamında audit `event_type` isimlendirmesini **tek kaynak sözleşme** olarak standardize eder.

> Not: Bu liste P1 sonunda sabitlenir. Yeni event tipleri v1.1 backlog’una alınır.

---

## Event Taxonomy (v1)

### Moderation
- `MODERATION_APPROVE`
- `MODERATION_REJECT`
- `MODERATION_NEEDS_REVISION`

### Auth / Security
- `FAILED_LOGIN`
- `RATE_LIMIT_BLOCK`

### Admin / Authorization
- `ADMIN_ROLE_CHANGE`
- `UNAUTHORIZED_ROLE_CHANGE_ATTEMPT`

---

## Alan Politikası
- `event_type`: Yukarıdaki taxonomy’den biri olmalıdır.
- `action`: UI geriye uyumluluğu için tutulabilir. Güvenlik event’lerinde `action == event_type` kullanımı uygundur.
