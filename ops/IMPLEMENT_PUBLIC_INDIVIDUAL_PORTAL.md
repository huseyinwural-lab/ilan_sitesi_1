# IMPLEMENT_PUBLIC_INDIVIDUAL_PORTAL

## Amaç
Public + Individual alanlarını aynı bundle’da tutarak MVP portal split.

## Yapılacaklar (code)
- Public route’lar (/, /search, /ilan/:id) main bundle’da.
- Individual account ( /account/* ) ProtectedRoute + role check.
- Individual kullanıcı admin/dealer path’e giderse:
  - 403 + /account home’a redirect

## Kabul
- Individual kullanıcı admin/dealer shell render etmez.
