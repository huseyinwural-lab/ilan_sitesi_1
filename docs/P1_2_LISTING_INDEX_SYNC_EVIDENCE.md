# P1.2 — Listing → Index Senkronizasyonu Evidence

Tarih: 2026-02-26

## 1) Sabitlenen Index Document Contract

Primary key:
- `listing_id`

Doküman alanları:
- `listing_id`
- `category_path_ids`
- `make_id`, `model_id`, `trim_id`
- `city_id`
- `attribute_flat_map`
- `price`, `premium_score`
- `published_at`
- `searchable_text` (title + description normalize)

Contract endpoint:
- `GET /api/admin/search/meili/contract`

## 2) Create/Update/Delete/Soft-delete Sync Hook

Uygulanan hook noktaları:
- `POST /api/v1/listings/vehicle` (create)
- `PATCH|POST /api/v1/listings/vehicle/{id}/draft` (update)
- `POST /api/v1/listings/vehicle/{id}/request-publish`
- `POST /api/v1/listings/vehicle/{id}/submit`
- `POST /api/v1/listings/vehicle/{id}/unpublish`
- `POST /api/v1/listings/vehicle/{id}/archive`
- Moderation transition (`approve/reject/...`) sonrası
- Admin soft-delete / force-unpublish sonrası

Beklenen davranış:
- Searchable status (`published|active`) ise upsert
- Aksi durumda remove (index’ten sil)

## 3) Retry Queue + Exponential Backoff + Dead-letter

Queue tablosu:
- `search_sync_jobs`
  - `status`: `pending | processing | retry | done | dead_letter`
  - `attempts`, `max_attempts`
  - `next_retry_at`
  - `last_error`

Endpointler:
- `GET /api/admin/search/meili/sync-jobs`
- `POST /api/admin/search/meili/sync-jobs/process`

Doğrulanan senaryo:
- Aktif config yokken sync job `retry` durumuna düşürüldü.
- `max_attempts` sınırına getirilip process edildiğinde `dead_letter` durumuna geçti.

## 4) Bulk Reindex

Endpoint:
- `POST /api/admin/search/meili/reindex`
  - `chunk_size`
  - `max_docs`
  - `reset_index`

Script:
- `python /app/backend/scripts/reindex_meili_projection.py --chunk-size 200 --max-docs 1000 --reset-index`

Memory-safe yaklaşım:
- Chunked query + chunked upsert

Log:
- `docs_indexed`, `elapsed_seconds`, `chunk_size` raporlanır.

## 5) Stage Smoke (P1.2)

Health:
- `GET /api/admin/search/meili/health`

Smoke:
- `GET /api/admin/search/meili/stage-smoke?q=bmw`
  - Ranking sort doğrulaması: `premium_score:desc`, `published_at:desc`

Public query endpoint:
- `GET /api/search/meili?q=...&limit=...&offset=...`

### Test raporu
- Testing agent: `/app/test_reports/iteration_14.json`
  - Backend: 21/21 PASS
  - Frontend: PASS
  - Doğrulanan kritikler:
    - RBAC (admin-only)
    - Fail-fast (`ACTIVE_CONFIG_REQUIRED`) davranışı
    - Ranking sort sözleşmesi (`premium_score:desc`, `published_at:desc`)

## 6) External Aktivasyon Sonrası Canlı PASS Çıktıları

Kaynaklar:
- `/app/test_reports/iteration_15.json`
- Canlı doğrulama script çıktıları (2026-02-26)

### 6.1 Health doğrulaması (PASS)
- `GET /api/admin/search/meili/health` → `200`, `ok=true`, `reason_code=ok`
- `ACTIVE_CONFIG_REQUIRED` hatası **yok**
- `index_document_count=5004`

### 6.2 Admin health panel doğrulaması (PASS)
- `GET /api/admin/system/health-detail`
  - `meili.status = connected`
  - `meili.connected = true`

### 6.3 Stage-smoke doğrulaması (PASS)
- `GET /api/admin/search/meili/stage-smoke?q=` → `200`
- `hits_count=10` (boş index değil)
- `ranking_sort = ["premium_score:desc", "published_at:desc"]`

### 6.4 Bulk reindex doğrulaması (PASS)
- `POST /api/admin/search/meili/reindex` → `indexed_docs=5004`
- Poll sonrası health `index_document_count=5004`
- DB active listing count = `5004`
- Sonuç: `Doc count == DB active listing count` ✅

### 6.5 Event-driven sync canlı doğrulama (PASS)
- Publish → index add ✅
- Unpublish → index remove ✅
- Soft-delete → index remove ✅

### 6.6 Retry queue doğrulaması (PASS)
- `POST /api/admin/search/meili/sync-jobs/retry-dead-letter` → retried `0`
- `POST /api/admin/search/meili/sync-jobs/process` → failed `0`, dead_letter `0`
- `GET /api/admin/search/meili/sync-jobs` metrics → `{"done": 39}`

## 7) P1.3 Facet + Dinamik Sidebar Başlangıç Doğrulaması

### 7.1 Facet mapping (Attribute Manager -> Meili)
- Filterable attribute: `renk_facet_test` (select)
- Meili filterable attributes içinde görünür: `attribute_renk_facet_test`

### 7.2 v2 search facet aggregation (PASS)
- `GET /api/v2/search?country=DE&category=<id>`
  - `facet_meta_keys = ["renk_facet_test"]`
  - `facets.renk_facet_test = [
      {"value":"siyah","count":1},
      {"value":"beyaz","count":0}
    ]`
- `GET /api/v2/search?...&attr[renk_facet_test]=siyah` → `200`, `pagination.total=1`

### 7.3 Sidebar UX davranışı
- Facet count dinamik güncelleniyor (Meili aggregation tabanlı)
- `count=0` olan seçenekler disable davranışını destekliyor (UI tarafında)

## 8) Bu Tur Sonucu

- P1.2 external doğrulaması gerçek Meili üzerinde PASS ile kapandı.
- P1.3 için facet aggregation + dinamik sidebar veri akışı backend/frontend’de aktif.