# MONGO_TO_SQL_MAP

**Son güncelleme:** 2026-02-24 00:36:08 UTC

| Mongo Koleksiyon | Status | Endpointler | SQL Tablo(lar) | Notlar |
|---|---|---|---|---|
| admin_invites | DONE | - | admin_invites | Admin invite token management |
| attributes | DONE | - | attributes, attribute_options, category_attribute_map | Attribute definitions |
| audit_logs | TODO | GET /admin/audit-logs, GET /admin/audit-logs/actions, GET /admin/audit-logs/event-types, GET /admin/audit-logs/export, GET /admin/audit-logs/resources, GET /admin/audit-logs/{log_id}, GET /admin/dealers/{dealer_id}/audit-logs, GET /admin/individual-users/export/csv, GET /admin/users/{user_id}/detail, GET /audit-logs, PATCH /countries/{country_id}, PATCH /users/{user_id}, POST /admin/dealer-applications/{app_id}/approve, POST /admin/dealer-applications/{app_id}/reject, POST /admin/dealers/{dealer_id}/plan, POST /admin/dealers/{dealer_id}/status, POST /admin/individual-applications/{app_id}/approve, POST /admin/individual-applications/{app_id}/reject, POST /admin/users/{user_id}/activate, POST /admin/users/{user_id}/suspend | audit_logs | Audit logs |
| categories | TODO | GET /admin/listings | categories | Category tree |
| categories_versions | DONE | - | category_schema_versions | Category schema versions |
| countries | TODO | GET /countries, PATCH /countries/{country_id} | countries | Country master |
| dealer_applications | TODO | GET /admin/dealer-applications, POST /admin/dealer-applications/{app_id}/approve, POST /admin/dealer-applications/{app_id}/reject | dealer_applications | Dealer applications |
| individual_applications | TODO | GET /admin/individual-applications, POST /admin/individual-applications/{app_id}/approve, POST /admin/individual-applications/{app_id}/reject | applications | Individual applications |
| menu_items | DONE | - | menu_items | Admin menu items |
| menu_top_items | DONE | - | top_menu_items | Public top menu |
| plans | TODO | GET /admin/dealers, GET /admin/dealers/{dealer_id}, GET /admin/individual-users, GET /admin/users/{user_id}/detail | plans | Plans |
| push_subscriptions | TODO | GET /v1/push/subscriptions, POST /v1/push/subscribe, POST /v1/push/unsubscribe | user_devices | Push subscriptions |
| reports | DONE | - | reports | Listing reports |
| system_settings | DONE | - | system_settings | System settings KV |
| tax_rates | DONE | - | vat_rates | Tax/VAT rates |
| users | TODO | DELETE /admin/users/{user_id}, GET /admin/dealers, GET /admin/dealers/{dealer_id}, GET /admin/dealers/{dealer_id}/audit-logs, GET /admin/individual-users, GET /admin/individual-users/export/csv, GET /admin/listings, GET /admin/users/{user_id}/detail, GET /dashboard/stats, GET /users, PATCH /users/{user_id}, POST /admin/dealer-applications/{app_id}/approve, POST /admin/dealers/{dealer_id}/plan, POST /admin/dealers/{dealer_id}/status, POST /admin/individual-applications/{app_id}/approve, POST /admin/users/{user_id}/activate, POST /admin/users/{user_id}/suspend | users | User accounts |
| vehicle_listings | TODO | GET /admin/dealers, GET /admin/individual-users, GET /admin/listings, GET /admin/users/{user_id}/detail, POST /admin/listings/{listing_id}/force-unpublish | listings | Listings |
| vehicle_makes | DONE | - | vehicle_makes | Vehicle makes |
| vehicle_models | DONE | - | vehicle_models | Vehicle models |