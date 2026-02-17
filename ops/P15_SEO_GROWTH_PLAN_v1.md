# P15 SEO Growth Plan (v1)

**Amaç:** Organik trafik artışı sağlayarak reklam maliyetlerini düşürmek (CAC - Customer Acquisition Cost).
**Hedef:** İlk 3 ayda organik trafikten %20 pay almak.

## 1. Teknik SEO (Technical SEO)

### A. Sitemap & Robots.txt
*   **Dinamik Sitemap:**
    *   `/sitemap.xml`: Index dosyası.
    *   `/sitemaps/static.xml`: Sabit sayfalar (Home, Plans, About).
    *   `/sitemaps/listings-active.xml`: Sadece `active` statüsündeki ilanlar. (Expired ilanlar sitemap'ten çıkarılır).
    *   `/sitemaps/categories.xml`: Kategori sayfaları.
*   **Robots.txt:** Admin paneli (`/admin`) ve kullanıcı paneli (`/dashboard`) engellenir (`Disallow`).

### B. Structured Data (Schema Markup)
İlan detay sayfalarında (`/listing/{slug}`) Google'ın zengin sonuçlar (Rich Snippets) göstermesi için JSON-LD formatında veri eklenir.
*   **Type:** `Product` veya `Offer`.
*   **Fields:** Name, Image, Description, Price, Currency, Availability (`InStock` -> Active).

### C. Canonical URLs
Arama parametreleri (sort, filter) nedeniyle oluşan kopya içerik algısını önlemek için:
*   `/listing/bmw-320i?sort=price` -> Canonical: `/listing/bmw-320i`
*   Expired ilanlar -> Kategori sayfasına veya benzer ilanlara 301 Redirect (veya 410 Gone, stratejiye göre). *Karar: P13 kapsamında 404/Soft 404, P15'te "Benzer İlanlar" ile 200 OK ama "Expired" uyarısı.*

## 2. İçerik Stratejisi (Content)

### A. Otomatik Meta Tagler
İlan başlığı ve özelliklerinden dinamik meta description üretimi:
*   *Template:* "{Marka} {Model} - {Yıl}, {Fiyat} {Para Birimi}. {Şehir} konumunda satılık."

### B. Kategori Açıklamaları
Her kategori listeleme sayfasının altına (footer üstü) SEO uyumlu, anahtar kelime zengini sabit metin alanları eklenir.

### C. Blog / Rehber (Future)
*   "2. El Araba Alırken Nelere Dikkat Edilmeli?" gibi rehber içerikler için `/blog` modülü.

## 3. İzleme (Monitoring)
*   **Google Search Console:** Mülk doğrulaması yapılır. "Crawl Errors" ve "Index Coverage" haftalık takip edilir.
*   **Core Web Vitals:** LCP, CLS, FID metrikleri. (P15 Real Traffic raporunda izlenir).
