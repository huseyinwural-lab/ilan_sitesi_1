# P14 Referral MVP (v1)

**Kapsam:** Davet Et & Kazan Sistemi
**Türü:** Growth Mechanism

## 1. İş Mantığı (Business Logic)
*   **Kurgu:** "Arkadaşını davet et, o ilk ödemesini yaptığında sen ödül kazan."
*   **Ödül (Reward):**
    *   **Davet Eden (Referrer):** Bir sonraki yenilemede veya faturada kullanılmak üzere kredi (Credit Balance) veya İndirim Kuponu. (MVP Kararı: **Stripe Customer Balance** eklemesi).
    *   **Davet Edilen (Referee):** İndirimli kayıt (Kupon sistemi üzerinden yönetilir veya otomatik indirim). MVP'de sadece Referrer ödüllendirilir.

## 2. Veritabanı Değişiklikleri

### `users` Tablosu Eklentileri
*   `referral_code`: String (Unique, 8-10 karakter). Kullanıcı oluşturulurken üretilir.
*   `referred_by`: UUID (FK -> users.id). Kayıt olurken kimin davet ettiği.

### `referral_rewards` Tablosu
*   `id`: UUID
*   `referrer_id`: UUID (Ödülü kazanan)
*   `referee_id`: UUID (Ödemeyi yapan)
*   `amount`: Decimal (Kazanılan tutar)
*   `status`: Enum (pending, applied, paid)
*   `created_at`: Datetime

## 3. Akışlar

### 3.1. Kod Üretimi
*   User create anında `referral_code` otomatik üretilir (Random String).

### 3.2. Kayıt (Attribution)
*   `/auth/register` endpoint'i `ref_code` parametresi alabilir.
*   Eğer kod geçerliyse ve kendi kodu değilse, `referred_by` alanına davet eden kullanıcının ID'si yazılır.

### 3.3. Ödül Dağıtımı (Reward Trigger)
*   **Tetikleyici:** `invoice.paid` webhook'u.
*   **Kontrol:** Ödeme yapan kullanıcının `referred_by` alanı dolu mu?
*   **Kural:** Sadece **İLK** ödemede ödül verilir (Referee'nin daha önce başarılı ödemesi yoksa).
*   **Aksiyon:**
    1.  Referrer kullanıcının `billing_customers.balance` (Stripe Balance) değerine ödül tutarı eklenir (Örn: 100 TRY).
    2.  `referral_rewards` tablosuna kayıt atılır.

## 4. Abuse Önlemleri
*   **Self-Referral:** `user.id != referred_by` kontrolü.
*   **Circular Referral:** A -> B -> A engellemesi (MVP'de opsiyonel, advanced fraud check P15).
*   **Duplicate IP:** Aynı IP'den kısa sürede çoklu kayıt (Rate limit + Flag).

## 5. Gate
Referral sistemi, kupon sistemi ile çakışmamalıdır (Hem kupon hem referral aynı anda kullanılabilir).
