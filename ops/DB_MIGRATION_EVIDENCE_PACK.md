# DB Migration Evidence Pack — Payments/UserSubscriptions/BillingAuditLog

## Tarih
- 2026-02-23

## ADR-MIG-01 (Alembic Comment DDL Uyum Kuralı)
- Karar: `op.create_table_comment(...)` kullanılmayacak.
- Gerekçe: Postgres/Alembic DDL uyumsuzluğu üretim riski.
- Uygulama: Bu repo’da migration dosyalarında `create_table_comment` bulunmadı. Kural `backend/migrations/README` içine eklendi.

## Alembic Upgrade Head
- Komut: `alembic upgrade head`
- Durum: **BLOCKED** (Local Postgres servisi çalışmıyor)
- Kanıt (DB bağlantı hatası):
```
DB_CONNECT_ERROR: OperationalError('(psycopg2.OperationalError) connection to server at "localhost" (127.0.0.1), port 5432 failed: Connection refused
	Is the server running on that host and accepting TCP/IP connections?
connection to server at "localhost" (::1), port 5432 failed: Cannot assign requested address
	Is the server running on that host and accepting TCP/IP connections?
')
```

## Alembic Current / Head Hash
- Komut: `alembic current`
- Durum: **BLOCKED** (aynı DB bağlantı hatası)

## Tablo Doğrulama (payments / user_subscriptions / billing_audit_log)
- Komutlar: `\dt`, `\d+ payments`, `\d+ user_subscriptions`, `\d+ billing_audit_log`
- Durum: **BLOCKED** (psql aracı ve DB erişimi yok)

## Notlar / Gate
- DB head’e çıkılmadan P1 adımına geçilmeyecek.
- Ops dependency: local/staging Postgres servisi erişilebilir olmalı.

## Local UNBLOCK (2026-02-21)
- Local Postgres (native) **aktif**
- `alembic upgrade heads` **PASS**
- `alembic current` heads:
  - c5833a1fffde, d2f4c9c4c7ab, aa12b9c8d7e1, f3b1c2d8a91b, p29_email_verification_tokens, p30_user_quota_limits, p31_listing_contact_options, p32_listing_category_required

### Tablo Doğrulama (Local)
- `payments`, `user_subscriptions`, `admin_invoices`, `email_verification_tokens` ✅
- `billing_audit_log` ❌ (audit_logs kullanılıyor)

### Constraint Kanıtı
- `uq_payments_provider_ref` UNIQUE (provider, provider_ref)
- `email_verification_tokens` → unique token + indexes (user_id, expires_at)

