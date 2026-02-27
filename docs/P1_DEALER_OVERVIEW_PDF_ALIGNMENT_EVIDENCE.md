# P1_DEALER_OVERVIEW_PDF_ALIGNMENT_EVIDENCE

Tarih: 2026-02-27

## Kapsam
- 2. satır menüde **Özet** tıklandığında PDF’e uygun içerik alanları
- Menü içinde sayfa dolaşımı (Özet kartlarından ilgili sayfalara geçiş)

## Uygulanan Alanlar (Özet)
- Mağaza Performansı kartı
  - Ziyaret Sayısı (Son 24 Saat)
  - Ziyaret Sayısı (Son 7 Gün)
  - İlan ziyaret kırılım tablosu (top listeler)
- Paket kartı
  - Paket adı
  - Durum
  - Kullanılan / Kalan
  - Satın Alma Sayfasına Git aksiyonu
- KPI kartları
  - Yayındaki İlan Sayısı
  - Talebi Olan Müşteri
  - Müşteriye Uygun İlanlar
- Veri uyarısı
  - Müşteri/talep verisi yoksa bilgi mesajı
- Hızlı Geçiş kartları
  - summary widget’ları üzerinden ilgili route’lara geçiş

## Backend Değişikliği
`GET /api/dealer/dashboard/summary`
- Yeni `overview` bloğu eklendi:
  - `store_performance`
  - `package_summary`
  - `kpi_cards`
  - `data_notice`

## Test Kanıtı
- Backend test: `backend/tests/test_dealer_portal_config.py -k "dashboard_summary or dealer_overview"` → **3 passed**
- Frontend smoke (auth sonrası):
  - `dealer-overview-store-performance-card` bulundu
  - `dealer-overview-package-card` bulundu
  - `dealer-overview-kpi-card-grid` bulundu
  - `dealer-layout-row2-primary-menu` bulundu

## Not
- Özet ana menü aktiflik davranışı tekilleştirildi (aynı route kullanan placeholder öğeler aynı anda aktif görünmüyor).

**MOCKED API YOK**