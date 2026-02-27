# P2 Dry-Run Alert Senaryosu

## Senaryo
1. Test alarmı tetikle (tek kanal):
   - `POST /api/admin/ops/alert-delivery/rerun-simulation`
   - body: `{"config_type":"dashboard","channels":["smtp"]}`
2. Correlation ID al:
   - response: `correlation_id`
3. Teslimat doğrula:
   - `GET /api/admin/ui/configs/dashboard/ops-alerts/delivery-audit?correlation_id=<id>&channels=smtp`
4. Sonucu değerlendir:
   - `delivery_status = ok`
   - `last_failure_classification = null`
5. Kapatma:
   - test alarmını ops playbook’a göre `ack/resolve` et

## Kanal Bazlı Dry-Run Sırası
1) SMTP
2) Slack
3) PagerDuty

## Başarılı Tamamlama Kriteri
- Her kanal için ayrı `correlation_id`
- Her kanalın audit kaydı mevcut
- Rate limit ihlali yok (dakikada max 3 simülasyon)
