## Hypercare Plan — v1.0.0 (48 Saat)

### Süre
- **T0–T48h** (prod rollout sonrası)

### İzlenecek Metrikler
- **Audit error spike:** audit_logs insert error / latency
- **403 anomalileri:** RBAC yanlışlıkları
- **Country-scope violation denemeleri:** 403 sayısında artış
- **Search error rate / latency**
- **Report submit başarısızlık oranı**

### İzleme Akışı
- İlk 6 saat: saatlik kontrol
- 6–24 saat: 3 saatte bir kontrol
- 24–48 saat: 6 saatte bir kontrol

### Alarm / Eskalasyon
- 403 oranı %X üstüne çıkarsa → engineering review
- Audit insert error > 0 → acil hata analizi
- Search 5xx spike → rollback değerlendirmesi

### Aksiyon Planı
- Konfig / index problemleri → hızlı hotfix
- RBAC yanlış izin → hızlı patch
- Kritik akış bozulması → rollback
