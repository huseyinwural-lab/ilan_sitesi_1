# BLOCKED_RUNBOOK_DB

## Amaç
Postgres erişimi yoksa doğrulamalar **BLOCKED** olarak işaretlenir; sadece wiring/şema hazırlığı yapılır.

## Kural
- DB yokken: sadece **schema/migration/endpoint wiring/test prep**.
- DB gerektiren tüm kanıtlar: **BLOCKED** etiketiyle evidence dosyasına yazılır.

## DB Gerektiren Kanıtlar (Örnek)
- `alembic upgrade head` / `alembic current`
- `\dt` / `\d+` tablo doğrulamaları
- Auth E2E / Stripe sandbox E2E / Ad Loop E2E

## Evidence Yazım Formatı
- Başlık: `Status: BLOCKED`
- Sebep: `Postgres bağlantısı yok (connection refused)`
- Plan: `UNBLOCK_DB_CHECKLIST_FINAL01.md` çalıştırılacak
