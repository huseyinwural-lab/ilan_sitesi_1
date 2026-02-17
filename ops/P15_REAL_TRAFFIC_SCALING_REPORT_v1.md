# P15 Real Traffic Scaling Report (v1)

**Amaç:** Public Launch sonrası oluşan gerçek trafik verilerini analiz ederek sistemin darboğazlarını tespit etmek.
**Dönem:** İlk 7 Gün ve İlk 30 Gün sonu.

## 1. Performans Metrikleri (KPIs)

| Metrik | Hedef (SLA) | Mevcut (Ölçülen) | Durum |
| :--- | :--- | :--- | :--- |
| **Search Latency (P95)** | < 200ms | *TBD* | ⚪ |
| **Checkout Latency** | < 2s | *TBD* | ⚪ |
| **Listing Detail Load** | < 300ms | *TBD* | ⚪ |
| **Webhook Process Time** | < 1s | *TBD* | ⚪ |
| **Error Rate (HTTP 5xx)** | < %0.1 | *TBD* | ⚪ |

## 2. Altyapı Kaynak Kullanımı

### Database (PostgreSQL)
*   **CPU:** Peak saatlerde % kullanım. (Hedef: < %60)
*   **Memory:** Buffer hit ratio. (Hedef: > %99)
*   **Connections:** Active connection sayısı / Max connection. (Hedef: < %70)
*   **Slow Queries:** > 500ms süren sorgular. (Hedef: 0)

### Cache (Redis)
*   **Hit Ratio:** Search cache isabet oranı. (Hedef: > %85)
*   **Evictions:** Bellek yetersizliğinden silinen anahtar sayısı. (Hedef: 0)

### Application (FastAPI)
*   **RPS:** Saniyedeki istek sayısı (Request per Second).
*   **Worker Saturation:** Uvicorn worker'larının doluluk oranı.

## 3. Darboğaz Analizi (Bottleneck Analysis)
*Bu bölüm trafik verisi toplandıktan sonra doldurulacaktır.*
*   **Örnek:** "Search sorguları CPU darboğazına takılıyor."
*   **Örnek:** "Webhook işleme sırasında DB kilitlenmeleri yaşanıyor."

## 4. Ölçekleme Tetikleyicileri (Scaling Triggers)
Aşağıdaki eşikler 15 dakika boyunca aşılırsa Altyapı Stratejisi devreye girer:
*   DB CPU > %80
*   Web Response Time P95 > 500ms
*   Redis Memory > %90
