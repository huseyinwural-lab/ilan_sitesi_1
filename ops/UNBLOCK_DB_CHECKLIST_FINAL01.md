# UNBLOCK_DB_CHECKLIST_FINAL01

## Ön Koşul
- Postgres erişimi sağlandı (connection OK)

## 1) Migration + Seed
1. `cd /app/backend`
2. `alembic upgrade head`
3. `alembic current`
4. Seed (gerekli master data):
   - `python backend/scripts/seed_core_sql.py`
   - `python backend/scripts/seed_default_plans_v1.py`

## 2) AUTH E2E
- Register → verify → login → portal redirect → protected endpoint
- Output: Auth E2E PASS kanıtı

## 3) Stripe Sandbox E2E
- Checkout/PaymentIntent → webhook → invoice paid → subscription active → quota update
- Output: Zincir PASS + replay PASS

## 4) Ad Loop E2E
- İlan oluştur → medya upload → publish → public görünür
- Output: Ad Loop PASS

## 5) Evidence Güncelle
- DB Migration Evidence Pack + FINAL-01 evidence dosyaları güncellenir
