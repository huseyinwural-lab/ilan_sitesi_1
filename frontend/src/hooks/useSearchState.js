import { useMemo, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

/**
 * Hook to manage search state in URL
 * Implements PUBLIC_SEARCH_URL_STATE_SPEC_v1
 */
export const useSearchState = () => {
  const navigate = useNavigate();
  const location = useLocation();

  // Parse URL query params into structured state
  const searchState = useMemo(() => {
    const params = new URLSearchParams(location.search);
    const state = {
      q: params.get('q') || '',
      category: params.get('category') || null,
      make: params.get('make') || null,
      model: params.get('model') || null,
      doping: params.get('doping') || null,
      sort: params.get('sort') || 'date_desc',
      page: parseInt(params.get('page') || '1', 10),
      limit: parseInt(params.get('limit') || '20', 10),
      filters: {}, // Attributes and price
    };

    // Parse Price
    if (params.has('price_min')) state.filters.price_min = parseInt(params.get('price_min'), 10);
    if (params.has('price_max')) state.filters.price_max = parseInt(params.get('price_max'), 10);

    // Parse Attribute Filters: attr[key] or attr[key]_min/_max
    // We scan all params
    for (const [key, value] of params.entries()) {
      const match = key.match(/^attr\[([^\]]+)\](_min|_max)?$/);
      if (match) {
        const attrKey = match[1];
        const suffix = match[2];

        if (!state.filters[attrKey]) {
            // Check if we need to init as range or array
            // If suffix exists, it's a range. If not, it's likely an array (comma sep)
            // But we need to handle mixed cases carefully. 
            // For simplicity, we initialize based on what we see first, but standard structure helps.
            state.filters[attrKey] = suffix ? {} : [];
        }

        if (!suffix) {
           // It's a select/multi-select value (comma separated)
           // If it was initialized as object (range) by mistake (unlikely if loop order), reset?
           // Actually, URL spec says attr[key] is array, attr[key]_min is range. They shouldn't overlap for same key in schema.
           state.filters[attrKey] = value.split(',');
        } else {
           // It's a range value
           if (Array.isArray(state.filters[attrKey])) state.filters[attrKey] = {}; // Correction
           const val = parseInt(value, 10);
           if (suffix === '_min') state.filters[attrKey].min = val;
           if (suffix === '_max') state.filters[attrKey].max = val;
        }
      }
    }

    return state;
  }, [location.search]);

  // Update URL based on state changes
  const setSearchState = useCallback((newState) => {
    const current = { ...searchState, ...newState };
    
    // Build Query String
    const query = new URLSearchParams();

    // Core
    if (current.q) query.set('q', current.q);
    if (current.category) query.set('category', current.category);
    if (current.make) query.set('make', current.make);
    if (current.model) query.set('model', current.model);
    if (current.doping) query.set('doping', current.doping);
    if (current.sort && current.sort !== 'date_desc') query.set('sort', current.sort);
    if (current.page && current.page > 1) query.set('page', current.page.toString());
    if (current.limit && current.limit !== 20) query.set('limit', current.limit.toString());

    // Filters
    if (current.filters) {
      Object.entries(current.filters).forEach(([key, val]) => {
        if (key === 'price_min') {
           query.set('price_min', val.toString());
        } else if (key === 'price_max') {
           query.set('price_max', val.toString());
        } else {
           // Attributes
           if (Array.isArray(val) && val.length > 0) {
             query.set(`attr[${key}]`, val.join(','));
           } else if (typeof val === 'object' && val !== null) {
             if (val.min !== undefined) query.set(`attr[${key}]_min`, val.min.toString());
             if (val.max !== undefined) query.set(`attr[${key}]_max`, val.max.toString());
           } else if (typeof val === 'boolean') {
             // For boolean toggle (not explicitly in spec example but needed)
             // Usually boolean might be passed as attr[key]=true or handled as special case
             // Spec says: "boolean" -> Toggle Switch. 
             // We can treat it as value 'true' or 'false' in array or specific param.
             // Let's assume standard attr[key]=true/false if needed, or if API expects dedicated handling.
             // API code: `if val is True: sub_q = sub_q.where(ListingAttribute.value_boolean == True)`
             // So passing `attr[has_balcony]=true` works with standard array/value logic if backend parses it.
             // Let's serialize as string.
             if (val !== null) query.set(`attr[${key}]`, val.toString());
           }
        }
      });
    }

    // Canonical Sort of Params (Alphabetical keys)
    query.sort();

    navigate({ search: query.toString() }, { replace: false });
  }, [searchState, navigate]);

  return [searchState, setSearchState];
};
