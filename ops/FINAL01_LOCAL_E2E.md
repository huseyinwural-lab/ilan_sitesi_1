# FINAL01_LOCAL_E2E — Local Postgres Unblock

## 1) Local Postgres Kurulum (Native)
- Docker mevcut değil: `docker: command not found`
- `psql --version`: **PostgreSQL 15.16**
- `service postgresql status`: **online (port 5432)**
- `systemctl status postgresql`: **BLOCKED** (systemd yok)

## 2) Local DB + ENV
- DB: `app_local`
- User: `app_user`
- PASS: `app_pass`
- `.env.local`:
  - DATABASE_URL=postgresql://app_user:app_pass@localhost:5432/app_local
  - DB_SSL_MODE=disable
  - PAYMENTS_ENABLED_COUNTRIES=DE
  - STRIPE_WEBHOOK_SECRET=whsec_local_test
  - STRIPE_API_KEY=sk_test_emergent
  - EMAIL_PROVIDER=mock

## 3) Alembic Upgrade + Heads
- `alembic upgrade heads` **PASS**
- `alembic current`:
  - c5833a1fffde (head)
  - d2f4c9c4c7ab (head)
  - aa12b9c8d7e1 (head)
  - f3b1c2d8a91b (head)
  - p29_email_verification_tokens (head)
  - p30_user_quota_limits (head)

## 4) DB Kanıtları
### Email Verification Tokens
```
\d+ email_verification_tokens
- UNIQUE: uq_email_verification_token_hash
- INDEX: ix_email_verification_tokens_user_id
- INDEX: ix_email_verification_tokens_expires_at
```

### Payments Unique Constraint
```
SELECT conname, pg_get_constraintdef(...) WHERE relname='payments';
- uq_payments_provider_ref UNIQUE (provider, provider_ref)
```

### Tablolar (özet)
- payments ✅
- user_subscriptions ✅
- admin_invoices ✅
- email_verification_tokens ✅
- billing_audit_log: **YOK** (audit_logs kullanılıyor)

## 5) Auth E2E (SQL Only)
- Register (consumer/dealer) → **PASS**
- Token row oluştu + consumed_at set:
```
SELECT user_id, expires_at, consumed_at FROM email_verification_tokens WHERE user_id='2985ef6f-cbdf-44d4-915a-c806f4e3da8f';
```
- Expired token test:
  - `expires_at` geçmişe çekildi → `/auth/verify-email` **400 Kod süresi doldu**
- Reuse token test:
  - Verified user için tekrar verify → **400 Zaten doğrulanmış**
- Resend rate limit:
  - `/auth/resend-verification` → **429 RATE_LIMITED**

- Login → portal_scope:
  - consumer → `account`
  - dealer → `dealer`
- Protected endpoint:
  - No token → **403 Not authenticated**
  - Valid token → **200** `/users/me`

## 6) Stripe Sandbox E2E (Local)
- `create-checkout-session` → **PASS**
  - session_id: `cs_test_a1S081pYmXnkhYNRIA5K1gxDVMhjgBsp4S4xBRspw7NAcFxPOdIfT8I8QC`
  - checkout_url: Stripe checkout URL
- Webhook (signed) → **processed**
- Invoice status:
```
SELECT status, payment_status FROM admin_invoices WHERE id='6c9654f5-793d-464b-95df-57c80f1422b6';
-- paid / succeeded
```
- Payment row:
```
SELECT status, provider_ref FROM payments WHERE invoice_id='6c9654f5-793d-464b-95df-57c80f1422b6';
-- succeeded / cs_test...
```
- Subscription:
```
SELECT status FROM user_subscriptions WHERE id='0fc127bd-6327-4302-853f-da78b0aba0bc';
-- active
```
- Quota:
```
SELECT listing_quota_limit, showcase_quota_limit FROM users WHERE id='127b0006-4db9-4290-af4a-63f795360bc6';
-- 50 / 5
```
- Audit events:
```
SELECT action FROM audit_logs WHERE user_id='127b0006-4db9-4290-af4a-63f795360bc6'
-- payment_succeeded, invoice_marked_paid, subscription_activated, quota_limits_updated
```
- Duplicate webhook → **{"status":"duplicate"}**

## 7) Ad Loop E2E (Local)
- Draft create → **PASS** (status: draft)
- Media upload → **PASS** (local storage stub)
- Submit → **PASS** (status: pending_moderation)
- Publish → **MANUAL SQL** (Mongo moderation path; SQL-only ortamda publish için DB update)
- `/v1/listings/my` → listing status **published**
- `/v1/listings/vehicle/{id}` detail → **PASS**
- Public search v2 → **BLOCKED** (Mongo-backed)

## 8) Notlar
- Billing audit log için ayrı tablo yok; audit_logs kullanılıyor. (Mongo Zero sonrası netleştirilecek)
