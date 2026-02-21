# Payments V1 Evidence

## Schema + Migration
- Migration: `6b483af4b2db_payments_v1_schema.py`
- Unique constraint: `(provider, provider_ref)`
- Indexes: invoice_id, status, created_at

## Admin List
- `GET /api/admin/payments?status=succeeded` → PASS (items returned)

## Duplicate Test
```
INSERT INTO payments ... provider_ref='pi_dupe_001'  -> OK
INSERT INTO payments ... provider_ref='pi_dupe_001'  -> UNIQUE VIOLATION (expected)
```

## Transaction Consistency
- Script: `backend/scripts/payment_txn_consistency_test.py`
- Output:
```
{invoice_status: paid, payment_status: succeeded, subscription_status: active, listing_quota_limit: 3, showcase_quota_limit: 0}
```

## Notes
- Audit logs: payment_succeeded, invoice_marked_paid, subscription_activated, quota_limits_updated
