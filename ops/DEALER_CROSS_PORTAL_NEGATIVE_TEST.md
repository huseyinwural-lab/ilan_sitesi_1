# DEALER_CROSS_PORTAL_NEGATIVE_TEST

## Senaryo
Dealer ile /admin/* erişim denemesi.

## Beklenen
- 403 + redirect dealer home
- Backoffice chunk request = 0

## Sonuç
✅ PASS
- /admin/users denemesinde erişim engellendi ve /dealer'a redirect oldu.
- Backoffice chunk yüklenmedi.
