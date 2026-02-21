# Mongo Endpoint Inventory (server.py)

| Endpoint | Domain | Model | Function |
|---|---|---|---|
| `/admin/attributes` | Attributes | Attribute | `admin_create_attribute` |
| `/admin/attributes` | Attributes | Attribute | `admin_list_attributes` |
| `/admin/attributes/{attribute_id}` | Attributes | Attribute | `admin_delete_attribute` |
| `/admin/attributes/{attribute_id}` | Attributes | Attribute | `admin_update_attribute` |
| `/admin/audit-logs` | Audit | AuditLog | `admin_list_audit_logs` |
| `/admin/audit-logs/actions` | Audit | AuditLog | `admin_audit_actions` |
| `/admin/audit-logs/event-types` | Audit | AuditLog | `admin_audit_event_types` |
| `/admin/audit-logs/export` | Audit | AuditLog | `admin_export_audit_logs` |
| `/admin/audit-logs/resources` | Audit | AuditLog | `admin_audit_resources` |
| `/admin/audit-logs/{log_id}` | Audit | AuditLog | `admin_audit_log_detail` |
| `/admin/campaigns` | Monetization/Campaigns | Campaign | `create_campaign` |
| `/admin/campaigns/{campaign_id}` | Monetization/Campaigns | Campaign | `archive_campaign` |
| `/admin/campaigns/{campaign_id}` | Monetization/Campaigns | Campaign | `get_campaign_detail` |
| `/admin/campaigns/{campaign_id}` | Monetization/Campaigns | Campaign | `update_campaign` |
| `/admin/campaigns/{campaign_id}/activate` | Monetization/Campaigns | Campaign | `activate_campaign` |
| `/admin/campaigns/{campaign_id}/archive` | Monetization/Campaigns | Campaign | `archive_campaign_action` |
| `/admin/campaigns/{campaign_id}/pause` | Monetization/Campaigns | Campaign | `pause_campaign` |
| `/admin/categories/import-export/publish` | Other | TBD | `admin_publish_category_import_batch` |
| `/admin/countries` | Countries | Country | `admin_create_country` |
| `/admin/countries` | Countries | Country | `admin_list_countries` |
| `/admin/countries/{code}` | Countries | Country | `admin_delete_country` |
| `/admin/countries/{code}` | Countries | Country | `admin_get_country` |
| `/admin/countries/{code}` | Countries | Country | `admin_update_country` |
| `/admin/dashboard/country-compare` | Other | TBD | `admin_dashboard_country_compare` |
| `/admin/dashboard/country-compare/export/csv` | Other | TBD | `admin_dashboard_country_compare_export_csv` |
| `/admin/dashboard/export/pdf` | Other | TBD | `admin_dashboard_export_pdf` |
| `/admin/dashboard/summary` | Other | TBD | `admin_dashboard_summary` |
| `/admin/dealer-applications` | Dealer Applications | DealerApplication | `admin_list_dealer_applications` |
| `/admin/dealer-applications/{app_id}/approve` | Dealer Applications | DealerApplication | `admin_approve_dealer_application` |
| `/admin/dealer-applications/{app_id}/reject` | Dealer Applications | DealerApplication | `admin_reject_dealer_application` |
| `/admin/dealers` | Dealer Management | Dealer/DealerProfile | `admin_list_dealers` |
| `/admin/dealers/{dealer_id}` | Dealer Management | Dealer/DealerProfile | `admin_get_dealer_detail` |
| `/admin/dealers/{dealer_id}/audit-logs` | Dealer Management | Dealer/DealerProfile | `admin_get_dealer_audit_logs` |
| `/admin/dealers/{dealer_id}/plan` | Dealer Management | Dealer/DealerProfile | `admin_assign_dealer_plan` |
| `/admin/dealers/{dealer_id}/status` | Dealer Management | Dealer/DealerProfile | `admin_set_dealer_status` |
| `/admin/finance/revenue` | Monetization/Finance | Invoice/Payment | `admin_revenue` |
| `/admin/individual-applications` | Support/Applications | Application | `admin_list_individual_applications` |
| `/admin/individual-applications/{app_id}/approve` | Support/Applications | Application | `admin_approve_individual_application` |
| `/admin/individual-applications/{app_id}/reject` | Support/Applications | Application | `admin_reject_individual_application` |
| `/admin/individual-users` | Other | TBD | `list_individual_users` |
| `/admin/individual-users/export/csv` | Other | TBD | `admin_individual_users_export_csv` |
| `/admin/invite/accept` | Other | TBD | `admin_invite_accept` |
| `/admin/invite/preview` | Other | TBD | `admin_invite_preview` |
| `/admin/listings` | Other | TBD | `admin_listings` |
| `/admin/listings/{listing_id}/approve` | Other | TBD | `admin_approve_listing` |
| `/admin/listings/{listing_id}/force-unpublish` | Other | TBD | `admin_force_unpublish_listing` |
| `/admin/listings/{listing_id}/needs_revision` | Other | TBD | `admin_needs_revision_listing` |
| `/admin/listings/{listing_id}/reject` | Other | TBD | `admin_reject_listing` |
| `/admin/listings/{listing_id}/soft-delete` | Other | TBD | `admin_soft_delete_listing` |
| `/admin/menu-items` | Navigation/Menu | TopMenuItem | `admin_create_menu_item` |
| `/admin/menu-items/{menu_id}` | Navigation/Menu | TopMenuItem | `admin_delete_menu_item` |
| `/admin/menu-items/{menu_id}` | Navigation/Menu | TopMenuItem | `admin_update_menu_item` |
| `/admin/moderation/listings/{listing_id}` | Moderation | ModerationQueue/Listing | `moderation_listing_detail` |
| `/admin/moderation/queue` | Moderation | ModerationQueue/Listing | `moderation_queue` |
| `/admin/moderation/queue/count` | Moderation | ModerationQueue/Listing | `moderation_queue_count` |
| `/admin/reports` | Reports | Report | `admin_reports` |
| `/admin/reports/{report_id}` | Reports | Report | `admin_report_detail` |
| `/admin/reports/{report_id}/status` | Reports | Report | `admin_report_status_change` |
| `/admin/system-settings` | System Settings | SystemSetting | `admin_create_system_setting` |
| `/admin/system-settings` | System Settings | SystemSetting | `admin_list_system_settings` |
| `/admin/system-settings/{setting_id}` | System Settings | SystemSetting | `admin_update_system_setting` |
| `/admin/tax-rates` | Monetization/Tax | TaxRate | `admin_create_tax_rate` |
| `/admin/tax-rates` | Monetization/Tax | TaxRate | `admin_list_tax_rates` |
| `/admin/tax-rates/{tax_id}` | Monetization/Tax | TaxRate | `admin_delete_tax_rate` |
| `/admin/tax-rates/{tax_id}` | Monetization/Tax | TaxRate | `admin_update_tax_rate` |
| `/admin/users` | Admin Users | User | `create_admin_user` |
| `/admin/users` | Admin Users | User | `list_admin_users` |
| `/admin/users/bulk-deactivate` | Admin Users | User | `bulk_deactivate_admins` |
| `/admin/users/{user_id}` | Admin Users | User | `delete_user` |
| `/admin/users/{user_id}` | Admin Users | User | `update_admin_user` |
| `/admin/users/{user_id}/activate` | Admin Users | User | `activate_user` |
| `/admin/users/{user_id}/detail` | Admin Users | User | `admin_user_detail` |
| `/admin/users/{user_id}/suspend` | Admin Users | User | `suspend_user` |
| `/admin/vehicle-import/apply` | Vehicle MDM | VehicleMake/Model | `admin_vehicle_import_apply` |
| `/admin/vehicle-import/dry-run` | Vehicle MDM | VehicleMake/Model | `admin_vehicle_import_dry_run` |
| `/admin/vehicle-makes` | Vehicle MDM | VehicleMake/Model | `admin_create_vehicle_make` |
| `/admin/vehicle-makes` | Vehicle MDM | VehicleMake/Model | `admin_list_vehicle_makes` |
| `/admin/vehicle-makes/{make_id}` | Vehicle MDM | VehicleMake/Model | `admin_delete_vehicle_make` |
| `/admin/vehicle-makes/{make_id}` | Vehicle MDM | VehicleMake/Model | `admin_update_vehicle_make` |
| `/admin/vehicle-models` | Vehicle MDM | VehicleMake/Model | `admin_create_vehicle_model` |
| `/admin/vehicle-models` | Vehicle MDM | VehicleMake/Model | `admin_list_vehicle_models` |
| `/admin/vehicle-models/{model_id}` | Vehicle MDM | VehicleMake/Model | `admin_delete_vehicle_model` |
| `/admin/vehicle-models/{model_id}` | Vehicle MDM | VehicleMake/Model | `admin_update_vehicle_model` |
| `/attributes` | Attributes | Attribute | `public_attributes` |
| `/audit-logs` | Audit | AuditLog | `list_audit_logs` |
| `/countries` | Countries | Country | `list_countries` |
| `/countries/{country_id}` | Countries | Country | `update_country` |
| `/dashboard/stats` | Admin Dashboard | Metrics | `get_dashboard_stats` |
| `/health` | Other | TBD | `health_check` |
| `/menu/top-items` | Navigation/Menu | TopMenuItem | `get_top_menu_items` |
| `/menu/top-items/{item_id}` | Navigation/Menu | TopMenuItem | `toggle_menu_item` |
| `/reports` | Reports | Report | `create_report` |
| `/system-settings/effective` | System Settings | SystemSetting | `system_settings_effective` |
| `/users` | Users | User | `list_users` |
| `/users/change-password` | Users | User | `change_password` |
| `/users/me` | Users | User | `update_user_profile` |
| `/users/me/export` | Users | User | `export_user_data` |
| `/users/{user_id}` | Users | User | `update_user` |
| `/v1/push/subscribe` | Notifications | PushSubscription | `subscribe_push_notifications` |
| `/v1/push/subscriptions` | Notifications | PushSubscription | `list_push_subscriptions` |
| `/v1/push/unsubscribe` | Notifications | PushSubscription | `unsubscribe_push_notifications` |
| `/v1/vehicle/makes` | Vehicle MDM | VehicleMake/Model | `public_vehicle_makes` |
| `/v1/vehicle/models` | Vehicle MDM | VehicleMake/Model | `public_vehicle_models` |
| `/v2/search` | Search | SearchIndex | `public_search_v2` |
| `/ws/messages` | Other | TBD | `websocket_messages` |