# P1_DEALER_MESSAGES_PDF_ALIGNMENT_EVIDENCE

Tarih: 2026-02-27

## Kapsam
- Sıralı ilerleme kapsamında `Mesajlar` menüsü PDF’e göre dolduruldu.
- Row2 menüde Avrupa kapsamı doğrultusunda `Sanal Turlar` kaldırılmış durumda korundu.

## Uygulanan Mesajlar Ekranı

### Başlık ve sayaç
- Başlık: `İlan Mesajlarım (x)`

### Filtre/Tabs
- `Yayında Olan İlanlar`
- `Bilgilendirmeler`

### Arama/Filtre
- Arama inputu: kullanıcı / ilan / mesaj metni
- `Filtrele` butonu

### Listing tablosu
- Kolonlar:
  - Kullanıcı
  - İlan
  - Mesaj
  - Mesaj Sayısı
  - Son Mesaj
  - İşlem

### Bilgilendirmeler tablosu
- Kolonlar:
  - Başlık
  - Mesaj
  - Kaynak
  - Tarih
  - Durum

## Backend güncellemesi
- `GET /api/dealer/messages` endpointi genişletildi:
  - `items` (konuşma listesi)
  - `notification_items` (dealer notification listesi)
  - `summary` (`listing_messages`, `notifications`)

## Test Kanıtı
- Frontend test agent: COMPLETE PASS
  - Row2 menüde `Sanal Turlar` yok
  - Mesajlar menüsü `/dealer/messages` yönlendiriyor
  - Tüm mesaj ekran bileşenleri görünür
  - `Bilgilendirmeler` tab switch + tablo render PASS
- Backend pytest:
  - `backend/tests/test_dealer_portal_config.py -k dealer_messages` → **2 passed**

**MOCKED API YOK**
