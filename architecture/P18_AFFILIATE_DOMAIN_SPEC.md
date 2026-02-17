# P18 Affiliate Domain Spec (v1)

**Amaç:** Profesyonel iş ortakları (Influencer, Blogger) üzerinden gelen trafiği takip etmek ve ödüllendirmek.

## 1. Veri Modeli

### `affiliates` Tablosu
Affiliate programına katılan kullanıcıların profil detayları.
*   `id`: UUID (PK)
*   `user_id`: UUID (FK -> users.id, Unique)
*   `custom_slug`: String (Unique, Index) - Örn: "fenomen_ali"
*   `commission_rate`: Decimal (Default: 0.20 - %20)
*   `status`: Enum ('pending', 'approved', 'rejected', 'suspended')
*   `payout_method`: JSON (IBAN, Stripe Connect ID vb.)
*   `created_at`, `updated_at`

### `users` Tablosu Eklentileri
*   `is_affiliate`: Boolean (Hızlı kontrol için flag)
*   `referred_by_affiliate_id`: UUID (FK -> affiliates.id, Nullable) - Hangi affiliate getirdi?

### `affiliate_clicks` Tablosu (Analytics)
*   `id`: UUID
*   `affiliate_id`: UUID
*   `ip_hash`: String
*   `user_agent_hash`: String
*   `created_at`: Datetime

## 2. Kurallar

### 2.1. Attribution (İlişkilendirme)
*   Ziyaretçi `/ref/{slug}` linkine tıklar.
*   Sistem `affiliate_id` içeren 30 günlük bir Cookie (`aff_ref`) bırakır.
*   Kullanıcı kayıt olurken Cookie kontrol edilir. Varsa `users.referred_by_affiliate_id` set edilir.
*   **Çatışma:** Eğer kullanıcı hem bir arkadaş daveti (`referral_code`) hem de affiliate linki ile gelirse?
    *   **Karar:** `referral_code` (Arkadaş) önceliklidir. (Affiliate sistemi genellikle soğuk trafik içindir, arkadaş daveti daha sıcak ve değerlidir).

### 2.2. Komisyon (Commission)
*   Tetikleyici: `invoice.paid`.
*   Koşul: Ödeyen kullanıcının `referred_by_affiliate_id` alanı dolu olmalı.
*   Hesap: `Invoice Subtotal * Affiliate.commission_rate`.
*   Kayıt: `RewardLedger` tablosuna `CREDIT` olarak işlenir (Type: `AFFILIATE_COMMISSION`).

## 3. Durumlar (Status)
*   **Pending:** Başvuru yapıldı, admin onayı bekleniyor.
*   **Approved:** Link aktif, komisyon kazanabilir.
*   **Rejected:** Başvuru reddedildi.
*   **Suspended:** Abuse nedeniyle donduruldu.
