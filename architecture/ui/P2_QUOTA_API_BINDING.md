# P2 Quota API Binding

## Amaç
Dashboard CTA için gerçek quota limit/remaining bilgisini bağlamak.

## Karar Noktaları
- Quota bilgisi consumer için nereden alınacak?
- Plan bazlı limit mi, global limit mi?

## Önerilen API
- `GET /api/v1/users/me/quota`
  - `{ limit, used, remaining }`

## Notlar
- API yoksa: `0` + “Veri hazırlanıyor” state.
- CTA disable kuralı: `remaining <= 0`.
