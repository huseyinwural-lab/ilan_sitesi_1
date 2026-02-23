# Search Cutover Plan (Feature Flag Rollout)

## Rollout Plan (SEARCH_SQL_ROLLOUT)
1) **%10** (SEARCH_SQL_ROLLOUT=0.1)
   - İzlenecek metrikler: error rate, p95 latency, slow query sayısı
2) **%50** (SEARCH_SQL_ROLLOUT=0.5)
   - Parity sonuçları ve p95 stabil ise artır
3) **%100** (SEARCH_SQL_ROLLOUT=1.0)
   - Postgres read-only search aktif

## Freeze Window (30 dakika hedef)
- Low-traffic zaman dilimi seçilecek.
- Cutover sırasında kısa süreli write-block (listing publish/update) veya read-only mod.
- Dry-run ile süre ölçülür; 30 dk aşarsa plan revize edilir.

## Rollback Prosedürü
- Feature flag geri alınır: SEARCH_SQL_ROLLOUT=0
- Mongo read fallback 24 saat açık tutulur.
- Hata kaydı + parity tekrar test edilir.

## Post-Cutover Monitoring
- Error rate (5dk)
- p95 latency (search endpoints)
- Slow query log (Postgres)
- DB connection pool saturation
