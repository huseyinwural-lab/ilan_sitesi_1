# LOGIN_RATE_LIMIT_EVIDENCE

**Tarih:** 2026-02-24 12:20:00 UTC
**Ortam URL:** https://category-wizard-1.preview.emergentagent.com

## Senaryo
- Aynı IP + aynı kullanıcı için 5 başarısız login denemesi

## Curl Kanıtı
```
attempt_1=401
attempt_2=401
attempt_3=401
attempt_4=401
attempt_5=429
```

## Log Kanıtı
- backend.err.log: `login_rate_limit_triggered`

## Not
- Rate limit anahtarı: `{email}:{ip}`
- Block süresi: 15 dakika
