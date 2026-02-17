
# P17 Dynamic Pricing Rules (v1)

**Amaç:** Statik fiyat listesi yerine, talep ve kategori bazlı değişken fiyatlandırma uygulayarak geliri maksimize etmek.

## 1. Temel Kurallar (Base Rules)
Fiyat hesaplama formülü:
`Final Price = Base Price * Category Multiplier * City Multiplier * Demand Multiplier`

### A. Kategori Çarpanı (Category Multiplier)
*   **Emlak (Real Estate):** x1.0 (Baz)
*   **Vasıta (Vehicle):** x0.8
*   **Alışveriş (Shopping):** x0.2
*   **Hizmetler (Services):** x0.5

### B. Şehir Çarpanı (City Multiplier)
*   **Tier 1 (İstanbul, Berlin, Paris):** x1.5
*   **Tier 2 (Ankara, Münih, Lyon):** x1.2
*   **Tier 3 (Diğer):** x1.0

### C. Talep Çarpanı (Demand Multiplier) - MVP
*   Şu an için manuel veya basit kural bazlı.
*   **Hafta Sonu (Cmt-Paz):** x1.1
*   **Prime Time (18:00 - 22:00):** x1.2 (Sadece Boost için)

## 2. Uygulama Alanı
Bu kurallar şu ürünlere uygulanır:
*   `Pay-per-Listing` (Ekstra ilan ücreti)
*   `Premium Products` (Showcase, Boost, Urgent)

*Not: Dealer Abonelik fiyatları sabittir (Sözleşmeli), dinamik fiyatlandırmadan etkilenmez.*

## 3. Teknik Mimari
`PriceService` içinde `calculate_price(product_key, context)` metodu.
`context` içeriği: `{category_id, city, user_segment, request_time}`.
