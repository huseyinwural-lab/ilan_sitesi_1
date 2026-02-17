# AUTH_ROLE_CONTRACT

## Token / User Contract

### Token claim alanları (MVP)
- `role`: string
- `country_scope`: string[] (örn: ['*'] veya ['DE'])
- `country_code`: string (default/UX)
- `permissions`: opsiyonel (future)

> Bu repo’da auth response `user` objesi ile birlikte dönüyor; UI role gate `user.role` kullanıyor.

## Portal eligibility

### allowed_portals
- `super_admin` → backoffice
- `country_admin` → backoffice
- `moderator` → backoffice (moderation scope)
- `finance` / `finance_admin` → backoffice (finance scope)
- `support` / `support_admin` → backoffice (support scope)
- `dealer` → dealer
- `individual` → public/individual

## Yanlış portal davranışı
- Auth yoksa: **401** → redirect ilgili portal login
- Auth var ama portal eligibility yoksa: **403** → redirect kullanıcının default home’una
- Mesaj: “Bu alana erişim yetkiniz yok.”
