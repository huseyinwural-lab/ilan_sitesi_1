# OPS_HARDENING_P2_CLEANUP_EVIDENCE

Tarih: 2026-02-27

## 1) Ops Alarm Eşikleri (P0)

Doküman:
- `/app/docs/PUBLISH_OPS_THRESHOLD_V1.md`

Canlı endpointler:
- `GET /api/admin/ui/configs/{config_type}/ops-thresholds`
- `POST /api/admin/ui/configs/{config_type}/ops-alerts/simulate`

Doğrulama:
- High lock wait simülasyonu (max_lock_wait_ms=520) -> critical alert tetiklendi.
- Conflict rate 45% -> critical alert tetiklendi.

Test kanıtı:
- `backend/tests/test_p67_ops_hardening_p2_cleanup.py::TestOpsAlertSimulation`

---

## 2) Publish KPI Dashboard

Doküman:
- `/app/docs/PUBLISH_KPI_DEFINITION_V1.md`

Backend aggregation çıktıları (`/publish-audits`):
- KPI: `median_retry_count`, `time_to_publish_ms`, `conflict_resolution_time_ms`, `publish_success_rate`
- Windows: `1h`, `24h`, `7d`
- Trend: son 24 saat saatlik bucket (`conflict_rate`, `avg_lock_wait_ms`, `publish_success_rate`)

Frontend görünürlük:
- Corporate Dashboard Designer > Publish Audit kartı
- KPI metrikleri
- Conflict sparkline + lock wait sparkline
- Alert badge listesi

Test kanıtı:
- `/app/test_reports/iteration_33.json` (frontend + backend PASS)

---

## 3) Legacy Publish Endpoint Kaldırımı (P2 Cleanup)

Doküman:
- `/app/docs/LEGACY_PUBLISH_DEPRECATION_PLAN.md`

Durum:
- Legacy endpoint (`/publish/{config_id}`) **fiziksel olarak kaldırıldı** (route yok)
- Beklenen davranış: `404 Not Found`

Usage analizi endpointi:
- `GET /api/admin/ui/configs/{config_type}/legacy-usage` kaldırıldı (P2 route cleanup)

Test kanıtı:
- `backend/tests/test_p67_ops_hardening_p2_cleanup.py::TestLegacyPublishEndpoint410`

---

## 4) Kontrat Son Durumu

Tek publish kontratı:
- `POST /api/admin/ui/configs/{config_type}/publish`

Guard’lar:
- `config_version` zorunlu
- `resolved_config_hash` drift guard
- owner scope doğrulama
- optimistic conflict + lock handling

---

## 5) Test Özeti

Self-test:
- `pytest -q backend/tests/test_p67_ops_hardening_p2_cleanup.py` -> **11 passed**
- ek regresyon setleri (p60..p66) PASS

Testing Agent:
- Rapor: `/app/test_reports/iteration_33.json`
- Sonuç: **20/20 PASS**

## Sonuç

- Alarm eşikleri aktif + test edilmiş.
- KPI dashboard (backend pipeline + frontend görünürlük) canlı.
- Legacy publish endpoint fiziksel kaldırımı tamamlandı.
- Publish domain tek kontrata indirgendi ve operasyonel olarak ölçülebilir hale geldi.

**MOCKED API YOK**
