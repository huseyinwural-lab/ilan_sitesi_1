import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useSearchState } from '@/hooks/useSearchState';
import { FacetRenderer } from '@/components/search/FacetRenderer';
import { CategorySidebar } from '@/components/search/CategorySidebar';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import AdSlot from '@/components/public/AdSlot';
import { Loader2, AlertCircle, Car, Search, ChevronRight, MapPin, List } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { GoogleMap, MarkerClustererF, MarkerF, useJsApiLoader } from '@react-google-maps/api';
import { format } from 'date-fns';
import { tr } from 'date-fns/locale';
import { useLocation, useNavigate } from 'react-router-dom';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${API_URL}/api`;
const DEFAULT_CENTER = { lat: 51.1657, lng: 10.4515 };

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
  mapKeyError,
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

  if (mapKeyError) {
    return (
      <div className="h-[70vh] rounded-xl border bg-muted/20 p-6 text-sm text-amber-700" data-testid="search-map-key-error">
        {mapKeyError}
      </div>
    );
  }

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

  const [mapKey, setMapKey] = useState('');
  const [mapKeyError, setMapKeyError] = useState('');
  const [mapBbox, setMapBbox] = useState('');
  const [debouncedMapBbox, setDebouncedMapBbox] = useState('');
  const [hoveredListingId, setHoveredListingId] = useState(null);
  const [selectedListingId, setSelectedListingId] = useState(null);
  const listRefs = useRef({});

  const isMapView = useMemo(() => {
    const params = new URLSearchParams(location.search);
    return params.get('view') === 'map';
  }, [location.search]);

  useEffect(() => {
    if (!isMapView) return;
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
      } catch (_err) {
        if (!alive) return;
        setMapKey('');
        setMapKeyError('Harita servisi yüklenemedi.');
      }
    };

    loadMapRuntime();
    return () => {
      alive = false;
    };
  }, [isMapView]);

  useEffect(() => {
    if (!isMapView) {
      setDebouncedMapBbox('');
      return;
    }
    const timer = setTimeout(() => {
      setDebouncedMapBbox(mapBbox || '');
    }, 450);
    return () => clearTimeout(timer);
  }, [mapBbox, isMapView]);

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const country = (localStorage.getItem('selected_country') || 'DE').toUpperCase();
        const res = await fetch(`${API}/categories?module=vehicle&country=${country}`);
        if (res.ok) setCategories(await res.json());
      } catch (_e) {}
    };
    fetchCategories();
  }, []);

  useEffect(() => {
    let alive = true;
    const fetchMakes = async () => {
      setLoadingMakes(true);
      try {
        const country = (localStorage.getItem('selected_country') || 'DE').toUpperCase();
        const res = await fetch(`${API}/v1/vehicle/makes?country=${country}`);
        if (res.ok && alive) setMakes((await res.json()).items || []);
      } finally {
        if (alive) setLoadingMakes(false);
      }
    };
    fetchMakes();
    return () => {
      alive = false;
    };
  }, []);

  useEffect(() => {
    let alive = true;
    const fetchModels = async () => {
      if (!searchState.make) {
        setModels([]);
        return;
      }
      setLoadingModels(true);
      try {
        const country = (localStorage.getItem('selected_country') || 'DE').toUpperCase();
        const res = await fetch(`${API}/v1/vehicle/models?make=${searchState.make}&country=${country}`);
        if (res.ok && alive) setModels((await res.json()).items || []);
      } finally {
        if (alive) setLoadingModels(false);
      }
    };
    fetchModels();
    return () => {
      alive = false;
    };
  }, [searchState.make]);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        const queryParams = new URLSearchParams();
        const country = (localStorage.getItem('selected_country') || 'DE').toUpperCase();
        queryParams.set('country', country);

        if (searchState.q) queryParams.set('q', searchState.q);
        if (searchState.category) queryParams.set('category', searchState.category);
        if (searchState.make) queryParams.set('make', searchState.make);
        if (searchState.model) queryParams.set('model', searchState.model);

        const dopingFromUrl = new URLSearchParams(location.search).get('doping');
        const activeDopingParam = searchState.doping || dopingFromUrl;
        if (activeDopingParam) queryParams.set('doping_type', activeDopingParam);

        if (searchState.sort) queryParams.set('sort', searchState.sort);
        queryParams.set('page', isMapView ? '1' : String(searchState.page));
        queryParams.set('limit', isMapView ? '300' : String(searchState.limit));

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

        if (isMapView && debouncedMapBbox) queryParams.set('bbox', debouncedMapBbox);

        const res = await fetch(`${API}/v2/search?${queryParams.toString()}`, { cache: 'no-store' });
        if (!res.ok) throw new Error('Search failed');

        const json = await res.json();
        setData(json);
        setFacetMeta(json.facet_meta || {});
      } catch (_err) {
        setError('İlanlar yüklenirken bir hata oluştu.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [searchState, location.search, isMapView, debouncedMapBbox]);

  useEffect(() => {
    if (!selectedListingId) return;
    const node = listRefs.current[selectedListingId];
    if (node && typeof node.scrollIntoView === 'function') {
      node.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, [selectedListingId, data.items]);

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

  const dopingFromUrl = useMemo(() => new URLSearchParams(location.search).get('doping'), [location.search]);
  const activeDoping = searchState.doping || dopingFromUrl;

  const handleCategoryChange = (categoryId) => setSearchState({ category: categoryId, filters: {}, page: 1 });

  const searchTitle = (() => {
    if (activeDoping === 'urgent') return 'Acil İlanlar';
    if (activeDoping === 'showcase') return 'Vitrin İlanları';
    if (searchState.category) {
      return `Kategori: ${categories.find((c) => c.id === searchState.category || c.slug === searchState.category)?.name || searchState.category}`;
    }
    return 'Tüm İlanlar';
  })();

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

  const renderListCards = (compact = false) => {
    if (loading) {
      return (
        <div className="flex justify-center items-center h-64" data-testid="search-results-loading">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      );
    }

    if (error) {
      return (
        <Alert variant="destructive" data-testid="search-results-error-alert">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Hata</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      );
    }

    if (data.items.length === 0) {
      return (
        <div className="text-center py-12 bg-muted/30 rounded-lg" data-testid="search-empty-state">
          <div className="bg-muted rounded-full p-4 w-16 h-16 mx-auto mb-4 flex items-center justify-center">
            <Search className="h-8 w-8 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-medium" data-testid="search-empty-title">
            {isUrgentSearch ? 'Şu an aktif acil ilan bulunmuyor' : 'Sonuç bulunamadı'}
          </h3>
          <p className="text-muted-foreground mt-2" data-testid="search-empty-description">
            Arama kriterlerinizi değiştirerek tekrar deneyin.
          </p>
          <Button variant="outline" className="mt-4" onClick={() => handleFilterChange({})} data-testid="search-empty-clear-filters">
            Filtreleri Temizle
          </Button>
        </div>
      );
    }

    return (
      <div className="space-y-6" data-testid={compact ? 'search-results-list-compact' : 'search-results-list'}>
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
                data-testid={`search-result-card-${item.id}`}
              >
                <div className="aspect-[4/3] relative bg-gray-100 overflow-hidden">
                  {item.image ? (
                    <img src={item.image} alt={item.title} className="object-cover w-full h-full group-hover:scale-105 transition-transform duration-300" loading="lazy" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-muted-foreground">
                      <Car className="h-12 w-12 opacity-20" />
                    </div>
                  )}
                  <Badge className="absolute top-2 right-2 bg-black/50 hover:bg-black/70 backdrop-blur-sm border-none">
                    {formatPrice(item.price_amount ?? item.price, item.currency, item.price_type, item.hourly_rate)}
                  </Badge>
                  {item.lat && item.lng ? (
                    <div className="absolute left-2 top-2 rounded-full bg-white/90 p-1" data-testid={`search-result-map-pin-indicator-${item.id}`}>
                      <MapPin className="h-3.5 w-3.5 text-blue-600" />
                    </div>
                  ) : null}
                </div>
                <CardHeader className="p-4 pb-2">
                  <div className="mb-1 flex flex-wrap items-center gap-1" data-testid={`search-result-doping-badges-${item.id}`}>
                    {item.is_featured ? <span className="rounded-full bg-indigo-100 px-2 py-0.5 text-[11px] font-semibold text-indigo-700">Vitrin</span> : null}
                    {item.is_urgent ? <span className="rounded-full bg-rose-100 px-2 py-0.5 text-[11px] font-semibold text-rose-700">Acil</span> : null}
                  </div>
                  <CardTitle className="text-base line-clamp-2 leading-tight">{item.title}</CardTitle>
                </CardHeader>
                <CardFooter className="p-4 pt-0 text-sm text-muted-foreground flex justify-between">
                  <span>{item.city || 'Konum yok'}</span>
                  <span>{format(new Date(), 'd MMM', { locale: tr })}</span>
                </CardFooter>
              </Card>
            );
          })}
        </div>

        {!compact && data.pagination.pages > 1 ? (
          <div className="flex justify-center gap-2 mt-8" data-testid="search-pagination">
            <Button variant="outline" size="sm" disabled={searchState.page <= 1} onClick={() => handlePageChange(searchState.page - 1)} data-testid="search-pagination-prev">
              Önceki
            </Button>
            <span className="flex items-center px-4 text-sm font-medium" data-testid="search-pagination-indicator">
              Sayfa {searchState.page} / {data.pagination.pages}
            </span>
            <Button variant="outline" size="sm" disabled={searchState.page >= data.pagination.pages} onClick={() => handlePageChange(searchState.page + 1)} data-testid="search-pagination-next">
              Sonraki
            </Button>
          </div>
        ) : null}
      </div>
    );
  };

  return (
    <div data-testid="search-page">
      <div className="container mx-auto px-4 py-6">
        <div className="mb-6" data-testid="search-ad-slot">
          <AdSlot placement="AD_SEARCH_TOP" />
        </div>

        {searchState.category ? (
          <div className="flex items-center text-sm text-muted-foreground mb-4" data-testid="search-breadcrumb">
            <span className="hover:text-foreground cursor-pointer" onClick={() => handleCategoryChange(null)} data-testid="search-breadcrumb-home">
              Ana Sayfa
            </span>
            <ChevronRight className="h-4 w-4 mx-1" />
            <span className="font-medium text-foreground" data-testid="search-breadcrumb-category">
              {categories.find((c) => c.id === searchState.category || c.slug === searchState.category)?.name || searchState.category}
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
                className={`inline-flex items-center gap-1 rounded-md px-3 py-2 text-sm ${!isMapView ? 'bg-primary text-primary-foreground' : 'text-muted-foreground'}`}
                data-testid="search-view-toggle-list"
              >
                <List className="h-4 w-4" /> Liste
              </button>
              <button
                type="button"
                onClick={() => toggleMapView(true)}
                className={`inline-flex items-center gap-1 rounded-md px-3 py-2 text-sm ${isMapView ? 'bg-primary text-primary-foreground' : 'text-muted-foreground'}`}
                data-testid="search-view-toggle-map"
              >
                <MapPin className="h-4 w-4" /> Harita
              </button>
            </div>

            <Select value={searchState.sort} onValueChange={handleSortChange}>
              <SelectTrigger className="w-full md:w-[180px]" data-testid="search-sort-trigger">
                <SelectValue placeholder="Sıralama" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="date_desc">En Yeni</SelectItem>
                <SelectItem value="date_asc">En Eski</SelectItem>
                <SelectItem value="price_asc">Fiyat (Artan)</SelectItem>
                <SelectItem value="price_desc">Fiyat (Azalan)</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {isMapView ? (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6" data-testid="search-map-layout">
            <div className="lg:col-span-5 space-y-4 max-h-[calc(100vh-140px)] overflow-y-auto pr-1" data-testid="search-map-left-panel">
              <Card data-testid="search-filter-card-map">
                <CardContent className="p-4">
                  <CategorySidebar categories={categories} activeCategorySlug={searchState.category} onCategoryChange={handleCategoryChange} />
                  <div className="my-4 border-t border-border" />
                  <div className="space-y-3" data-testid="search-make-model-filters">
                    <div>
                      <div className="text-sm font-medium text-muted-foreground mb-1">Marka</div>
                      <Select value={searchState.make || 'all'} onValueChange={handleMakeChange}>
                        <SelectTrigger data-testid="search-make-trigger"><SelectValue placeholder={loadingMakes ? 'Yükleniyor...' : 'Tüm Markalar'} /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">Tümü</SelectItem>
                          {makes.map((make) => <SelectItem key={make.id} value={make.key}>{make.label}</SelectItem>)}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <div className="text-sm font-medium text-muted-foreground mb-1">Model</div>
                      <Select value={searchState.model || 'all'} onValueChange={handleModelChange} disabled={!searchState.make || loadingModels}>
                        <SelectTrigger data-testid="search-model-trigger"><SelectValue placeholder="Tüm Modeller" /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">Tümü</SelectItem>
                          {models.map((model) => <SelectItem key={model.id} value={model.key}>{model.label}</SelectItem>)}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  {facetsEnabled ? (
                    <>
                      <div className="my-4 border-t" />
                      <FacetRenderer facets={data.facets} facetMeta={facetMeta} selections={searchState.filters} onFilterChange={handleFilterChange} />
                    </>
                  ) : null}
                </CardContent>
              </Card>

              <div data-testid="search-map-result-list-wrap">{renderListCards(true)}</div>
            </div>

            <div className="lg:col-span-7 lg:sticky lg:top-4 h-fit" data-testid="search-map-right-panel">
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
                resultCount={data.items.length}
                mapKeyError={mapKeyError}
              />
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6" data-testid="search-list-layout">
            <div className="hidden md:block md:col-span-1 space-y-6" data-testid="search-filter-sidebar">
              <Card>
                <CardContent className="p-4">
                  <CategorySidebar categories={categories} activeCategorySlug={searchState.category} onCategoryChange={handleCategoryChange} />
                  <div className="my-4 border-t border-border" />
                  <div className="space-y-3" data-testid="search-make-model-filters">
                    <div>
                      <div className="text-sm font-medium text-muted-foreground mb-1">Marka</div>
                      <Select value={searchState.make || 'all'} onValueChange={handleMakeChange}>
                        <SelectTrigger data-testid="search-make-trigger"><SelectValue placeholder={loadingMakes ? 'Yükleniyor...' : 'Tüm Markalar'} /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">Tümü</SelectItem>
                          {makes.map((make) => <SelectItem key={make.id} value={make.key}>{make.label}</SelectItem>)}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <div className="text-sm font-medium text-muted-foreground mb-1">Model</div>
                      <Select value={searchState.model || 'all'} onValueChange={handleModelChange} disabled={!searchState.make || loadingModels}>
                        <SelectTrigger data-testid="search-model-trigger"><SelectValue placeholder="Tüm Modeller" /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">Tümü</SelectItem>
                          {models.map((model) => <SelectItem key={model.id} value={model.key}>{model.label}</SelectItem>)}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  {facetsEnabled ? (
                    <>
                      <div className="my-4 border-t" />
                      <FacetRenderer facets={data.facets} facetMeta={facetMeta} selections={searchState.filters} onFilterChange={handleFilterChange} />
                    </>
                  ) : null}
                </CardContent>
              </Card>
            </div>

            <div className="md:col-span-3" data-testid="search-results-panel">
              {renderListCards(false)}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
