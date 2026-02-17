# P18 SEO URL Contract (v1)

**Amaç:** Programmatic SEO sayfalarının URL yapısını ve davranışını standardize etmek.

## 1. URL Pattern
`/{city_slug}/{category_slug}/{price_range?}`

### Örnekler
*   `/istanbul/satilik-daire` (Tüm Fiyatlar)
*   `/ankara/otomobil/500k-1m` (Fiyat Aralığı)
*   `/izmir/kiralik-isyeri` (Kategori)

## 2. Slug Kuralları
*   **Lowercase:** Tüm karakterler küçük harf olmalıdır.
*   **Hyphenated:** Boşluklar tire (`-`) ile değiştirilir.
*   **ASCII:** Türkçe karakterler dönüştürülür (ş->s, ı->i, ü->u, ö->o, ç->c, ğ->g).
*   **Trailing Slash:** Yok (Varsa 301 Redirect).

## 3. Parametre Validasyonu

### City Slug
*   `countries.json` veya DB'deki şehir listesinde tanımlı olmalıdır.
*   Geçersiz şehir -> `404 Not Found`.

### Category Slug
*   `categories` tablosundaki `slug` alanıyla eşleşmelidir (Dil bazlı, örn: 'en' veya 'tr').
*   Geçersiz kategori -> `404 Not Found`.

### Price Range (Opsiyonel)
*   Format: `{min}-{max}`, `{min}-plus`, `under-{max}`.
*   Örnekler: `100k-500k`, `1m-plus`, `under-500k`.
*   Suffix: 'k' = 1.000, 'm' = 1.000.000.
*   Geçersiz format -> `404 Not Found` (veya ignore edilip genel listeye redirect?). **Karar: 404** (Duplicate content riskini önlemek için).

## 4. Response
*   **200 OK:** Geçerli kombinasyon ve sonuç var.
*   **404 Not Found:** Geçersiz slug veya mantıksız kombinasyon.
*   **301 Redirect:** Canonical olmayan format (örn: büyük harf, parametre sırası).
