# P14 Coupon Webhook Security Review (v1)

**Kapsam:** Stripe Webhook Güvenliği ve Idempotency
**Durum:** DOĞRULANDI

## 1. Güvenlik Katmanı
*   **İmza Doğrulama:** `stripe.Webhook.construct_event` kullanılıyor. Yanlış imzalı istekler `400 Bad Request` ile reddediliyor.
*   **Secret Management:** `STRIPE_WEBHOOK_SECRET` environment variable üzerinden alınıyor.

## 2. Idempotency (Tekrarlanan İstek Koruması)
*   **Mekanizma:** `StripeEvent` tablosunda `event_id` unique constraint (`ix_stripe_events_event_id`).
*   **Akış:**
    1.  Webhook gelir.
    2.  Event ID loglanır.
    3.  Eğer ID zaten varsa, transaction `IntegrityError` verir.
    4.  Hata yakalanır ve `200 OK` dönülür ("already_processed").
    5.  İş mantığı (Redemption) çalıştırılmaz.

## 3. Replay Attack Testi
*   **Senaryo:** Aynı payload ve signature ile ikinci istek.
*   **Sonuç:** Sistem isteği "duplicate" olarak algıladı ve işlem yapmadan başarılı yanıt döndü.
*   **Double Redemption:** Oluşmadı. `coupon_redemptions` tablosunda mükerrer kayıt yok.

## 4. Limit Yarışı (Race Condition)
*   **Senaryo:** Limit dolmak üzereyken gelen webhooklar.
*   **Koruma:** `record_redemption` içinde `WITH FOR UPDATE` ile kupon satırı kilitleniyor. `usage_count` artırımı atomik.
