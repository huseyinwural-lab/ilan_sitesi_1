# STRIPE_IDEMPOTENCY_LOCAL_EVIDENCE

**Tarih:** 2026-02-22 00:54:38 UTC
**Durum:** BLOCKED (Stripe CLI yok)

## Öncelik (Gerçek imza)
- Stripe CLI ile aynı event iki kez gönderilecek.

## Mevcut Durum
`stripe --version` → `command not found`

## Fallback
- CLI sağlanırsa gerçek signature ile test yapılacak.
