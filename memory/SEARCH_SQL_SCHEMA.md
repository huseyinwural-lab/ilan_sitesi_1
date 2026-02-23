# Public Search SQL Şeması (listings_search)

**Amaç:** Public Search için denormalize read model.

## Ana Alanlar
- listing_id (PK, UUID, FK → listings.id)
- title, description
- module, category_id, country_code, city
- price_amount, price_type, hourly_rate, currency
- status, is_premium, is_showcase
- seller_type, is_verified
- make_id, model_id, year
- attributes (JSONB), images (JSONB)
- published_at, created_at, updated_at
- tsv_tr, tsv_de (TSVECTOR, generated)

## Index Seti (v1)
- GIN: tsv_tr, tsv_de
- GIN: attributes (faceted filters)
- BTree: (status, country_code, module, published_at)
- BTree: (category_id, price_amount)
- BTree: (make_id, model_id, year)
- BTree: (seller_type, is_verified, published_at)

## Denormalize Stratejisi
- İlk faz: Mongo → Postgres ETL ile doldurulur
- İkinci faz: listing publish/update sırasında SQL update (event/queue)
- Opsiyonel: günlük incremental refresh (cron)
