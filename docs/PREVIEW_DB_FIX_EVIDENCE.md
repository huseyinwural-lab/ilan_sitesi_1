# PREVIEW_DB_FIX_EVIDENCE

**Tarih:** 2026-02-21
**Durum:** BLOCKED (Preview DB secret injection bekleniyor)

## Beklenen Aksiyonlar (Ops)
- Secret Manager: `DATABASE_URL_PREVIEW` set edilmeli (format: postgresql://<user>:<pass>@<host>:5432/<db>?sslmode=require)
- Firewall/allowlist: “Preview backend → Postgres 5432 outbound allow”

## Uygulanan Kod Değişikliği
- Preview/Prod ortamında localhost/127.0.0.1 yasaklandı.
- Preview/Prod için `DB_SSL_MODE=require` zorunlu.
- `DATABASE_URL` eksikse fail-fast.

## Doğrulama (Yapılacak)
```
GET /api/health/db
```
Beklenen çıktı: `200` ve `db_status=ok`

## Backend Log Kanıtı
```
SQL init skipped: Multiple exceptions: [Errno 111] Connect call failed ('127.0.0.1', 5432)
```

## Mevcut Durum (2026-02-22)
```
GET /api/health
```
Sonuç: `520` (Cloudflare: Web server is returning an unknown error)

> Not: Secret injection tamamlandığında gerçek curl çıktıları eklenecek.
