# EMAIL_PROVIDER_SWITCH

## Amaç
Email gönderimini ENV bazlı provider seçimiyle yönetmek (mock → prod).

## ENV Standardı
- `EMAIL_PROVIDER`: `mock` | `smtp` | `sendgrid`

### SMTP Konfigürasyonu
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_FROM`
- `SMTP_USERNAME` (opsiyonel)
- `SMTP_PASSWORD` (opsiyonel)

### SendGrid Konfigürasyonu
- `SENDGRID_API_KEY`
- `SENDER_EMAIL`

## Kurallar
- **Prod ortamında `EMAIL_PROVIDER=mock` yasak** (startup validation).
- Provider geçersizse servis açılmaz.

## Mock Davranışı
- Email gönderimi yapılmaz, log’a yazılır.

## Evidence (DB Unblock Sonrası)
- Register → verification mail gönderimi PASS
- Resend rate limit PASS
