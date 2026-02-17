# P13 Search Stale Data Policy (v1)

**Amaç:** Arama (Search) sonuçlarında süresi dolmuş veya silinmiş (stale) verilerin görünmesini engellemek.

## 1. Temizleme Mekanizması (Self-Cleaning)
Arama altyapısı Redis Cache (`search:v2:*`) ve PostgreSQL indeksine dayanır. "Expiration Job" (İlan Süre Aşımı İşlemi) veri hijyeninin kritik bir parçasıdır.

### Kural: "Expire -> Invalidate"
Her `process_expirations.py` çalıştırıldığında ve en az bir ilan `expired` statüsüne çekildiğinde:
1.  Veritabanı transaction'ı commit edilir.
2.  **ZORUNLU:** Redis üzerindeki `search:v2:*` namespace'ine ait tüm cache anahtarları silinir (Invalidation).

## 2. Revalidation Job (Günlük)
Risk: Expiration job çalışmazsa veya cache invalidation başarısız olursa.
Önlem: Günde 1 kez (gece yarısı) çalışacak `scripts/revalidate_search_index.py` (henüz implemente edilmedi, backlog P14) ile cache tamamen temizlenir.

## 3. Runtime Filtreleme
Search API (`/v2/search`), her sorguda veritabanından veri çekerken `WHERE status = 'active'` filtresini uygular. Cache miss durumunda her zaman güncel veri gelir.

## 4. Gate
Bu politika uygulanmadan Expiration Job production'a alınamaz. (Şu an uygulanmıştır: `process_expirations.py` v2).
