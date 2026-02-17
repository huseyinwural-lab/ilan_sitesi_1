# IMPLEMENT_MODERATION_AUDIT_LOGGING

## Amaç
Moderation aksiyonlarının tamamı için zorunlu audit logging (v1.0.0 P0 release blocker).

## Koleksiyon
- `audit_logs` (MongoDB)

## Log Alanları (minimum)
- `id`
- `event_type` (approve / reject / needs_revision)
- `listing_id`
- `admin_user_id`
- `role` (moderator / country_admin / super_admin)
- `country_code`
- `country_scope` (kullanıcının country_scope listesi veya ["*"])
- `reason` (reject/needs_revision için zorunlu)
- `reason_note` (`other` için zorunlu)
- `previous_status`
- `new_status`
- `created_at` (ISO)

## Transaction Kuralı
- Listing status update + audit log insert **aynı transaction** içinde yapılmalıdır.
- Kabul edilemez durum: “state change oldu ama audit yok”.

## Kabul Kriteri
- Her state change için **tek satır** log oluşur
- Audit log alanları dolu ve tutarlı (prev→new)
