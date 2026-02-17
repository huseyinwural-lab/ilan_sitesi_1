# P16 Webhook Idempotency Rules (v1)

**Amaç:** Stripe'ın "at-least-once" delivery garantisi nedeniyle oluşabilecek mükerrer işlemleri engellemek.

## 1. Event ID Kontrolü
*   Her gelen webhook isteğinin `id` alanı (`evt_...`) `stripe_events` tablosunda sorgulanır.
*   Eğer kayıt varsa -> İşlem yapılmaz, `200 OK` dönülür.
*   Kayıt yoksa -> İşlem başlatılır ve transaction sonunda event kaydedilir.

## 2. Mantıksal Idempotency (Business Logic Guard)
Event ID kontrolü bir şekilde aşılsa bile (örn: farklı event ID ama aynı charge için ikinci refund), iş mantığı seviyesinde koruma sağlanır:

*   **Revocation Guard:** Bir ödül zaten `revoked` statüsündeyse, tekrar revoke edilmeye çalışılmaz.
*   **Ledger Guard:** `reward_ledger` tablosuna kayıt atarken `reward_id` ve `reason` (örn: `refund_evt_123`) kombinasyonu kontrol edilir veya ödülün mevcut statüsü baz alınır.

## 3. Transaction Atomicity
Tüm işlemler (Statü güncellemesi + Ledger kaydı + Event logu) **tek bir veritabanı transaction'ı** içinde yapılır.
*   Hata durumunda hepsi rollback olur.
*   Başarı durumunda hepsi commit olur.
