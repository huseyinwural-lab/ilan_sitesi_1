# SQL Migration Checklist

## Schema
- [ ] Model + Alembic migration (idempotent)
- [ ] Index/unique constraint’ler

## Backfill
- [ ] Export formatı (JSON/CSV)
- [ ] Import job (idempotent)
- [ ] Row count doğrulama
- [ ] Örneklem checksum

## Switch
- [ ] SQL repo aktif
- [ ] Mongo read-only (varsa)
- [ ] Feature flag/switch güncel

## Test
- [ ] 3 kritik senaryo E2E
- [ ] Negatif senaryo (rate-limit, validation)

## Observability
- [ ] Error rate
- [ ] Latency (p95)
- [ ] DB pool / lock wait

## Decommission
- [ ] Mongo kodu kaldır
- [ ] Mongo bağımlılıkları kaldır
- [ ] Doküman güncelle

