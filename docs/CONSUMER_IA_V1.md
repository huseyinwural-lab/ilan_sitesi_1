# CONSUMER_IA_V1 (EU Uyumlu)

## Top Navigation (standard)
- İlanlarım
- Alışveriş İşlemlerim
- Favoriler
- Mesajlar
- Servisler
- Hesabım

## Sayfalar — Wireframe Özeti

### 1) Özet
- **Amaç:** Kullanıcının hesap, ilan ve ödeme durumunu hızlı görmesi.
- **Bileşenler:** özet kartları (ilan sayısı, bekleyen işlemler), son mesajlar listesi, son bildirimler.
- **Empty state:** "Henüz aktivite yok".
- **Success/Error:** kart yüklenemedi → retry CTA.
- **RBAC:** consumer.
- **GDPR notu:** kişisel veri gösterimi minimum.

### 2) İlanlarım
- **Amaç:** Tüm ilanların yönetimi.
- **Bileşenler:** ilan tablosu, durum filtreleri (draft/pending/active/paused), detay CTA.
- **Empty state:** "İlan oluştur" CTA.
- **Success/Error:** yayın/paused işlemi sonrası toast.
- **RBAC:** consumer.
- **GDPR notu:** yok.

### 3) Alışveriş İşlemlerim
- **Amaç:** ödeme ve fatura geçmişi.
- **Bileşenler:** fatura listesi, iade listesi, ödeme yöntemi kartı.
- **Empty state:** "Henüz işlem yok".
- **Success/Error:** indirme hatası → error banner.
- **RBAC:** consumer.
- **GDPR notu:** finansal veri maskelenir.

### 4) Favoriler
- **Amaç:** favori ilan ve listeleri yönetmek.
- **Bileşenler:** liste kartları, liste oluşturma modalı.
- **Empty state:** "Favori ekle".
- **Success/Error:** liste oluşturma başarısız → retry.
- **RBAC:** consumer.
- **GDPR notu:** yok.

### 5) Mesajlar
- **Amaç:** 12 ay mesaj geçmişi.
- **Bileşenler:** mesaj liste paneli, arama, okunmamış filtresi.
- **Empty state:** "Mesaj bulunamadı".
- **Success/Error:** mesaj yüklenemedi → retry.
- **RBAC:** consumer.
- **GDPR notu:** retention 12 ay.

### 6) Servisler
- **Amaç:** abonelik/ek servis yönetimi.
- **Bileşenler:** aktif hizmet kartları, yenileme CTA.
- **Empty state:** "Aktif servis yok".
- **Success/Error:** satın alma başarısız → hata banner.
- **RBAC:** consumer.
- **GDPR notu:** ödeme verisi minimal.

### 7) Hesabım
- **Amaç:** profil, güvenlik, gizlilik ayarları.
- **Bileşenler:** profil formu, güvenlik kartları, privacy center linki.
- **Empty state:** yok.
- **Success/Error:** form save toast.
- **RBAC:** consumer.
- **GDPR notu:** Right to be Forgotten + export linki.
