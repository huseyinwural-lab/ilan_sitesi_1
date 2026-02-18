## P1 — Audit Dashboard Widget Spec

### Widget: “Son 24 Saat Kritik Event”

#### Event Whitelist
- FAILED_LOGIN
- RATE_LIMIT_BLOCK
- UNAUTHORIZED_ROLE_CHANGE_ATTEMPT
- LISTING_FORCE_UNPUBLISH
- LISTING_SOFT_DELETE
- REPORT_STATUS_CHANGE
- INVOICE_STATUS_CHANGE

#### Filtreler
- **Country filter:** country_code (opsiyonel)
- **Role filter:** actor_role (opsiyonel)
- **Event filter:** whitelist içinden multi-select

#### Pagination & Retention
- Limit: 50/event type
- Retention: 30 gün görünür (ops, UI)

#### Örnek Endpoint
- `GET /api/admin/audit-logs/critical?country=DE&role=country_admin&limit=50`

#### Non-Goals
- Real-time streaming yok (polling yeterli)
- Export yok (P2)
