# Public Search URL State Specification

**Document ID:** PUBLIC_SEARCH_URL_STATE_SPEC_v1  
**Date:** 2026-02-13  
**Status:** 🔒 FROZEN  
**Sprint:** P7.3  

---

## Purpose

This specification defines the URL query parameter format for public search, ensuring:
- SEO-friendly, indexable URLs
- Shareable links
- Browser back/forward support
- Canonical parameter ordering

---

## Parameter Reference

### Core Parameters

| Param | Type | Description | Example |
|-------|------|-------------|---------|
| `q` | string | Search query text | `q=bmw+3+series` |
| `category` | string | Category slug | `category=cars` |
| `sort` | string | Sort order | `sort=price_asc` |
| `page` | integer | Page number (1-based) | `page=2` |
| `limit` | integer | Items per page | `limit=20` |

### Price Filter

| Param | Type | Description | Example |
|-------|------|-------------|---------|
| `price_min` | integer | Minimum price | `price_min=10000` |
| `price_max` | integer | Maximum price | `price_max=50000` |

### Attribute Filters

| Param | Type | Description | Example |
|-------|------|-------------|---------|
| `attr[{key}]` | string/array | Attribute filter | `attr[brand]=bmw,mercedes` |
| `attr[{key}]_min` | number | Range min | `attr[year]_min=2020` |
| `attr[{key}]_max` | number | Range max | `attr[year]_max=2024` |

---

## URL Examples

### Basic Search

```
/search?q=apartment
```

### Category Browse

```
/search?category=real-estate
```

### Category + Filters

```
/search?category=cars&attr[brand]=bmw,mercedes&price_min=20000&price_max=80000
```

### Full Complex Query

```
/search?category=cars&q=sedan&attr[brand]=bmw&attr[fuel_type]=benzin,dizel&attr[year]_min=2020&price_max=100000&sort=price_asc&page=2&limit=20
```

---

## Canonicalization Rules

### Parameter Order

Parameters MUST be ordered alphabetically:

```
# Canonical Order:
1. attr[*] (alphabetically by key)
2. category
3. limit
4. page
5. price_max
6. price_min
7. q
8. sort
```

**Example:**
```
# Non-canonical:
/search?sort=date_desc&category=cars&q=bmw

# Canonical:
/search?category=cars&q=bmw&sort=date_desc
```

### Empty Value Handling

| Rule | Example |
|------|---------|
| Omit empty strings | `q=` → omit |
| Omit null values | `price_min=null` → omit |
| Omit default values | `page=1` → omit |
| Omit `limit=20` (default) | → omit |

### Array Value Format

```
# Single value:
attr[brand]=bmw

# Multiple values (comma-separated):
attr[brand]=bmw,mercedes,audi

# URL encoded:
attr[brand]=bmw%2Cmercedes%2Caudi
```

---

## Sort Options

| Value | Description | API Mapping |
|-------|-------------|-------------|
| `date_desc` | Newest first (default) | `created_at DESC` |
| `date_asc` | Oldest first | `created_at ASC` |
| `price_asc` | Cheapest first | `price ASC` |
| `price_desc` | Most expensive first | `price DESC` |

---

## Default Values

| Param | Default | Behavior |
|-------|---------|----------|
| `page` | 1 | Omit from URL if 1 |
| `limit` | 20 | Omit from URL if 20 |
| `sort` | `date_desc` | Omit from URL if default |

---

## URL Building Logic

### TypeScript Implementation

```typescript
interface SearchParams {
  q?: string;
  category?: string;
  sort?: string;
  page?: number;
  limit?: number;
  price_min?: number;
  price_max?: number;
  attrs?: Record<string, string[] | { min?: number; max?: number }>;
}

function buildSearchUrl(params: SearchParams): string {
  const query = new URLSearchParams();
  
  // Attributes (alphabetically)
  if (params.attrs) {
    const sortedKeys = Object.keys(params.attrs).sort();
    for (const key of sortedKeys) {
      const value = params.attrs[key];
      if (Array.isArray(value) && value.length > 0) {
        query.set(`attr[${key}]`, value.join(','));
      } else if (typeof value === 'object') {
        if (value.min != null) query.set(`attr[${key}]_min`, String(value.min));
        if (value.max != null) query.set(`attr[${key}]_max`, String(value.max));
      }
    }
  }
  
  // Core params (alphabetically)
  if (params.category) query.set('category', params.category);
  if (params.limit && params.limit !== 20) query.set('limit', String(params.limit));
  if (params.page && params.page !== 1) query.set('page', String(params.page));
  if (params.price_max != null) query.set('price_max', String(params.price_max));
  if (params.price_min != null) query.set('price_min', String(params.price_min));
  if (params.q) query.set('q', params.q);
  if (params.sort && params.sort !== 'date_desc') query.set('sort', params.sort);
  
  const queryString = query.toString();
  return queryString ? `/search?${queryString}` : '/search';
}
```

