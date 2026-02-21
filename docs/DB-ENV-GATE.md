# DB-ENV-GATE (Ops Gate-0)

## Amaç
Preview/Prod ortamlarında **DATABASE_URL** sağlanmadan deploy **bloklanır**. Geliştirme yalnızca lokal/CI/staging üzerinde ilerler.

## Zorunlu Environment Değişkenleri
### Preview / Prod
- **DATABASE_URL** (zorunlu)
- **DB_SSL_MODE=require** (zorunlu)
- **ECB_DAILY_URL** (zorunlu)
- **ECB_CACHE_TTL_SECONDS** (zorunlu,  olmayan pozitif)

### Lokal / CI / Staging
- **DATABASE_URL** (lokal/staging hedefi)
- **DB_SSL_MODE=disable** (lokal için önerilir)
- **ECB_DAILY_URL**
- **ECB_CACHE_TTL_SECONDS**

## Deploy Gate Kuralı
- `APP_ENV=prod` iken **DATABASE_URL yoksa deploy PASSED OLMAMALI**.
- `DB_SSL_MODE=require` zorunlu.
- `DATABASE_URL` localhost ya da placeholder olmamalı.

## Kontrol
- Script: `backend/scripts/deploy_gate_check.py`
- Çıktı: Alembic head ile DB migration revizyonu eşleşmeli.

## Notlar
- Ops bağımlılığı net: DATABASE_URL sağlanana kadar preview/prod deploy **kapalı**.
- Staging ortamı, migrations ve smoke testler için kullanılmalıdır.
