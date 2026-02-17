# P15 Financial Audit Baseline (v1)

**Amaç:** Gelir bütünlüğünü korumak ve kaçağı önlemek.
**Sıklık:** Günlük (Otomatik/Manuel)

## 1. Stripe Reconciliation (Mutabakat)
Stripe Dashboard ile Internal DB (`invoices` tablosu) karşılaştırması.

### Kontrol Noktaları
1.  **Gross Volume:** Stripe "Payments" toplamı == `SUM(invoices.gross_total)` (Paid olanlar).
2.  **Discount Impact:** Stripe "Discounts" toplamı == `SUM(coupon_redemptions.discount_amount)`.
3.  **Refunds:** Stripe "Refunds" == `SUM(refunds.amount)`.

**Eylem:** Fark > 0.01 EUR ise "Financial Alert" tetiklenir.

## 2. Fraud & Abuse Monitoring

### A. Referral Abuse
*   **Kural:** Bir kullanıcı (Referrer) 24 saat içinde 5'ten fazla ödül (Credit) kazandıysa.
*   **Aksiyon:** Ödemeleri incele. Referee'ler farklı IP/Kart mı? Değilse hesabı dondur.

### B. Coupon Abuse
*   **Kural:** `max_redemptions` limitinin %105 üzerine çıkılması (Concurrency açığı).
*   **Aksiyon:** Kuponu acil `disable` et.

### C. Card Testing
*   **Kural:** Aynı IP'den 10+ başarısız ödeme denemesi.
*   **Aksiyon:** IP Ban.

## 3. Chargeback (Ters İbraz) Yönetimi
*   **Hedef:** Chargeback oranı < %0.5.
*   **Prosedür:** Stripe'dan chargeback bildirimi geldiğinde:
    1.  Kullanıcıyı `suspended` yap.
    2.  Referral ödülü verdiyse (manuel) iptal etmeyi değerlendir.
    3.  Kanıt sun (IP logları, hizmet kullanım dökümü).

## 4. Denetim Logları
Tüm finansal düzeltmeler (Manuel refund, Credit adjustment) `audit_logs` tablosunda `FINANCIAL_ADJUSTMENT` aksiyonu ile kayıt altına alınmak zorundadır.
