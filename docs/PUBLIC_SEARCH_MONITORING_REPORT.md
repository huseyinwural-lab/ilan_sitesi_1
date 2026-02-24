# PUBLIC_SEARCH_MONITORING_REPORT — Log-based 24h window (operational)

**Tarih:** 2026-02-24 13:47:41 UTC
**Ortam URL:** https://public-site-build.preview.emergentagent.com
**Durum:** CLOSED

## 24h Log Window (Operational)
- Kaynak: `/api/admin/system/health-detail` (error_buckets_24h + endpoint_stats)
- Zaman aralığı: `2026-02-23T13:37:33.787664+00:00` → `2026-02-24T13:32:33.787664+00:00`
- Error rate (5m): `0.0`
- Error buckets (24h): toplam `0` (anomali yok)
- 5xx toplamı: `0`
- Slow query count (24h): `3`
- Slow query threshold: `800ms`
- p95 latency (search): `N/A` (search endpoint telemetry yok)
- Endpoint stats:
  - /api/admin/* p95=2037.21ms, slow_query_count=5
  - /api/listings p95=4479.12ms, slow_query_count=1

## Query / Filter Dağılımı
- Log-based telemetry şu anda query/filter dağılımı üretmiyor. (N/A)
