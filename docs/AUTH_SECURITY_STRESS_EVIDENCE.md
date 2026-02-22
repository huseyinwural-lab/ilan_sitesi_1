# AUTH_SECURITY_STRESS_EVIDENCE

**Tarih:** 2026-02-22 00:54:38 UTC
**Durum:** BLOCKED (Local Postgres yok / backend preview strict mode)

## Beklenen Testler (DB hazır olduğunda)
- 10 yanlış login → rate limit tetikleme
- 2FA backup code reuse → reject
- Soft delete → login block
- Honeypot dolu → 400 + register_honeypot_hit audit
- GDPR export → notification + audit + severity=warning

## Not
Local DB olmadığı için auth uçtan uca test edilemedi.
