# SECRETS_PROVISIONING_REQUEST_FINAL01

## Amaç
FAZ-FINAL-01 go-live öncesi **secret provisioning** talebi. Bu dosya ops/altyapı ekibine gönderilmelidir.

## Zorunlu Secret Listesi (Staging + Prod)
1) **DATABASE_URL**
   - Postgres instance + user/password
   - Network erişim (IP allowlist / VPC route)

2) **SENDGRID_API_KEY**
3) **SENDER_EMAIL** (SendGrid verified sender)

4) **STRIPE_API_KEY** (Test mode – staging)
5) **STRIPE_WEBHOOK_SECRET** (Test mode – staging)

## Dağıtım Politikası
- Secret’lar **chat üzerinden paylaşılmayacak**.
- Secret manager (Vault/Doppler/SSM vb.) üzerinden inject edilecek.

## Doğrulama (Ops tamamlayınca yapılacak)
- `EMAIL_PROVIDER=sendgrid` ile backend startup **PASS**
- `/api/health` → healthy
- SendGrid gerçek inbox’a doğrulama maili
- Stripe webhook → invoice paid + subscription active + quota set

## Ek Not
- Test inbox: ops tarafından belirlenmiş shared mailbox (ör. test@company-domain)
