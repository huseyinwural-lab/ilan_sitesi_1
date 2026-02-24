# REGISTER_ANTIBOT_HONEYPOT_EVIDENCE

**Tarih:** 2026-02-24 11:24:45 UTC
**Durum:** CLOSED

## Kanıt
- `company_website` dolu gönderildiğinde 400
- Audit log: `register_honeypot_hit` (user_email=honeypot@platform.com)

## Örnek (gerçek)
```
POST /api/auth/register/consumer
{
  "full_name": "Honeypot Test",
  "email": "honeypot@platform.com",
  "password": "User123!",
  "country_code": "DE",
  "company_website": "http://bot.example"
}
```
Beklenen: 400 + audit log.
