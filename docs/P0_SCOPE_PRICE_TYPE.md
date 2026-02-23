# P0 Scope Freeze — Price Type (FIXED/HOURLY)

## Kapsam Kilidi (ADR-PRICE-001..004)
Bu P0 döngüsünde aşağıdaki teslimatlar dışına çıkılmayacaktır.

### Kapsam İçi
1) **Model & API kontratı**
   - price_type (FIXED/HOURLY), price_amount (mevcut), hourly_rate (nullable)
   - Server-side validation: yalnız seçili tip dolu, diğeri null
   - Response mapping: price_type + ilgili değer
2) **Frontend — Çekirdek Alanlar / Fiyat bloğu**
   - Radio/segmented kontrol + tek input swap
   - Tip değişiminde diğer alan reset ve payload’dan çıkar
   - Hata mesajları: “Fiyat giriniz.” / “Saatlik ücret giriniz.”
3) **Public detay & arama davranışı**
   - FIXED: “{amount} {currency}”
   - HOURLY: “{rate} {currency} / saat”
   - Fiyat filtresi sadece FIXED (HOURLY hariç)
4) **Test paketi (UI + API + E2E)**

### Kapsam Dışı
- HOURLY için ayrı arama filtresi (P2)
- Kategori bazlı hourly yetkilendirme (hook noktası P2)

## Kapanış Kriteri
- UI toggle + swap + reset
- API validasyonları (FIXED/HOURLY/invalid)
- Detay ve search gösterimi uygun formatta
- HOURLY filtre hariç davranışı doğrulandı
