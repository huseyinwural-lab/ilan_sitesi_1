# GO_LIVE_DECISION_v1.0.0

## Release Gate (v1.0.0)

### P0 (Release Blocker) — PASS
- Public Search çalışıyor (v2 search endpoint + UI entegrasyon)
- Moderation state machine çalışıyor (pending → approve/reject/needs_revision)
- Moderation audit log yazılıyor

### P1 (Security & Permission Audit) — PASS
- Failed login audit: **PASS**
  - 3 failed login → 3 `FAILED_LOGIN`
  - Rate limit block başlangıcı → 1 `RATE_LIMIT_BLOCK`
- Admin role change audit: **PASS**
  - Role update + audit atomik garanti
  - `ADMIN_ROLE_CHANGE` kaydı oluşuyor (prev/new doğru)
- Unauthorized role change attempt audit: **PASS**
  - Scope dışı deneme → 403 + `UNAUTHORIZED_ROLE_CHANGE_ATTEMPT`

## Notlar
- `country` bilgisi failed login audit’inde P1 kararı gereği boş bırakılır.
- Rate limit in-process; v1.1’de Redis/tabanlı paylaşımlı rate limit değerlendirilebilir.
