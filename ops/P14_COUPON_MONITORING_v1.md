# P14 Promotion Monitoring Policy (v1)

**Kapsam:** Kupon ve Kampanya Sisteminin Sağlığı
**Tarih:** 14 Şubat 2026

## 1. Business Metrics (İş Metrikleri)

### `coupon_validate_attempt_total`
*   **Tanım:** Kullanıcıların kupon kodu deneme sayısı.
*   **Kaynak:** `POST /api/v1/billing/checkout` (Validation phase).
*   **Önemi:** Kampanya ilgisini gösterir.

### `coupon_redeem_success_total`
*   **Tanım:** Başarılı şekilde kullanılan kupon sayısı.
*   **Kaynak:** Webhook (DB `coupon_redemptions` tablosu).
*   **Önemi:** Gerçekleşen dönüşüm.

### `coupon_revenue_impact_total`
*   **Tanım:** Kuponlar sayesinde verilen toplam indirim tutarı.
*   **Hesaplama:** `SUM(coupon_redemptions.discount_amount)`.
*   **Önemi:** Maliyet analizi.

### `coupon_conversion_rate`
*   **Tanım:** Validation / Redemption oranı.
*   **Hesaplama:** `redeem_success_total / validate_attempt_total`.

## 2. Operational Metrics (Operasyonel Metrikler)

### `coupon_validate_fail_total`
*   **Tanım:** Hatalı kod, süresi geçmiş kod veya limit aşımı nedeniyle reddedilen denemeler.
*   **Kırılım:** `reason` etiketi ile (invalid, expired, limit).
*   **Alert:** Dakikada > 50 fail (Brute force atağı).

### `coupon_redeem_conflict_total`
*   **Tanım:** Webhook sırasında limit veya kullanıcı çakışması.
*   **Alert:** > 0 (Sistemde mantıksal hata var).

### `coupon_webhook_error_total`
*   **Tanım:** Webhook işlerken alınan hatalar.
*   **Alert:** > 0 (Kritik).

## 3. Alarm Kuralları (Alerting Rules)

| Metrik | Eşik (Threshold) | Sev | Aksiyon |
| :--- | :--- | :--- | :--- |
| `webhook_error` | > 0 | P0 | Logları incele, Stripe retry takibi. |
| `validate_fail` | > 50/dk | P1 | IP block, Rate limit kontrolü. |
| `max_redemption` | 1 saatte limitin %80'i | P2 | Admin bilgilendirme (Stok bitiyor). |
