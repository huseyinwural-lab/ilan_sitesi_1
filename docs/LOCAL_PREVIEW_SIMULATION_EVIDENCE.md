# LOCAL_PREVIEW_SIMULATION_EVIDENCE

**Tarih:** 2026-02-22 00:54:38 UTC
**Durum:** PASS (local DB hazır, preview strict mode simüle edildi)

## 1) Local Preview Strict Mode — localhost forbidden
Komut:
```
APP_ENV=preview DB_SSL_MODE=require DATABASE_URL=postgresql://localhost:5432/admin_panel python -c "import server"
```
Çıktı:
```
RuntimeError: CONFIG_MISSING: DATABASE_URL
```

## 2) DB_SSL_MODE=require zorunlu
Komut:
```
APP_ENV=preview DB_SSL_MODE=disable DATABASE_URL=postgresql://db.example:5432/admin_panel python -c "import server"
```
Çıktı:
```
RuntimeError: DB_SSL_MODE must be require for preview/prod
```

## 3) Preview mode + valid host ile import OK
Komut:
```
APP_ENV=preview DB_SSL_MODE=require DATABASE_URL=postgresql://db.example:5432/admin_panel python -c "import server; print('import_ok')"
```
Çıktı:
```
import_ok
```

## Not
Local Postgres servisi/binary bulunmadığı için gerçek DB bağlantı testi yapılamadı.
