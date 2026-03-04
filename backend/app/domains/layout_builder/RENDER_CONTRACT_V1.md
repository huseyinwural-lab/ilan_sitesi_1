# Content Layout Render Contract v1

This document defines the `payload_json` contract returned by:

- `GET /api/site/content-layout/resolve`

## 1) Top-level shape

```json
{
  "rows": [
    {
      "id": "hero-row",
      "columns": [
        {
          "id": "col-main",
          "width": {
            "desktop": 12,
            "tablet": 12,
            "mobile": 12
          },
          "components": [
            {
              "key": "hero.banner",
              "props": {
                "title": "Öne çıkan ilanlar"
              },
              "visibility": {
                "desktop": true,
                "tablet": true,
                "mobile": true
              }
            }
          ]
        }
      ]
    }
  ]
}
```

## 2) Required fields

- `rows[]`
  - `id: string`
  - `columns[]`
    - `id: string`
    - `width.desktop|tablet|mobile: int` (1..12)
    - `components[]`
      - `key: string` (must exist in `layout_component_definitions.key`)
      - `props: object`

## 3) Optional fields

- `components[].visibility.desktop|tablet|mobile: boolean`
- `components[].variant: string`
- `components[].meta: object`

## 4) Runtime guarantees

- Endpoint only serves **published** revision payload.
- Resolve strategy order:
  1. Active category binding
  2. Default page (`category_id = null`)
- If no published revision exists, endpoint returns controlled 409 error.

## 5) Non-goals in v1

- Header/Footer rendering is out of scope (global shell remains static).
- Server-side component rendering is out of scope.
