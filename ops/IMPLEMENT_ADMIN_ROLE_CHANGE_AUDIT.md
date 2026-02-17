# IMPLEMENT_ADMIN_ROLE_CHANGE_AUDIT

## Amaç
Admin panelinden yapılan kullanıcı rol değişikliklerini audit’lemek ve değişimi audit ile atomik garantide tutmak.

## Endpoint
- `PATCH /api/users/{user_id}` (body: `{ role: "..." }`)

## Event
- `event_type`: `ADMIN_ROLE_CHANGE`

## Log Alanları (minimum)
- `id`
- `event_type`: `ADMIN_ROLE_CHANGE`
- `action`: `ADMIN_ROLE_CHANGE`
- `target_user_id`
- `changed_by_admin_id`
- `previous_role`
- `new_role`
- `country_scope` (admin’in scope’u)
- `created_at` (ISO)

## Transaction / Atomiklik Kuralı
- Zorunlu garanti: **“Audit yoksa role change yok.”**
- Mongo tek-node ortamında multi-doc transaction desteklenmeyebilir.
- Bu yüzden uygulanacak strateji:
  1) Audit kaydı **önce** `applied=false` ile yazılır.
  2) User role update yapılır.
  3) Audit kaydı `applied=true` ile işaretlenir.

Bu strateji, audit insert başarısızsa role update’in hiç yapılmamasını garanti eder.

## Kabul Kriteri
- Admin panelden rol değiştirildiğinde 1 adet `ADMIN_ROLE_CHANGE` oluşur.
- previous/new role doğru yazılır.
- Audit yazılamazsa role değişimi commit edilmez.
