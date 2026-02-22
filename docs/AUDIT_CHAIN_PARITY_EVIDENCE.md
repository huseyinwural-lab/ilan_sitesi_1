# AUDIT_CHAIN_PARITY_EVIDENCE

**Tarih:** 2026-02-22 01:20:30 UTC

## Audit Zinciri
```
register_honeypot_hit
gdpr_export_completed
gdpr_export_notification_sent
```

## EXPLAIN (index kullanımı)
```
EXPLAIN SELECT * FROM audit_logs WHERE action='gdpr_export_completed' ORDER BY created_at DESC LIMIT 5;
```
Çıktı:
```
Limit
  -> Sort (created_at DESC)
       -> Index Scan using ix_audit_logs_action on audit_logs
```
