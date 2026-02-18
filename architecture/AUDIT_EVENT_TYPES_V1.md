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

### Dealer Domain
- `DEALER_STATUS_CHANGE`
- `DEALER_APPLICATION_APPROVED`
- `DEALER_APPLICATION_REJECTED`
- `INDIVIDUAL_APPLICATION_APPROVED`
- `INDIVIDUAL_APPLICATION_REJECTED`

### Listing Ops (Admin)
- `LISTING_SOFT_DELETE`
- `LISTING_FORCE_UNPUBLISH`

### Reports
- `REPORT_STATUS_CHANGE`
- `REPORT_CREATED`

### Finance Domain
- `INVOICE_STATUS_CHANGE`
- `TAX_RATE_CHANGE`
- `PLAN_CHANGE`
- `ADMIN_PLAN_ASSIGNMENT`

### System Domain
- `COUNTRY_CHANGE`
- `SYSTEM_SETTING_CHANGE`

### Master Data Domain
- `CATEGORY_CHANGE`
- `MENU_CHANGE`
- `ATTRIBUTE_CHANGE`
- `VEHICLE_MASTER_DATA_CHANGE`

---

## Alan Politikası
- `event_type`: Yukarıdaki taxonomy’den biri olmalıdır.
- `action`: UI geriye uyumluluğu için tutulabilir. Güvenlik event’lerinde `action == event_type` kullanımı uygundur.
