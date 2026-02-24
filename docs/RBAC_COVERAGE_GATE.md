# RBAC_COVERAGE_GATE

**Tarih:** 2026-02-24 12:01:16 UTC
**Durum:** ACTIVE (CI Hard Gate)

## Amaç
RBAC endpoint map kapsamı (RBAC_ENDPOINT_MAP.md) CI’da zorunlu kontrol edilir. Map’te olmayan admin endpointi release edilemez.

## CI Adımı
- Workflow: `.github/workflows/rbac-coverage.yml`
- Script: `backend/scripts/check_rbac_coverage.py`

## Komut
```
python backend/scripts/check_rbac_coverage.py
```

## Örnek Failure Çıktısı
```
RBAC COVERAGE FAIL: endpoints missing from RBAC_ENDPOINT_MAP
MISSING: GET /api/admin/applications/assignees
```

## Politika
- RBAC_ENDPOINT_MAP.md değişikliği **diff-onay** gerektirir.
- Yeni admin endpoint eklenirse map’e eklenmeden CI FAIL olur.
