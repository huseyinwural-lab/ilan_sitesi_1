# SQL_SCHEMA_GAP_REPORT

**Son güncelleme:** 2026-02-23 23:44:57 UTC

## Eksik Tablo/Şema
| Mongo Koleksiyon | Eksik SQL Tablo |
|---|---|
| audit_logs | audit_logs |
| attributes | attribute_options |
| attributes | category_attribute_map |
| menu_items | top_menu_sections |
| menu_items | top_menu_links |
| tax_rates | vat_rates |
| push_subscriptions | user_devices |
| vehicle_models | vehicle_models |

## Notlar
- system_settings + admin_invites tabloları oluşturulmalı.
- reports için support_messages yeterli değilse yeni tablo gerekir.