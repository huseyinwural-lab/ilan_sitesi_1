# P17 Revenue KPI Definition (v1)

**Amaç:** Monetization başarısını ölçülebilir, sayısal hedeflere bağlamak.

## 1. Temel Gelir Metrikleri (North Star Metrics)

| KPI | Tanım | Hedef (İlk Çeyrek) |
| :--- | :--- | :--- |
| **MRR (Monthly Recurring Revenue)** | Aktif aboneliklerden elde edilen aylık öngörülebilir gelir. | > 10.000 EUR |
| **ARPU (Average Revenue Per User)** | Toplam Gelir / Aktif Kullanıcı Sayısı. | > 5 EUR |
| **Gross Revenue** | Toplam Brüt Ciro (Abonelik + Tek Seferlik + Premium). | - |

## 2. Ürün Bazlı Metrikler

### A. Abonelik (Dealer)
*   **Subscriber Growth Rate:** Aylık yeni abone artış oranı.
*   **Churn Rate:** Abonelik iptal oranı. (Hedef: < %5).
*   **Tier Distribution:** Basic / Pro / Enterprise dağılımı. (Hedef: %20 Pro üzeri).

### B. Premium Visibility
*   **Attach Rate:** İlan veren kullanıcıların yüzde kaçı premium ürün satın alıyor? (Hedef: %10).
*   **Repurchase Rate:** Bir kez Boost alan kullanıcının tekrar alma oranı.

## 3. Operasyonel Metrikler
*   **Payment Failure Rate:** Başarısız ödeme oranı. (Hedef: < %5).
*   **Refund Rate:** İade oranı. (Hedef: < %1).
*   **Discount Impact:** Toplam gelirin ne kadarı kuponla "vazgeçildi"? (Hedef: < %10).

## 4. Dashboard Tasarımı (Admin Panel)
Admin panelindeki "Revenue" sekmesi şu widget'ları içermelidir:
1.  **MRR Trend Grafiği:** Son 12 ay.
2.  **Product Breakdown (Pie Chart):** Gelirin ürünlere göre dağılımı (Sub vs Premium).
3.  **Top Spenders:** En çok harcama yapan 10 bayi.
4.  **Daily Sales Feed:** Son gerçekleşen satışlar listesi.
