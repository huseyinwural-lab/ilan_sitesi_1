## SPRINT 5 PLAN LOCK (Master Data Engines)

### Kapsam
1. **Category Engine** (CRUD, flat response, audit-first)
2. **Attribute Engine** (CRUD, required/select validation, audit-first)
3. **Vehicle Master Data** (Make/Model CRUD, audit-first)
4. **Search Entegrasyonu** (public filter seçenekleri master data’dan)
5. **Admin UI Wiring** (/admin/categories, /admin/attributes, /admin/vehicle-makes, /admin/vehicle-models)
6. **Audit Taxonomy** (CATEGORY_CHANGE / ATTRIBUTE_CHANGE / VEHICLE_MASTER_DATA_CHANGE)
7. **E2E Gate** (kategori/attribute/make-model + search görünürlüğü)

### Kabul Kriterleri
- Category listesi **flat + parent_id** döner (tree UI frontend).
- Category slug unique: **(slug + country_code)**, global slug kendi içinde unique.
- Attribute key unique: **(key + category_id + country_code)**.
- Vehicle Model unique: **(slug + make_id)**.
- Public search filter seçenekleri **aktif master data** üzerinden gelir.
- Country-scope enforced (admin CRUD’da zorunlu).
- Audit-first tüm mutasyonlarda zorunlu.
