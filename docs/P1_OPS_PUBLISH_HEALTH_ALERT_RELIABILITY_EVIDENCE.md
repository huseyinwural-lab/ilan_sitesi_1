# P1_OPS_PUBLISH_HEALTH_ALERT_RELIABILITY_EVIDENCE

Tarih: 2026-02-27

## Uygulanan Kapsam

1. `GET /api/admin/ops/alert-delivery-metrics?window=24h`
   - Server-side aggregation: `total_attempts`, `successful_deliveries`, `failed_deliveries`, `success_rate`, `last_failure_timestamp`, `channel_breakdown(slack/smtp/pd)`
   - Guardrail: `window <= 24h` (aksi halde `400 INVALID_WINDOW`)

2. `POST /api/admin/ops/alert-delivery/rerun-simulation`
   - Admin/Ops role kontrolü
   - Rate limit: dakika başına maksimum 3
   - Audit event: `OPS_ALERT_SIMULATION_TRIGGERED`
   - Zorunlu metadata: `actor_id`, `correlation_id`, `timestamp`

3. UI: `/admin/ops/publish-health`
   - “Son 24s Alarm Teslimat Başarı Oranı” kartı
   - Kanal breakdown mini kartları
   - “Re-run Alert Simulation” butonu + canlı sonuç kartı
   - Rate-limit warning + disabled state
   - Publish Health özet kartı (mevcut publish KPI entegrasyonu)

4. Performans/Stabilite
   - Query window limit: max 24h
   - Index migration: `ix_audit_logs_ops_alert_delivery_time_channel` (`created_at`, `resource_id`) partial index (`action='ui_config_ops_alert_delivery'`)

## Test Kanıtları

- Pytest: `backend/tests/test_p0_ops_alerts_channel_integration.py` + `backend/tests/test_p1_ops_publish_health_alert_reliability.py`
  - Sonuç: `37 passed, 2 skipped`
- Testing agent raporu: `/app/test_reports/iteration_35.json` (PASS)
- Frontend smoke + responsive doğrulama:
  - Desktop route load: `/admin/ops/publish-health`
  - Mobile overflow fix doğrulandı (390px, overflow=0)

## Maskeli Çalışma Notu

- Bu ortamda alert secret’ları eksik olduğunda rerun sonucu güvenli şekilde:
  - `delivery_status=blocked_missing_secrets`
  - `fail_fast.status="Blocked: Missing Secrets"`
- Secret değerleri raporlanmaz; sadece key isimleri ve maskeli durum kullanılır.

## Kapanış Kriterleri Durumu

- [x] Alert delivery success rate kartı canlı
- [x] Tek tık simülasyon akışı aktif
- [x] Role-based + rate-limit enforce ediliyor
- [x] Audit trigger event + zorunlu alanlar üretildi
- [x] Testler PASS

**MOCKED API YOK**