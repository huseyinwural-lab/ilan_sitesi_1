# Monetization E2E Gate Checklist (Campaigns → Plans → Invoices → Payments → Webhooks)

## 1) Webhook Idempotency & Replay Gate
- [ ] `idempotency_key` tanımı net (event_id + provider_signature).
- [ ] Unique constraint (idempotency_key) uygulanır.
- [ ] Replay senaryosu: aynı payload ikinci kez geldiğinde **no-op**.

## 2) Subscription State Machine
- [ ] States: `trial` → `active` → `past_due` → `canceled` (geçiş kuralları).
- [ ] Stripe webhook mapping (invoice.payment_failed, customer.subscription.updated).
- [ ] Backfill: mevcut abonelikler için state normalize.

## 3) Quota Update Atomicity
- [ ] Quota düşümü tek transaction içinde.
- [ ] Concurrent kullanım testi (lock/optimistic)
- [ ] Negative quota engeli.

## 4) Admin Data Source Parity
- [ ] Admin UI list/detail SQL read-path.
- [ ] Filters + pagination parity.
- [ ] CSV export saha eşleştirmeleri.

## 5) Payments + Webhooks (Tek Zincir Gate)
- [ ] Checkout → Payment → Invoice update akışı tek zincir.
- [ ] Webhook failure -> retry queue/log.
- [ ] Manual replay endpoint (admin-only).
