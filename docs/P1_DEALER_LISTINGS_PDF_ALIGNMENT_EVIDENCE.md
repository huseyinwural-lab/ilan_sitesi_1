# P1_DEALER_LISTINGS_PDF_ALIGNMENT_EVIDENCE

Tarih: 2026-02-27

## Kapsam
- 2. satır menüde sıralama korunarak devam edildi.
- Avrupa kapsamı gereği **Sanal Turlar** ana menüden kaldırıldı.
- `İlanlar` sayfası PDF akışına uygun dolduruldu.

## Uygulanan Değişiklikler

1. Row2 ana menü
- Kaldırıldı: `Sanal Turlar`
- Aktif başlıklar: `Özet, İlanlar, Mesajlar, Müşteri Yönetimi, Favoriler, Raporlar, Danışman Takibi, Satın Al, Hesabım`

2. İlanlar sayfası (`/dealer/listings`)
- Başlık: `Yayında Olan İlanlar (x)`
- Arama kutusu: başlığa göre filtre
- Durum tabları:
  - `Yayında`
  - `Yayında Değil`
  - `Tümü`
- Tablo kolonları:
  - seçim
  - ilan başlığı + durum etiketi
  - fiyat
  - görüntülenme
  - favori
  - mesaj
  - bitiş
  - işlem
- Satır aksiyonları:
  - `Yayına Al`
  - `Arşivle`

## Test Kanıtı
- Frontend test agent sonucu: **COMPLETE PASS**
  - `Sanal Turlar` görünmüyor
  - `İlanlar` menüsü `/dealer/listings` yönlendirmesi başarılı
  - İstenen UI alanları tam görünüyor
  - Durum tabları çalışıyor
  - Satır aksiyon butonları render ediliyor

## Not
- Mevcut veri modelinde ilan bazlı görüntülenme/favori/mesaj metrikleri sınırlı olduğundan sayfa yapısı PDF’e hizalandı; metrik kaynak entegrasyonu bir sonraki adımda derinleştirilebilir.

**MOCKED API YOK**