# ATTR_IMPORT_V1_SCHEMA

## JSON Yapısı
```json
{
  "attributes": [
    {
      "key": "engine_cc",
      "name": {"tr": "Motor Hacmi (cc)", "de": "Hubraum (cc)", "fr": "Cylindrée (cc)"},
      "attribute_type": "number",
      "unit": "cc",
      "is_filterable": true,
      "is_required": false,
      "options": [],
      "category_scope": [
        {"category_slug": "vasita", "inherit_to_children": true}
      ]
    }
  ]
}
```

## Alanlar
- `key` (string, zorunlu)
- `name` (object, zorunlu) → {tr, de, fr}
- `attribute_type` (string, zorunlu) → number | select | multi_select | text | boolean | date
- `unit` (string, opsiyonel)
- `is_filterable` (boolean, opsiyonel)
- `is_required` (boolean, opsiyonel)
- `options` (array, opsiyonel) → select/multi_select için
- `category_scope` (array, zorunlu) → {category_slug, inherit_to_children}

## Select Options Şeması
```json
{
  "value": "gasoline",
  "label": {"tr": "Gasoline", "de": "Gasoline", "fr": "Gasoline"}
}
```

## V1 Category Scope
- `category_slug`: **vasita** (root vehicle category)
