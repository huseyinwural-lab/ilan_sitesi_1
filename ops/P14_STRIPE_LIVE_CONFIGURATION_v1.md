# P14 Stripe Live Configuration (v1)

**Tarih:** 14 Şubat 2026
**Durum:** TAMAMLANDI
**Ortam:** PRODUCTION

## 1. Anahtar Değişimi
Platform "Test Mode"dan "Live Mode"a geçirildi.

*   `STRIPE_SECRET_KEY`: Canlı (sk_live_...) anahtarı ile güncellendi.
*   `STRIPE_PUBLISHABLE_KEY`: Canlı (pk_live_...) anahtarı frontend env dosyasına eklendi.
*   `STRIPE_WEBHOOK_SECRET`: Production webhook secret (whsec_...) backend'e tanımlandı.

## 2. Webhook Konfigürasyonu
Stripe Dashboard üzerinden `https://api.platform.com/api/v1/payment/webhook` endpoint'i tanımlandı.

**Aktif Eventler:**
*   `checkout.session.completed`: Abonelik başlatma ve tek seferlik ödemeler.
*   `invoice.paid`: Yinelenen abonelik ödemeleri (Referral Reward tetikleyicisi).
*   `customer.subscription.updated`: Plan değişiklikleri ve iptaller.
*   `customer.subscription.deleted`: İptal kesinleşmesi.

## 3. Doğrulama (Verification)
*   **Signature Check:** `stripe.Webhook.construct_event` fonksiyonu canlı secret ile test edildi. Geçersiz imzalar 400 ile reddedildi.
*   **Delivery:** Test amaçlı gönderilen "ping" eventi 200 OK yanıtı aldı.
