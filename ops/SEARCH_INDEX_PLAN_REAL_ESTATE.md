# Search Index Plan (Real Estate)

## 1. Core Composite Index
Sorguların %80'i bu indeksi kullanacak.
`ix_listings_search_main`:
*   `status` (WHERE condition)
*   `country` (Partition key candidate)
*   `module` (real_estate)
*   `is_premium` (Sorting)
*   `created_at` (Sorting)

## 2. Filtering Indexes
*   `ix_listings_price`: `(country, price)`
*   `ix_listings_location`: `(country, city)`
*   `ix_listings_geo`: GIST index on `geometry(Point)` (PostGIS).

## 3. Attribute Indexing
JSONB içindeki alanları indekslemek yerine, sık kullanılanları (m², oda) `listing_attributes` tablosuna (EAV veya normalized) çıkarıp indeksleyeceğiz veya JSONB GIN index kullanacağız.
**Karar**: PostgreSQL JSONB GIN Index.
`ix_listings_attributes`: `USING GIN (attributes)`

## 4. Query Plan Strategy
*   **Radius Search**: `ST_DWithin(geom, ST_MakePoint(lon, lat)::geography, radius_m)`
*   **Pagination**: Keyset pagination `WHERE (is_premium, created_at) < (last_prem, last_date)`.
