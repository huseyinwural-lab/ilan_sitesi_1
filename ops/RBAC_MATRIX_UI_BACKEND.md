# RBAC_MATRIX_UI_BACKEND

Bu doküman mevcut repo baz alınarak UI + backend erişim matrisini çıkarır.

> Not: Backend’in büyük kısmı /app/backend/app/routers altında olsa da, bu repo’da admin UI’nın çağırdığı core endpoint’ler server.py’da.

## Roller
- super_admin
- country_admin
- moderator
- finance_admin *(repo’da finance rolü var; isim standardı gap)*
- support_admin *(repo’da support rolü var; isim standardı gap)*
- dealer
- individual

## UI Erişim (frontend ProtectedRoute)
### Admin
- `/admin` roles: `super_admin, country_admin, moderator, support, finance`
- `/admin/users` roles: `super_admin, country_admin`
- `/admin/feature-flags` roles: `super_admin, country_admin`
- `/admin/countries` roles: `super_admin, country_admin`
- `/admin/categories` roles: `super_admin, country_admin`
- `/admin/attributes` roles: `super_admin, country_admin` *(dosyada bazı yerler super_admin-only olabilir; kontrol gerekir)*
- `/admin/master-data/vehicles` roles: `super_admin, country_admin`
- `/admin/billing` roles: `super_admin, country_admin, dealer` *(dealer burada muhtemelen yanlış scope; gap)*
- `/admin/plans` roles: `super_admin, country_admin, dealer, individual` *(muhtemelen yanlış scope; gap)*

### User Panel
- `/account/*` şu an ProtectedRoute yok (gap)

### Dealer Panel
- Dedicated dealer panel route yok (gap)

## Backend Erişim (server.py)
- `/api/users` : `check_permissions(['super_admin','country_admin'])`
- `/api/countries` PATCH: `check_permissions(['super_admin','country_admin'])`
- `/api/v1/admin/vehicle-master/*` : `check_permissions(['super_admin','country_admin'])`
- `/api/dashboard/stats` : login olan herkes (get_current_user)

## Country Scope Enforcement (v2)
- `/api/users?country=XX` ve `/api/dashboard/stats?country=XX` enforce
- Invalid country => 400
- Scope forbidden => 403

## Moderation (RBAC notları)
- moderator rolü:
  - Hangi queue’lara erişir? (INDIVIDUAL / DEALER ayrımı şu an yok → GAP)
  - Eğer dealer queue ayrı olacaksa “senior moderator” gibi ayrı bir rol ihtiyacı doğabilir → GAP

## Kritik Gap’ler (Özet)
- finance_admin/support_admin/moderator ayrımları UI menüde var ama backend endpoint kapsamı net değil.
- /account (user panel) auth guard eksik. (FIXED)
- dealer/individual rollerinin admin finance sayfalarına erişimi şüpheli.
- Moderation: audit + reason enum + queue ayrımı eksik.
