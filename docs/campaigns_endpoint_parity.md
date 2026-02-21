# Campaigns Endpoint Parity Checklist (SQL)

## POST `/api/admin/campaigns`
- Auth: campaigns_admin / super_admin / country_admin
- Required: name, status, start_at, country_code
- Optional: end_at, budget_amount, budget_currency, notes, rules_json
- Response: Campaign V1 payload

## GET `/api/admin/campaigns`
- Filters: status, country, period/date_range, q
- Pagination: page, limit
- Sorting: start_at DESC, updated_at DESC

## GET `/api/admin/campaigns/{id}`
- Campaign V1 payload
- `audit[]` SQL audit log entries

## PUT `/api/admin/campaigns/{id}`
- Status transitions: draft↔active/paused/ended
- Response: updated campaign

## POST `/api/admin/campaigns/{id}/activate`
- Status: draft/paused → active

## POST `/api/admin/campaigns/{id}/pause`
- Status: active → paused

## DELETE `/api/admin/campaigns/{id}`
## POST `/api/admin/campaigns/{id}/archive`
- Status: → ended

## Response Schema (V1)
- id, name, status, start_at, end_at, country_code
- budget_amount, budget_currency, notes, rules_json
- created_at, updated_at
