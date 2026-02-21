# DEALER_IA_V1 (EU Uyumlu)

## Top Navigation (consumer ile aynı)
- İlanlarım
- Alışveriş İşlemlerim
- Favoriler
- Mesajlar
- Servisler
- Hesabım

## Sol Menü (ek modüller)
- Firma Profili
- Paket & Kota
- İlan Yönetimi
- Performans
- Fatura & Muhasebe
- GDPR Data Controller Paneli

## Sayfalar — Wireframe Özeti

### 1) Firma Profili
- **Amaç:** şirket bilgileri ve AB ticari gereklilikler.
- **Bileşenler:** firma formu, logo upload, VAT ID doğrulama.
- **Empty state:** zorunlu alanlar placeholder.
- **Success/Error:** doğrulama hatası banner.
- **RBAC:** dealer.
- **GDPR notu:** data controller bilgisi.

### 2) Paket & Kota
- **Amaç:** plan + kota görünürlük.
- **Bileşenler:** plan kartı, kota sayaçları, upgrade CTA.
- **Empty state:** plan yok → satın al.
- **Success/Error:** upgrade başarısız → retry.
- **RBAC:** dealer.
- **GDPR notu:** yok.

### 3) İlan Yönetimi
- **Amaç:** profesyonel ilan yönetimi.
- **Bileşenler:** tablo, status filtre, bulk actions.
- **Empty state:** "İlk ilan" CTA.
- **Success/Error:** bulk update error.
- **RBAC:** dealer.
- **GDPR notu:** yok.

### 4) Performans
- **Amaç:** metrik görünürlük.
- **Bileşenler:** grafikler, lead sayıları.
- **Empty state:** veri yok mesajı.
- **Success/Error:** data fetch error.
- **RBAC:** dealer.

### 5) Fatura & Muhasebe
- **Amaç:** VAT ve fatura süreçleri.
- **Bileşenler:** VAT badge, PDF download, reverse charge notu.
- **Empty state:** fatura yok.
- **Success/Error:** download error.
- **RBAC:** dealer.

### 6) GDPR Controller Paneli
- **Amaç:** müşteri verisi yönetimi.
- **Bileşenler:** export, deletion request queue, retention ayarı.
- **Empty state:** talep yok.
- **Success/Error:** export fail.
- **RBAC:** dealer.
- **GDPR notu:** controller sorumlulukları açık.
