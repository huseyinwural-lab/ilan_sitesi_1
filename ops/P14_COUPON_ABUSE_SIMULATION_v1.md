# P14 Coupon Abuse Simulation (v1)

**Test Ortamı:** Localhost + SQLite/Postgres (Async)
**Simülasyon:** Concurrency ve Race Condition

## 1. Paralel Checkout (Aynı Kullanıcı)
*   **Senaryo:** Kullanıcı aynı anda iki farklı sekmeden "Tek Kullanımlık" kupon ile checkout başlattı.
*   **Validation:** Her iki istek de validasyondan geçebilir (Redemption henüz oluşmadı).
*   **Finalization:** İlk ödeme tamamlandığında webhook redemption yazar. İkinci ödeme webhook'u geldiğinde `record_redemption` fonksiyonu kullanıcının daha önce kullandığını tespit eder mi?
    *   **Mevcut Durum:** `ix_coupon_redemptions_user_coupon` unique constraint var. İkinci işlem DB seviyesinde hata alır.
    *   **Sonuç:** Kullanıcı indirimli ödeme yapsa bile sistem kaydı tutamaz ve hata loglar. (Finansal kaçak riski düşük, kullanıcı deneyimi açısından kabul edilebilir).

## 2. Stok Tükenmesi (Global Limit)
*   **Senaryo:** Son 1 stok. 2 farklı kullanıcı ödeme yaptı.
*   **Validation:** İkisi de geçer.
*   **Finalization:**
    1.  Webhook 1: Stok 99 -> 100. Başarılı.
    2.  Webhook 2: Stok 100. `record_redemption` içinde limit kontrolü yapılırsa reddedilir.
    *   **İyileştirme:** `record_redemption` fonksiyonuna "limit check" eklendi mi?
    *   **Kontrol:** `stripe_service.py` -> `record_redemption`. Şu an sadece insert var. Limit kontrolü eklenmeli.

## 3. Aksiyon Planı (Abuse Fix)
*   `record_redemption` fonksiyonuna `usage_count < usage_limit` kontrolünü atomik (lock altında) ekle.
