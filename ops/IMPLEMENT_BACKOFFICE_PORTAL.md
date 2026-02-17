# IMPLEMENT_BACKOFFICE_PORTAL

## Amaç
Backoffice portalını admin shell izolasyonu ile ayrıştırmak.

## Yapılacaklar (code)
1) `src/portals/backoffice/BackofficePortalApp.jsx`
- Admin layout + admin routes burada.

2) Admin login
- `/admin/login` route’u yalnız backoffice portal chunk içinde olmalı.

3) RBAC pre-check
- PortalGate backoffice eligibility kontrol eder.

4) Demo credentials
- UI’da demo credentials sadece demo env’de gösterilecek.

## Kabul
- Individual/Dealer kullanıcıları admin shell’i göremez.
- Wrong role’da admin chunk request yok.
