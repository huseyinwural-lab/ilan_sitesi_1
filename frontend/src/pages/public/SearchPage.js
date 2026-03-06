import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import { tr } from 'date-fns/locale';
import { GoogleMap, MarkerClustererF, MarkerF, useJsApiLoader } from '@react-google-maps/api';
import { Loader2, AlertCircle, Car, Search, ChevronRight, MapPin, List } from 'lucide-react';
import { useSearchState } from '@/hooks/useSearchState';
import { useContentLayoutResolve } from '@/hooks/useContentLayoutResolve';
import { FacetRenderer } from '@/components/search/FacetRenderer';
import { CategorySidebar } from '@/components/search/CategorySidebar';
import LayoutRenderer from '@/components/layout-builder/LayoutRenderer';
import { MenuSnapshotBlock } from '@/components/layout-builder/MenuSnapshotBlock';
import { EXTENDED_RUNTIME_REGISTRY } from '@/components/layout-builder/ExtendedRuntimeBlocks';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import AdSlot from '@/components/public/AdSlot';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${API_URL}/api`;
const DEFAULT_CENTER = { lat: 51.1657, lng: 10.4515 };
const SEARCH_MODULES = ['real_estate', 'vehicle', 'other'];

const formatPrice = (priceAmount, currency, priceType = 'FIXED', hourlyRate = null) => {
  const numeric = priceType === 'HOURLY' ? hourlyRate : priceAmount;
  if (numeric === null || numeric === undefined || numeric === '') return '-';
  const formatted = new Intl.NumberFormat('tr-TR', { maximumFractionDigits: 0 }).format(Number(numeric));
  const currencyLabel = currency || 'EUR';
  return priceType === 'HOURLY' ? `${formatted} ${currencyLabel} / saat` : `${formatted} ${currencyLabel}`;
};

const slugify = (text) => {
  return text
    .toString()
    .toLowerCase()
    .replace(/\s+/g, '-')
    .replace(/[^\w\-]+/g, '')
    .replace(/\-\-+/g, '-')
    .replace(/^-+/, '')
    .replace(/-+$/, '');
};

const parseCoordinate = (value) => {
  if (value === null || value === undefined || value === '') return null;
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return null;
  return numeric;
};

const normalizeCategoryToken = (value) => String(value || '').trim().toLowerCase();
const getCategoryQueryValue = (category) => category?.slug || category?.id || '';

const SearchMapPanel = ({
  apiKey,
  loading,
  mapItems,
  selectedListingId,
  hoveredListingId,
  onPinClick,
  onPinHover,
  onViewportBboxChange,
  resultCount,
}) => {
  const mapRef = useRef(null);
  const lastBboxRef = useRef('');
  const { isLoaded } = useJsApiLoader({
    id: 'search-map-script',
    googleMapsApiKey: apiKey || '',
  });

  const center = useMemo(() => {
    const first = mapItems[0];
    if (!first) return DEFAULT_CENTER;
    return { lat: first.lat, lng: first.lng };
  }, [mapItems]);

  const handleIdle = useCallback(() => {
    if (!mapRef.current || !onViewportBboxChange) return;
    const bounds = mapRef.current.getBounds();
    if (!bounds) return;
    const ne = bounds.getNorthEast();
    const sw = bounds.getSouthWest();
    const bboxValue = `${sw.lng()},${sw.lat()},${ne.lng()},${ne.lat()}`;
    if (bboxValue !== lastBboxRef.current) {
      lastBboxRef.current = bboxValue;
      onViewportBboxChange(bboxValue);
    }
  }, [onViewportBboxChange]);

  if (loading || !isLoaded) {
    return (
      <div className="h-[70vh] rounded-xl border bg-muted/20 flex items-center justify-center" data-testid="search-map-loading">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="relative h-[70vh] rounded-xl overflow-hidden border" data-testid="search-map-panel">
      <GoogleMap
        mapContainerStyle={{ width: '100%', height: '100%' }}
        center={center}
        zoom={10}
        onLoad={(map) => {
          mapRef.current = map;
          if (typeof window !== 'undefined') {
            window.__searchMapRef = map;
          }
        }}
        onIdle={handleIdle}
        options={{
          streetViewControl: false,
          mapTypeControl: false,
          fullscreenControl: false,
        }}
      >
        <MarkerClustererF options={{ maxZoom: 14 }}>
          {(clusterer) => (
            <>
              {mapItems.map((item) => {
                const isActive = selectedListingId === item.id || hoveredListingId === item.id;
                return (
                  <MarkerF
                    key={item.id}
                    clusterer={clusterer}
                    position={{ lat: item.lat, lng: item.lng }}
                    icon={isActive ? 'http://maps.google.com/mapfiles/ms/icons/red-dot.png' : 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png'}
                    onClick={() => onPinClick(item.id)}
                    onMouseOver={() => onPinHover(item.id)}
                    onMouseOut={() => onPinHover(null)}
                  />
                );
              })}
            </>
          )}
        </MarkerClustererF>
      </GoogleMap>

      {resultCount === 0 ? (
        <div className="absolute inset-0 bg-white/90 flex items-center justify-center p-6 text-center" data-testid="search-map-empty-state">
          <div>
            <div className="font-semibold">Sonuç bulunamadı</div>
            <div className="text-sm text-muted-foreground mt-1">Filtreleri değiştirerek tekrar deneyin.</div>
          </div>
        </div>
      ) : null}

      {resultCount > 0 && mapItems.length === 0 ? (
        <div className="absolute inset-x-4 top-4 rounded-lg border bg-white/95 p-3 text-xs" data-testid="search-map-no-coordinate-note">
          Bu sonuçlarda harita koordinatı olan ilan yok. İlanlar listede gösterilmeye devam ediyor.
        </div>
      ) : null}
    </div>
  );
};

export default function SearchPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchState, setSearchState] = useSearchState();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState({ items: [], facets: {}, pagination: {} });
  const [facetMeta, setFacetMeta] = useState({});
  const facetsEnabled = Object.keys(facetMeta || {}).length > 0;

  const [categories, setCategories] = useState([]);
  const [makes, setMakes] = useState([]);
  const [models, setModels] = useState([]);
  const [loadingMakes, setLoadingMakes] = useState(false);
  const [loadingModels, setLoadingModels] = useState(false);

  const [categoryShowcase, setCategoryShowcase] = useState([]);
  const [categoryShowcaseLoading, setCategoryShowcaseLoading] = useState(false);

  const [mapKey, setMapKey] = useState('');
  const [mapKeyError, setMapKeyError] = useState('');
  const [mapBbox, setMapBbox] = useState('');
  const [debouncedMapBbox, setDebouncedMapBbox] = useState('');

  const [hoveredListingId, setHoveredListingId] = useState(null);
  const [selectedListingId, setSelectedListingId] = useState(null);
  const [saveModalOpen, setSaveModalOpen] = useState(false);
  const [saveName, setSaveName] = useState('');
  const [saveEmailEnabled, setSaveEmailEnabled] = useState(true);
  const [savePushEnabled, setSavePushEnabled] = useState(false);
  const [saveLoading, setSaveLoading] = useState(false);
  const [saveError, setSaveError] = useState('');
  const [saveSuccess, setSaveSuccess] = useState('');
  const listRefs = useRef({});

  const countryCode = useMemo(() => (localStorage.getItem('selected_country') || 'DE').toUpperCase(), []);
  const isMapView = useMemo(() => new URLSearchParams(location.search).get('view') === 'map', [location.search]);

  useEffect(() => {
    let alive = true;
    const fetchCategories = async () => {
      try {
        const responses = await Promise.allSettled(
          SEARCH_MODULES.map((module) => fetch(`${API}/categories?module=${module}&country=${countryCode}`, { cache: 'no-store' })),
        );

        if (!alive) return;

        const payloads = await Promise.all(
          responses.map(async (result) => {
            if (result.status !== 'fulfilled') return [];
            const res = result.value;
            if (!res.ok) return [];
            const json = await res.json().catch(() => []);
            return Array.isArray(json) ? json : [];
          }),
        );

        setCategories(payloads.flat());
      } catch (_error) {
        if (alive) setCategories([]);
      }
    };

    fetchCategories();
    return () => {
      alive = false;
    };
  }, [countryCode]);

  useEffect(() => {
    let alive = true;
    const fetchMakes = async () => {
      setLoadingMakes(true);
      try {
        const res = await fetch(`${API}/v1/vehicle/makes?country=${countryCode}`);
        if (res.ok && alive) setMakes((await res.json()).items || []);
      } finally {
        if (alive) setLoadingMakes(false);
      }
    };
    fetchMakes();
    return () => {
      alive = false;
    };
  }, [countryCode]);

  useEffect(() => {
    let alive = true;
    const fetchModels = async () => {
      if (!searchState.make) {
        setModels([]);
        return;
      }
      setLoadingModels(true);
      try {
        const res = await fetch(`${API}/v1/vehicle/models?make=${searchState.make}&country=${countryCode}`);
        if (res.ok && alive) setModels((await res.json()).items || []);
      } finally {
        if (alive) setLoadingModels(false);
      }
    };
    fetchModels();
    return () => {
      alive = false;
    };
  }, [searchState.make, countryCode]);

  const categoryContext = useMemo(() => {
    if (!searchState.category || categories.length === 0) return null;

    const normalizedToken = normalizeCategoryToken(searchState.category);
    const selected = categories.find((item) => {
      const idMatch = normalizeCategoryToken(item.id) === normalizedToken;
      const slugMatch = normalizeCategoryToken(item.slug) === normalizedToken;
      return idMatch || slugMatch;
    });

    if (!selected) return null;

    const byId = new Map(categories.map((item) => [item.id, item]));
    const breadcrumb = [];
    let cursor = selected;
    const visited = new Set();
    while (cursor && !visited.has(cursor.id)) {
      visited.add(cursor.id);
      breadcrumb.unshift(cursor);
      cursor = cursor.parent_id ? byId.get(cursor.parent_id) : null;
    }

    const level = Math.max(0, breadcrumb.length - 1);
    const children = categories
      .filter((item) => item.parent_id === selected.id)
      .sort((a, b) => Number(a.sort_order || 0) - Number(b.sort_order || 0));

    const parent = selected.parent_id ? byId.get(selected.parent_id) : null;
    const siblings = categories
      .filter((item) => item.parent_id === selected.parent_id && item.id !== selected.id)
      .sort((a, b) => Number(a.sort_order || 0) - Number(b.sort_order || 0));

    return { selected, level, parent, breadcrumb, children, siblings };
  }, [searchState.category, categories]);

  const isL1CategoryTemplate = Boolean(categoryContext && categoryContext.level === 1);
  const isL2CategoryTemplate = Boolean(categoryContext && categoryContext.level >= 2);
  const isCategoryTemplate = isL1CategoryTemplate || isL2CategoryTemplate;
  const isVehicleCategory = (categoryContext?.selected?.module || '') === 'vehicle';
  const effectiveMapView = isMapView && !isCategoryTemplate;

  const runtimePageType = isL1CategoryTemplate ? 'category_l0_l1' : (isL2CategoryTemplate ? 'search_ln' : null);
  const runtimeModule = categoryContext?.selected?.module || 'global';
  const {
    layout: resolvedCategoryLayout,
    hasLayoutRows: hasResolvedCategoryLayoutRows,
  } = useContentLayoutResolve({
    country: countryCode,
    module: runtimeModule,
    pageType: runtimePageType,
    categoryId: categoryContext?.selected?.id,
    enabled: Boolean(runtimePageType && categoryContext?.selected?.id),
  });

  useEffect(() => {
    if (!isL1CategoryTemplate || !categoryContext?.selected?.id) {
      setCategoryShowcase([]);
      setCategoryShowcaseLoading(false);
      return;
    }

    let alive = true;
    const fetchCategoryShowcase = async () => {
      setCategoryShowcaseLoading(true);
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);
      try {
        const params = new URLSearchParams();
        params.set('country', countryCode);
        params.set('category', categoryContext.selected.id);
        params.set('doping_type', 'showcase');
        params.set('sort', 'date_desc');
        params.set('page', '1');
        params.set('limit', '8');
        const res = await fetch(`${API}/v2/search?${params.toString()}`, { cache: 'no-store', signal: controller.signal });
        if (!alive) return;
        if (!res.ok) {
          setCategoryShowcase([]);
          return;
        }
        const payload = await res.json();
        setCategoryShowcase(Array.isArray(payload?.items) ? payload.items : []);
      } catch (_error) {
        if (alive) setCategoryShowcase([]);
      } finally {
        clearTimeout(timeoutId);
        if (alive) setCategoryShowcaseLoading(false);
      }
    };

    fetchCategoryShowcase();
    return () => {
      alive = false;
    };
  }, [isL1CategoryTemplate, categoryContext?.selected?.id, countryCode]);

  useEffect(() => {
    if (!effectiveMapView) return;
    let alive = true;

    const loadMapRuntime = async () => {
      try {
        const res = await fetch(`${API}/places/map-runtime`, { cache: 'no-store' });
        if (!res.ok) throw new Error('Map runtime alınamadı');
        const payload = await res.json();
        if (!alive) return;
        if (!payload?.api_key) {
          setMapKey('');
          setMapKeyError('Google Maps API key yapılandırılmamış.');
          return;
        }
        setMapKey(payload.api_key);
        setMapKeyError('');
      } catch (_error) {
        if (!alive) return;
        setMapKey('');
        setMapKeyError('Harita servisi yüklenemedi.');
      }
    };

    loadMapRuntime();
    return () => {
      alive = false;
    };
  }, [effectiveMapView]);

  useEffect(() => {
    if (!effectiveMapView) {
      setDebouncedMapBbox('');
      return;
    }
    const timer = setTimeout(() => {
      setDebouncedMapBbox(mapBbox || '');
    }, 450);
    return () => clearTimeout(timer);
  }, [mapBbox, effectiveMapView]);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        const queryParams = new URLSearchParams();
        queryParams.set('country', countryCode);

        if (searchState.q) queryParams.set('q', searchState.q);
        if (searchState.category) queryParams.set('category', searchState.category);
        if (searchState.make) queryParams.set('make', searchState.make);
        if (searchState.model) queryParams.set('model', searchState.model);

        const queryParamsFromUrl = new URLSearchParams(location.search);
        const dopingFromUrl = queryParamsFromUrl.get('doping') || queryParamsFromUrl.get('badge');
        const activeDopingParam = searchState.doping || dopingFromUrl;
        if (activeDopingParam) queryParams.set('doping_type', activeDopingParam);

        if (searchState.sort) queryParams.set('sort', searchState.sort);
        queryParams.set('page', effectiveMapView ? '1' : String(searchState.page));
        queryParams.set('limit', effectiveMapView ? '300' : String(searchState.limit));

        if (searchState.filters.price_min !== undefined && searchState.filters.price_min !== null) {
          queryParams.set('price_min', searchState.filters.price_min);
        }
        if (searchState.filters.price_max !== undefined && searchState.filters.price_max !== null) {
          queryParams.set('price_max', searchState.filters.price_max);
        }

        Object.entries(searchState.filters || {}).forEach(([key, value]) => {
          if (key === 'price_min' || key === 'price_max') return;
          if (Array.isArray(value) && value.length > 0) {
            queryParams.set(`attr[${key}]`, value.join(','));
            return;
          }
          if (typeof value === 'object' && value !== null) {
            if (value.min !== undefined && value.min !== null) queryParams.set(`attr[${key}]_min`, String(value.min));
            if (value.max !== undefined && value.max !== null) queryParams.set(`attr[${key}]_max`, String(value.max));
            return;
          }
          if (typeof value === 'boolean') queryParams.set(`attr[${key}]`, value ? 'true' : 'false');
        });

        if (effectiveMapView && debouncedMapBbox) queryParams.set('bbox', debouncedMapBbox);

        const res = await fetch(`${API}/v2/search?${queryParams.toString()}`, { cache: 'no-store' });
        if (!res.ok) throw new Error('Search failed');

        const json = await res.json();
        setData(json);
        setFacetMeta(json.facet_meta || {});
      } catch (_error) {
        setError('İlanlar yüklenirken bir hata oluştu.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [searchState, location.search, effectiveMapView, debouncedMapBbox, countryCode]);

  useEffect(() => {
    if (!selectedListingId) return;
    const node = listRefs.current[selectedListingId];
    if (node && typeof node.scrollIntoView === 'function') {
      node.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, [selectedListingId, data.items]);

  useEffect(() => {
    if (!effectiveMapView || typeof window === 'undefined') return;
    window.__searchMapDebug = {
      selectFromPin: (listingId) => {
        setSelectedListingId(listingId);
        setHoveredListingId(listingId);
      },
      getMapItemIds: () => {
        return (data.items || [])
          .map((item) => ({ id: item.id, lat: parseCoordinate(item.lat), lng: parseCoordinate(item.lng) }))
          .filter((item) => item.lat !== null && item.lng !== null)
          .slice(0, 300)
          .map((item) => item.id);
      },
    };
    return () => {
      if (window.__searchMapDebug) {
        delete window.__searchMapDebug;
      }
    };
  }, [data.items, effectiveMapView]);

  const mapItems = useMemo(() => {
    return (data.items || [])
      .map((item) => ({
        ...item,
        lat: parseCoordinate(item.lat),
        lng: parseCoordinate(item.lng),
      }))
      .filter((item) => item.lat !== null && item.lng !== null)
      .slice(0, 300);
  }, [data.items]);

  const dopingFromUrl = useMemo(() => {
    const params = new URLSearchParams(location.search);
    return params.get('doping') || params.get('badge');
  }, [location.search]);
  const activeDoping = searchState.doping || dopingFromUrl;

  const handleCategoryChange = (categoryId) => setSearchState({ category: categoryId, filters: {}, page: 1 });

  const searchTitle = useMemo(() => {
    if (activeDoping === 'urgent') return 'Acil İlanlar';
    if (activeDoping === 'showcase') return 'Vitrin İlanları';
    if (categoryContext?.selected) return categoryContext.selected.name;
    if (searchState.category) return `Kategori: ${searchState.category}`;
    return 'Tüm İlanlar';
  }, [activeDoping, categoryContext, searchState.category]);

  const isUrgentSearch = activeDoping === 'urgent';
  const isShowcaseSearch = activeDoping === 'showcase';

  useEffect(() => {
    const title = `${searchTitle} | annonceia`;
    let description = 'Güncel ilanları filtreleyin, kategorilere göre keşfedin ve size uygun sonuçlara hızlıca ulaşın.';
    if (isUrgentSearch) description = 'Acil ilanları tek listede görüntüleyin.';
    if (isShowcaseSearch) description = 'Vitrin ilanlarında öne çıkan seçenekleri keşfedin.';

    document.title = title;
    const meta = document.querySelector('meta[name="description"]');
    if (meta) meta.setAttribute('content', description);
  }, [searchTitle, isUrgentSearch, isShowcaseSearch]);

  const handleMakeChange = (makeKey) => setSearchState({ make: makeKey === 'all' ? null : makeKey, model: null, page: 1 });
  const handleModelChange = (modelKey) => setSearchState({ model: modelKey === 'all' ? null : modelKey, page: 1 });
  const handleFilterChange = (newFilters) => setSearchState({ filters: newFilters, page: 1 });
  const handleSortChange = (val) => setSearchState({ sort: val });

  const handlePageChange = (newPage) => {
    setSearchState({ page: newPage });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleOpenSaveSearch = () => {
    const token = localStorage.getItem('access_token') || localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }
    setSaveName(searchState.q ? `"${searchState.q}" araması` : 'Yeni kayıtlı arama');
    setSaveEmailEnabled(true);
    setSavePushEnabled(false);
    setSaveError('');
    setSaveSuccess('');
    setSaveModalOpen(true);
  };

  const handleSaveSearch = async () => {
    const token = localStorage.getItem('access_token') || localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }

    const payload = {
      name: (saveName || '').trim(),
      filters_json: {
        q: searchState.q || '',
        category: searchState.category || null,
        make: searchState.make || null,
        model: searchState.model || null,
        sort: searchState.sort || null,
        page: searchState.page || 1,
        limit: searchState.limit || 20,
        filters: searchState.filters || {},
        country: countryCode,
      },
      query_string: location.search.startsWith('?') ? location.search.slice(1) : location.search,
      email_enabled: saveEmailEnabled,
      push_enabled: savePushEnabled,
    };

    if (!payload.name || payload.name.length < 2) {
      setSaveError('Arama adı en az 2 karakter olmalı.');
      return;
    }

    setSaveLoading(true);
    setSaveError('');
    setSaveSuccess('');
    try {
      const res = await fetch(`${API}/v1/saved-searches`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });
      const responseData = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(responseData?.detail || 'Arama kaydedilemedi');
      }
      setSaveSuccess('Arama kaydedildi.');
      setTimeout(() => setSaveModalOpen(false), 600);
    } catch (err) {
      setSaveError(err.message || 'Arama kaydedilemedi');
    } finally {
      setSaveLoading(false);
    }
  };

  const toggleMapView = (enableMap) => {
    const params = new URLSearchParams(location.search);
    if (enableMap) {
      params.set('view', 'map');
      params.delete('page');
    } else {
      params.delete('view');
      params.delete('bbox');
      setMapBbox('');
      setDebouncedMapBbox('');
    }
    navigate({ pathname: location.pathname, search: params.toString() }, { replace: false });
  };

  const renderStateBlock = (prefix = 'search') => {
    if (loading) {
      return (
        <div className="flex justify-center items-center h-64" data-testid={`${prefix}-results-loading`}>
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      );
    }

    if (error) {
      return (
        <Alert variant="destructive" data-testid={`${prefix}-results-error-alert`}>
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Hata</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      );
    }

    if ((data.items || []).length === 0) {
      return (
        <div className="text-center py-12 bg-muted/30 rounded-lg" data-testid={`${prefix}-empty-state`}>
          <div className="bg-muted rounded-full p-4 w-16 h-16 mx-auto mb-4 flex items-center justify-center" data-testid={`${prefix}-empty-icon-wrap`}>
            <Search className="h-8 w-8 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-medium" data-testid={`${prefix}-empty-title`}>
            {isUrgentSearch ? 'Şu an aktif acil ilan bulunmuyor' : 'Sonuç bulunamadı'}
          </h3>
          <p className="text-muted-foreground mt-2" data-testid={`${prefix}-empty-description`}>
            Arama kriterlerinizi değiştirerek tekrar deneyin.
          </p>
          <Button variant="outline" className="mt-4" onClick={() => handleFilterChange({})} data-testid={`${prefix}-empty-clear-filters`}>
            Filtreleri Temizle
          </Button>
        </div>
      );
    }

    return null;
  };

  const renderPagination = (prefix = 'search', compact = false) => {
    if (compact || !data.pagination?.pages || data.pagination.pages <= 1) return null;
    return (
      <div className="flex flex-wrap justify-center gap-2 mt-8" data-testid={`${prefix}-pagination`}>
        <Button variant="outline" size="sm" disabled={searchState.page <= 1} onClick={() => handlePageChange(searchState.page - 1)} data-testid={`${prefix}-pagination-prev`}>
          Önceki
        </Button>
        <span className="flex items-center px-4 text-sm font-medium" data-testid={`${prefix}-pagination-indicator`}>
          Sayfa {searchState.page} / {data.pagination.pages}
        </span>
        <Button variant="outline" size="sm" disabled={searchState.page >= data.pagination.pages} onClick={() => handlePageChange(searchState.page + 1)} data-testid={`${prefix}-pagination-next`}>
          Sonraki
        </Button>
      </div>
    );
  };

  const renderGridCards = (compact = false, prefix = 'search') => {
    const state = renderStateBlock(prefix);
    if (state) return state;

    return (
      <div className="space-y-6" data-testid={compact ? `${prefix}-results-list-compact` : `${prefix}-results-list`}>
        <div className={compact ? 'space-y-3' : 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4'}>
          {data.items.map((item) => {
            const isActive = selectedListingId === item.id || hoveredListingId === item.id;
            return (
              <Card
                key={item.id}
                ref={(node) => {
                  if (node) listRefs.current[item.id] = node;
                }}
                className={`overflow-hidden hover:shadow-md transition-shadow group cursor-pointer ${isActive ? 'ring-2 ring-blue-500' : ''}`}
                style={{
                  borderColor: item.is_featured ? '#4f46e5' : (item.is_urgent ? '#e11d48' : undefined),
                  borderWidth: item.is_featured || item.is_urgent ? 2 : 1,
                }}
                onMouseEnter={() => setHoveredListingId(item.id)}
                onMouseLeave={() => setHoveredListingId(null)}
                onClick={() => navigate(`/ilan/${slugify(item.title)}-${item.id}`)}
                data-testid={`${prefix}-result-card-${item.id}`}
              >
                <div className="aspect-[4/3] relative bg-gray-100 overflow-hidden" data-testid={`${prefix}-result-image-wrap-${item.id}`}>
                  {item.image ? (
                    <img src={item.image} alt={item.title} className="object-cover w-full h-full group-hover:scale-105 transition-transform duration-300" loading="lazy" data-testid={`${prefix}-result-image-${item.id}`} />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-muted-foreground" data-testid={`${prefix}-result-image-empty-${item.id}`}>
                      <Car className="h-12 w-12 opacity-20" />
                    </div>
                  )}
                  <Badge className="absolute top-2 right-2 bg-black/50 hover:bg-black/70 backdrop-blur-sm border-none" data-testid={`${prefix}-result-price-badge-${item.id}`}>
                    {formatPrice(item.price_amount ?? item.price, item.currency, item.price_type, item.hourly_rate)}
                  </Badge>
                </div>
                <CardHeader className="p-4 pb-2">
                  <div className="mb-1 flex flex-wrap items-center gap-1" data-testid={`${prefix}-result-doping-badges-${item.id}`}>
                    {item.is_featured ? <span className="rounded-full bg-indigo-100 px-2 py-0.5 text-[11px] font-semibold text-indigo-700" data-testid={`${prefix}-result-badge-showcase-${item.id}`}>Vitrin</span> : null}
                    {item.is_urgent ? <span className="rounded-full bg-rose-100 px-2 py-0.5 text-[11px] font-semibold text-rose-700" data-testid={`${prefix}-result-badge-urgent-${item.id}`}>Acil</span> : null}
                  </div>
                  <CardTitle className="text-base line-clamp-2 leading-tight" data-testid={`${prefix}-result-title-${item.id}`}>{item.title}</CardTitle>
                </CardHeader>
                <CardFooter className="p-4 pt-0 text-sm text-muted-foreground flex justify-between">
                  <span data-testid={`${prefix}-result-city-${item.id}`}>{item.city || 'Konum yok'}</span>
                  <span data-testid={`${prefix}-result-date-${item.id}`}>{format(new Date(), 'd MMM', { locale: tr })}</span>
                </CardFooter>
              </Card>
            );
          })}
        </div>
        {renderPagination(prefix, compact)}
      </div>
    );
  };

  const renderRowCards = (prefix = 'search-row') => {
    const state = renderStateBlock(prefix);
    if (state) return state;

    return (
      <div className="space-y-3" data-testid={`${prefix}-results-list`}>
        {data.items.map((item) => (
          <article
            key={item.id}
            ref={(node) => {
              if (node) listRefs.current[item.id] = node;
            }}
            className="rounded-2xl border bg-white p-3 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
            data-testid={`${prefix}-card-${item.id}`}
          >
            <Link to={`/ilan/${slugify(item.title)}-${item.id}`} className="grid grid-cols-1 md:grid-cols-[220px_minmax(0,1fr)_160px] gap-3" data-testid={`${prefix}-link-${item.id}`}>
              <div className="relative aspect-[4/3] md:aspect-auto md:h-[132px] overflow-hidden rounded-xl bg-muted" data-testid={`${prefix}-image-wrap-${item.id}`}>
                {item.image ? (
                  <img src={item.image} alt={item.title} className="h-full w-full object-cover" loading="lazy" data-testid={`${prefix}-image-${item.id}`} />
                ) : (
                  <div className="h-full w-full flex items-center justify-center text-muted-foreground" data-testid={`${prefix}-image-empty-${item.id}`}>
                    <Car className="h-8 w-8 opacity-30" />
                  </div>
                )}
              </div>

              <div className="min-w-0 space-y-2" data-testid={`${prefix}-content-${item.id}`}>
                <div className="flex flex-wrap items-center gap-1" data-testid={`${prefix}-badges-${item.id}`}>
                  {item.is_featured ? <span className="rounded-full bg-indigo-100 px-2 py-0.5 text-[11px] font-semibold text-indigo-700" data-testid={`${prefix}-badge-showcase-${item.id}`}>Vitrin</span> : null}
                  {item.is_urgent ? <span className="rounded-full bg-rose-100 px-2 py-0.5 text-[11px] font-semibold text-rose-700" data-testid={`${prefix}-badge-urgent-${item.id}`}>Acil</span> : null}
                </div>
                <h3 className="line-clamp-2 font-semibold text-base" data-testid={`${prefix}-title-${item.id}`}>{item.title}</h3>
                <div className="text-sm text-muted-foreground flex items-center gap-2" data-testid={`${prefix}-meta-${item.id}`}>
                  <span data-testid={`${prefix}-city-${item.id}`}>{item.city || 'Konum yok'}</span>
                  <span aria-hidden>•</span>
                  <span data-testid={`${prefix}-date-${item.id}`}>{format(new Date(), 'd MMM', { locale: tr })}</span>
                </div>
              </div>

              <div className="md:text-right md:flex md:flex-col md:justify-between" data-testid={`${prefix}-price-wrap-${item.id}`}>
                <div className="text-lg font-extrabold text-primary" data-testid={`${prefix}-price-${item.id}`}>
                  {formatPrice(item.price_amount ?? item.price, item.currency, item.price_type, item.hourly_rate)}
                </div>
                <div className="text-xs text-muted-foreground" data-testid={`${prefix}-cta-${item.id}`}>
                  İlanı incele →
                </div>
              </div>
            </Link>
          </article>
        ))}
        {renderPagination(prefix, false)}
      </div>
    );
  };

  const renderFilterPanel = (prefix = 'search-filter', showVehicleFilters = false) => (
    <Card data-testid={`${prefix}-card`}>
      <CardContent className="p-4" data-testid={`${prefix}-content`}>
        <CategorySidebar
          categories={categories}
          activeCategorySlug={searchState.category}
          onCategoryChange={handleCategoryChange}
          treeBehavior="expanded"
          showCounts
        />
        {showVehicleFilters ? (
          <>
            <div className="my-4 border-t border-border" data-testid={`${prefix}-vehicle-divider`} />
            <div className="space-y-3" data-testid={`${prefix}-vehicle-filters`}>
              <div data-testid={`${prefix}-make-wrap`}>
                <div className="text-sm font-medium text-muted-foreground mb-1" data-testid={`${prefix}-make-label`}>Marka</div>
                <Select value={searchState.make || 'all'} onValueChange={handleMakeChange}>
                  <SelectTrigger data-testid={`${prefix}-make-trigger`}><SelectValue placeholder={loadingMakes ? 'Yükleniyor...' : 'Tüm Markalar'} /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Tümü</SelectItem>
                    {makes.map((make) => <SelectItem key={make.id} value={make.key}>{make.label}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div data-testid={`${prefix}-model-wrap`}>
                <div className="text-sm font-medium text-muted-foreground mb-1" data-testid={`${prefix}-model-label`}>Model</div>
                <Select value={searchState.model || 'all'} onValueChange={handleModelChange} disabled={!searchState.make || loadingModels}>
                  <SelectTrigger data-testid={`${prefix}-model-trigger`}><SelectValue placeholder="Tüm Modeller" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Tümü</SelectItem>
                    {models.map((model) => <SelectItem key={model.id} value={model.key}>{model.label}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </>
        ) : null}

        {facetsEnabled ? (
          <>
            <div className="my-4 border-t" data-testid={`${prefix}-facet-divider`} />
            <div data-testid={`${prefix}-facet-renderer`}>
              <FacetRenderer facets={data.facets} facetMeta={facetMeta} selections={searchState.filters} onFilterChange={handleFilterChange} />
            </div>
          </>
        ) : null}
      </CardContent>
    </Card>
  );

  const renderSortAndSave = (prefix = 'search-header') => (
    <div className="flex items-center gap-2 w-full md:w-auto" data-testid={`${prefix}-actions`}>
      <Select value={searchState.sort} onValueChange={handleSortChange}>
        <SelectTrigger className="w-full md:w-[180px]" data-testid={`${prefix}-sort-trigger`}>
          <SelectValue placeholder="Sıralama" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="date_desc">En Yeni</SelectItem>
          <SelectItem value="date_asc">En Eski</SelectItem>
          <SelectItem value="price_asc">Fiyat (Artan)</SelectItem>
          <SelectItem value="price_desc">Fiyat (Azalan)</SelectItem>
        </SelectContent>
      </Select>

      <Button type="button" onClick={handleOpenSaveSearch} data-testid={`${prefix}-save-open-button`}>
        Aramayı Kaydet
      </Button>
    </div>
  );

  const renderL1DefaultTemplate = () => (
    <section className="space-y-6" data-testid="search-l1-template-root">
      <header className="rounded-2xl border border-slate-200 bg-gradient-to-r from-amber-50 via-white to-sky-50 p-5 md:p-6" data-testid="search-l1-header">
        <nav className="flex items-center flex-wrap gap-1 text-sm text-muted-foreground mb-3" data-testid="search-l1-breadcrumb">
          <button type="button" className="hover:text-foreground" onClick={() => handleCategoryChange(null)} data-testid="search-l1-breadcrumb-home">Ana Sayfa</button>
          {categoryContext?.breadcrumb?.map((node, index) => (
            <React.Fragment key={node.id}>
              <ChevronRight className="h-4 w-4" />
              {index === categoryContext.breadcrumb.length - 1 ? (
                <span className="font-semibold text-foreground" data-testid={`search-l1-breadcrumb-current-${node.id}`}>{node.name}</span>
              ) : (
                <button
                  type="button"
                  className="hover:text-foreground"
                  onClick={() => handleCategoryChange(getCategoryQueryValue(node))}
                  data-testid={`search-l1-breadcrumb-link-${node.id}`}
                >
                  {node.name}
                </button>
              )}
            </React.Fragment>
          ))}
        </nav>

        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4" data-testid="search-l1-header-row">
          <div>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold leading-[1.05]" data-testid="search-l1-title">{categoryContext?.selected?.name}</h1>
            <p className="text-sm md:text-base text-muted-foreground mt-2" data-testid="search-l1-result-count">{data.pagination.total || 0} ilan bulundu</p>
          </div>
          {renderSortAndSave('search-l1-header')}
        </div>
      </header>

      <section className="rounded-2xl border bg-card p-4 md:p-5" data-testid="search-l1-subcategory-section">
        <div className="flex items-center justify-between gap-2 mb-3" data-testid="search-l1-subcategory-heading-wrap">
          <h2 className="text-base md:text-lg font-bold" data-testid="search-l1-subcategory-heading">Alt Kategoriler</h2>
          <span className="text-xs text-muted-foreground" data-testid="search-l1-subcategory-count">{categoryContext?.children?.length || 0} kategori</span>
        </div>
        {categoryContext?.children?.length ? (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4" data-testid="search-l1-subcategory-grid">
            {categoryContext.children.map((child) => (
              <button
                type="button"
                key={child.id}
                onClick={() => handleCategoryChange(getCategoryQueryValue(child))}
                className="rounded-xl border bg-white px-4 py-3 text-left transition hover:border-primary hover:shadow-sm"
                data-testid={`search-l1-subcategory-card-${child.id}`}
              >
                <div className="font-semibold text-sm" data-testid={`search-l1-subcategory-name-${child.id}`}>{child.name}</div>
                <div className="text-xs text-muted-foreground mt-1" data-testid={`search-l1-subcategory-listing-count-${child.id}`}>{Number(child.listing_count || 0)} ilan</div>
              </button>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground" data-testid="search-l1-subcategory-empty">Bu kategoride alt kategori bulunmuyor.</p>
        )}
      </section>

      <section className="rounded-2xl border bg-card p-4 md:p-5" data-testid="search-l1-showcase-section">
        <div className="flex items-center justify-between gap-2 mb-3" data-testid="search-l1-showcase-heading-wrap">
          <h2 className="text-base md:text-lg font-bold" data-testid="search-l1-showcase-heading">Bu Kategoride Vitrin İlanları</h2>
          <Link
            to={`/search?category=${encodeURIComponent(categoryContext?.selected?.id || '')}&doping=showcase`}
            className="text-xs font-semibold hover:underline"
            data-testid="search-l1-showcase-see-all-link"
          >
            Tümünü Gör
          </Link>
        </div>

        {categoryShowcaseLoading ? (
          <div className="h-24 flex items-center justify-center" data-testid="search-l1-showcase-loading">
            <Loader2 className="h-5 w-5 animate-spin text-primary" />
          </div>
        ) : categoryShowcase.length ? (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4" data-testid="search-l1-showcase-grid">
            {categoryShowcase.map((item) => (
              <Link
                key={item.id}
                to={`/ilan/${slugify(item.title)}-${item.id}`}
                className="rounded-xl border overflow-hidden bg-white hover:shadow-sm"
                data-testid={`search-l1-showcase-card-${item.id}`}
              >
                <div className="aspect-[4/3] bg-muted" data-testid={`search-l1-showcase-image-wrap-${item.id}`}>
                  {item.image ? <img src={item.image} alt={item.title} className="h-full w-full object-cover" data-testid={`search-l1-showcase-image-${item.id}`} /> : null}
                </div>
                <div className="p-3">
                  <div className="text-xs text-amber-700 font-semibold" data-testid={`search-l1-showcase-badge-${item.id}`}>VİTRİN</div>
                  <div className="line-clamp-2 text-sm font-semibold" data-testid={`search-l1-showcase-title-${item.id}`}>{item.title}</div>
                  <div className="mt-1 text-sm font-bold text-primary" data-testid={`search-l1-showcase-price-${item.id}`}>{formatPrice(item.price_amount ?? item.price, item.currency, item.price_type, item.hourly_rate)}</div>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground" data-testid="search-l1-showcase-empty">Bu kategori için aktif vitrin ilanı bulunamadı.</p>
        )}
      </section>

      <section className="grid grid-cols-1 xl:grid-cols-[320px_minmax(0,1fr)] gap-5" data-testid="search-l1-results-shell">
        <aside className="space-y-4" data-testid="search-l1-filter-sidebar">
          {renderFilterPanel('search-l1-filter', isVehicleCategory)}
        </aside>
        <div className="space-y-3" data-testid="search-l1-results-panel">
          {renderRowCards('search-l1-row')}
        </div>
      </section>
    </section>
  );

  const renderL2DefaultTemplate = () => (
    <section className="space-y-4" data-testid="search-l2-template-root">
      <header className="rounded-2xl border bg-card p-4 md:p-5" data-testid="search-l2-header">
        <nav className="flex items-center flex-wrap gap-1 text-sm text-muted-foreground mb-3" data-testid="search-l2-breadcrumb">
          <button type="button" className="hover:text-foreground" onClick={() => handleCategoryChange(null)} data-testid="search-l2-breadcrumb-home">Ana Sayfa</button>
          {categoryContext?.breadcrumb?.map((node, index) => (
            <React.Fragment key={node.id}>
              <ChevronRight className="h-4 w-4" />
              {index === categoryContext.breadcrumb.length - 1 ? (
                <span className="font-semibold text-foreground" data-testid={`search-l2-breadcrumb-current-${node.id}`}>{node.name}</span>
              ) : (
                <button
                  type="button"
                  className="hover:text-foreground"
                  onClick={() => handleCategoryChange(getCategoryQueryValue(node))}
                  data-testid={`search-l2-breadcrumb-link-${node.id}`}
                >
                  {node.name}
                </button>
              )}
            </React.Fragment>
          ))}
        </nav>

        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-3" data-testid="search-l2-header-row">
          <div>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold leading-[1.05]" data-testid="search-l2-title">{categoryContext?.selected?.name}</h1>
            <p className="text-sm md:text-base text-muted-foreground mt-2" data-testid="search-l2-result-count">{data.pagination.total || 0} ilan bulundu</p>
          </div>
          {renderSortAndSave('search-l2-header')}
        </div>
      </header>

      <div className="grid grid-cols-1 xl:grid-cols-[300px_minmax(0,1fr)] gap-5" data-testid="search-l2-main-layout">
        <aside className="space-y-4" data-testid="search-l2-filter-sidebar">
          {renderFilterPanel('search-l2-filter', isVehicleCategory)}

          {categoryContext?.siblings?.length ? (
            <Card data-testid="search-l2-sibling-card">
              <CardContent className="p-4 space-y-2" data-testid="search-l2-sibling-content">
                <h2 className="text-base font-semibold" data-testid="search-l2-sibling-title">Aynı Seviyedeki Kategoriler</h2>
                <div className="space-y-1" data-testid="search-l2-sibling-list">
                  {categoryContext.siblings.map((sibling) => (
                    <button
                      key={sibling.id}
                      type="button"
                      onClick={() => handleCategoryChange(getCategoryQueryValue(sibling))}
                      className="w-full rounded-md border px-3 py-2 text-left text-sm hover:border-primary"
                      data-testid={`search-l2-sibling-button-${sibling.id}`}
                    >
                      <span data-testid={`search-l2-sibling-name-${sibling.id}`}>{sibling.name}</span>
                    </button>
                  ))}
                </div>
              </CardContent>
            </Card>
          ) : null}
        </aside>

        <div className="space-y-3" data-testid="search-l2-results-panel">
          {renderRowCards('search-l2-row')}
        </div>
      </div>
    </section>
  );

  const runtimeRegistry = {
    ...EXTENDED_RUNTIME_REGISTRY,
    'search.l1.default-content': () => renderL1DefaultTemplate(),
    'search.l2.default-content': () => renderL2DefaultTemplate(),
    'shared.text-block': ({ props }) => (
      <section className="rounded-xl border bg-white p-4" data-testid="search-runtime-text-block">
        <h2 className="text-base font-semibold" data-testid="search-runtime-text-title">{props?.title || 'Metin bloğu'}</h2>
        <p className="text-sm text-slate-600 mt-1" data-testid="search-runtime-text-body">{props?.body || ''}</p>
      </section>
    ),
    'shared.ad-slot': ({ props }) => (
      <section data-testid="search-runtime-ad-slot">
        <AdSlot placement={props?.placement || 'AD_SEARCH_TOP'} />
      </section>
    ),
    'menu.snapshot.*': ({ props, component }) => (
      <MenuSnapshotBlock props={props} componentKey={component?.key} />
    ),
  };

  const runtimeContext = useMemo(() => ({
    countryCode,
    categories,
    activeCategorySlug: searchState.category || null,
    onCategoryChange: handleCategoryChange,
    searchItems: Array.isArray(data?.items) ? data.items : [],
    categoryShowcase,
    selectedListingId,
    featuredListing: (Array.isArray(data?.items) && data.items.length > 0 ? data.items[0] : null)
      || (Array.isArray(categoryShowcase) && categoryShowcase.length > 0 ? categoryShowcase[0] : null),
    listingCandidates: [
      ...(Array.isArray(data?.items) ? data.items : []),
      ...(Array.isArray(categoryShowcase) ? categoryShowcase : []),
    ].filter(Boolean),
  }), [countryCode, categories, searchState.category, handleCategoryChange, data, categoryShowcase, selectedListingId]);

  return (
    <div data-testid="search-page">
      <div className="container mx-auto px-4 py-6">
        <div className="mb-6" data-testid="search-ad-slot">
          <AdSlot placement="AD_SEARCH_TOP" />
        </div>

        {isCategoryTemplate && hasResolvedCategoryLayoutRows ? (
          <section className="space-y-4" data-testid="search-runtime-layout-wrapper">
            <LayoutRenderer
              payload={resolvedCategoryLayout?.revision?.payload_json}
              registry={runtimeRegistry}
              runtimeContext={runtimeContext}
              dataTestIdPrefix="search-runtime-layout"
            />
          </section>
        ) : null}

        {isL1CategoryTemplate && !hasResolvedCategoryLayoutRows ? (
          <section className="space-y-6" data-testid="search-l1-template-root">
            <header className="rounded-2xl border border-slate-200 bg-gradient-to-r from-amber-50 via-white to-sky-50 p-5 md:p-6" data-testid="search-l1-header">
              <nav className="flex items-center flex-wrap gap-1 text-sm text-muted-foreground mb-3" data-testid="search-l1-breadcrumb">
                <button type="button" className="hover:text-foreground" onClick={() => handleCategoryChange(null)} data-testid="search-l1-breadcrumb-home">Ana Sayfa</button>
                {categoryContext?.breadcrumb?.map((node, index) => (
                  <React.Fragment key={node.id}>
                    <ChevronRight className="h-4 w-4" />
                    {index === categoryContext.breadcrumb.length - 1 ? (
                      <span className="font-semibold text-foreground" data-testid={`search-l1-breadcrumb-current-${node.id}`}>{node.name}</span>
                    ) : (
                      <button
                        type="button"
                        className="hover:text-foreground"
                        onClick={() => handleCategoryChange(getCategoryQueryValue(node))}
                        data-testid={`search-l1-breadcrumb-link-${node.id}`}
                      >
                        {node.name}
                      </button>
                    )}
                  </React.Fragment>
                ))}
              </nav>

              <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4" data-testid="search-l1-header-row">
                <div>
                  <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold leading-[1.05]" data-testid="search-l1-title">{categoryContext?.selected?.name}</h1>
                  <p className="text-sm md:text-base text-muted-foreground mt-2" data-testid="search-l1-result-count">{data.pagination.total || 0} ilan bulundu</p>
                </div>
                {renderSortAndSave('search-l1-header')}
              </div>
            </header>

            <section className="rounded-2xl border bg-card p-4 md:p-5" data-testid="search-l1-subcategory-section">
              <div className="flex items-center justify-between gap-2 mb-3" data-testid="search-l1-subcategory-heading-wrap">
                <h2 className="text-base md:text-lg font-bold" data-testid="search-l1-subcategory-heading">Alt Kategoriler</h2>
                <span className="text-xs text-muted-foreground" data-testid="search-l1-subcategory-count">{categoryContext?.children?.length || 0} kategori</span>
              </div>
              {categoryContext?.children?.length ? (
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4" data-testid="search-l1-subcategory-grid">
                  {categoryContext.children.map((child) => (
                    <button
                      type="button"
                      key={child.id}
                      onClick={() => handleCategoryChange(getCategoryQueryValue(child))}
                      className="rounded-xl border bg-white px-4 py-3 text-left transition hover:border-primary hover:shadow-sm"
                      data-testid={`search-l1-subcategory-card-${child.id}`}
                    >
                      <div className="font-semibold text-sm" data-testid={`search-l1-subcategory-name-${child.id}`}>{child.name}</div>
                      <div className="text-xs text-muted-foreground mt-1" data-testid={`search-l1-subcategory-listing-count-${child.id}`}>{Number(child.listing_count || 0)} ilan</div>
                    </button>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground" data-testid="search-l1-subcategory-empty">Bu kategoride alt kategori bulunmuyor.</p>
              )}
            </section>

            <section className="rounded-2xl border bg-card p-4 md:p-5" data-testid="search-l1-showcase-section">
              <div className="flex items-center justify-between gap-2 mb-3" data-testid="search-l1-showcase-heading-wrap">
                <h2 className="text-base md:text-lg font-bold" data-testid="search-l1-showcase-heading">Bu Kategoride Vitrin İlanları</h2>
                <Link
                  to={`/search?category=${encodeURIComponent(categoryContext?.selected?.id || '')}&doping=showcase`}
                  className="text-xs font-semibold hover:underline"
                  data-testid="search-l1-showcase-see-all-link"
                >
                  Tümünü Gör
                </Link>
              </div>

              {categoryShowcaseLoading ? (
                <div className="h-24 flex items-center justify-center" data-testid="search-l1-showcase-loading">
                  <Loader2 className="h-5 w-5 animate-spin text-primary" />
                </div>
              ) : categoryShowcase.length ? (
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4" data-testid="search-l1-showcase-grid">
                  {categoryShowcase.map((item) => (
                    <Link
                      key={item.id}
                      to={`/ilan/${slugify(item.title)}-${item.id}`}
                      className="rounded-xl border overflow-hidden bg-white hover:shadow-sm"
                      data-testid={`search-l1-showcase-card-${item.id}`}
                    >
                      <div className="aspect-[4/3] bg-muted" data-testid={`search-l1-showcase-image-wrap-${item.id}`}>
                        {item.image ? <img src={item.image} alt={item.title} className="h-full w-full object-cover" data-testid={`search-l1-showcase-image-${item.id}`} /> : null}
                      </div>
                      <div className="p-3">
                        <div className="text-xs text-amber-700 font-semibold" data-testid={`search-l1-showcase-badge-${item.id}`}>VİTRİN</div>
                        <div className="line-clamp-2 text-sm font-semibold" data-testid={`search-l1-showcase-title-${item.id}`}>{item.title}</div>
                        <div className="mt-1 text-sm font-bold text-primary" data-testid={`search-l1-showcase-price-${item.id}`}>{formatPrice(item.price_amount ?? item.price, item.currency, item.price_type, item.hourly_rate)}</div>
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground" data-testid="search-l1-showcase-empty">Bu kategori için aktif vitrin ilanı bulunamadı.</p>
              )}
            </section>

            <section className="grid grid-cols-1 xl:grid-cols-[320px_minmax(0,1fr)] gap-5" data-testid="search-l1-results-shell">
              <aside className="space-y-4" data-testid="search-l1-filter-sidebar">
                {renderFilterPanel('search-l1-filter', isVehicleCategory)}
              </aside>
              <div className="space-y-3" data-testid="search-l1-results-panel">
                {renderRowCards('search-l1-row')}
              </div>
            </section>
          </section>
        ) : null}

        {isL2CategoryTemplate && !hasResolvedCategoryLayoutRows ? (
          <section className="space-y-4" data-testid="search-l2-template-root">
            <header className="rounded-2xl border bg-card p-4 md:p-5" data-testid="search-l2-header">
              <nav className="flex items-center flex-wrap gap-1 text-sm text-muted-foreground mb-3" data-testid="search-l2-breadcrumb">
                <button type="button" className="hover:text-foreground" onClick={() => handleCategoryChange(null)} data-testid="search-l2-breadcrumb-home">Ana Sayfa</button>
                {categoryContext?.breadcrumb?.map((node, index) => (
                  <React.Fragment key={node.id}>
                    <ChevronRight className="h-4 w-4" />
                    {index === categoryContext.breadcrumb.length - 1 ? (
                      <span className="font-semibold text-foreground" data-testid={`search-l2-breadcrumb-current-${node.id}`}>{node.name}</span>
                    ) : (
                      <button
                        type="button"
                        className="hover:text-foreground"
                        onClick={() => handleCategoryChange(getCategoryQueryValue(node))}
                        data-testid={`search-l2-breadcrumb-link-${node.id}`}
                      >
                        {node.name}
                      </button>
                    )}
                  </React.Fragment>
                ))}
              </nav>

              <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-3" data-testid="search-l2-header-row">
                <div>
                  <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold leading-[1.05]" data-testid="search-l2-title">{categoryContext?.selected?.name}</h1>
                  <p className="text-sm md:text-base text-muted-foreground mt-2" data-testid="search-l2-result-count">{data.pagination.total || 0} ilan bulundu</p>
                </div>
                {renderSortAndSave('search-l2-header')}
              </div>
            </header>

            <div className="grid grid-cols-1 xl:grid-cols-[300px_minmax(0,1fr)] gap-5" data-testid="search-l2-main-layout">
              <aside className="space-y-4" data-testid="search-l2-filter-sidebar">
                {renderFilterPanel('search-l2-filter', isVehicleCategory)}

                {categoryContext?.siblings?.length ? (
                  <Card data-testid="search-l2-sibling-card">
                    <CardContent className="p-4 space-y-2" data-testid="search-l2-sibling-content">
                      <h2 className="text-base font-semibold" data-testid="search-l2-sibling-title">Aynı Seviyedeki Kategoriler</h2>
                      <div className="space-y-1" data-testid="search-l2-sibling-list">
                        {categoryContext.siblings.map((sibling) => (
                          <button
                            key={sibling.id}
                            type="button"
                            onClick={() => handleCategoryChange(getCategoryQueryValue(sibling))}
                            className="w-full rounded-md border px-3 py-2 text-left text-sm hover:border-primary"
                            data-testid={`search-l2-sibling-button-${sibling.id}`}
                          >
                            <span data-testid={`search-l2-sibling-name-${sibling.id}`}>{sibling.name}</span>
                          </button>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                ) : null}
              </aside>

              <div className="space-y-3" data-testid="search-l2-results-panel">
                {renderRowCards('search-l2-row')}
              </div>
            </div>
          </section>
        ) : null}

        {!isCategoryTemplate ? (
          <>
            {searchState.category ? (
              <div className="flex items-center text-sm text-muted-foreground mb-4" data-testid="search-breadcrumb">
                <button type="button" className="hover:text-foreground" onClick={() => handleCategoryChange(null)} data-testid="search-breadcrumb-home">
                  Ana Sayfa
                </button>
                <ChevronRight className="h-4 w-4 mx-1" />
                <span className="font-medium text-foreground" data-testid="search-breadcrumb-category">
                  {categoryContext?.selected?.name || searchState.category}
                </span>
              </div>
            ) : null}

            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4" data-testid="search-header-row">
              <div>
                <h1 className="text-2xl font-bold tracking-tight" data-testid="search-results-title">{searchTitle}</h1>
                <p className="text-muted-foreground text-sm mt-1" data-testid="search-results-count">{data.pagination.total || 0} sonuç bulundu</p>
              </div>

              <div className="flex items-center gap-2 w-full md:w-auto" data-testid="search-header-actions">
                <div className="inline-flex rounded-lg border p-1" data-testid="search-view-toggle">
                  <button
                    type="button"
                    onClick={() => toggleMapView(false)}
                    className={`inline-flex items-center gap-1 rounded-md px-3 py-2 text-sm ${!effectiveMapView ? 'bg-primary text-primary-foreground' : 'text-muted-foreground'}`}
                    data-testid="search-view-toggle-list"
                  >
                    <List className="h-4 w-4" /> Liste
                  </button>
                  <button
                    type="button"
                    onClick={() => toggleMapView(true)}
                    className={`inline-flex items-center gap-1 rounded-md px-3 py-2 text-sm ${effectiveMapView ? 'bg-primary text-primary-foreground' : 'text-muted-foreground'}`}
                    data-testid="search-view-toggle-map"
                  >
                    <MapPin className="h-4 w-4" /> Harita
                  </button>
                </div>

                {renderSortAndSave('search-header')}
              </div>
            </div>

            {effectiveMapView ? (
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6" data-testid="search-map-layout">
                <div className="lg:col-span-5 space-y-4 max-h-[calc(100vh-140px)] overflow-y-auto pr-1" data-testid="search-map-left-panel">
                  {renderFilterPanel('search-map-filter', true)}
                  <div data-testid="search-map-result-list-wrap">{renderGridCards(true, 'search-map')}</div>
                </div>

                <div className="lg:col-span-7 lg:sticky lg:top-4 h-fit" data-testid="search-map-right-panel">
                  {mapKeyError ? (
                    <div className="h-[70vh] rounded-xl border bg-muted/20 p-6 text-sm text-amber-700" data-testid="search-map-key-error">
                      {mapKeyError}
                    </div>
                  ) : !mapKey ? (
                    <div className="h-[70vh] rounded-xl border bg-muted/20 flex items-center justify-center" data-testid="search-map-runtime-loading">
                      <Loader2 className="h-6 w-6 animate-spin text-primary" />
                    </div>
                  ) : (
                    <SearchMapPanel
                      apiKey={mapKey}
                      loading={loading}
                      mapItems={mapItems}
                      selectedListingId={selectedListingId}
                      hoveredListingId={hoveredListingId}
                      onPinClick={(listingId) => {
                        setSelectedListingId(listingId);
                        setHoveredListingId(listingId);
                      }}
                      onPinHover={(listingId) => setHoveredListingId(listingId)}
                      onViewportBboxChange={(bboxValue) => setMapBbox(bboxValue)}
                      resultCount={(data.items || []).length}
                    />
                  )}
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6" data-testid="search-list-layout">
                <div className="hidden md:block md:col-span-1 space-y-6" data-testid="search-filter-sidebar">
                  {renderFilterPanel('search-list-filter', true)}
                </div>
                <div className="md:col-span-3" data-testid="search-results-panel">
                  {renderGridCards(false, 'search-list')}
                </div>
              </div>
            )}
          </>
        ) : null}

        {saveModalOpen ? (
          <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4" data-testid="search-save-modal">
            <div className="w-full max-w-md rounded-xl border bg-white p-5 space-y-4" data-testid="search-save-modal-content">
              <h3 className="text-lg font-semibold" data-testid="search-save-modal-title">Aramayı Kaydet</h3>

              <div className="space-y-1" data-testid="search-save-name-wrap">
                <label className="text-sm font-medium" htmlFor="saved-search-name">Ad</label>
                <input
                  id="saved-search-name"
                  value={saveName}
                  onChange={(e) => setSaveName(e.target.value)}
                  className="w-full rounded-md border px-3 py-2 text-sm"
                  data-testid="search-save-name-input"
                />
              </div>

              <label className="inline-flex items-center gap-2 text-sm" data-testid="search-save-email-toggle-wrap">
                <input
                  type="checkbox"
                  checked={saveEmailEnabled}
                  onChange={(e) => setSaveEmailEnabled(e.target.checked)}
                  data-testid="search-save-email-toggle"
                />
                Email bildirimi
              </label>

              <label className="inline-flex items-center gap-2 text-sm" data-testid="search-save-push-toggle-wrap">
                <input
                  type="checkbox"
                  checked={savePushEnabled}
                  onChange={(e) => setSavePushEnabled(e.target.checked)}
                  data-testid="search-save-push-toggle"
                />
                Push bildirimi
              </label>

              {saveError ? <div className="text-sm text-rose-600" data-testid="search-save-error">{saveError}</div> : null}
              {saveSuccess ? <div className="text-sm text-emerald-600" data-testid="search-save-success">{saveSuccess}</div> : null}

              <div className="flex justify-end gap-2" data-testid="search-save-actions">
                <Button type="button" variant="outline" onClick={() => setSaveModalOpen(false)} data-testid="search-save-cancel-button">
                  Vazgeç
                </Button>
                <Button type="button" onClick={handleSaveSearch} disabled={saveLoading} data-testid="search-save-submit-button">
                  {saveLoading ? 'Kaydediliyor...' : 'Kaydet'}
                </Button>
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
