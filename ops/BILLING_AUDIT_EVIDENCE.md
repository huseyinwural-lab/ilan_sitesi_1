# BILLING_AUDIT_EVIDENCE (Local)

## Query
```
SELECT action, resource_type, resource_id, created_at
FROM audit_logs
WHERE action IN (
  'payment_succeeded','invoice_marked_paid','subscription_activated','quota_limits_updated'
)
ORDER BY created_at DESC LIMIT 10;
```

## Output (Local)
```
 quota_limits_updated   | user          | 127b0006-4db9-4290-af4a-63f795360bc6 | 2026-02-21 21:13:48.748559+00
 subscription_activated | subscription  | 0fc127bd-6327-4302-853f-da78b0aba0bc | 2026-02-21 21:13:48.746931+00
 invoice_marked_paid    | invoice       | 6c9654f5-793d-464b-95df-57c80f1422b6 | 2026-02-21 21:13:48.739479+00
 payment_succeeded      | payment       | 90cbfdb1-7100-4f32-b388-ee57153ee0e5 | 2026-02-21 21:13:48.737477+00
```
