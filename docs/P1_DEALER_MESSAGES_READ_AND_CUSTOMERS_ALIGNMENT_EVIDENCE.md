# P1_DEALER_MESSAGES_READ_AND_CUSTOMERS_ALIGNMENT_EVIDENCE

Tarih: 2026-02-27

## Kapsam
- Mesajlar ekranına **okundu bilgisi** eklendi.
- Sıralı akışta bir sonraki menü olan **Müşteri Yönetimi** PDF yapısına göre dolduruldu.

## 1) Mesajlar – Okundu Bilgisi

### Backend
- `GET /api/dealer/messages`
  - `items[].unread_count`
  - `items[].read_status` (`okundu` / `okunmadı`)
  - `summary.unread_listing_messages`
- Yeni endpoint:
  - `POST /api/dealer/messages/{conversation_id}/read`
  - Satıcı dışından gelen okunmamış mesajları `is_read=true` yapar

### Frontend (`/dealer/messages`)
- Listing tablosuna yeni kolon: `Okunma`
- Badge:
  - `Okunmadı (n)`
  - `Okundu`
- Aksiyon:
  - Okunmamış satırda `Okundu İşaretle`

## 2) Müşteri Yönetimi – PDF Hizalama

### Frontend (`/dealer/customers`)
- Başlık: `Müşteri Yönetimi`
- Tablar:
  - `Kullanıcı Listesi (x)`
  - `Mağaza Kullanıcısı Olmayanlar (y)`
- Filtreler:
  - `Ad Soyad`
  - `E-Posta`
  - `Durumu`
- Tablo kolonları:
  - `Ad Soyad`
  - `E-Posta`
  - `Durumu`
  - `İşlemler`

### Backend (`GET /api/dealer/customers`)
- `items` (mevcut müşteri listesi)
- `non_store_users` (mağaza kullanıcısı olmayanlar)
- `summary` (`users_count`, `non_store_users_count`)

## Test Kanıtı
- Testing agent raporu: `/app/test_reports/iteration_36.json` (Backend 100%, Frontend 100%)
- Pytest:
  - `backend/tests/test_dealer_messages_customers.py` + dealer portal subset
  - Sonuç: `19 passed`
- Frontend test agent: PASS
  - Okunma kolonu/badge/aksiyon doğrulandı
  - Müşteri Yönetimi tab/filtre/kolon doğrulandı
  - Row2 menüde `Sanal Turlar` yok

**MOCKED API YOK**
