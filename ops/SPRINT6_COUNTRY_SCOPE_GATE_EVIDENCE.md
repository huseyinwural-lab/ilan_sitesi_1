## Sprint 6 — Country-Scope Gate Evidence

### Country Admin scope doğrulama (DE)
```bash
# DE → OK
curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $COUNTRY_ADMIN" \
  "${BASE}/api/admin/categories?country=DE"

# FR → 403
curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $COUNTRY_ADMIN" \
  "${BASE}/api/admin/categories?country=FR"

# FR (vehicle-makes) → 403
curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $COUNTRY_ADMIN" \
  "${BASE}/api/admin/vehicle-makes?country=FR"
```
**Sonuç:** DE=200, FR=403

### Invalid / Missing param davranışı
```bash
# Invalid country → 400
curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $COUNTRY_ADMIN" \
  "${BASE}/api/admin/categories?country=ZZ"

# Missing country (default scope) → 200
curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $COUNTRY_ADMIN" \
  "${BASE}/api/admin/categories"
```
**Sonuç:** invalid=400, missing=200 (default scope)
