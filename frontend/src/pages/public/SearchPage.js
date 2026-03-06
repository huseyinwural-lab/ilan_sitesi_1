import React, { useEffect, useMemo, useState } from 'react';
import { Loader2 } from 'lucide-react';
import { useLocation } from 'react-router-dom';
import AdSlot from '@/components/public/AdSlot';
import LayoutRenderer from '@/components/layout-builder/LayoutRenderer';
import { MenuSnapshotBlock } from '@/components/layout-builder/MenuSnapshotBlock';
import { EXTENDED_RUNTIME_REGISTRY } from '@/components/layout-builder/ExtendedRuntimeBlocks';
import { useSearchState } from '@/hooks/useSearchState';
import { useContentLayoutResolve } from '@/hooks/useContentLayoutResolve';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const SEARCH_MODULES = ['real_estate', 'vehicle', 'other'];

const normalizeCategoryToken = (value) => String(value || '').trim().toLowerCase();

const resolveCategoryContext = (categories, token) => {
  const normalizedToken = normalizeCategoryToken(token);
  if (!normalizedToken) return { selected: null, parent: null, isL1: false, isL2: false };

  for (const root of categories || []) {
    if (!root || typeof root !== 'object') continue;
    const rootTokens = [root.id, root.slug, root.slug_tr, root.slug_en].map(normalizeCategoryToken);
    if (rootTokens.includes(normalizedToken)) {
      return { selected: root, parent: null, isL1: true, isL2: false };
    }

    const children = Array.isArray(root.children) ? root.children : [];
    for (const child of children) {
      const childTokens = [child.id, child.slug, child.slug_tr, child.slug_en].map(normalizeCategoryToken);
      if (childTokens.includes(normalizedToken)) {
        return { selected: child, parent: root, isL1: false, isL2: true };
      }
    }
  }

  return { selected: null, parent: null, isL1: false, isL2: false };
};

const SearchLayoutEmptyState = ({ countryCode, pageType, moduleName, categoryId, error }) => (
  <section className="rounded-xl border border-dashed bg-white p-6 text-center" data-testid="search-runtime-layout-empty-state">
    <h1 className="text-base font-semibold" data-testid="search-runtime-layout-empty-title">Layout bulunamadı</h1>
    <p className="mt-1 text-sm text-slate-600" data-testid="search-runtime-layout-empty-description">
      Bu sayfa sadece Admin &gt; Site Design &gt; Content Builder publish edilmiş layoutlardan beslenir.
    </p>
    <p className="mt-2 text-xs text-slate-500" data-testid="search-runtime-layout-empty-meta">
      country={countryCode} · page_type={pageType} · module={moduleName} · category_id={categoryId || 'null'} · error={error || 'none'}
    </p>
  </section>
);

