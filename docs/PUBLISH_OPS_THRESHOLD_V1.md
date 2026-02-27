# PUBLISH_OPS_THRESHOLD_V1

Tarih: 2026-02-27

## Ölçüm Modeli
- Rolling window: **5 dakika**
- Değerlendirme frekansı: **1 dakika**
- Metrikler publish attempt telemetry üzerinden hesaplanır.

## Threshold Tablosu

| Metrik | Warning | Critical | Ölçüm Periyodu |
|---|---:|---:|---|
| `avg_lock_wait_ms` | >= 120ms | >= 220ms | 5 dk rolling |
| `max_lock_wait_ms` | >= 250ms | >= 450ms | 5 dk rolling |
| `publish_duration_ms_p95` | >= 1000ms | >= 1700ms | 5 dk rolling |
| `conflict_rate` | >= 25% | >= 40% | 5 dk rolling |

## Alert Policy

### Warning Seviyesi
- Kanal: Slack
- Tetikleyiciler:
  - `conflict_rate > 25%`
  - `publish_duration_ms_p95 > 1000`
  - `avg_lock_wait_ms > 120`
  - `max_lock_wait_ms > 250`

### Critical Seviyesi
- Kanal: Slack + Email + On-call
- Tetikleyiciler:
  - `max_lock_wait_ms > 450`
  - `conflict_rate > 40%`
  - `publish_duration_ms_p95 > 1700`

## Simülasyon Senaryosu (Ops Test)

Endpoint:
- `POST /api/admin/ui/configs/{config_type}/ops-alerts/simulate`

Örnek payload:
```json
{
  "avg_lock_wait_ms": 300,
  "max_lock_wait_ms": 520,
  "publish_duration_ms_p95": 1800,
  "conflict_rate": 45
}
```

Beklenen sonuç:
- Alert tetiklenir (warning/critical)
- Simulation event audit log’a yazılır (`ui_config_ops_alert_simulation`)
