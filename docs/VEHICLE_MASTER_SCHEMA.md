# Vehicle Master Data JSON Schema

## Root Structure
- **Root**: JSON array
- **Format**: `Array<Record>`

## Required Fields (min)
| Field | Type | Description |
| --- | --- | --- |
| `year` | integer | Model year |
| `make` | string or object | Marka adı (`make.name` desteklenir) |
| `model` | string or object | Model adı (`model.name` desteklenir) |
| `trim` | string or object | Trim adı (`trim.name` desteklenir) |

## Optional Fields
| Field | Type | Description |
| --- | --- | --- |
| `trim_id` | string | Provider trim ID (varsa unique key olarak kullanılır) |
| `fuel_type` | string | Yakıt tipi |
| `body` | string | Kasa tipi |
| `transmission` | string | Vites |
| `drive` | string | Çekiş |
| `engine_type` | string | Motor tipi |
| `engine_position` | string | Motor konumu |
| `doors` | integer | Kapı sayısı |
| `cylinders` | integer | Silindir |
| `power` | number | Güç |
| `torque` | number | Tork |
| `top_speed` | number | Maks hız |
| `weight` | number | Ağırlık |
| `lkm_hwy` | number | L/100km |
| `seats` | integer | Koltuk |
| `sold_in_us` | boolean | US satış flag |

## Validation Rules
- **Parse → Schema → Business**
- Root mutlaka **array** olmalı.
- `year`, `make`, `model`, `trim` alanları zorunludur.
- `year` aralığı: **1900–2100**.
- Unique key: `trim_id` varsa o, yoksa `year + make + model + trim`.

## Example
```json
[
  {
    "make": "Audi",
    "model": "A4",
    "trim": "S Line",
    "year": 2022,
    "fuel_type": "gasoline",
    "body": "sedan",
    "transmission": "automatic",
    "power": 150
  }
]
```
