# FINAL-01_ORDER_LOCK

## Karar (ADR-FINAL-01)
- **Sıra:** AUTH → Stripe → Ad Loop
- Bu sıra kilitlidir; başka geliştirme yok.

## Kapsam
1) **AUTH (SQL full migration + E2E)**
   - Register → verify → login → doğru portal → session stabil.
2) **Stripe + Payment Zinciri**
   - Payment → Webhook → Invoice paid → Subscription active → Quota update.
3) **Ad Loop**
   - İlan oluştur → medya → publish → public görünür.

## Gate
- Auth E2E PASS olmadan Stripe’a geçilmez.
- Stripe sandbox ödeme zinciri PASS olmadan Ad Loop go‑live yapılmaz.
