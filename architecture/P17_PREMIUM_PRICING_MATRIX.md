# P17 Premium Pricing Matrix (v1)

**Amaç:** Premium ürünlerin kategori ve süre bazlı fiyatlandırması.

## Fiyatlandırma Mantığı (Base Prices)
Fiyatlar `PriceConfig` tablosunda tutulur ve ülkeye/para birimine göre değişir. Aşağıdaki örnekler **TRY** bazındadır.

| Ürün | Süre / Adet | Emlak (Konut) | Vasıta (Otomobil) | Diğer (Alışveriş) |
| :--- | :--- | :--- | :--- | :--- |
| **Showcase** | 1 Hafta | 250 TRY | 200 TRY | 50 TRY |
| **Showcase** | 4 Hafta | 750 TRY (3x) | 600 TRY | 150 TRY |
| **Boost** | 1 Adet | 50 TRY | 40 TRY | 10 TRY |
| **Boost** | 5'li Paket | 200 TRY | 160 TRY | 40 TRY |
| **Urgent** | 1 Hafta | 100 TRY | 80 TRY | 20 TRY |
| **Bold Title** | İlan Süresince | 75 TRY | 60 TRY | 15 TRY |

## Dinamik Çarpanlar (P17.3 Hazırlığı)
*   **Şehir Çarpanı:** İstanbul x1.5, Ankara x1.2, Diğer x1.0.
*   **Fiyat Çarpanı:** İlan fiyatı > 10 Milyon ise x2.0.
