# RBAC_ENDPOINT_MAP

**Son güncelleme:** 2026-02-24 11:21:40 UTC
**Kaynak:** server.py RBAC allowlist (deny-by-default)
**Durum:** FREEZE v1 (değişiklikler PR diff-onay zorunlu)

## Format
- METHOD PATH → allowed roles (runtime)

## Endpoint Allowlist
| Method | Path | Allowed Roles |
|---|---|---|
| POST | /api/admin/analytics/events | super_admin, country_admin |
| PATCH | /api/admin/applications/{application_id}/assign | super_admin, country_admin, support |
| PATCH | /api/admin/applications/{application_id}/status | super_admin, country_admin, support, moderator |
| GET | /api/admin/applications/assignees | super_admin, country_admin, support, moderator |
| GET | /api/admin/attributes | super_admin, country_admin, moderator |
| POST | /api/admin/attributes | super_admin, country_admin, moderator |
| DELETE | /api/admin/attributes/{attribute_id} | super_admin, country_admin, moderator |
| PATCH | /api/admin/attributes/{attribute_id} | super_admin, country_admin, moderator |
| GET | /api/admin/audit-logs | super_admin, finance, ROLE_AUDIT_VIEWER, audit_viewer |
| GET | /api/admin/audit-logs/actions | super_admin, ROLE_AUDIT_VIEWER, audit_viewer |
| GET | /api/admin/audit-logs/event-types | super_admin, ROLE_AUDIT_VIEWER, audit_viewer |
| GET | /api/admin/audit-logs/export | super_admin, ROLE_AUDIT_VIEWER, audit_viewer |
| GET | /api/admin/audit-logs/resources | super_admin, ROLE_AUDIT_VIEWER, audit_viewer |
| GET | /api/admin/audit-logs/{log_id} | super_admin, ROLE_AUDIT_VIEWER, audit_viewer |
| GET | /api/admin/campaigns | super_admin, country_admin, campaigns_admin, campaigns_supervisor |
| POST | /api/admin/campaigns | super_admin, country_admin, campaigns_admin |
| DELETE | /api/admin/campaigns/{campaign_id} | super_admin, country_admin, campaigns_supervisor |
| GET | /api/admin/campaigns/{campaign_id} | super_admin, country_admin, campaigns_admin, campaigns_supervisor |
| PUT | /api/admin/campaigns/{campaign_id} | super_admin, country_admin, campaigns_admin |
| POST | /api/admin/campaigns/{campaign_id}/activate | super_admin, country_admin, campaigns_supervisor |
| POST | /api/admin/campaigns/{campaign_id}/archive | super_admin, country_admin, campaigns_supervisor |
| POST | /api/admin/campaigns/{campaign_id}/pause | super_admin, country_admin, campaigns_supervisor |
| GET | /api/admin/categories | super_admin, country_admin, moderator |
| POST | /api/admin/categories | super_admin, country_admin, moderator |
| GET | /api/admin/categories/import-export/export/csv | super_admin, country_admin |
| GET | /api/admin/categories/import-export/export/json | super_admin, country_admin |
| GET | /api/admin/categories/import-export/export/xlsx | super_admin, country_admin |
| POST | /api/admin/categories/import-export/import/commit | super_admin, country_admin |
| POST | /api/admin/categories/import-export/import/dry-run | super_admin, country_admin |
| POST | /api/admin/categories/import-export/import/dry-run/pdf | super_admin, country_admin |
| GET | /api/admin/categories/import-export/sample/csv | super_admin, country_admin |
| GET | /api/admin/categories/import-export/sample/xlsx | super_admin, country_admin |
| DELETE | /api/admin/categories/{category_id} | super_admin, country_admin, moderator |
| PATCH | /api/admin/categories/{category_id} | super_admin, country_admin, moderator |
| GET | /api/admin/categories/{category_id}/export/csv | super_admin, country_admin, moderator |
| GET | /api/admin/categories/{category_id}/export/pdf | super_admin, country_admin, moderator |
| GET | /api/admin/categories/{category_id}/versions | super_admin, country_admin, moderator |
| GET | /api/admin/categories/{category_id}/versions/{version_id} | super_admin, country_admin, moderator |
| GET | /api/admin/countries | super_admin, country_admin, support |
| POST | /api/admin/countries | super_admin |
| DELETE | /api/admin/countries/{code} | super_admin |
| GET | /api/admin/countries/{code} | super_admin, country_admin, support |
| PATCH | /api/admin/countries/{code} | super_admin |
| GET | /api/admin/dashboard/country-compare | super_admin, country_admin, support, finance |
| GET | /api/admin/dashboard/country-compare/export/csv | super_admin, country_admin, support, finance |
| GET | /api/admin/dashboard/export/pdf | super_admin |
| GET | /api/admin/dashboard/summary | super_admin, country_admin, support, finance |
| GET | /api/admin/dealer-applications | super_admin, country_admin, moderator |
| POST | /api/admin/dealer-applications/{app_id}/approve | super_admin, country_admin, moderator |
| POST | /api/admin/dealer-applications/{app_id}/reject | super_admin, country_admin, moderator |
| GET | /api/admin/dealers | super_admin, country_admin, moderator |
| GET | /api/admin/dealers/{dealer_id} | super_admin, country_admin, moderator |
| GET | /api/admin/dealers/{dealer_id}/audit-logs | super_admin, country_admin, moderator |
| POST | /api/admin/dealers/{dealer_id}/plan | super_admin, country_admin, moderator |
| POST | /api/admin/dealers/{dealer_id}/status | super_admin, country_admin, moderator |
| GET | /api/admin/finance/revenue | super_admin, finance |
| GET | /api/admin/individual-applications | super_admin, country_admin, moderator |
| POST | /api/admin/individual-applications/{app_id}/approve | super_admin, country_admin, moderator |
| POST | /api/admin/individual-applications/{app_id}/reject | super_admin, country_admin, moderator |
| GET | /api/admin/individual-users | super_admin, country_admin, support, moderator |
| GET | /api/admin/individual-users/export/csv | super_admin, marketing |
| POST | /api/admin/invite/accept | public |
| GET | /api/admin/invite/preview | public |
| GET | /api/admin/invoices | super_admin, finance |
| POST | /api/admin/invoices | super_admin, finance |
| GET | /api/admin/invoices/{invoice_id} | super_admin, finance |
| POST | /api/admin/invoices/{invoice_id}/cancel | super_admin, finance |
| POST | /api/admin/invoices/{invoice_id}/mark-paid | super_admin, finance |
| POST | /api/admin/invoices/{invoice_id}/refund | super_admin, finance |
| GET | /api/admin/listings | super_admin, country_admin, moderator |
| POST | /api/admin/listings/{listing_id}/approve | country_admin, moderator, super_admin |
| POST | /api/admin/listings/{listing_id}/force-unpublish | super_admin, country_admin, moderator |
| POST | /api/admin/listings/{listing_id}/needs_revision | country_admin, moderator, super_admin |
| POST | /api/admin/listings/{listing_id}/reject | country_admin, moderator, super_admin |
| POST | /api/admin/listings/{listing_id}/soft-delete | super_admin, country_admin, moderator |
| GET | /api/admin/menu-items | super_admin, country_admin, moderator |
| POST | /api/admin/menu-items | super_admin, country_admin, moderator |
| DELETE | /api/admin/menu-items/{menu_id} | super_admin, country_admin, moderator |
| PATCH | /api/admin/menu-items/{menu_id} | super_admin, country_admin, moderator |
| POST | /api/admin/moderation/bulk-approve | country_admin, moderator, super_admin |
| POST | /api/admin/moderation/bulk-reject | country_admin, moderator, super_admin |
| GET | /api/admin/moderation/listings/{listing_id} | country_admin, moderator, super_admin |
| GET | /api/admin/moderation/queue | country_admin, moderator, super_admin |
| GET | /api/admin/moderation/queue/count | country_admin, moderator, super_admin |
| GET | /api/admin/payments | super_admin, finance |
| GET | /api/admin/plans | super_admin, finance |
| POST | /api/admin/plans | super_admin, finance |
| GET | /api/admin/plans/{plan_id} | super_admin, finance |
| PUT | /api/admin/plans/{plan_id} | super_admin, finance |
| POST | /api/admin/plans/{plan_id}/archive | super_admin, finance |
| POST | /api/admin/plans/{plan_id}/toggle-active | super_admin, finance |
| GET | /api/admin/reports | super_admin, country_admin, moderator |
| GET | /api/admin/reports/{report_id} | super_admin, country_admin, moderator |
| POST | /api/admin/reports/{report_id}/status | super_admin, country_admin, moderator |
| GET | /api/admin/session/health | support, ROLE_AUDIT_VIEWER, finance, moderator, country_admin, campaigns_supervisor, campaigns_admin, super_admin |
| GET | /api/admin/system-settings | super_admin, country_admin, support |
| POST | /api/admin/system-settings | super_admin |
| GET | /api/admin/system-settings/cloudflare | super_admin |
| POST | /api/admin/system-settings/cloudflare | super_admin |
| POST | /api/admin/system-settings/cloudflare/canary | super_admin |
| PATCH | /api/admin/system-settings/{setting_id} | super_admin |
| GET | /api/admin/system/health-detail | support, ROLE_AUDIT_VIEWER, finance, moderator, country_admin, campaigns_supervisor, campaigns_admin, super_admin |
| GET | /api/admin/system/health-summary | support, ROLE_AUDIT_VIEWER, finance, moderator, country_admin, campaigns_supervisor, campaigns_admin, super_admin |
| GET | /api/admin/tax-rates | super_admin, finance |
| POST | /api/admin/tax-rates | super_admin, finance |
| DELETE | /api/admin/tax-rates/{tax_id} | super_admin, finance |
| PATCH | /api/admin/tax-rates/{tax_id} | super_admin, finance |
| GET | /api/admin/users | super_admin |
| POST | /api/admin/users | super_admin |
| POST | /api/admin/users/bulk-deactivate | super_admin |
| DELETE | /api/admin/users/{user_id} | super_admin |
| PATCH | /api/admin/users/{user_id} | super_admin |
| POST | /api/admin/users/{user_id}/activate | super_admin, moderator |
| GET | /api/admin/users/{user_id}/detail | super_admin, country_admin, support |
| POST | /api/admin/users/{user_id}/suspend | super_admin, moderator |
| POST | /api/admin/vehicle-import/apply | super_admin, country_admin, moderator |
| POST | /api/admin/vehicle-import/dry-run | super_admin, country_admin, moderator |
| GET | /api/admin/vehicle-makes | super_admin, country_admin, moderator |
| POST | /api/admin/vehicle-makes | super_admin, country_admin, moderator |
| DELETE | /api/admin/vehicle-makes/{make_id} | super_admin, country_admin, moderator |
| PATCH | /api/admin/vehicle-makes/{make_id} | super_admin, country_admin, moderator |
| GET | /api/admin/vehicle-models | super_admin, country_admin, moderator |
| POST | /api/admin/vehicle-models | super_admin, country_admin, moderator |
| DELETE | /api/admin/vehicle-models/{model_id} | super_admin, country_admin, moderator |
| PATCH | /api/admin/vehicle-models/{model_id} | super_admin, country_admin, moderator |
| POST | /api/admin/webhooks/events/{event_id}/replay | super_admin, finance |
| POST | /api/v1/admin/vehicle-master/activate | super_admin, country_admin |
| POST | /api/v1/admin/vehicle-master/rollback | super_admin, country_admin |
| GET | /api/v1/admin/vehicle-master/status | super_admin, country_admin |
| POST | /api/v1/admin/vehicle-master/validate | super_admin, country_admin |
