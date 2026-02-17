# P14 Promotion Admin Validation Rules (v1)

**Kapsam:** Backend API Validasyon Mantığı

## 1. Kampanya (Promotion) Kuralları
1.  **Tarih Tutarlılığı:** `start_at` < `end_at` olmak zorundadır. `start_at` geçmişte olabilir (hemen başlatma).
2.  **Değer Aralığı:**
    *   Eğer `type` = `percentage` ise: `value` 0 ile 100 arasında olmalıdır (0 < v <= 100).
    *   Eğer `type` = `fixed_amount` ise: `value` > 0 olmalıdır.
3.  **Para Birimi:** Fixed amount için `currency` zorunludur ve desteklenenler listesinde (EUR, TRY, USD, CHF) olmalıdır.
4.  **Değişmezlik:** Kampanya oluşturulduktan sonra `type` ve `currency` değiştirilemez (Veri tutarlılığı için).

## 2. Kupon (Coupon) Kuralları
1.  **Format:** Kupon kodu sadece A-Z, 0-9 ve Tire (-) içerebilir. Boşluk olamaz. Otomatik uppercase'e çevrilir.
2.  **Unique:** Kupon kodu sistem genelinde (veya en azından aktif kuponlar arasında) unique olmalıdır.
3.  **Limitler:**
    *   `usage_limit` (varsa) > 0 olmalıdır.
    *   `per_user_limit` >= 1 olmalıdır.

## 3. Durum Yayılımı (State Propagation)
*   **Kural:** Bir Promotion `is_active=False` yapıldığında veya süresi dolduğunda (`end_at` < NOW), ona bağlı kuponlar Runtime'da geçersiz sayılır. Veritabanında kuponların tek tek update edilmesine gerek yoktur; sorgularda `JOIN` ile promotion durumu kontrol edilir.

## 4. Hata Yönetimi
*   Validasyon başarısız olursa `400 Bad Request` ve açıklayıcı mesaj (`detail`) dönülür.
*   Çakışma (Duplicate Code) durumunda `409 Conflict` dönülür.
