# P17 Funnel Revenue Analysis (v1)

**Amaç:** Ödeme adımındaki kayıpları (Drop-off) tespit edip geliri artırmak.

## 1. İzlenecek Adımlar (Funnel Steps)
1.  **View Premium Options:** Kullanıcı "Doping Al" sayfasına baktı.
2.  **Select Product:** Kullanıcı bir ürün (örn: Boost) seçti.
3.  **Start Checkout:** "Öde" butonuna bastı (Stripe'a yönlendi).
4.  **Payment Success:** Ödeme tamamlandı.

## 2. Mevcut Sorunlar (Hipotez)
*   **Fiyat Belirsizliği:** Kullanıcı ödeme sayfasına gitmeden son fiyatı (Vergi + Dinamik Fiyat) göremiyor.
*   **Seçenek Karmaşası:** Çok fazla seçenek (Showcase 7 gün, 14 gün, 30 gün...) karar felcine yol açıyor.

## 3. İyileştirme Planı
*   **Dynamic Price Preview:** `PriceService` kullanılarak ürün seçim anında "Sizin için fiyat: 50 TRY" (Şehir/Kategori çarpanlı) gösterilecek.
*   **Best Value Badge:** En karlı paket (Örn: 5'li Boost) "En Popüler" olarak işaretlenecek.
