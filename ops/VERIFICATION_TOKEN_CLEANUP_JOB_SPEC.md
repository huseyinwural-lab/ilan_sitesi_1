# VERIFICATION_TOKEN_CLEANUP_JOB_SPEC

## Zamanlama
- Günlük 00:30 UTC

## İşlem Adımları
1) Expired + consumed tokenlar: `consumed_at` + `expires_at` 
   - `expires_at < now - 24h` → delete
2) Expired + not consumed tokenlar:
   - `expires_at < now - 7d` → delete
3) İşlem sonrası:
   - silinen satır sayısı loglanır
   - index ve row count kontrolü yapılır

## Maintenance Log
- Çıktı: `/app/ops/VERIFICATION_TOKEN_CLEANUP_LOG.md`
