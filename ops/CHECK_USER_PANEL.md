# CHECK_USER_PANEL

## Amaç
Bireysel kullanıcı paneli (User Panel) için checklist + gap matrisi.

## 1) Panel Yapısı
### Mevcut gözlem
- `UserPanelLayout` var.
- `/account/*` route’ları App.js’de var.

### Kontrol
- [ ] Dashboard var mı? (route var mı?)
- [ ] İlanlarım listeleme stabil mi?
- [ ] İlan düzenleme akışı tutarlı mı?

### Gap
- `/account` altında Overview sayfası yok.

## 2) Wizard Entegrasyonu
### Mevcut gözlem
- Vehicle wizard UI var.
- Publish (backend) hazır.

### Kontrol
- [ ] Emlak wizard publish var mı? (UI/BE)
- [ ] Vehicle wizard gerçek publish mi?
- [ ] Draft mantığı çalışıyor mu?

### Gap
- `MyListings` mock data kullanıyor.

## 3) Mesajlaşma
### Mevcut gözlem
- `/account/messages` route UI yok (gap)

### Kontrol
- [ ] Thread bazlı mı?
- [ ] Spam kontrolü var mı?
- [ ] Kullanıcı engelleme var mı?

## 4) Hesap Güvenliği
- [ ] Şifre değiştirme
- [ ] E-mail doğrulama
- [ ] Hesap silme

## Auth Guard
### Mevcut gözlem
- `/account/*` route’ları ProtectedRoute ile korunmuyor (gap)

## PASS/PARTIAL/FAIL (Ön karar)
- Panel yapısı: PARTIAL
- Wizard: PARTIAL (Vehicle akışı var, Emlak yok)
- Mesajlaşma: FAIL
- Hesap güvenliği: FAIL
