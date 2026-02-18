## P1 Billing Payments Spec

### Veri Kaynağı
- Ödeme sağlayıcı webhook kayıtları (örn. Stripe) + manual override

### Payment Record Alanları
- id
- invoice_id
- dealer_user_id
- provider (stripe/paypal/other)
- provider_payment_id
- amount
- currency
- status (pending/paid/failed/refunded)
- paid_at
- created_at
- metadata (JSON)

### Admin UI Planı
- Ödeme listesi (status, provider, date, dealer)
- Detay ekranı + invoice bağlantısı
- Read-only v1
