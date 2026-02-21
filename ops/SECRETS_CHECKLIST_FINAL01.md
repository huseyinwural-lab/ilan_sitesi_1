# SECRETS_CHECKLIST_FINAL01

## Gate: Secret’lar Set Edilmeden Go‑Live YOK
- [ ] DATABASE_URL (staging/prod)
- [ ] SENDGRID_API_KEY
- [ ] SENDER_EMAIL
- [ ] STRIPE_API_KEY (staging test)
- [ ] STRIPE_WEBHOOK_SECRET (staging test)

## Smoke sonrası
- [ ] SendGrid delivery smoke PASS
- [ ] Staging payment→approve→search smoke PASS
- [ ] Preview/Prod parity smoke PASS
