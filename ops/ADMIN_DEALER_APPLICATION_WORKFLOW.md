# ADMIN_DEALER_APPLICATION_WORKFLOW

## Amaç
Dealer onboarding approve/reject iş akışını üretime hazır hale getirmek.

## Endpoints
### Reject
`POST /api/admin/dealer-applications/{id}/reject`
- reason zorunlu
- reason=other → reason_note zorunlu
- status: pending → rejected
- Audit: `DEALER_APPLICATION_REJECTED` (audit-first)

### Approve
`POST /api/admin/dealer-applications/{id}/approve`
- status: pending → approved
- Yeni `users` kaydı oluşturulur:
  - role="dealer"
  - dealer_status="active"
  - country_code = application.country_code
- Audit: `DEALER_APPLICATION_APPROVED` (audit-first)

## Atomiklik
- Audit insert olmadan approve/reject commit olmaz.
- Mongo transaction yoksa bile audit-first pattern ile “audit yoksa commit yok” garantisi sağlanır.
