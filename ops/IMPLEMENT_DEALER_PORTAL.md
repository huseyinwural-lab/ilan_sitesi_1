# IMPLEMENT_DEALER_PORTAL

## Amaç
Dealer portalını ayrı chunk ile izolasyon.

## Yapılacaklar (code)
1) `src/portals/dealer/DealerPortalApp.jsx`
- Dealer layout + dealer routes burada.

2) Dealer login
- `/dealer/login` route’u yalnız dealer portal chunk içinde olmalı.

3) Pre-layout guard
- Dealer eligibility kontrolü.

4) Wrong path davranışı
- Dealer kullanıcı /admin/* denerse: 403 + dealer home’a redirect

## Kabul
- Wrong role’da admin chunk request yok.
- Dealer chunk sadece dealer portalda yüklenir.
