## Sprint 6 — Non-Functional Gate

### Empty State / Loading
```bash
# Search empty
curl "${BASE}/api/v2/search?country=DE&price_min=9999999" # pagination.total=0

# Admin list empty
curl -H "Authorization: Bearer $ADMIN" \
  "${BASE}/api/admin/reports?country=DE&status=dismissed" # pagination.total=0
```

### 403 / 404 Kontrollü UI
- Dealer → /api/admin/invoices: **403** (RBAC gate’e referans)
- Country admin → /api/admin/categories?country=ZZ: **400** (invalid country)

### Draft Media / Draft Access Safety
```bash
curl -o /dev/null -w "%{http_code}" \
  "${BASE}/api/v1/listings/vehicle/1526e3d2-78c8-4a5f-bfb0-baa9ea8fbb27"
```
**Sonuç:** 403 (draft listing public erişime kapalı)
