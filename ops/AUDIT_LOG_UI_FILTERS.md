# AUDIT_LOG_UI_FILTERS

## Amaç
Backoffice `/admin/audit-logs` ekranında P1 güvenlik ve yetki event’lerinin görünürlüğünü artırmak.

## Filtreler (P1)
- `event_type`
- `country` (log.country_code üzerinden)
- `date range` (created_at)
- `admin_user` (user_email / admin_user_id)

## Kabul Kriteri
- `FAILED_LOGIN` event’leri filtrelenebilir.
- `ADMIN_ROLE_CHANGE` event’leri filtrelenebilir.
