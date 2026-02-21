# BILLING_V1_LOCK (Decisions)

## 1) Invoice V1 Alan Seti
**Zorunlu:**
- id
- user_id
- status
- amount_total
- currency
- created_at

**Koşullu:**
- issued_at (status issued/paid ise zorunlu)
- due_at (issued ise opsiyonel; yoksa immediate due)

**Opsiyonel:**
- subscription_id (nullable FK)
- plan_id (nullable FK)
- campaign_id (nullable)
- provider_customer_id (nullable)
- meta_json (nullable)

## 2) subscription_id Nullable
- Geçiş güvenliği için nullable FK.
- One-off invoice senaryoları desteklenir.

## 3) provider_ref Mapping (Stripe)
- **provider_ref = payment_intent.id**
- checkout_session_id opsiyonel alan (nullable)

## 4) Replay Endpoint
- Path: **/api/admin/webhooks/events/{event_id}/replay**
- Admin-only + audit zorunlu.

## 5) Admin Filtre Kapsamı (V1)
- **Invoices:** sadece `status` filtresi
- **Payments:** sadece `status` filtresi
