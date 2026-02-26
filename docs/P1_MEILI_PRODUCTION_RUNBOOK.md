# Meilisearch Production Runbook (P1)

## 1) Pre-check

1. Admin panelde aktif config doğrula:
   - `/admin/system-settings` → Search / Meilisearch
2. Health kontrolü:
   - `GET /api/admin/search/meili/health`
3. Queue backlog kontrolü:
   - `GET /api/admin/search/meili/sync-jobs`

## 2) Reindex Prosedürü

### API ile
`POST /api/admin/search/meili/reindex`

Örnek payload:
```json
{
  "chunk_size": 300,
  "max_docs": null,
  "reset_index": true
}
```

### Script ile
```bash
python /app/backend/scripts/reindex_meili_projection.py --chunk-size 300 --reset-index
```

Başarı kriteri:
- `indexed_docs > 0`
- `elapsed_seconds` raporlandı
- `GET /api/admin/search/meili/stage-smoke?q=<query>` hit döndürüyor

## 3) Config Rollback Prosedürü

1. `/admin/system-settings` → Search / Meilisearch → Geçmiş
2. İstenen kayıt için:
   - **Bu konfigi tekrar aktif et**
3. Aktivasyon gate:
   - Sistem önce test çalıştırır.
   - Test PASS ise active olur.
   - FAIL ise inactive kalır.

## 4) Index Reset Senaryosu

Kullanım:
- Büyük şema değişikliği
- Index bozulması / drift

Adımlar:
1. Health PASS teyit
2. Reindex endpointini `reset_index=true` ile çalıştır
3. Stage smoke ile query/hit kontrolü
4. Queue dead-letter varsa process + retry

## 5) Incident Response

### A) Search sonuç vermiyor
1. `GET /api/admin/search/meili/health`
2. Aktif config + URL/key doğrula
3. `GET /api/admin/search/meili/sync-jobs` → `dead_letter` / `retry` sayıları
4. `POST /api/admin/search/meili/sync-jobs/process` ile manuel drain
5. Gerekirse rollback + full reindex

### B) Sync backlog artıyor
1. Meili erişilebilirlik ve latency kontrolü
2. `SEARCH_SYNC_MAX_RETRIES` ve backoff env’lerini gözden geçir
3. Process endpoint ile batch drain
4. İhtiyaç halinde reset+reindex

### C) Yanlış ranking
1. `GET /api/admin/search/meili/stage-smoke?q=<query>`
2. Sort beklentisi:
   - `premium_score:desc`
   - `published_at:desc`
3. Index settings’i tekrar uygula (health/test aktivasyon akışı)
