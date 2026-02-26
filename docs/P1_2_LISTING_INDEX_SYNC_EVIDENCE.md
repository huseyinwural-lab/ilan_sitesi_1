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

## 6) Bu Tur Sonucu

- P1.2 backend sync altyapısı aktif.
- Meili projection modeli event-driven olarak listing lifecycle’a bağlandı.
- Retry/dead-letter mekanizması ve bulk reindex operasyonu hazır.

Not:
- "Gerçek external Meili URL + key" stage doğrulaması, admin panelden gerçek config girildikten sonra aynı endpointlerle (`health`, `stage-smoke`, `reindex`) canlı çalıştırılabilir.