## Hypercare Alert Spec — v1.0.0

**Durum:** Onay Bekliyor (kanal seçimi gerekli)

### Threshold Önerileri
- **403 anomaly:** 5 dakikada > %5 oranı
- **Audit error spike:** 5 dakikada > %1 hata
- **Failed login burst:** 5 dakikada > 20 deneme

### Bildirim Kanalı
- Seçenekler: Slack / Email / Ops webhook
- Karar: TBD

### Alarm Test Senaryosu
1. 403 spike simülasyonu
2. Audit insert hata simülasyonu
3. Failed login burst simülasyonu

### Notlar
- Seçilen kanal doğrultusunda webhook konfigürasyonu yapılacak.
