# Public Search Facet Renderer Specification

**Document ID:** PUBLIC_SEARCH_FACET_RENDERER_SPEC_v1  
**Date:** 2026-02-13  
**Status:** 🔒 FROZEN  
**Sprint:** P7.3  

---

## Purpose

This specification defines how Search API v2 facet data maps to UI components. The frontend renders facets **contract-driven** - no hardcoded rules, only response-based rendering.

---

## Facet Type → Component Mapping

| Facet Type | UI Component | Behavior |
|------------|--------------|----------|
| `select` | Checkbox List | Multi-select, any combination |
| `multi_select` | Checkbox List | Same as select |
| `boolean` | Toggle Switch | On/Off single state |
| `number` (range) | Range Slider | Min/Max with inputs |
| `date` (range) | Date Picker | From/To selection |

---

## Component Specifications

### 1. Checkbox List (select, multi_select)

**Use For:** Brand, Color, Fuel Type, Body Type, etc.

**Layout:**
```
┌─────────────────────────────────────┐
│ Marka                          [▼]  │
├─────────────────────────────────────┤
│ ☑ BMW (45)                          │
│ ☐ Mercedes (38)                     │
│ ☐ Audi (32)                         │
│ ☐ Volkswagen (28)                   │
│ ☑ Tesla (15)                        │
│ ─────────────────                   │
│ [+ Daha fazla göster]               │
└─────────────────────────────────────┘
```

**Props:**
```typescript
interface CheckboxFacet {
  key: string;           // attribute key
  label: string;         // localized label
  options: FacetOption[];
  selectedValues: string[];
  onChange: (values: string[]) => void;
  maxVisible?: number;   // default 5
}

interface FacetOption {
  value: string;
  label: string;
  count: number;
  disabled?: boolean;    // if count = 0
}
```

**Behavior:**
- Multiple selection allowed
- Options sorted by count DESC, then label ASC
- Zero-count options shown but disabled
- "Show more" expands full list (if > maxVisible)
- Search within options (if > 10 options)

### 2. Toggle Switch (boolean)

**Use For:** Has Parking, Has Balcony, Furnished, etc.

**Layout:**
```
┌─────────────────────────────────────┐
│ Balkon        [═══●] Evet (120)     │
├─────────────────────────────────────┤
│ Eşyalı       [●═══] Hayır           │
└─────────────────────────────────────┘
```

**Props:**
```typescript
interface ToggleFacet {
  key: string;
  label: string;
  value: boolean | null;   // null = not filtered
  trueCount: number;
  falseCount: number;
  onChange: (value: boolean | null) => void;
}
```

**Behavior:**
- Three states: true, false, null (any)
- Click toggles through states
- Show count for selected state

### 3. Range Slider (number)

**Use For:** Price, Area (m²), Year, Mileage, etc.

**Layout:**
```
┌─────────────────────────────────────┐
│ Fiyat (EUR)                         │
├─────────────────────────────────────┤
│ [  10.000  ] — [  50.000  ]         │
│                                     │
│ ├──────●═════════●──────┤           │
│ 0                      100.000      │
└─────────────────────────────────────┘
```

**Props:**
```typescript
interface RangeFacet {
  key: string;
  label: string;
  unit?: string;          // EUR, m², km
  min: number;            // data min
  max: number;            // data max
  selectedMin?: number;
  selectedMax?: number;
  step?: number;          // default: auto
  onChange: (min: number | null, max: number | null) => void;
}
```

**Behavior:**
- Slider + manual input fields
- Input validation (min <= max)
- Debounce on input (300ms)
- Show unit suffix

### 4. Date Range Picker (date)

**Use For:** Listed Date, Build Year, etc.

**Layout:**
```
┌─────────────────────────────────────┐
│ İlan Tarihi                         │
├─────────────────────────────────────┤
│ [  01.01.2024  ] — [  31.12.2024  ] │
│         📅              📅          │
└─────────────────────────────────────┘
```

**Props:**
```typescript
interface DateFacet {
  key: string;
  label: string;
  minDate?: Date;
  maxDate?: Date;
  selectedFrom?: Date;
  selectedTo?: Date;
  onChange: (from: Date | null, to: Date | null) => void;
}
```

