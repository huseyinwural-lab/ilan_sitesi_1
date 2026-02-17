# DEALER_TEST_USER_SEED

## Amaç
Dealer portal pozitif test için yalnızca **dev/test** ortamında dealer rolünde test kullanıcısı seed etmek.

## Seed edilen kullanıcı
- email: `dealer@platform.com`
- role: `dealer`
- password: `Dealer123!`
- country_code: `DE`
- country_scope: `["DE"]`
- is_active: `true`

## Guard
- Seed yalnızca `ENV != production` iken çalışır.

## Implementasyon
- Backend: `/app/backend/server.py` içinde `_ensure_dealer_user(db)`
- Lifespan sırasında çağrılır.
