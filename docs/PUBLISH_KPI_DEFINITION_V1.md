# PUBLISH_KPI_DEFINITION_V1

Tarih: 2026-02-27

## KPI Seti

1. `median_retry_count`
2. `time_to_publish_ms`
3. `conflict_resolution_time_ms`
4. `publish_success_rate`

## Hesaplama Kuralları

### median_retry_count
- Kaynak: publish attempt `retry_count`
- Hesap: medyan

### time_to_publish_ms
- Kaynak: başarılı publish attempt `publish_duration_ms`
- Hesap: medyan

### conflict_resolution_time_ms
- Kaynak: aynı owner üzerinde conflict sonrası ilk success arası süre
- Hesap: medyan

### publish_success_rate
- Kaynak: success_count / total_attempts
- Hesap: yüzde

## Aggregation Pencereleri

- `1h`
- `24h`
- `7d`

Endpoint response içinde `windows` objesi ile sunulur.

## Trend Görselleştirme

Publish Audit kartında:
- Son 24 saat conflict rate sparkline
- Son 24 saat avg lock wait sparkline

## Alert Reliability KPI (P1)

- Metrik: `alert_delivery_success_rate_24s`
- Formül: `successful_deliveries / total_attempts` (son 24 saat)
- Endpoint: `GET /api/admin/ops/alert-delivery-metrics?window=24h`
- Dönen alanlar:
  - `total_attempts`
  - `successful_deliveries`
  - `failed_deliveries`
  - `success_rate`
  - `last_failure_timestamp`
  - `channel_breakdown` (`slack`, `smtp`, `pd`)
- Eşik renkleri:
  - `>= 99%` → normal
  - `95-99%` → warning
  - `< 95%` → critical
- Kurallar:
  - Aggregation tamamen server-side yapılır (UI hesap yapmaz)
  - `window` en fazla `24h` olabilir (fail-fast validation)

## Deterministiklik Notları

- Timestamp bazlı sıralama ve pencereler sabit UTC ile hesaplanır.
- Medyan/p95 hesapları deterministic sırayla uygulanır.
