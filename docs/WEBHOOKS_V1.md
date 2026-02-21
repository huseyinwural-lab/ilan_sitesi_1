# WEBHOOKS_V1 (ADR-WH-01)

## Provider
- **Stripe** (tek kaynak)

## Idempotency
- `event_id` = Stripe `event.id`
- SQL: `payment_event_logs.event_id` üzerinde **unique constraint**

## Event Log
- `provider` (stripe)
- `event_id` (unique)
- `event_type`
- `raw_payload`
- `status` (pending/processed/failed)
- `processed_at`

## Replay Stratejisi
- Event log üzerinden manuel replay (admin-only)
- Duplicate event geldiğinde **no-op**
- Replay sonucu `event_log.status` güncellenir

## Notlar
- İleride çoklu provider gelirse `provider + event_id` composite unique kullanılmalı.
