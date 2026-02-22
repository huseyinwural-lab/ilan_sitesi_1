# REGISTER_ANTIBOT_HONEYPOT_EVIDENCE

**Tarih:** 2026-02-22
**Durum:** BLOCKED (Preview DB erişimi yok)

## Beklenen Kanıt
- `company_website` dolu gönderildiğinde 400
- `register_honeypot_hit` audit log kaydı

## Örnek (beklenen)
```
POST /api/auth/register/consumer
{
  "full_name": "Bot",
  "email": "bot@example.com",
  "password": "Secret123!",
  "country_code": "DE",
  "company_website": "https://spam.example"
}
```
Beklenen: 400 + audit log.
