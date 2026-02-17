# ADMIN_DEALER_APPLICATION_WORKFLOW

## Amaç
Dealer onboarding approve/reject iş akışını üretime hazır hale getirmek.

## Reason Enum (tek kaynak)
- `/app/architecture/DEALER_APPLICATION_REASON_ENUMS_V1.md`

## Endpoints

### 1) Liste
`GET /api/admin/dealer-applications`
- Country-scope enforced (admin context `?country=XX`)
- Filtre: `status`
- Pagination: `skip`, `limit`
- Search: `email` veya `company_name` regex

### 2) Reject
`POST /api/admin/dealer-applications/{id}/reject`
- `reason` zorunlu
- `reason=other` → `reason_note` zorunlu
- status: pending → rejected
- Audit (audit-first): `DEALER_APPLICATION_REJECTED`

### 3) Approve
`POST /api/admin/dealer-applications/{id}/approve`
- status: pending → approved
- Yeni user oluşturulur:
  - `role="dealer"`
  - `dealer_status="active"`
  - `country_code=application.country_code`
- Audit (audit-first): `DEALER_APPLICATION_APPROVED`

## Atomiklik
- Audit insert başarısızsa approve/reject commit edilmez.
- Mongo transaction yoksa bile audit-first pattern ile “audit yoksa commit yok” garantisi sağlanır.

## Notlar (MVP)
- Approve response’unda test amaçlı `temp_password` döndürülür (prod’da email gönderimine bağlanır).
