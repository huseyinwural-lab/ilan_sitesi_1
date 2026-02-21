# SMOKE_FINAL01_STAGING

## Run (tek komut)
- `bash /app/scripts/smoke_final01_staging.sh`
- Output: `/app/ops/SMOKE_FINAL01_STAGING_EVIDENCE.md`

## Amaç
Staging ortamında hızlı smoke testi: **payment → approve → search görünür**

## Ön Koşullar
- Staging DB hazır
- SendGrid env hazır (EMAIL_PROVIDER=sendgrid)
- Stripe test key + webhook secret hazır

## Runbook (Tek Komut Mantığı)
1) Seed + test user:
```
python backend/scripts/seed_core_sql.py
python backend/scripts/seed_default_plans_v1.py
python backend/scripts/seed_vehicle_master_data.py
```

2) Auth + invoice oluşturma
- Register dealer → verify → login
- Invoice + subscription oluştur

3) Payment zinciri
- `POST /api/payments/create-checkout-session`
- Stripe CLI forward → `/api/webhook/stripe`
- Audit 4 event doğrula

4) Moderation + Search
- Listing create → submit
- `POST /api/admin/listings/{id}/approve`
- `GET /api/v2/search?country=DE` → listing görünür

## Evidence
- `/app/ops/SMOKE_FINAL01_STAGING_EVIDENCE.md`
