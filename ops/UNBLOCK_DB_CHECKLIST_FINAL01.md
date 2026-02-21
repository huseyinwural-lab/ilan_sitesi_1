# UNBLOCK_DB_CHECKLIST_FINAL01

## Ön Koşul
- Postgres erişimi sağlandı (connection OK)

| # | Adım | Evidence Path |
|---|------|---------------|
| 1 | `alembic upgrade head` | `/app/ops/DB_MIGRATION_EVIDENCE_PACK.md` |
| 2 | `alembic current` (head hash) | `/app/ops/DB_MIGRATION_EVIDENCE_PACK.md` |
| 3 | Seed / master data (`seed_core_sql.py`, `seed_default_plans_v1.py`) | `/app/ops/FINAL01_SEED_EVIDENCE.md` |
| 4 | Test user oluşturma (consumer + dealer) | `/app/ops/FINAL01_TEST_USER_EVIDENCE.md` |
| 5 | Auth E2E (register → verify → login → portal) | `/app/ops/FINAL01_AUTH_E2E_EVIDENCE.md` |
| 6 | Stripe sandbox E2E (checkout → webhook → invoice/subscription/quota) | `/app/ops/FINAL01_STRIPE_E2E_EVIDENCE.md` |
| 7 | Ad Loop E2E (create → media → publish → public search) | `/app/ops/FINAL01_AD_LOOP_E2E_EVIDENCE.md` |
