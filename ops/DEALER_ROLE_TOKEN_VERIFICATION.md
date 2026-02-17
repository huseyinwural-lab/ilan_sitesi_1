# DEALER_ROLE_TOKEN_VERIFICATION

## Amaç
Dealer rolü için token claim doğrulaması.

## Test Kullanıcısı
- dealer@platform.com / Dealer123!

## Doğrulama
- Login response `user.role` = `dealer`
- Access token JWT payload içinde `role` claim = `dealer`

## Kanıt (çıktı özeti)
- jwt_payload: {"email":"dealer@platform.com", "role":"dealer", ...}

## Kabul
✅ PASS — token içinde `role=dealer` doğru set ediliyor.
