# P14 Coupon Runtime Policy (v1)

**Kapsam:** Kupon Kullanım ve Doğrulama Kuralları
**Tarih:** 14 Şubat 2026

## 1. Temel Kurallar (Rules)

### 1.1. Geçerlilik Kontrolü
Bir kuponun kullanılabilmesi için (`validate_coupon`):
1.  **Promotion Aktif Olmalı:** Bağlı olduğu kampanya `is_active=True` olmalıdır.
2.  **Coupon Aktif Olmalı:** Kupon `is_active=True` olmalıdır.
3.  **Tarih Aralığı:** Şu anki zaman (`NOW`), kampanyanın `start_at` ve `end_at` (varsa) aralığında olmalıdır.
4.  **Kampanya Global Limiti:** `promotions.max_redemptions` doluysa (redemption count >= max) kupon kullanılamaz.
5.  **Kupon Özel Limiti:** `coupons.usage_limit` doluysa (usage_count >= limit) kupon kullanılamaz.

### 1.2. Kullanıcı Kısıtlamaları
1.  **User Başına Limit:** `coupons.per_user_limit` (Varsayılan: 1) kontrol edilir. Kullanıcı bu kuponu daha önce kullandıysa reddedilir.
2.  **Stacking Yasak:** Aynı ödeme işleminde (Checkout Session) sadece **1 adet** kupon kullanılabilir.

### 1.3. Plan Uyumluluğu
*   Varsayım: Şu aşamada kuponlar tüm abonelik planlarında (Dealer Basic/Pro/Ent) geçerlidir. İleride `allowed_plans` eklenebilir.

## 2. Redemption (Kullanım) Akışı

### 2.1. Validation (Ödeme Öncesi)
*   Sadece uygunluk kontrolü yapılır.
*   Redemption kaydı oluşturulmaz.
*   Stripe Checkout Session'a indirim uygulanır.

### 2.2. Finalization (Ödeme Sonrası)
*   Kullanım, **sadece** başarılı ödeme (`invoice.paid` veya `checkout.session.completed`) sonrası kesinleşir.
*   **Concurrency:** Webhook işlenirken `usage_count` artırımı transaction içinde ve row-lock ile yapılmalıdır.

## 3. Edge Cases & Handling

| Senaryo | Davranış |
| :--- | :--- |
| **Checkout Cancel** | Redemption oluşmaz. Kupon hakkı yanmaz. |
| **Webhook Replay** | `stripe_event_id` ve `unique(user_id, coupon_id)` sayesinde çift kullanım (double spend) engellenir. |
| **Limit Yarışı** | Son 1 stok kaldı, 2 kişi aynı anda checkout yaptı. -> Stripe'da ödeme başarılı olsa bile, webhook sırasında limit dolduysa redemption "failed" işaretlenir (veya kullanıcıya manuel iade yapılır). Ancak MVP'de Stripe tarafında limit kontrolü yapmadığımız için (internal DB check), nadir de olsa limit aşımı (over-issue) olabilir. Bu risk kabul edilmiştir (Soft limit). |
| **Süresi Dolan Kod** | Kullanıcı checkout ekranında beklerken süre dolarsa, ödeme anında Stripe "expired coupon" hatası verebilir (Eğer Stripe Coupon objesi de expire olduysa). Bizim sistemde ise webhook geldiğinde tarih geçmiş olsa bile, "ödeme anı" (created_at) referans alınmalıdır. |

## 4. Hata Kodları
*   `COUPON_NOT_FOUND`: Geçersiz kod.
*   `COUPON_EXPIRED`: Süresi dolmuş.
*   `COUPON_LIMIT_REACHED`: Stok bitmiş.
*   `COUPON_ALREADY_USED`: Kullanıcı limitini doldurmuş.
