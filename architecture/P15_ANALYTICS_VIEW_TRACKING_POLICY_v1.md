# P15 Analytics View Tracking Policy (v1)

**Kapsam:** İlan Görüntülenme (View) Sayımı
**Hedef:** Dashboard'da gösterilen "Görüntülenme" sayısının manipülasyondan arındırılmış, gerçek kullanıcı etkileşimini yansıtması.

## 1. Sayım Kuralları (Counting Rules)

### 1.1. Geçerli İstekler
*   Endpoint: `GET /api/v2/listings/{id}`
*   Statü: İlan `active` olmalı.
*   Kullanıcı: Anonim veya giriş yapmış herhangi bir kullanıcı.

### 1.2. Hariç Tutulanlar (Exclusions)
*   **Owner:** İlan sahibi kendi ilanını görüntülerse sayılmaz.
*   **Bot/Crawler:** `User-Agent` içinde "bot", "crawl", "spider", "headless" geçen istekler.
*   **Duplicate:** Aynı IP adresinden, aynı ilana, **30 dakika** içinde yapılan mükerrer istekler.

## 2. Teknik Model

### Veritabanı
*   `listings.view_count` (Integer): Denormalize sayaç (Hızlı okuma için).
*   `listing_views` (Table): Detaylı log (Audit ve Deduplication için).
    *   `listing_id`
    *   `ip_hash` (Privacy için hash'lenmiş IP)
    *   `user_agent_hash`
    *   `created_at`

### Akış
1.  Request gelir.
2.  `AnalyticsService.track_view(listing_id, request)` çağrılır.
3.  Bot kontrolü yapılır (Fail ise return).
4.  Owner kontrolü yapılır (Fail ise return).
5.  Dedup kontrolü yapılır (Redis veya DB query).
6.  Geçerliyse: `view_count += 1` ve `listing_views` insert (Atomic transaction).

## 3. Güvenlik
*   **IP Hashing:** KVKK/GDPR uyumu için IP adresleri salt ile hashlenerek saklanır.
*   **Rate Limit:** Çok yüksek frekanslı IP'ler (DDoS/Scraping) 429 alır ve view sayılmaz.
