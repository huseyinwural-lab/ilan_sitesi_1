# MONGO_INVENTORY

**Son güncelleme:** 2026-02-24 10:43:01 UTC
**Durum:** CLOSED (Mongo runtime 0-iz)

## Koleksiyon Envanteri
| Koleksiyon | Status | Kullanım (satır) | Endpointler |
|---|---|---|---|
| admin_invites | DONE | - | - |
| attributes | DONE | - | - |
| audit_logs | DONE | 756, 4443, 4487, 4493, 4968, 5039 | GET /admin/audit-logs, GET /admin/audit-logs/actions, GET /admin/audit-logs/event-types, GET /admin/audit-logs/export, GET /admin/audit-logs/resources, GET /admin/audit-logs/{log_id}, GET /admin/dealers/{dealer_id}/audit-logs, GET /admin/individual-users/export/csv, GET /admin/users/{user_id}/detail, GET /audit-logs, PATCH /countries/{country_id}, PATCH /users/{user_id}, POST /admin/dealer-applications/{app_id}/approve, POST /admin/dealer-applications/{app_id}/reject, POST /admin/dealers/{dealer_id}/plan, POST /admin/dealers/{dealer_id}/status, POST /admin/individual-applications/{app_id}/approve, POST /admin/individual-applications/{app_id}/reject, POST /admin/users/{user_id}/activate, POST /admin/users/{user_id}/suspend |
| categories | DONE | 12042 | GET /admin/listings |
| categories_versions | DONE | - | - |
| countries | DONE | 8755, 9275, 9291 | GET /countries, PATCH /countries/{country_id} |
| dealer_applications | DONE | 8950, 8953, 9007, 9052, 9082, 9142 | GET /admin/dealer-applications, POST /admin/dealer-applications/{app_id}/approve, POST /admin/dealer-applications/{app_id}/reject |
| individual_applications | DONE | 8981, 8983, 9171, 9195, 9230, 9240 | GET /admin/individual-applications, POST /admin/individual-applications/{app_id}/approve, POST /admin/individual-applications/{app_id}/reject |
| menu_items | DONE | - | - |
| menu_top_items | DONE | - | - |
| plans | DONE | 5189, 7743, 8031, 8718, 8743, 8810 | GET /admin/dealers, GET /admin/dealers/{dealer_id}, GET /admin/individual-users, GET /admin/users/{user_id}/detail |
| push_subscriptions | DONE | 580, 590, 6537, 6568, 6586 | GET /v1/push/subscriptions, POST /v1/push/subscribe, POST /v1/push/unsubscribe |
| reports | DONE | - | - |
| system_settings | DONE | - | - |
| tax_rates | DONE | - | - |
| users | DONE | 625, 725, 1208, 1213, 1228, 1253 | DELETE /admin/users/{user_id}, GET /admin/dealers, GET /admin/dealers/{dealer_id}, GET /admin/dealers/{dealer_id}/audit-logs, GET /admin/individual-users, GET /admin/individual-users/export/csv, GET /admin/listings, GET /admin/users/{user_id}/detail, GET /dashboard/stats, GET /users, PATCH /users/{user_id}, POST /admin/dealer-applications/{app_id}/approve, POST /admin/dealers/{dealer_id}/plan, POST /admin/dealers/{dealer_id}/status, POST /admin/individual-applications/{app_id}/approve, POST /admin/users/{user_id}/activate, POST /admin/users/{user_id}/suspend |
| vehicle_listings | DONE | 5161, 7734, 8022, 8709, 9790, 9849 | GET /admin/dealers, GET /admin/individual-users, GET /admin/listings, GET /admin/users/{user_id}/detail, POST /admin/listings/{listing_id}/force-unpublish |
| vehicle_makes | DONE | - | - |
| vehicle_models | DONE | - | - |

## TODO (Kanonik Backlog)
- Yok

## Mongo Env Değişkenleri
- MONGO_URL (backend/.env) **(platform kısıtı nedeniyle anahtar silinmedi)**
- DB_NAME (backend/.env) **(platform kısıtı nedeniyle anahtar silinmedi)**

## Mongo Bağımlılıkları
- pymongo (kaldırıldı)

## Mongo Dokümantasyon/Notlar
- /app/legacy/mongo_archive (read-only arşiv)
- /app/docs/notifications-mongo.md
- /app/memory/MONGO_DEPENDENCY_REPORT.md