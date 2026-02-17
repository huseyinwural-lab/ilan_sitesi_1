# P14: Growth & Scale Scope (v1)

**Faz:** P14
**Türü:** Hibrit (Growth + Scale)
**Tarih:** 14 Şubat 2026
**Durum:** PLANLAMA

## 1. Fazın Amacı
Platformun "Soft Launch" sürecinden "Public Launch"a geçişini desteklemek için iki ana eksende ilerlemek:
1.  **Growth (Büyüme):** Gelir üretme kapasitesini artırmak (Kuponlar, Dönüşüm Optimizasyonu, Referral).
2.  **Scale (Ölçekleme):** Artan kullanıcı ve veri yükünü kaldırabilecek performans ve güvenlik altyapısını kurmak (SEO, Cache, Abuse Monitoring).

## 2. Temel KPI'lar (Key Performance Indicators)
Aşağıdaki metrikler P14 başarısını ölçmek için kullanılacaktır (30 Günlük Hedefler):

| KPI | Tanım | Hedef |
| :--- | :--- | :--- |
| **MRR (Monthly Recurring Revenue)** | Aylık yinelenen abonelik geliri. | > 0 (İlk ödeyen kullanıcılar) |
| **Upgrade Conversion Rate** | Free/Limit aşımı -> Paid Plan geçiş oranı. | %5 |
| **Listing-to-Subscription** | İlan oluşturan kullanıcıların abonelik alma oranı. | %10 |
| **Search-to-Contact** | Arama yapan kullanıcının detay sayfasına gidip satıcıyla iletişime geçme oranı. | %20 |

## 3. Kapsam (Scope) & Öncelik Sıralaması

### Sprint 1: Revenue Engine (Öncelikli)
*   **Kampanya & Kupon Sistemi:** Admin yönetimli indirim kodları.
*   **Conversion Optimizasyonu:** Kullanıcıyı ödemeye teşvik eden UI/UX iyileştirmeleri.

### Sprint 2: User Engagement & Analytics
*   **Referral (MVP):** Arkadaşını getir sistemi.
*   **User Dashboard:** Kullanıcıya kendi verisini (görüntülenme, favori) gösterme.

### Sprint 3: Infrastructure & Scale
*   **SEO:** Google indexleme altyapısı (Sitemap, Schema).
*   **Performans:** Redis optimizasyonu ve sorgu iyileştirmeleri.
*   **Abuse Monitoring:** Fraud ve spam tespiti.

## 4. Gate (Çıkış Kriteri)
*   Canlı ortamda en az 1 gerçek ödeme (Stripe) ve 1 başarılı kupon kullanımı gerçekleşmiş olmalı.
*   Search latency P95 < 200ms korunmalı.
