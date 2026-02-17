# P19 URL Contract v2.0 (Multi-Country)

**Amaç:** Platformun uluslararası SEO uyumluluğunu sağlamak için URL yapısını güncellemek.

## 1. URL Pattern
`/{country_code}/{city_slug}/{category_slug}/{price_range?}`

### Örnekler
*   `/tr/istanbul/satilik-daire` (Türkiye)
*   `/de/berlin/auto-kaufen` (Almanya)
*   `/fr/paris/appartement` (Fransa)

## 2. Kurallar
1.  **Country Code:** ISO 3166-1 alpha-2 standardı (2 harfli, lowercase). Örn: `tr`, `de`, `fr`.
2.  **Fallback:** Eğer URL'de ülke kodu yoksa (eski linkler veya direkt giriş), kullanıcının IP adresine göre (GeoIP) veya `default_country` (TR) ayarına göre 301 Redirect yapılır.
3.  **Hreflang:** Sayfa header'ında alternatif dil/ülke linkleri belirtilir.

## 3. Localization
*   Kategori slug'ları dile göre değişir (`otomobil` vs `cars`).
*   Fiyat aralıkları para birimine göre değişir (100k -> 100.000 TRY veya 100.000 EUR).

## 4. Migration Planı (URL Rewrite)
*   Eski: `/istanbul/otomobil`
*   Yeni: `/tr/istanbul/otomobil` (301 Redirect)
