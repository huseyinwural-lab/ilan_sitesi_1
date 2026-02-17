# MVP Production Readiness Audit Checklist

## 1. API Health
- [ ] **Error Rate**: 5xx responses < 0.1% over 24h.
- [ ] **Latency**: Search API P95 < 500ms.
- [ ] **Validation**: All public endpoints handle invalid inputs gracefully (400 vs 500).

## 2. Database Health
- [ ] **Slow Queries**: No queries taking > 1s in `pg_stat_statements`.
- [ ] **Connections**: Pool usage < 50% under normal load.
- [ ] **Indexes**: All `ix_` defined in models are present in DB.

## 3. Security
- [ ] **Rate Limiting**: Active on public routes (`/search`, `/reveal`).
- [ ] **Auth**: JWT secret is secure and not default.
- [ ] **Permissions**: Standard users cannot access Admin APIs.

## 4. Operational
- [ ] **Logs**: Structured logging enabled (JSON or detailed text).
- [ ] **Backups**: Daily backup job configured.
- [ ] **Monitoring**: Uptime checks configured (e.g., `/health` endpoint).