### URL Parsing Logic

```typescript
function parseSearchUrl(url: string): SearchParams {
  const params = new URLSearchParams(url.split('?')[1] || '');
  const result: SearchParams = {};
  
  // Parse core params
  if (params.has('q')) result.q = params.get('q')!;
  if (params.has('category')) result.category = params.get('category')!;
  if (params.has('sort')) result.sort = params.get('sort')!;
  if (params.has('page')) result.page = parseInt(params.get('page')!, 10);
  if (params.has('limit')) result.limit = parseInt(params.get('limit')!, 10);
  if (params.has('price_min')) result.price_min = parseInt(params.get('price_min')!, 10);
  if (params.has('price_max')) result.price_max = parseInt(params.get('price_max')!, 10);
  
  // Parse attribute params
  result.attrs = {};
  params.forEach((value, key) => {
    const match = key.match(/^attr\[([^\]]+)\](_min|_max)?$/);
    if (match) {
      const attrKey = match[1];
      const suffix = match[2];
      
      if (!suffix) {
        // Array values
        result.attrs![attrKey] = value.split(',');
      } else {
        // Range values
        if (!result.attrs![attrKey]) result.attrs![attrKey] = {};
        const range = result.attrs![attrKey] as { min?: number; max?: number };
        if (suffix === '_min') range.min = parseInt(value, 10);
        if (suffix === '_max') range.max = parseInt(value, 10);
      }
    }
  });
  
  return result;
}
```

---

## Browser History Integration

### React Hook Example

```typescript
function useSearchParams() {
  const navigate = useNavigate();
  const location = useLocation();
  
  const params = useMemo(() => parseSearchUrl(location.search), [location.search]);
  
  const setParams = useCallback((newParams: Partial<SearchParams>) => {
    const merged = { ...params, ...newParams };
    const url = buildSearchUrl(merged);
    navigate(url, { replace: false }); // Add to history
  }, [params, navigate]);
  
  return [params, setParams] as const;
}
```

### History Behavior

| Action | History Entry |
|--------|---------------|
| Filter change | Push new entry |
| Page change | Push new entry |
| Sort change | Push new entry |
| Clear all | Push new entry |
| Initial load | Replace current |

---

## SEO Considerations

### Canonical URL

```html
<link rel="canonical" href="https://example.com/search?category=cars&sort=price_asc" />
```

### Robots Meta

```html
<!-- Searchable category pages: index -->
<meta name="robots" content="index, follow" />

<!-- Filtered results: noindex (too many variations) -->
<meta name="robots" content="noindex, follow" />
```

### Indexability Rules

| Page Type | Index | Follow |
|-----------|-------|--------|
| Category root | ✅ Yes | ✅ Yes |
| Category + sort | ✅ Yes | ✅ Yes |
| Category + 1 filter | ✅ Yes | ✅ Yes |
| Category + 2+ filters | ❌ No | ✅ Yes |
| Text search results | ❌ No | ✅ Yes |
| Page 2+ | ❌ No | ✅ Yes |

---

## Shareable Link Guarantee

Every URL state MUST be:

1. **Reproducible:** Same URL → Same results
2. **Bookmarkable:** Save and return later
3. **Shareable:** Send to another user
4. **Stable:** No session dependencies

---

## Validation Rules

| Param | Validation |
|-------|------------|
| `page` | Integer >= 1 |
| `limit` | Integer 1-100 |
| `price_min` | Integer >= 0 |
| `price_max` | Integer > price_min |
| `sort` | Enum of valid options |
| `category` | Valid category slug |
| `attr[*]` | Valid attribute key |

### Invalid Parameter Handling

- Invalid values: Ignore, use default
- Unknown params: Pass through (forward compat)
- Malformed syntax: Ignore

---

## Gate Status

**SPEC FROZEN** - Implementation may begin.

---

## References

- Facet Renderer Spec: `/app/architecture/PUBLIC_SEARCH_FACET_RENDERER_SPEC_v1.md`
- Search API v2: `/app/backend/app/routers/search_routes.py`
