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

## Deterministiklik Notları

- Timestamp bazlı sıralama ve pencereler sabit UTC ile hesaplanır.
- Medyan/p95 hesapları deterministic sırayla uygulanır.
