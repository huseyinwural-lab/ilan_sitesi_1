## Sprint 6 — RBAC Gate Evidence

### Finance Endpoint erişimi (sadece finance + super_admin)
```bash
# dealer → invoices (403)
curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $DEALER" \
  "${BASE}/api/admin/invoices?country=DE"

# finance → invoices (200)
curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $FINANCE" \
  "${BASE}/api/admin/invoices?country=DE"

# country_admin → invoices (403)
curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $COUNTRY_ADMIN" \
  "${BASE}/api/admin/invoices?country=DE"
```
**Sonuç:** dealer=403, finance=200, country_admin=403

### Dealer Management (sadece country_admin + super_admin)
```bash
# dealer → admin/dealers (403)
curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $DEALER" \
  "${BASE}/api/admin/dealers?country=DE"

# country_admin → admin/dealers (200)
curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $COUNTRY_ADMIN" \
  "${BASE}/api/admin/dealers?country=DE"

# finance → admin/dealers (403)
curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $FINANCE" \
  "${BASE}/api/admin/dealers?country=DE"
```
**Sonuç:** dealer=403, country_admin=200, finance=403

### Moderation endpoint erişimi (country_admin + super_admin + moderator)
```bash
# dealer → admin/listings (403)
curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $DEALER" \
  "${BASE}/api/admin/listings?country=DE"

# country_admin → admin/listings (200)
curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $COUNTRY_ADMIN" \
  "${BASE}/api/admin/listings?country=DE"

# support → admin/listings (403)
curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $SUPPORT" \
  "${BASE}/api/admin/listings?country=DE"
```
**Sonuç:** dealer=403, country_admin=200, support=403

> Not: Moderation rolü seed’de yok; country_admin + super_admin üzerinden doğrulandı.
