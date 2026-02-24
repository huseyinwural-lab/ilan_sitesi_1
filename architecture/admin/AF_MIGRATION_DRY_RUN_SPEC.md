# AF Migration Dry-Run Spec

## Amaç
Production migration öncesi veri bütünlüğü risklerini **read-only** kontrollerle tespit etmek ve CI’da fail-fast davranmak.

## Çalıştırma
```bash
python scripts/migration_dry_run.py
```

**Varsayımlar**
- `DATABASE_URL` env ile sağlanır.
- Script read-only çalışır (DDL/DML yok).
- Opsiyonel audit log için: `MIGRATION_DRY_RUN_AUDIT=1` (DML yazar).

## Kontrol Matrisi

| Kontrol | Açıklama | Blocking? |
| --- | --- | --- |
| Tablo varlık kontrolü | `users`, `plans`, `subscription_plans`, `user_subscriptions`, `listings`, `audit_logs` | Evet |
| Kolon tip uyumu | risk_level, ban_reason, suspension_until, quota alanları, limits | Kritik mismatch → Evet |
| Foreign key integrity | user_subscriptions.user_id/plan_id orphan kontrolü | Evet |
| Null constraint taraması | risk_level null, suspended ban_reason null | Evet |
| Enum değer uyumu | risk_level low/medium/high | Evet |
| Index varlık kontrolü | plan ve subscription indeksleri | Uyarı |
| Row count delta | snapshot karşılaştırması | Uyarı |

## Çıktı Formatı (Örnek)
```
[MIGRATION-DRY-RUN] RESULT: PASS
Timestamp: 2026-02-24T17:50:00+00:00
Blocking Issues: 0
Warnings: 2
- Column not present yet (expected via migration): users.risk_level
- No previous snapshot found; created new snapshot file
```

## Failure Davranışı
- **FAIL**: `Blocking Issues > 0`
- Exit code: `2`
- CI job FAIL eder.

## Artifact
- Snapshot: `/tmp/migration_dry_run_snapshot.json` (varsayılan)
- Opsiyonel audit log: `action=MIGRATION_DRY_RUN` (env: `MIGRATION_DRY_RUN_AUDIT=1`)
- Opsiyonel JSON output (P2)
