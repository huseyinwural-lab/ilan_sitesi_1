# Search Parity Checklist (Mongo vs Postgres)

## Kapsam
- Public Search v2 (text + faceted)
- Real estate search endpoint
- Sıralama (date_desc, price_asc/desc)

## Kontrol Listesi
1) **Temel Sayım**
- [ ] Mongo ve Postgres toplam sonuç sayıları (same filters) 
- [ ] İlk 50 sonuç ID eşleşme oranı (>= %95)

2) **Text Search**
- [ ] Kısa query (1–2 kelime) sonuç eşleşmesi
- [ ] Çok kelimeli query (title+description)
- [ ] TR/DE dil varyasyonları

3) **Faceted Filters**
- [ ] category_id + price range
- [ ] city + price range
- [ ] make/model/year filtreleri
- [ ] seller_type + is_verified filtreleri

4) **Sorting**
- [ ] date_desc (published_at)
- [ ] price_asc/price_desc

5) **Edge Cases**
- [ ] price_type=HOURLY listings (price filter dışı)
- [ ] premium/showcase ordering
- [ ] unpublished/draft listing görünmeme

## Parity Başarı Kriteri
- Toplam count farkı <= %1
- İlk 50 sonuç ID eşleşmesi >= %95
- Facet count farkı <= %2
