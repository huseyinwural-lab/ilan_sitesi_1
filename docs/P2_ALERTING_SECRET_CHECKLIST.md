# P2 Alerting Secret Checklist (Tek Sayfa)

Bu checklist, `Admin Publish Health` alerting kanallarını (SMTP → Slack → PagerDuty) modül modül devreye almak için hazırlanmıştır.

## 1) SMTP (kritik e-posta fallback)
- Secretlar:
  - `ALERT_SMTP_HOST` → SMTP host (FQDN/IP)
  - `ALERT_SMTP_PORT` → `25|465|587`
  - `ALERT_SMTP_FROM` → gönderen e-posta (`noreply@domain.com`)
  - `ALERT_SMTP_TO` → alıcı listesi (`ops1@domain.com,ops2@domain.com`)
  - `ALERT_SMTP_AUTH_REQUIRED` → `true|false`
  - `ALERT_SMTP_USER` / `ALERT_SMTP_PASS` → auth açıksa zorunlu
  - `ALERT_SMTP_STARTTLS` → `true|false`
- Kullanıldığı yer:
  - `backend/app/routers/ui_designer_routes.py::_simulate_smtp_delivery`
- Test:
  - `GET /api/admin/ui/configs/dashboard/ops-alerts/secret-presence?channels=smtp`
  - `POST /api/admin/ops/alert-delivery/rerun-simulation` body: `{"config_type":"dashboard","channels":["smtp"]}`

## 2) Slack (ops kanal bildirimleri)
- Secretlar:
  - `ALERT_SLACK_WEBHOOK_URL` → Slack incoming webhook URL
- Kullanıldığı yer:
  - `backend/app/routers/ui_designer_routes.py::_simulate_slack_delivery`
- Test:
  - `GET /api/admin/ui/configs/dashboard/ops-alerts/secret-presence?channels=slack`
  - `POST /api/admin/ops/alert-delivery/rerun-simulation` body: `{"config_type":"dashboard","channels":["slack"]}`

## 3) PagerDuty (incident escalation)
- Secretlar:
  - `ALERT_PAGERDUTY_ROUTING_KEY` → integration routing key
  - `ALERT_PAGERDUTY_EVENTS_URL` → opsiyonel override (`default: https://events.pagerduty.com/v2/enqueue`)
- Kullanıldığı yer:
  - `backend/app/routers/ui_designer_routes.py::_simulate_pagerduty_delivery`
- Test:
  - `GET /api/admin/ui/configs/dashboard/ops-alerts/secret-presence?channels=pagerduty`
  - `POST /api/admin/ops/alert-delivery/rerun-simulation` body: `{"config_type":"dashboard","channels":["pagerduty"]}`

## Audit Doğrulama (ortak)
- `GET /api/admin/ui/configs/dashboard/ops-alerts/delivery-audit?correlation_id=<id>&channels=<channel>`
- Beklenen:
  - `total_records >= 1`
  - `channels_logged` seçilen kanalı içermeli
  - `all_channels_recorded = true`
