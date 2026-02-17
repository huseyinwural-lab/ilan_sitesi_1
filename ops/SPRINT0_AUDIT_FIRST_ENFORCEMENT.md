# SPRINT0_AUDIT_FIRST_ENFORCEMENT

## Amaç
Tüm admin mutasyonlarında **audit-first** kuralını zorunlu hale getirmek ve country-scope enforcement’ı standardize etmek.

---

## 1) Audit-first kuralı
Mutasyon yapan tüm admin endpoint’lerinde:
- Audit insert başarısızsa **işlem commit edilmez**.

### Uygulama stratejisi (Mongo)
Mongo tek-node ortamında multi-doc transaction bulunmayabilir.
Bu nedenle şu pattern zorunludur:
1) Audit kaydını **önce** `applied=false` ile insert et
2) Mutasyon update’ini uygula
3) Audit kaydını `applied=true` ile işaretle

Bu sayede audit insert fail ederse update hiç başlamaz.

---

## 2) Country-scope enforcement standardı
- Admin context **URL query** ile gelir: `?country=XX` (source-of-truth)
- Backend `resolve_admin_country_context` ile:
  - country validate
  - country_scope RBAC enforce

### Mutasyonlar
- Country-mode’da yapılan tüm domain mutasyonları (dealer status, application approve/reject, invoice status, tax-rate CRUD, plan CRUD, listing unpublish, report lifecycle vb.)
  - request context üzerinden country_code üretir
  - scope dışı işlem → 403

---

## 3) Audit event tipleri
- `event_type` taxonomy: `/app/architecture/AUDIT_EVENT_TYPES_V1.md`
- Domain bazlı event_type’lar Sprint’lerde eklenecek (örn. DEALER_STATUS_CHANGE).
