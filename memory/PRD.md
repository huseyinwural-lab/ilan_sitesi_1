# PRD — İlan Ver Overhaul (Canlı Çalışma Dokümanı)

## 1) Orijinal Problem Tanımı
Kullanıcı, mevcut full-stack uygulamada (React + FastAPI + PostgreSQL) özellikle **İlan Ver** akışını PDF standardına göre yeniden inşa etmek ve admin kontrollü kategori/modül yönetimi ile entegre etmek istedi.

Ana hedefler:
- İlan 1: Modül grid seçimi (admin config kontrollü)
- İlan 2: Sonsuz seviye kategori seçimi + Vasıta master data entegrasyonu
- İlan 3: 8 bloklu form + autosave + doğrulama + preview/submit
- Backend: Draft -> Preview Ready -> Submitted state machine + idempotency + audit

---

## 2) Mevcut Mimari
- **Frontend:** React (route tabanlı ilan akışı)
  - `/ilan-ver` -> `ListingCategorySelect.js`
  - `/ilan-ver/arac-sec` -> `VehicleSelector.js`
  - `/ilan-ver/detaylar` -> `ListingDetails.js`
  - `/ilan-ver/onizleme` -> `ListingPreview.js`
- **Backend:** FastAPI (monolith `backend/server.py`)
  - İlan draft/patch/preview-ready/submit endpoints
  - Kategori children endpoint
  - Vehicle years/makes/models/trims endpoint
  - Home category layout config endpoint
- **DB:** PostgreSQL

---

## 3) Bu Iterasyonda Tamamlananlar (2026-03-01)

### P0 — İlan 1 (Module Grid)
- Modül grid fallback değerleri **2x4** olacak şekilde güncellendi.
  - Backend default: `listing_module_grid_columns=4`
  - Frontend default: `listing_module_grid_columns=4`
- `listing_lx_limit` fallback **5** olacak şekilde güncellendi (Devamını Gör için).
- Modüller deterministik sıralama mantığıyla render ediliyor (config order + stable fallback).
- Modül context persist iyileştirildi:
  - `ilan_ver_module`
  - `ilan_ver_module_id`
  - URL query `module_id`

### P0 — İlan 2 (Kategori + Vasıta)
- Kolonlarda **Devamını Gör / Daha Az Göster** eklendi (varsayılan 5, config override destekli).
- Vehicle trim listesinde duplicate önleme eklendi:
  - Backend `/api/vehicle/trims` dedupe
  - Frontend `VehicleSelector` dedupe
- Vehicle seçim payload’ına `trim_key` eklendi ve localStorage persist edildi.
- Vehicle modülde Continue routing davranışı stabil hale getirildi (`/ilan-ver/arac-sec`).

### P0 — İlan 3 (8 Blok Form)
`ListingDetails.js` 8 blok yapısına genişletildi:
1. Çekirdek alanlar
2. Parametre alanları (schema/dynamic)
3. Adres formu
4. Detay grupları
5. Fotoğraf (20 limit) + 1 video URL
6. İletişim bilgileri
7. İlan süresi (fiyat + indirim çizgisi kartları)
8. Onay kutusu

Ekler:
- Blok bazlı autosave (PATCH draft)
- Draft hydrate (var olan draft geri doldurma)
- Client-side doğrulama
- Eksik config durumunda blok bazlı disabled + admin uyarısı

> Not: Google autocomplete API key olmadığı durumda blok otomatik fallback ile manuel girişe düşer ve uyarı gösterir.

### P0 — Backend State/Audit/Idempotency
- Draft create için audit: `LISTING_DRAFT_CREATED`
- Draft patch için audit: `LISTING_UPDATED`
- Submit için audit: `LISTING_SUBMITTED`
- Submit response’a `detail_url` eklendi: `/ilan/{id}?preview=1`
- Idempotency tekrar çağrılarında `detail_url` korunuyor.

### P0 — Preview + Detay Yönlendirme
- `ListingPreview.js` submit sonrası `detail_url`’e redirect ediyor.

---

## 4) Test Durumu

### Yapılan Doğrulamalar
- Backend curl/python testleri:
  - create draft ✅
  - patch draft ✅
  - preview-ready ✅
  - submit-review + idempotency ✅
  - submit response `detail_url` ✅
  - vehicle trims uniqueness ✅
- Frontend smoke/playwright:
  - `/ilan-ver` yüklenme ✅
  - vehicle continue ile `/ilan-ver/arac-sec` yönlendirme ✅

### Testing Agent Çıktısı
- `/app/test_reports/iteration_69.json`
- Agent bulgusu: vehicle continue routing medium issue
- Bu issue bu iterasyonda düzeltildi ve self-test ile doğrulandı.

---

## 5) Açık İşler / Backlog

### P0 (devam eden)
- İlan 3’te gerçek Google autocomplete entegrasyonu (API key sağlanırsa)
- Emlak tarafında zengin seed/category verisi ile E2E senaryo genişletme
- Leaf lock davranışının admin/create tarafında kapsamlı doğrulaması

### P1
- Vitrin değişikliği anasayfaya yansımama bug fix
- Acil ilanlar sayfası canlı veri + pagination doğrulama

### P2
- Category Builder drag&drop sıralama
- Batch publish scheduler
- Slack/SMTP/PagerDuty alert entegrasyonları
- PDF piksel uyum polish

---

## 6) Mock Durumu
- MOCKED API: **Yok**

