# P14 Conversion Tracking Spec (v1)

**Kapsam:** Dönüşüm Hunisi (Conversion Funnel) Ölçümlemesi
**Tarih:** 14 Şubat 2026

## 1. Takip Edilecek Olaylar (Events)

| Event Adı | Tetikleyici | Veri Payload (Context) | KPI Etkisi |
| :--- | :--- | :--- | :--- |
| `plan_viewed` | Kullanıcı `/plans` veya `/admin/billing` sayfasına girdiğinde. | `user_id`, `current_plan` | Interest |
| `checkout_started` | Kullanıcı "Satın Al" veya "Upgrade" butonuna bastığında. | `user_id`, `target_plan`, `coupon_code` | Intent |
| `coupon_applied` | Kullanıcı başarılı bir kupon validation yaptığında. | `user_id`, `coupon_code`, `discount_amount` | Coupon Impact |
| `checkout_completed` | Stripe ödemesi başarılı olduğunda (Webhook). | `user_id`, `amount`, `plan`, `is_referral` | Revenue (MRR) |
| `subscription_activated` | Abonelik aktif hale geldiğinde. | `user_id`, `plan`, `term` | Activation |
| `quota_upsell_viewed` | Limit aşımı (403) sonrası upsell modalı görüntülendiğinde. | `user_id`, `resource` | Upsell Efficiency |

## 2. Teknik Uygulama

### 2.1. Backend Event Logging Standardı
Yüksek hacimli "View" eventleri için log tabanlı, finansal değeri olan "Transactional" eventler için veritabanı tabanlı takip uygulanacaktır.

**Tablo: `conversion_events`**
*   `id`: UUID
*   `event_name`: String (Index)
*   `user_id`: UUID (Index)
*   `properties`: JSON (Payload)
*   `created_at`: Datetime

### 2.2. Servis (`AnalyticsService`)
*   `track_event(name, user_id, properties)` fonksiyonu.
*   Bu servis `BillingService` ve `StripeService` içinden kritik anlarda çağrılır.

## 3. KPI Mapping
*   **Upgrade Conversion Rate:** `checkout_completed` / `plan_viewed`
*   **Coupon Conversion:** `coupon_applied` (with payment) / `coupon_applied` (total)
*   **Upsell Success:** `checkout_started` (source=upsell) / `quota_upsell_viewed`

## 4. Gate
Bu altyapı kurulmadan UI optimizasyonlarına başlanmayacaktır.
