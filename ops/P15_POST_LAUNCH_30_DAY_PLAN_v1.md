# P15 Post-Launch 30-Day Plan (v1)

**Faz:** P15 Post-Launch Stabilizasyon
**Dönem:** Public Launch + 30 Gün (Hyper-care Period)
**Durum:** AKTİF

## 1. Altın Kural: Feature Freeze
Bu 30 günlük dönemde sisteme **yeni özellik (feature) eklenmeyecektir.**
*   **İzin Verilen:** Kritik bug fixleri, güvenlik yamaları, performans iyileştirmeleri.
*   **Yasaklanan:** Yeni UI ekranları, yeni ödeme metodları, DB şema değişiklikleri (fix hariç).

## 2. Günlük Rutin (Daily Checklist)
Her sabah 09:00'da Ops ekibi (veya Admin) tarafından kontrol edilir:

### A. Finansal Metrikler
*   [ ] **MRR Trendi:** Düne göre artış/azalış.
*   [ ] **Conversion:** Kayıt -> Ödeme oranı (%5 altına düşerse alarm).
*   [ ] **Coupon Usage:** Toplam indirim tutarı bütçeyi aşıyor mu?
*   [ ] **Referral Cost:** Dağıtılan ödül (Stripe Credit) makul seviyede mi?

### B. Teknik Metrikler
*   [ ] **Error Rate:** HTTP 5xx oranı < %0.1 olmalı.
*   [ ] **Latency:** P95 Search < 200ms.
*   [ ] **Webhook Errors:** `stripe_event` tablosunda `failed` kaydı var mı?

## 3. Haftalık Rutin (Weekly Health Check)
*   **Database:** Disk kullanımı ve connection pool doluluk oranı.
*   **Redis:** Cache hit ratio ve memory fragmentation.
*   **Incident Review:** Haftalık yaşanan sorunların kök neden analizi (RCA).

## 4. Olay Yönetimi (Incident Management)
| Seviye | Tanım | SLA (Müdahale) |
| :--- | :--- | :--- |
| **P0 (Critical)** | Sistem tamamen kapalı, Ödeme alınamıyor. | 15 dk |
| **P1 (High)** | Arama çalışmıyor, Kayıt yapılamıyor. | 1 saat |
| **P2 (Medium)** | Resim yükleme yavaş, Mail gitmiyor. | 4 saat |
| **P3 (Low)** | UI görsel hatası, yazım yanlışı. | 24 saat |

## 5. Çıkış Kriteri (Gate)
30. günün sonunda:
*   Son 7 gün içinde P0/P1 olayı yaşanmamış olmalı.
*   Stripe bakiyesi ile DB kayıtları %100 tutarlı olmalı.
