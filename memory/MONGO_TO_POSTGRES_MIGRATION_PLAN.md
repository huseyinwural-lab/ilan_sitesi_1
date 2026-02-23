# Mongo → PostgreSQL Migration Plan (Public Search & Moderation)

**Kapsam:** Public Search + Moderation Flow
**Hedef:** Tek DB standardizasyonu, search performansı ve audit bütünlüğü

---

## 1) Collection → SQL Tablo Eşlemesi

| Mongo Collection | PostgreSQL Tablo | Notlar |
| --- | --- | --- |
| listings | listings | Ana ilan verisi (mevcut SQL modeline taşınır) |
| listings_search_index | listings_search | Search için denormalize alanlar + tsvector |
| moderation_queue | moderation_queue | Moderasyon kuyruğu, durum ve SLA alanları |
| moderation_actions | moderation_actions | Onay/ret, sebep, admin_id, timestamp |
| listing_reports | listing_reports | Kullanıcı şikayetleri |
| listing_views | listing_views | View/engagement metrikleri |
| listing_media | listing_media | Medya metaları (kapak, sıralama) |

> Not: Exact schema mevcut SQLAlchemy modelleri ile hizalanacak (listing, media, audit_log).

---

## 2) Veri Tip Dönüşüm Tablosu

| Mongo Tip | PostgreSQL Tip | Not |
| --- | --- | --- |
| ObjectId | UUID | Mapping tablosu ile deterministik dönüşüm |
| ISODate | timestamptz | UTC korunur |
| string | varchar/text | Uzun metinler için text |
| number (int/float) | integer/numeric | Price ve rating için numeric(12,2) |
| boolean | boolean | - |
| array | JSONB / ARRAY | Facet alanları JSONB, sabit liste ARRAY |
| object | JSONB | Esnek şema alanları |
| geo (lat/lon) | geography(Point) + numeric | PostGIS opsiyonu |

---

## 3) Index Stratejisi (Search Performance-First)

**Tam metin arama (tsvector):**
- `listings_search.tsv` → GIN (tr + de locale)

**Faceted filtreler (bileşik):**
- `(category_id, country_code, city_slug, price_amount)`
- `(category_id, price_amount)`
- `(module, status, published_at)`
- `(brand_id, model_id, year)`
- `(seller_type, verified, published_at)`

**Moderation:**
- `moderation_queue(status, priority, created_at)`
- `moderation_actions(listing_id, created_at)`

**Diğer:**
- `listing_media(listing_id, is_cover)`
- `listing_reports(listing_id, created_at)`

---

## 4) Cutover Stratejisi (Freeze Window + Controlled Cutover)

1. **Freeze Window** (trafik düşük saat):
   - Public search & moderation write işlemleri durdurulur (read-only mode)
2. **Data Snapshot**
   - Mongo snapshot al, export dump
3. **Transform**
   - ObjectId → UUID mapping
   - Denormalize search alanları oluştur
4. **Load**
   - Bulk insert (COPY) ile Postgres’e yükle
5. **Integrity Check**
   - Count eşleşmesi, random sample hash
6. **Switch Read Source**
   - Search ve moderation read’leri Postgres’e yönlendir
7. **Monitor**
   - 24h latency, error rate, query time takip

---

## 5) Rollback Planı (Mongo Read Fallback)

- Cutover sonrası ilk 24 saat:
  - `READ` fallback toggle aktif
  - Kritik hata durumunda Mongo read’e geri dön
- Postgres’e yazılan yeni datalar queue ile tamponlanır
- Fallback sonrası yeniden deneme

---

## 6) Risk Analizi

| Risk | Etki | Önlem |
| --- | --- | --- |
| Tsvector eşleşme farkı | Arama sonuçları sapar | A/B test + relevance tuning |
| Index şişmesi | Write latency artar | Index aşamalı açılır |
| Veri drift | Moderasyon akışı bozulur | Freeze window + integrity check |
| Geo filtre performansı | Yavaş query | PostGIS + bounding box index |

---

## 7) Migration Adımları (Özet)

1. Snapshot
2. Transform
3. Load
4. Integrity check
5. Switch read source
6. Monitor
7. Rollback window (Mongo read fallback)

## 8) Migration Task Breakdown (Uygulama)

1. **Schema Create**
   - listings_search, moderation_queue, moderation_actions, listing_reports, listing_media
2. **Data Migrate**
   - Snapshot al → ETL pipeline
3. **Index Build**
   - GIN tsvector + composite facets + geo
4. **Verify**
   - Row count + sample hash + referential integrity
5. **Freeze Window Cutover**
   - Read switch + monitor

## 9) Search Performance Benchmark (Mongo vs Postgres)

- Senaryolar:
  - Tam metin arama (başlık/description)
  - Facet filtre (kategori + fiyat + lokasyon)
  - Sıralama (price, published_at)
- Metikler:
  - p50/p95 latency
  - sonuç sayısı doğruluğu
  - CPU/memory

## 10) Moderation Workflow Parity Test

- Kuyruğa düşen ilan sayısı eşleşmesi
- Durum geçişleri: pending → approved/rejected
- SLA/priority hesapları
- Audit log tutarlılığı

