# CHECK_ADMIN_DOMAIN_BLOCKS

## Amaç
Admin panel domain bloklarına göre mevcut durum + gap listesi.

## Dashboard
- Mevcut: `Dashboard.js` + `/api/dashboard/stats`
- [ ] Global KPI: PARTIAL (users/countries/feature_flags placeholder)
- [ ] Country karşılaştırma: FAIL (yakında)
- [ ] Moderation sayısı: FAIL (endpoint/UI yok)
- [ ] Revenue overview: FAIL

## Kullanıcı & Dealer
- Users listesi: ✅ (UI + /api/users)
- Dealer listesi: FAIL (UI var gibi ama backend bağ yok)
- Onboarding akışı: FAIL

## İlan & Moderasyon
- Moderation Queue: UI sayfası var, route yok (gap)
- Report edilen ilanlar: FAIL
- Admin ilan arama: FAIL

## Finans
- Plans UI: `/admin/plans` var
- Invoices UI: mevcut sayfa var (Invoices.js) ama App.js route yok (gap)
- Billing UI: `/admin/billing` var
- Tax Rates UI: sayfa var ama route yok (gap)
- Revenue dashboard: FAIL

## Master Data
- Categories yönetimi: ✅
- Attributes yönetimi: ✅
- Vehicle JSON import: ✅ (AdminVehicleMDM + backend v1/admin/vehicle-master)
- Menü yönetimi: sayfa var (MenuManager.js) ama route yok (gap)

## Sistem
- Countries yönetimi: ✅
- Feature flags: ✅
- Audit logs: sayfa var (AuditLogs.js) ama route yok (gap)

## PASS/PARTIAL/FAIL (Ön karar)
- Admin: PARTIAL (çekirdek MDM + countries + users var; moderation/finance/audit eksik)
