## Sprint 3 Plan Lock — Finance Domain

### Kapsam
1) Invoice Engine (entity + admin API + revenue)
2) Tax Rate Engine (CRUD)
3) Plan Engine (CRUD)
4) Dealer ↔ Plan ↔ Invoice entegrasyonu
5) Admin UI wiring (invoices, tax-rates, plans)
6) Audit taxonomy güncelleme
7) E2E kanıt paketi

### Kabul Kriterleri (Özet)
- Invoice list/detail/status + create endpoint çalışır, country-scope zorunlu
- Revenue endpoint: paid invoices sum (UTC, end_date inclusive)
- TaxRate & Plan CRUD audit-first + soft delete
- Dealer detail sayfası: aktif plan + son invoice + unpaid count
- UI: /admin/invoices, /admin/tax-rates, /admin/plans
- Audit event types: INVOICE_STATUS_CHANGE, TAX_RATE_CHANGE, PLAN_CHANGE, ADMIN_PLAN_ASSIGNMENT
