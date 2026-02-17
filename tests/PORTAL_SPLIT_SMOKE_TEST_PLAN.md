# PORTAL_SPLIT_SMOKE_TEST_PLAN

## Amaç
Portal split v1’in en kritik kabul kriterlerini smoke + negatif testlerle doğrulamak.

## Kanıt Standardı
- PASS iddiası için yalnız UI değil, **Network** kanıtı gerekir:
  - Wrong role’da ilgili portal chunk request **yok**.

## Test 1 — Individual ile /admin
1) Individual ile login ol.
2) `/admin` ve `/admin/users` dene.

Beklenen:
- 403 + redirect (login veya account home)
- **admin chunk request yok** (network)
- admin shell DOM mount yok

## Test 2 — Dealer ile /admin
Beklenen:
- 403 + redirect dealer home
- **admin chunk request yok**

## Test 3 — Admin ile /dealer
Beklenen:
- 403 + redirect admin home
- **dealer chunk request yok**

## Test 4 — Doğru rolde chunk yüklenir
- Admin ile `/admin`: backoffice chunk yüklenir; dealer chunk yüklenmez.
- Dealer ile `/dealer`: dealer chunk yüklenir; backoffice chunk yüklenmez.

## Test 5 — Login ekranları portal doğru mu?
- `/login` public/individual login
- `/dealer/login` dealer login
- `/admin/login` admin login

## Test 6 — Prod’da demo credentials render olmuyor
- Prod build’de login sayfalarında demo credentials DOM’da yok.

## Not
Bu repo’da şimdilik tek login `/auth/login` var. Portal split implementasyonunda login route’ları yeni namespace’e taşınmalıdır.
