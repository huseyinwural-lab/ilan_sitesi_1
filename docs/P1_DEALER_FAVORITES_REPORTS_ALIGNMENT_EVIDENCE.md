# P1_DEALER_FAVORITES_REPORTS_ALIGNMENT_EVIDENCE

Tarih: 2026-02-27

## Kapsam
- Sıralama korunarak devam edildi.
- `Favoriler` ve `Raporlar` ekranları PDF akışına göre dolduruldu.
- Mesajlar için okunma bilgisi korunarak iyileştirildi.

## Menü Sırası Doğrulama
- Row2 menü sırası korunuyor:
  - Özet
  - İlanlar
  - Mesajlar
  - Müşteri Yönetimi
  - Favoriler
  - Raporlar
  - Danışman Takibi
  - Satın Al
  - Hesabım
- `Sanal Turlar` menüde yok.

## Favoriler Ekranı (`/dealer/favorites`)

### Backend
- Yeni endpoint: `GET /api/dealer/favorites`
- Dönen alanlar:
  - `favorite_listings`
  - `favorite_searches`
  - `favorite_sellers`
  - `summary`

### Frontend
- Başlık + alt metin
- 3 tab:
  - Favori İlanlar
  - Favori Aramalar
  - Favori Satıcılar
- Arama inputu
- Tab bazlı tablolar + boş durum

## Raporlar Ekranı (`/dealer/reports`)

### Backend
- `GET /api/dealer/reports?window_days=...` genişletildi
- Geçerli window: `7/14/30/90` (diğerleri `400`)
- Dönen alanlar:
  - `kpis`
  - `filters`
  - `report_sections` (listing/views/favorites/messages/mobile_calls)
  - `package_reports`
  - `doping_usage_report`

### Frontend
- Pencere filtreleri: 7/14/30/90
- Bölüm tabları:
  - Yayındaki İlan Raporu
  - Görüntülenme Raporu
  - Favoriye Alınma Raporu
  - Gelen Mesaj Raporu
  - Gelen Arama Raporu (Mobil)
  - Paket Raporları
  - Doping Kullanım Raporu
- Bölüm bazlı metrik + seri tablo render

## Test Kanıtı
- Testing agent: `/app/test_reports/iteration_37.json`
  - Backend: 100% (27/27)
  - Frontend: 100%
- Pytest:
  - `backend/tests/test_dealer_favorites_reports_v2.py` → 27 passed
  - `backend/tests/test_dealer_messages_customers.py` → 20 passed

## Durum
- `Sanal Turlar` kaldırılmış durumda korunuyor.
- Favoriler ve Raporlar akışı çalışır durumda.
- Mesaj okundu bilgisi çalışır durumda.

**MOCKED API YOK**
