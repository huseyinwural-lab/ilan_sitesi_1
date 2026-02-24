# MONGO_INVENTORY

**Son güncelleme:** 2026-02-24 00:24:40 UTC

## Koleksiyon Envanteri
| Koleksiyon | Status | Kullanım (satır) | Endpointler |
|---|---|---|---|
| admin_invites | DONE | - | - |
| attributes | DONE | - | - |
| audit_logs | TODO | 755, 4442, 4486, 4492, 4967, 5038 | DELETE /admin/tax-rates/{tax_id}, GET /admin/audit-logs, GET /admin/audit-logs/actions, GET /admin/audit-logs/event-types, GET /admin/audit-logs/export, GET /admin/audit-logs/resources, GET /admin/audit-logs/{log_id}, GET /admin/dealers/{dealer_id}/audit-logs, GET /admin/individual-users/export/csv, GET /admin/users/{user_id}/detail, GET /audit-logs, PATCH /admin/tax-rates/{tax_id}, PATCH /countries/{country_id}, PATCH /users/{user_id}, POST /admin/dealer-applications/{app_id}/approve, POST /admin/dealer-applications/{app_id}/reject, POST /admin/dealers/{dealer_id}/plan, POST /admin/dealers/{dealer_id}/status, POST /admin/individual-applications/{app_id}/approve, POST /admin/individual-applications/{app_id}/reject, POST /admin/tax-rates, POST /admin/users/{user_id}/activate, POST /admin/users/{user_id}/suspend, POST /reports |
| categories | TODO | 12054 | GET /admin/listings |
| categories_versions | DONE | - | - |
| countries | TODO | 8754, 9274, 9290 | GET /countries, PATCH /countries/{country_id} |
| dealer_applications | TODO | 8949, 8952, 9006, 9051, 9081, 9141 | GET /admin/dealer-applications, POST /admin/dealer-applications/{app_id}/approve, POST /admin/dealer-applications/{app_id}/reject |
| individual_applications | TODO | 8980, 8982, 9170, 9194, 9229, 9239 | GET /admin/individual-applications, POST /admin/individual-applications/{app_id}/approve, POST /admin/individual-applications/{app_id}/reject |
| menu_items | DONE | - | - |
| menu_top_items | DONE | - | - |
| plans | TODO | 5188, 7742, 8030, 8717, 8742, 8809 | GET /admin/dealers, GET /admin/dealers/{dealer_id}, GET /admin/individual-users, GET /admin/users/{user_id}/detail |
| push_subscriptions | TODO | 579, 589, 6536, 6567, 6585 | GET /v1/push/subscriptions, POST /v1/push/subscribe, POST /v1/push/unsubscribe |
| reports | TODO | 11749, 11788, 11803, 12209, 12263, 12306 | GET /admin/reports, GET /admin/reports/{report_id}, POST /reports |
| system_settings | DONE | - | - |
| tax_rates | TODO | 13883, 13931, 13948, 13981, 13984, 13997 | DELETE /admin/tax-rates/{tax_id}, GET /admin/tax-rates, PATCH /admin/tax-rates/{tax_id}, POST /admin/tax-rates |
| users | TODO | 624, 724, 1207, 1212, 1227, 1252 | DELETE /admin/users/{user_id}, GET /admin/dealers, GET /admin/dealers/{dealer_id}, GET /admin/dealers/{dealer_id}/audit-logs, GET /admin/individual-users, GET /admin/individual-users/export/csv, GET /admin/listings, GET /admin/reports, GET /admin/reports/{report_id}, GET /admin/users/{user_id}/detail, GET /dashboard/stats, GET /users, PATCH /users/{user_id}, POST /admin/dealer-applications/{app_id}/approve, POST /admin/dealers/{dealer_id}/plan, POST /admin/dealers/{dealer_id}/status, POST /admin/individual-applications/{app_id}/approve, POST /admin/users/{user_id}/activate, POST /admin/users/{user_id}/suspend |
| vehicle_listings | TODO | 5160, 7733, 8021, 8708, 9789, 9848 | GET /admin/dealers, GET /admin/individual-users, GET /admin/listings, GET /admin/reports, GET /admin/reports/{report_id}, GET /admin/users/{user_id}/detail, POST /admin/listings/{listing_id}/force-unpublish, POST /reports |
| vehicle_makes | DONE | - | - |
| vehicle_models | DONE | - | - |

## TODO (Kanonik Backlog)
- audit_logs
- categories
- countries
- dealer_applications
- individual_applications
- plans
- push_subscriptions
- reports
- tax_rates
- users
- vehicle_listings

## Mongo Env Değişkenleri
- MONGO_URL (backend/.env) **(platform kısıtı nedeniyle anahtar silinmedi)**
- DB_NAME (backend/.env) **(platform kısıtı nedeniyle anahtar silinmedi)**

## Mongo Bağımlılıkları
- pymongo (kaldırılacak)

## Mongo Dokümantasyon/Notlar
- /app/docs/notifications-mongo.md
- /app/memory/MONGO_DEPENDENCY_REPORT.md