---

## Selected State Management

### Visual Indicators

| State | Visual |
|-------|--------|
| No filter | Default appearance |
| Filter active | Highlighted border + badge count |
| Multiple values | "2 seçili" badge |

### Selected Filters Summary

```
┌─────────────────────────────────────────────────────────┐
│ Aktif Filtreler:                                        │
│ [Marka: BMW, Tesla ×] [Fiyat: 10K-50K ×] [Temizle]     │
└─────────────────────────────────────────────────────────┘
```

---

## Apply/Clear Behavior

### Option 1: Instant Apply (Recommended)

- Each change immediately updates results
- No "Apply" button needed
- URL updates on each change
- Debounce rapid changes (300ms)

### Option 2: Batch Apply (Mobile Alternative)

- Changes staged locally
- "Uygula" button commits all
- Better for slow connections

**Decision:** Use **Instant Apply** for desktop, **Batch Apply** on mobile filter modal.

---

## Option Sorting

### Default Sort Order

1. **Count DESC** - Most results first
2. **Label ASC** - Alphabetical tiebreaker

### Special Cases

| Case | Handling |
|------|----------|
| Zero count | Show at bottom, disabled |
| Selected but zero | Keep visible, show strikethrough |
| New options | Insert by count |

---

## Facet Section Order

| Priority | Section | Example |
|----------|---------|---------|
| 1 | Category | Ana Kategori, Alt Kategori |
| 2 | Price/Range | Fiyat, m² |
| 3 | Primary Attributes | Marka, Model (vehicle) |
| 4 | Secondary Attributes | Renk, Yakıt Tipi |
| 5 | Boolean Filters | Balkon, Eşyalı |

---

## Responsive Behavior

### Desktop (>1024px)

- Sidebar always visible (280px width)
- Collapsible sections
- All facets visible

### Tablet (768-1024px)

- Sidebar collapsible
- Toggle button to show/hide
- Overlay mode optional

### Mobile (<768px)

- Full-screen filter modal
- Bottom sheet option
- "Filtrele" floating button
- Batch apply mode

---

## Empty/Error States

### No Options Available

```
┌─────────────────────────────────────┐
│ Renk                                │
├─────────────────────────────────────┤
│ Bu kategoride renk filtresi yok     │
└─────────────────────────────────────┘
```

### Loading State

```
┌─────────────────────────────────────┐
│ Marka                               │
├─────────────────────────────────────┤
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░     │
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░     │
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░     │
└─────────────────────────────────────┘
```

---

## API Contract Reference

### Search v2 Facet Response

```json
{
  "facets": {
    "brand": [
      {"value": "bmw", "label": "BMW", "count": 45},
      {"value": "mercedes", "label": "Mercedes", "count": 38}
    ],
    "fuel_type": [
      {"value": "benzin", "label": "Benzin", "count": 120},
      {"value": "dizel", "label": "Dizel", "count": 95}
    ]
  },
  "facet_meta": {
    "brand": {"type": "select", "label": "Marka"},
    "fuel_type": {"type": "select", "label": "Yakıt Tipi"},
    "price": {"type": "range", "label": "Fiyat", "min": 0, "max": 500000}
  }
}
```

---

## Component Registry

```typescript
const FACET_COMPONENTS = {
  'select': CheckboxFacetComponent,
  'multi_select': CheckboxFacetComponent,
  'boolean': ToggleFacetComponent,
  'number': RangeFacetComponent,
  'range': RangeFacetComponent,
  'date': DateFacetComponent,
};

function renderFacet(key: string, meta: FacetMeta, data: FacetData) {
  const Component = FACET_COMPONENTS[meta.type];
  return <Component key={key} {...meta} {...data} />;
}
```

---

## Gate Status

**SPEC FROZEN** - Implementation may begin.

Changes require:
1. Document version bump
2. Impact analysis
3. User approval

---

## References

- Search API v2: `/app/backend/app/routers/search_routes.py`
- Attribute Types: `/app/backend/app/models/attribute.py`
