# FAILED_LOGIN_RATE_LIMIT_INTEGRATION

## Amaç
Brute-force giriş denemelerini azaltmak için failed login bazlı rate-limit uygulamak ve blok başlangıcını audit’lemek.

## Politika (P1 kararı)
- Sliding window: **10 dakika**
- Threshold: **3 başarısız deneme**
- Blok: **4. denemede** tetiklenir
- Blok süresi: **15 dakika**

## Davranış
- Blok başladığında:
  - HTTP **429**
  - `event_type=RATE_LIMIT_BLOCK` audit kaydı yazılır
  - Blok süresince aynı key için tekrar tekrar `RATE_LIMIT_BLOCK` yazılmaz (tek kayıt).

## Log Alanları (minimum)
- `id`
- `event_type`: `RATE_LIMIT_BLOCK`
- `action`: `RATE_LIMIT_BLOCK`
- `email` (varsa)
- `ip_address`
- `user_agent`
- `created_at` (ISO)

## Kabul Kriteri
- 3 başarısız login → 3 `FAILED_LOGIN`
- 4. deneme → 429 + **1** `RATE_LIMIT_BLOCK` (blok başlangıcında)
