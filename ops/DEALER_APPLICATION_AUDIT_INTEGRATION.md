# DEALER_APPLICATION_AUDIT_INTEGRATION

## Amaç
Dealer application approve/reject aksiyonlarının audit’te zorunlu ve filtrelenebilir olması.

## Event Types
- `DEALER_APPLICATION_APPROVED`
- `DEALER_APPLICATION_REJECTED`

## Audit-first
- Approve / Reject mutasyonları audit insert başarısızsa commit olmaz.

## Audit Logs UI
- `/admin/audit-logs` ekranında event_type filtresi üzerinden seçilebilir.
