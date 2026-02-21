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
