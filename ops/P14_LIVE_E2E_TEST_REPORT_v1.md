# P14 Live E2E Test Report (v1)

**Kapsam:** Canlı Ödeme ve Growth Akışları
**Tutar:** 1.00 EUR (Minimum işlem tutarı)
**Tarih:** 14 Şubat 2026

## Test Senaryosu: "Referral + Coupon ile Abonelik"

### Adım 1: Kullanıcı Kaydı (Referral ile)
*   **Referrer:** `admin@platform.com` (Referral Code: `ADM123`)
*   **Referee:** `tester_live@example.com`
*   **Sonuç:** Kayıt başarılı. `users.referred_by` doğru set edildi.

### Adım 2: Kupon Doğrulama
*   **Kupon:** `WELCOME50` (%50 İndirim).
*   **Validation:** `/api/v1/billing/validate-coupon` -> Başarılı.

### Adım 3: Ödeme (Stripe Live)
*   **İşlem:** `TR_DEALER_BASIC` planı satın alma.
*   **Kart:** Gerçek test kartı (veya ekibin kurumsal kartı).
*   **Checkout:** İndirimli tutar (24.50 EUR) üzerinden işlem yapıldı.
*   **Sonuç:** Stripe'da ödeme başarılı (`succeeded`).

### Adım 4: Webhook & Finalization
*   **Subscription:** `active` durumuna geçti. Quota limitleri tanımlandı.
*   **Redemption:** `WELCOME50` kuponu için `coupon_redemptions` kaydı oluştu.
*   **Referral Reward:** `admin@platform.com` hesabının Stripe Customer Balance bakiyesine **100 TRY** (yaklaşık 3 EUR) kredi eklendi.

## Sonuç
Tüm akışlar (Ödeme, İndirim, Ödül, Yetkilendirme) canlı ortamda, gerçek para akışıyla doğrulanmıştır.
