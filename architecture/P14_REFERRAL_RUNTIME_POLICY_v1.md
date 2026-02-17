# P14 Referral Runtime Policy (v1)

**Kapsam:** Referral (Davet) Sisteminin Runtime Kuralları
**Tarih:** 14 Şubat 2026

## 1. Temel Kurallar (Core Rules)

### 1.1. Referral İlişkisi Kurma (Attribution)
*   **Zamanlama:** Sadece kullanıcı kaydı (`/auth/register`) sırasında yapılır. Sonradan ekleme yapılamaz (`referred_by` immutable).
*   **Self-Referral Yasak:** Kullanıcı kendi referral kodunu kullanamaz.
*   **Validasyon:** Geçersiz, pasif veya hatalı bir `referral_code` ile kayıt denemesi `400 Bad Request` döndürür (Silent ignore yapılmaz).

### 1.2. Ödül Dağıtımı (Reward Distribution)
*   **Tetikleyici:** `invoice.paid` webhook'u (Sadece **ilk** başarılı ödeme).
*   **Koşul:** Ödeme yapan kullanıcının `referred_by` alanı dolu olmalı ve daha önce bu ilişki için ödül (`referral_rewards`) verilmemiş olmalı.
*   **Ödül Tipi:** Referrer (Davet eden) kullanıcının Stripe Bakiyesine (`billing_customers.balance` -> Stripe Customer Balance) kredi eklenir.
*   **Tutar:** Sabit tutar (Örn: 100 TRY). İleride parametrik yapılabilir.

## 2. Abuse Kontrolü (Güvenlik)

### 2.1. Teknik Engeller
*   **Duplicate IP:** Aynı IP adresinden kısa sürede (örn: 1 saat) yapılan 5. kayıt şüpheli olarak işaretlenir (`users.is_flagged`).
*   **Stripe Customer ID:** Aynı kredi kartı/Stripe Customer ID ile farklı kullanıcılar üzerinden referral ödülü alınmaya çalışılırsa sistem reddeder (Stripe webhook içinde kontrol).

### 2.2. İade Politikası
*   **Chargeback/Refund:** MVP kapsamında, ödül verildikten sonra yapılan iadelerde ödül **geri alınmaz**. (Bu bir risk kararıdır, P15'te "pending period" eklenebilir).

## 3. Edge Cases & Handling

| Senaryo | Davranış |
| :--- | :--- |
| **Webhook Replay** | Idempotency sayesinde ikinci istekte ödül verilmez. |
| **Referrer Silinmiş** | Davet eden kullanıcı silinmişse (`is_active=False` veya `deleted`), ödül verilmez. |
| **Referrer Limiti** | Bir kullanıcı en fazla 50 kişiyi davet edebilir (Soft limit). |

## 4. Hata Kodları
*   `INVALID_REFERRAL_CODE`: Kod bulunamadı.
*   `SELF_REFERRAL`: Kendi kendine davet.
