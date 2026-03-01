# Moderation Parity Report (Mongo → SQL)

**Tarih:** 2026-02-24 12:55:00 UTC
**Ortam URL:** https://ad-posting-flow.preview.emergentagent.com

## Scope
- SQL moderation state machine parity (pending_moderation → approved/rejected)
- Admin approve/reject akışları

## Test Verileri
- Listing A: `7eea560e-a9db-4aff-b96f-a68ed4bf279c`
- Listing B: `b284385b-46a6-40ff-bacc-a6f07334f711`

## Geçiş Kanıtı
| Listing | Başlangıç | Aksiyon | Son Durum |
|---|---|---|---|
| A | pending_moderation | admin approve | published |
| B | pending_moderation | admin reject | rejected |

## DB Doğrulaması
- Listing A status: `published`
- Listing B status: `rejected`

## Sonuç
- SQL moderation state machine, eski akış ile **parite** sağladı (approve/reject geçişleri).
