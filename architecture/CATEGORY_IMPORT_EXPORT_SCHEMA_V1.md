# CATEGORY_IMPORT_EXPORT_SCHEMA_V1

Tarih: 2026-02-21
Amaç: Category master datanın JSON ile import/export edilmesi (full paket).

## 1) JSON Üst Şema

```json
{
  "metadata": {
    "schema": "CATEGORY_IMPORT_EXPORT_SCHEMA_V1",
    "exported_at": "ISO-8601",
    "module": "vehicle",
    "count": 12
  },
  "categories": [
    {
      "slug": {"tr": "otomobil", "en": "cars", "de": "autos"},
      "name": {"tr": "Otomobil", "en": "Cars", "de": "Autos"},
      "translations": {
        "tr": {"name": "Otomobil", "description": null, "meta_title": null, "meta_description": null},
        "en": {"name": "Cars", "description": null, "meta_title": null, "meta_description": null},
        "de": {"name": "Autos", "description": null, "meta_title": null, "meta_description": null}
      },
      "country_code": null,
      "allowed_countries": ["DE", "CH", "FR", "AT"],
      "sort_order": 10,
      "active_flag": true,
      "hierarchy_complete": true,
      "module": "vehicle",
      "schema_status": "published",
      "schema_version": 3,
      "form_schema": {
        "status": "published",
        "core_fields": {"title": {"required": true}}
      },
      "children": []
    }
  ]
}
```

## 2) Kurallar
- **slug**: dict veya string olabilir. Dict verilirse tr/en/de alanları tercih edilir.
- **name**: dict (tr/en/de) önerilir. Tek string gelirse tüm dillere kopyalanır.
- **children**: hiyerarşik yapı; import sırasında parent-child ilişkisi buradan çıkarılır.
- **schema_status**: import sırasında **draft** olarak yazılır, publish ayrı aksiyondur.

## 3) Dry-run + Commit
- Dry-run: ekleme/güncelleme/silme diff üretir.
- Commit: aynı dosyayı transactional uygular, schema_version **draft** olarak açılır.
- Publish: import batch ID ile draft → published.

## 4) Upload Limit
- Maks dosya boyutu: **10MB**
- Limit aşımı: **413**

