# MONGO_INVENTORY

**Son güncelleme:** 2026-02-23 23:44:57 UTC

## Runtime Mongo Kullanımları (server.py)
Aşağıdaki koleksiyonlar server.py içinde `request.app.state.db` üzerinden kullanılıyor.

| Koleksiyon | Kullanım (satır) | Örnek endpointler |
|---|---|---|
| attributes | 11639, 16542, 16566, 16626, 16644, 16694, 16712, 16729 | DELETE /admin/attributes/{attribute_id}, GET /admin/attributes, GET /attributes, PATCH /admin/attributes/{attribute_id}, POST /admin/attributes |
| audit_logs | 751, 4419, 4463, 4469, 4944, 5015, 5118, 5169 | DELETE /admin/attributes/{attribute_id}, DELETE /admin/menu-items/{menu_id}, DELETE /admin/tax-rates/{tax_id}, DELETE /admin/vehicle-makes/{make_id}, DELETE /admin/vehicle-models/{model_id}, GET /admin/audit-logs, GET /admin/audit-logs/actions, GET /admin/audit-logs/event-types, GET /admin/audit-logs/export, GET /admin/audit-logs/resources, GET /admin/audit-logs/{log_id}, GET /admin/dealers/{dealer_id}/audit-logs, GET /admin/individual-users/export/csv, GET /admin/users/{user_id}/detail, GET /audit-logs, PATCH /admin/attributes/{attribute_id}, PATCH /admin/menu-items/{menu_id}, PATCH /admin/tax-rates/{tax_id}, PATCH /admin/vehicle-makes/{make_id}, PATCH /admin/vehicle-models/{model_id}, PATCH /countries/{country_id}, PATCH /users/{user_id}, POST /admin/attributes, POST /admin/dealer-applications/{app_id}/approve, POST /admin/dealer-applications/{app_id}/reject, POST /admin/dealers/{dealer_id}/plan, POST /admin/dealers/{dealer_id}/status, POST /admin/individual-applications/{app_id}/approve, POST /admin/individual-applications/{app_id}/reject, POST /admin/menu-items, POST /admin/tax-rates, POST /admin/users/{user_id}/activate, POST /admin/users/{user_id}/suspend, POST /admin/vehicle-makes, POST /admin/vehicle-models, POST /reports |
| categories | 1580, 1595, 1604, 11995, 16588 | GET /admin/listings, POST /admin/attributes |
| categories_versions | 11077, 11094, 11097, 11102, 11114, 11121, 11262 | - |
| countries | 8706, 9226, 9242 | GET /countries, PATCH /countries/{country_id} |
| dealer_applications | 8901, 8904, 8958, 9003, 9033, 9093 | GET /admin/dealer-applications, POST /admin/dealer-applications/{app_id}/approve, POST /admin/dealer-applications/{app_id}/reject |
| individual_applications | 8932, 8934, 9122, 9146, 9181, 9191 | GET /admin/individual-applications, POST /admin/individual-applications/{app_id}/approve, POST /admin/individual-applications/{app_id}/reject |
| menu_items | 16359, 16383, 16387, 16417, 16431, 16449, 16468, 16488 | DELETE /admin/menu-items/{menu_id}, GET /admin/menu-items, PATCH /admin/menu-items/{menu_id}, POST /admin/menu-items |
| menu_top_items | 8110, 8129 | GET /menu/top-items, PATCH /menu/top-items/{item_id} |
| plans | 5165, 7719, 8007, 8669, 8694, 8761 | GET /admin/dealers, GET /admin/dealers/{dealer_id}, GET /admin/individual-users, GET /admin/users/{user_id}/detail |
| push_subscriptions | 575, 585, 6513, 6544, 6562 | GET /v1/push/subscriptions, POST /v1/push/subscribe, POST /v1/push/unsubscribe |
| reports | 11690, 11729, 11744, 12150, 12204, 12247, 12260 | GET /admin/reports, GET /admin/reports/{report_id}, POST /reports |
| tax_rates | 13824, 13872, 13889, 13922, 13925, 13938, 13962 | DELETE /admin/tax-rates/{tax_id}, GET /admin/tax-rates, PATCH /admin/tax-rates/{tax_id}, POST /admin/tax-rates |
| users | 620, 720, 1203, 1208, 1223, 1248, 1252, 1268 | DELETE /admin/users/{user_id}, GET /admin/dealers, GET /admin/dealers/{dealer_id}, GET /admin/dealers/{dealer_id}/audit-logs, GET /admin/individual-users, GET /admin/individual-users/export/csv, GET /admin/listings, GET /admin/reports, GET /admin/reports/{report_id}, GET /admin/users/{user_id}/detail, GET /dashboard/stats, GET /users, PATCH /users/{user_id}, POST /admin/dealer-applications/{app_id}/approve, POST /admin/dealers/{dealer_id}/plan, POST /admin/dealers/{dealer_id}/status, POST /admin/individual-applications/{app_id}/approve, POST /admin/users/{user_id}/activate, POST /admin/users/{user_id}/suspend |
| vehicle_listings | 5137, 7710, 7998, 8660, 9741, 9800, 9810, 10276 | GET /admin/dealers, GET /admin/individual-users, GET /admin/listings, GET /admin/reports, GET /admin/reports/{report_id}, GET /admin/users/{user_id}/detail, POST /admin/listings/{listing_id}/force-unpublish, POST /reports |
| vehicle_makes | 11646, 16757, 16771, 16838, 16856, 16891, 16909, 16926 | DELETE /admin/vehicle-makes/{make_id}, DELETE /admin/vehicle-models/{model_id}, GET /admin/vehicle-makes, GET /admin/vehicle-models, GET /v1/vehicle/makes, GET /v1/vehicle/models, PATCH /admin/vehicle-makes/{make_id}, PATCH /admin/vehicle-models/{model_id}, POST /admin/vehicle-import/apply, POST /admin/vehicle-makes, POST /admin/vehicle-models |
| vehicle_models | 11662, 16768, 16775, 16965, 17018, 17036, 17079, 17097 | DELETE /admin/vehicle-models/{model_id}, GET /admin/vehicle-makes, GET /admin/vehicle-models, GET /v1/vehicle/models, PATCH /admin/vehicle-models/{model_id}, POST /admin/vehicle-import/apply, POST /admin/vehicle-models |

## Mongo Env Değişkenleri
- `MONGO_URL` (backend/.env)
- `DB_NAME` (backend/.env)

## Mongo Bağımlılıkları
- `pymongo` (backend/requirements.txt)

## Legacy / Archive Mongo Scriptleri
- backfill_notifications.py
- campaigns_backfill_report.py
- migrate_listings_search_from_mongo.py
- migrate_moderation_from_mongo.py
- migrate_moderation_items_from_mongo.py
- rollback_moderation_to_mongo.sh
- run_moderation_items_parity.py
- run_moderation_parity.py
- run_search_reports.py
- seed_mongo_listings.py

## Mongo Dokümantasyon/Notlar
- /app/docs/notifications-mongo.md
- /app/memory/MONGO_DEPENDENCY_REPORT.md
