# CATEGORY_IMPORT_EXPORT_CSV_V1

Tarih: 2026-02-21
Delimiter: **,**
Amaç: Category master datayı flat CSV olarak import/export etmek.

## 1) CSV Kolonları

| Kolon | Zorunlu | Açıklama |
| --- | --- | --- |
| id | Hayır | Category UUID (export sırasında dolu) |
| parent_slug | Hayır | Üst kategori slug (tr) |
| path | Hayır | Hiyerarşik yol (otomobil.sedan) |
| module | Evet | vehicle / real_estate / services ... |
| country_code | Hayır | Tek ülke kısıtı (DE) |
| allowed_countries | Hayır | Pipe ile ayrılmış (DE|CH|FR) |
| sort_order | Hayır | Sıralama |
| active_flag | Hayır | true/false |
| slug_tr | Evet | TR slug |
| slug_en | Hayır | EN slug |
| slug_de | Hayır | DE slug |
| name_tr | Evet | TR isim |
| name_en | Hayır | EN isim |
| name_de | Hayır | DE isim |
| schema_status | Hayır | draft/published (importta draft yazılır) |
| schema_version | Hayır | latest version (exportta dolu) |
| form_schema | Hayır | JSON string |

## 2) Örnek Satır

```csv
id,parent_slug,path,module,country_code,allowed_countries,sort_order,active_flag,slug_tr,slug_en,slug_de,name_tr,name_en,name_de,schema_status,schema_version,form_schema
,otomobil,otomobil.sedan,vehicle,DE,DE|CH,20,true,sedan,sedan,limousine,Sedan,Sedan,Limousine,draft,1,"{""status"":""draft"",""core_fields"":{}}"
```

## 3) Kurallar
- **delimiter**: virgül (,)
- **allowed_countries** boş ise country_code uygulanır, o da boşsa global.
- **form_schema** JSON string olmalı.
- Import sonrası schema otomatik **draft** olur; publish batch üzerinden yapılır.

## 4) Upload Limit
- Maks dosya boyutu: **10MB**
- Limit aşımı: **413**

