## Sprint 6 — Audit Coverage Evidence

Audit log doğrulaması:
```bash
curl -H "Authorization: Bearer $ADMIN" \
  "${BASE}/api/audit-logs?event_type=<EVENT>&limit=1"
```

| Event Type | Observed Count | Notlar |
| --- | --- | --- |
| FAILED_LOGIN | 1 | Seed log mevcut |
| RATE_LIMIT_BLOCK | 1 | Seed log mevcut |
| ADMIN_ROLE_CHANGE | 1 | Rol güncelleme testleri |
| UNAUTHORIZED_ROLE_CHANGE_ATTEMPT | 0 | Permission guard handler’a düşmedi (log üretimi yok) |
| MODERATION_APPROVE | 1 | Listing approve aksiyonu |
| MODERATION_REJECT | 1 | Listing reject aksiyonu |
| MODERATION_NEEDS_REVISION | 1 | Listing needs_revision aksiyonu |
| LISTING_SOFT_DELETE | 1 | Admin soft-delete |
| LISTING_FORCE_UNPUBLISH | 1 | Admin force-unpublish |
| DEALER_STATUS_CHANGE | 1 | Dealer status update |
| DEALER_APPLICATION_APPROVED | 1 | Seed log mevcut |
| DEALER_APPLICATION_REJECTED | 1 | Seed log mevcut |
| REPORT_STATUS_CHANGE | 1 | Report status change |
| INVOICE_STATUS_CHANGE | 1 | Invoice status paid |
| TAX_RATE_CHANGE | 1 | Tax rate update |
| PLAN_CHANGE | 1 | Plan update |
| ADMIN_PLAN_ASSIGNMENT | 1 | Dealer plan assign |
| COUNTRY_CHANGE | 1 | Country update |
| SYSTEM_SETTING_CHANGE | 1 | System setting update |
| CATEGORY_CHANGE | 1 | Category create |
| ATTRIBUTE_CHANGE | 1 | Attribute create |
| VEHICLE_MASTER_DATA_CHANGE | 1 | Vehicle make create |

> Not: UNAUTHORIZED_ROLE_CHANGE_ATTEMPT log’u, yetkisiz isteğin handler’a düşmemesinden dolayı gözlemlenemedi. Gerekirse middleware seviyesinde log’lanacak şekilde genişletilebilir.
