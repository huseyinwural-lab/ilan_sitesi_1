# DEALER DASHBOARD V2 — FRONTEND ENTEGRASYON EVIDENCE (P1)

## Kapsam (Bu Faz)
- Corporate Dashboard Grid DnD editör (12 kolon, widget palette, guardrail UI)
- Bireysel Header DnD editör (row bazlı sıralama, visible toggle, logo fallback)
- Draft → Preview(diff) → Publish + confirm modal + rollback akışı
- Publish sonrası canlı render doğrulama kartı ve dealer dashboard config-driven render

## Implementasyon Referansları
- Frontend
  - `/app/frontend/src/pages/admin/ui-designer/CorporateDashboardDesigner.jsx`
  - `/app/frontend/src/pages/admin/ui-designer/IndividualHeaderDesigner.jsx`
  - `/app/frontend/src/pages/admin/AdminUserInterfaceDesignV2.jsx`
  - `/app/frontend/src/pages/dealer/DealerDashboard.jsx`
- Backend
  - `/app/backend/app/routers/ui_designer_routes.py`

## Endpoint Doğrulama (P1)
- `GET /api/admin/ui/configs/dashboard`
- `POST /api/admin/ui/configs/dashboard`
- `POST /api/admin/ui/configs/dashboard/publish` (require_confirm zorunlu)
- `GET /api/admin/ui/configs/dashboard/diff`
- `POST /api/admin/ui/configs/dashboard/rollback` (require_confirm zorunlu)
- Header için aynı publish/diff/rollback akışları (`config_type=header`, `segment=individual`)

## Guardrail Kanıtı
- Backend enforce:
  - min 1 KPI
  - max 12 widget
- UI enforce:
  - KPI yoksa publish disabled
  - Widget sayısı sınırı UI ve API tarafında birlikte korunuyor

## Test Sonuçları
- Self-test (main agent)
  - `pytest -q backend/tests/test_p61_dashboard_backend.py backend/tests/test_p62_ui_publish_workflow.py`
  - Sonuç: **13 PASS**
- Testing Agent
  - Rapor: `/app/test_reports/iteration_28.json`
  - Özet: **Backend 23/23 PASS**, **Frontend kritik akışlar PASS**
  - Ek test dosyası: `/app/backend/tests/test_p62_extended_dashboard_ui.py`
  - Pytest XML:
    - `/app/test_reports/pytest/p61_dashboard_backend_results.xml`
    - `/app/test_reports/pytest/p62_extended_dashboard_results.xml`

## Notlar
- **MOCKED API YOK**
- Admin test hesabı: `admin@platform.com / Admin123!`