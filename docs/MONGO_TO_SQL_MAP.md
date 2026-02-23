# MONGO_TO_SQL_MAP

**Son güncelleme:** 2026-02-23 23:44:57 UTC

| Mongo Koleksiyon | SQL Tablo(lar) | Notlar |
|---|---|---|
| admin_invites | admin_invites | Yeni tablo (invite token hash, user_id FK). |
| system_settings | system_settings | KV + country_code + is_readonly + description. SystemConfig yerine yeni tablo önerisi. |
| users | users | role, country_scope, is_active, is_verified alanları eşleşir. |
| audit_logs | audit_logs | action/resource/metadata eşleşmesi (metadata_info). |
| countries | countries | Mongo active_flag → SQL is_enabled. |
| categories | categories | category translations ilişkisi korunmalı. |
| categories_versions | category_schema_versions | schema_version mapping. |
| attributes | attributes, attribute_options, category_attribute_map | attribute options ayrı tablo. |
| menu_items | top_menu_items, top_menu_sections, top_menu_links | menu hiyerarşisi SQL üçlü tablo. |
| menu_top_items | top_menu_items | top menu cache |
| dealer_applications | dealer_applications | status/reason alanları eşleşir. |
| individual_applications | applications | bireysel başvurular uygulama tablosu. |
| plans | plans | admin plan yönetimi. |
| tax_rates | vat_rates | tax_rates → vat_rates (country, rate, is_active). |
| push_subscriptions | user_devices | push token + platform eşleşmesi. |
| reports | support_messages | report modeli ile support mesaj ilişkisi; eksikse yeni tablo gerekebilir. |
| vehicle_listings | listings | listing temel alanlar + moderation queue ilişkisi. |
| vehicle_makes | vehicle_makes | MDM makes. |
| vehicle_models | vehicle_models | MDM models. |