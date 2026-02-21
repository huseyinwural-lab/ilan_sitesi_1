# BILLING_AUDIT_STANDARD_V1

## Tek Kaynak Tablo
- **Tablo:** `audit_logs`
- **Kaynak:** SQL (Mongo yok)

## Billing Event Seti (action)
- `payment_succeeded`
- `invoice_marked_paid`
- `subscription_activated`
- `quota_limits_updated`

## Zorunlu Kolonlar
- `id` (UUID)
- `created_at` (timestamp)
- `action` (event_type)
- `resource_type`
- `resource_id`
- `user_id` (dealer/user)
- `user_email`
- `country_scope`
- `metadata_info` (JSON)

## Scope Filter (API)
- `/api/admin/audit-logs?scope=billing`
- `ref` paramı `resource_id` veya metadata içindeki `invoice_id/subscription_id/payment_id` ile eşleşir.

## RBAC
- **Sadece:** `super_admin`, `finance`
- `audit_viewer` V2
