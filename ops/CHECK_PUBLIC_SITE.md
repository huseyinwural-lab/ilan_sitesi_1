# CHECK_PUBLIC_SITE

## Amaç
Public Site (ziyaretçi) arayüzünde navigasyon, arama/listeleme, ilan detay, dealer profil ve güven katmanı maddelerini kontrol etmek.

## 1) Menü + Country Path Tutarlılığı
### Mevcut gözlem
- `PublicLayout` country slug: `/${selectedCountry.toLowerCase()}/...`
- Menü API fallback var.

### Kontrol Maddeleri
- [ ] Üst menüde tüm ana dikeyler görünür mü? (en az Emlak + Vasıta)
- [ ] Mega menu segment bazlı mı? (Vasıta altında segment linkleri)
- [ ] Country path tutarlı mı? (`/de`, `/fr` vb.)

### Kanıt
- URL: `/` (header)
- URL: `/{country}/vasita` (landing)

## 2) Arama ve Listeleme
### Mevcut gözlem
- SearchPage endpoint: `GET /api/v2/search?...`
- State URL-sync: `useSearchState` ile.

### Kontrol Maddeleri
- [ ] Filtreler segment-aware mi? (category değişince facet reset)
- [ ] Querystring canonical mı? (aynı state aynı URL)
- [ ] Pagination stabil mi? (page/limit)
- [ ] Premium boost doğru çalışıyor mu? (backend sinyali var mı?)

### Gap Notu
- Premium boost davranışı server tarafı doğrulanmalı.

## 3) İlan Detay
### Mevcut gözlem
- DetailPage vehicle listing endpoint kullanıyor.
- Phone reveal şu an **mock**.
- Canonical URL hard-coded (`platform.com`) (gap).

### Kontrol Maddeleri
- [ ] Foto galeri performansı (lazy load/preview)
- [ ] Seller badge doğru mu?
- [ ] Structured data var mı? (json-ld)
- [ ] Benzer ilan önerisi var mı?
- [ ] PII minimizasyonu (liste response vs detay)

## 4) Bayi Public Profil
### Mevcut gözlem
- Dedicated dealer public profile route görünmüyor (gap).

### Kontrol Maddeleri
- [ ] SEO slug doğru mu?
- [ ] Dealer istatistik gösteriliyor mu?
- [ ] Inventory pagination çalışıyor mu?

## 5) Güven Katmanı
### Mevcut gözlem
- Reveal phone rate limit: yok (gap)
- Spam mesaj koruması: yok (gap)

### Kontrol Maddeleri
- [ ] Reveal phone rate limit var mı?
- [ ] Spam mesaj koruması var mı?
- [ ] PII liste response’ta yok mu?

## PASS/PARTIAL/FAIL (Ön karar)
- Navigasyon: PARTIAL
- Arama: PARTIAL
- Detay: PARTIAL
- Dealer public profil: FAIL
- Güven katmanı: FAIL
