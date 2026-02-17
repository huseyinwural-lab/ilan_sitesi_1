# P18 Referral Tier Domain Spec (v1)

**Amaç:** Kullanıcıları davet sayılarına göre segmente ayırarak (Tier) farklı ödül ve ayrıcalıklar sunmak.

## 1. Tier Yapısı (Örnek Konfigürasyon)

| Tier Adı | Min. Referral (Confirmed) | Ödül Tutarı | Badge | Ayrıcalıklar |
| :--- | :--- | :--- | :--- | :--- |
| **Standard** | 0 | 100 TRY | - | Standart Destek |
| **Gold** | 5 | 150 TRY | 🥇 Leader | Öncelikli Destek |
| **Platinum** | 20 | 200 TRY | 💎 VIP | VIP Destek + Özel Kampanya |

## 2. Veritabanı Modeli

### `referral_tiers` Tablosu
*   `id`: UUID (PK)
*   `name`: String (Unique) - Örn: "Gold"
*   `min_count`: Integer (Eşik değeri) - Örn: 5
*   `reward_amount`: Decimal - Örn: 150.00
*   `currency`: String - Örn: "TRY"
*   `badge_url`: String (Opsiyonel)
*   `is_active`: Boolean

### `users` Tablosu Eklentileri
*   `referral_tier_id`: UUID (FK -> referral_tiers.id) - Mevcut seviye.
*   `referral_count_confirmed`: Integer - Toplam onaylanmış davet sayısı (Cache/Denormalized).

## 3. Geçiş Kuralları (Transition Rules)

### 3.1. Upgrade (Yükselme)
*   **Tetikleyici:** `referral_reward` statüsü `confirmed` olduğunda.
*   **İşlem:**
    1.  `user.referral_count_confirmed` artırılır.
    2.  `referral_tiers` tablosundan `min_count <= user.referral_count` olan en yüksek tier bulunur.
    3.  Eğer bulunan tier, mevcut tier'dan yüksekse -> Upgrade.
    4.  `TierUpgradeEvent` loglanır.

### 3.2. Downgrade (Düşme)
*   **Kural:** P18 kapsamında **Downgrade YOKTUR**.
*   **Gerekçe:** Kazanılmış hak korunur. Kullanıcı 20 referansı varken 1 tanesi refund olsa bile Platinum kalır (Motivasyon kaybını önlemek için).
*   **İstisna:** Abuse tespit edilirse manuel olarak "Standard" seviyesine çekilebilir.

## 4. Ödül Hesaplama
*   `calculate_reward(user_id)` fonksiyonu:
    *   Kullanıcının `referral_tier_id`'sine bakar.
    *   O tier'ın `reward_amount` değerini döndürür.
    *   Sabit değer (hardcoded) yerine DB'den dinamik okunur.