export default function SearchPage() {
  const location = useLocation();
  const [searchState, setSearchState] = useSearchState();
  const countryCode = useMemo(() => (localStorage.getItem('selected_country') || 'DE').toUpperCase(), []);

  const [categories, setCategories] = useState([]);
  const [searchItems, setSearchItems] = useState([]);

  useEffect(() => {
    let cancelled = false;

    const loadCategories = async () => {
      try {
        const responses = await Promise.all(
          SEARCH_MODULES.map((moduleKey) => fetch(`${API}/categories?module=${moduleKey}&country=${countryCode}`, { cache: 'no-store' })),
        );

        const payloads = await Promise.all(
          responses.map(async (response) => {
            if (!response.ok) return [];
            const data = await response.json().catch(() => ({}));
            return Array.isArray(data?.items) ? data.items : [];
          }),
        );

        if (cancelled) return;
        setCategories(payloads.flat());
      } catch {
        if (!cancelled) setCategories([]);
      }
    };

    loadCategories();
    return () => { cancelled = true; };
  }, [countryCode]);

  const categoryContext = useMemo(
    () => resolveCategoryContext(categories, searchState?.category),
    [categories, searchState?.category],
  );

  const queryParams = useMemo(() => new URLSearchParams(location.search || ''), [location.search]);
  const activeDoping = String(searchState?.doping || queryParams.get('doping_type') || '').toLowerCase();
  const isUrgentRoute = location.pathname.toLowerCase().includes('/acil') || activeDoping === 'urgent';

  const runtimePageType = useMemo(() => {
    if (isUrgentRoute) return 'urgent_listings';
    if (categoryContext.isL1) return 'category_l0_l1';
    return 'search_ln';
  }, [isUrgentRoute, categoryContext.isL1]);

  const runtimeModule = useMemo(() => {
    if (isUrgentRoute) return 'global';
    return String(categoryContext.selected?.module || 'global');
  }, [isUrgentRoute, categoryContext.selected]);

  const runtimeCategoryId = useMemo(() => {
    if (isUrgentRoute) return null;
    return categoryContext.selected?.id || null;
  }, [isUrgentRoute, categoryContext.selected]);

  const {
    loading: layoutLoading,
    error: layoutError,
    layout: resolvedLayout,
    hasLayoutRows,
  } = useContentLayoutResolve({
    country: countryCode,
    module: runtimeModule,
    pageType: runtimePageType,
    categoryId: runtimeCategoryId,
    enabled: Boolean(countryCode && runtimePageType && runtimeModule),
  });

  useEffect(() => {
    let cancelled = false;

    const loadSearchItems = async () => {
      try {
        const params = new URLSearchParams();
        params.set('country', countryCode);
        params.set('page', String(searchState.page || 1));
        params.set('limit', String(searchState.limit || 20));

        if (searchState.q) params.set('q', searchState.q);
        if (searchState.category) params.set('category', searchState.category);
        if (activeDoping) params.set('doping_type', activeDoping);

        const response = await fetch(`${API}/v2/search?${params.toString()}`, { cache: 'no-store' });
        if (!response.ok) throw new Error('search_failed');
        const payload = await response.json();
        if (cancelled) return;
        setSearchItems(Array.isArray(payload?.items) ? payload.items : []);
      } catch {
        if (!cancelled) setSearchItems([]);
      }
    };

    loadSearchItems();
    return () => { cancelled = true; };
  }, [countryCode, searchState.page, searchState.limit, searchState.q, searchState.category, activeDoping]);

  const runtimeRegistry = {
    ...EXTENDED_RUNTIME_REGISTRY,
    'shared.text-block': ({ props }) => (
      <section className="rounded-xl border bg-white p-4" data-testid="search-runtime-text-block">
        <h2 className="text-base font-semibold" data-testid="search-runtime-text-title">{props?.title || 'Başlık'}</h2>
        <p className="mt-1 text-sm text-slate-600" data-testid="search-runtime-text-body">{props?.body || ''}</p>
      </section>
    ),
    'shared.ad-slot': ({ props }) => (
      <section data-testid="search-runtime-ad-slot">
        <AdSlot placement={props?.placement || 'AD_SEARCH_TOP'} className="rounded-xl border" />
      </section>
    ),
    'menu.snapshot.*': ({ props, component }) => (
      <MenuSnapshotBlock props={props} componentKey={component?.key} />
    ),
  };

  const handleCategoryChange = (nextCategory) => {
    setSearchState({
      category: nextCategory || '',
      page: 1,
      doping: '',
    });
  };

  const runtimeContext = useMemo(() => ({
    countryCode,
    module: runtimeModule,
    categories,
    activeCategorySlug: searchState.category || runtimeCategoryId || null,
    activeCategoryId: runtimeCategoryId || null,
    onCategoryChange: handleCategoryChange,
    searchItems,
    listingCandidates: searchItems,
    featuredListing: searchItems[0] || null,
    urgentItems: isUrgentRoute ? searchItems : [],
    showcaseItems: activeDoping === 'showcase' ? searchItems : [],
  }), [
    countryCode,
    runtimeModule,
    categories,
    searchState.category,
    runtimeCategoryId,
    searchItems,
    isUrgentRoute,
    activeDoping,
  ]);

  return (
    <div className="bg-slate-50 py-6" data-testid="search-page">
      <div className="container mx-auto px-4" data-testid="search-runtime-layout-wrap">
        {layoutLoading ? (
          <div className="flex min-h-[220px] items-center justify-center" data-testid="search-runtime-layout-loading">
            <Loader2 className="h-6 w-6 animate-spin text-primary" />
          </div>
        ) : null}

        {!layoutLoading && hasLayoutRows ? (
          <LayoutRenderer
            payload={resolvedLayout?.revision?.payload_json}
            registry={runtimeRegistry}
            runtimeContext={runtimeContext}
            dataTestIdPrefix="search-runtime-layout"
          />
        ) : null}

        {!layoutLoading && !hasLayoutRows ? (
          <SearchLayoutEmptyState
            countryCode={countryCode}
            pageType={runtimePageType}
            moduleName={runtimeModule}
            categoryId={runtimeCategoryId}
            error={layoutError}
          />
        ) : null}
      </div>
    </div>
  );
}
