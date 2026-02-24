# STRIPE_IDEMPOTENCY_EVIDENCE

**Tarih:** 2026-02-24 13:03:30 UTC
**Ortam URL:** https://mongo-tasfiye.preview.emergentagent.com
**Commit Ref:** d05848ad
**Seçilen Akış (Aktif):** Checkout Session (`POST /api/payments/create-checkout-session`)
**Idempotency Header:** `Idempotency-Key`

## Test Özeti
- Aynı `Idempotency-Key` ile ardışık iki çağrı yapıldı.
- İkinci çağrı **aynı session_id** ve **aynı checkout_url** döndürdü.
- DB kontrolü: ilgili invoice için **tek** PaymentTransaction kaydı bulundu.

## Test Parametreleri
- Invoice ID: `0259a06f-876e-48ab-aaa0-5c664b1e97ae`
- Idempotency Key: `idem-1771938207`
- Session ID: `cs_test_a19IYb91lvhUdJkMgIzX4oYwHkdhAGsQsm7csc9BoXGedRZsiLiQ14CLNK`

## Curl Kanıtı
```
# 1. çağrı
curl -X POST {BASE}/api/payments/create-checkout-session \
  -H "Authorization: Bearer <DEALER_TOKEN>" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: idem-1771938207" \
  -d '{"invoice_id":"0259a06f-876e-48ab-aaa0-5c664b1e97ae","origin_url":"{BASE}"}'

# 2. çağrı (aynı key)
curl -X POST {BASE}/api/payments/create-checkout-session \
  -H "Authorization: Bearer <DEALER_TOKEN>" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: idem-1771938207" \
  -d '{"invoice_id":"0259a06f-876e-48ab-aaa0-5c664b1e97ae","origin_url":"{BASE}"}'
```

## Response Özetleri
- 1. çağrı: `idempotency_reused=false`, `session_id=cs_test_a1kIR5L...`
- 2. çağrı: `idempotency_reused=true`, `session_id=cs_test_a1kIR5L...`

## DB Kayıt Kontrolü
```
PaymentTransaction (invoice_id=826c754f-6954-485f-b987-fe68997927c1)
- count = 1
- session_id = cs_test_a1kIR5LJoZCPYmCmILHnZhtb2l7ToMFaSIVK8U0KWrqnHwlehYkLNGorBN

Payment
- count = 1
```

## Not
- Akış seçim önceliği: Checkout → Subscription → PaymentIntent. Sistem aktif akış: **Checkout Session**.
