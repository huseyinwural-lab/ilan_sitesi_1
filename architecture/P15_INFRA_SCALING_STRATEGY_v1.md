# P15 Infrastructure Scaling Strategy (v1)

**Amaç:** Trafik artışı durumunda sistemin nasıl büyütüleceğini (Scale Up/Out) belirlemek.

## 1. Veritabanı Stratejisi (Database)

### A. Connection Pooling
*   **Mevcut:** SQLAlchemy Async Engine (Application side pooling).
*   **Sonraki Adım:** **PgBouncer** (Transaction pooling).
    *   *Tetikleyici:* Active connection sayısı 100'ü aştığında veya "Too many clients" hatası alındığında.

### B. Read-Write Splitting (Okuma-Yazma Ayrımı)
*   **Mevcut:** Tek instance (Primary).
*   **Sonraki Adım:** **Read Replica** eklenmesi.
    *   *Kullanım:* Arama (`/v2/search`) ve Listeleme (`GET /listings`) trafiği Replica'ya yönlendirilir.
    *   *Tetikleyici:* DB CPU > %70 (Read-heavy yük altında).

## 2. Caching Stratejisi

### A. Katmanlı Cache
*   **L1 (In-Memory):** Çok sık erişilen konfigürasyonlar (Country list, Categories) için uygulama belleği (LRU).
*   **L2 (Redis):** Search sonuçları ve Session verisi.

### B. Redis Scaling
*   **Mevcut:** Tek instance.
*   **Sonraki Adım:** Redis Cluster veya daha yüksek bellekli instance.

## 3. Asenkron İşlemler (Background Jobs)

### Queue Ayrıştırma
Mevcut `process_expirations.py` cron tabanlıdır. Yük arttığında **Celery** veya **ARQ** (Redis tabanlı) kuyruk sistemine geçilecektir.
*   **Queue 1 (High Priority):** Webhooks (Ödeme, Referral).
*   **Queue 2 (Low Priority):** Email gönderimi, Image processing.
*   **Queue 3 (Maintenance):** Expiration, Index revalidation.

## 4. Statik İçerik (Assets)
*   **Mevcut:** Doğrudan URL (Picsum vb. demo, Prod'da S3 varsayımı).
*   **Strateji:** **CDN (Cloudflare/AWS CloudFront)** kullanımı zorunludur.
    *   Tüm görseller ve statik JS/CSS dosyaları CDN üzerinden sunulmalı.
    *   Bandwidth maliyetini düşürür ve yükleme hızını artırır.

## 5. Horizontal Scaling (Application)
*   **Container:** Kubernetes (K8s) pod sayısı artırılır (HPA - Horizontal Pod Autoscaler).
*   **Metrik:** CPU veya Request Queue uzunluğuna göre otomatik ölçeklenme.
