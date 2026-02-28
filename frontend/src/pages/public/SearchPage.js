import React, { useEffect, useState } from 'react';
import { useSearchState } from '@/hooks/useSearchState';
import { FacetRenderer } from '@/components/search/FacetRenderer';
import { CategorySidebar } from '@/components/search/CategorySidebar';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import AdSlot from '@/components/public/AdSlot';
import { Loader2, AlertCircle, ShoppingCart, Home, Car, Search, ChevronRight } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { format } from 'date-fns';
import { tr } from 'date-fns/locale';

import { useNavigate } from 'react-router-dom';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${API_URL}/api`;

// Helper to format currency
const formatPrice = (priceAmount, currency, priceType = 'FIXED', hourlyRate = null) => {
  const numeric = priceType === 'HOURLY' ? hourlyRate : priceAmount;
  if (numeric === null || numeric === undefined || numeric === '') return '-';
  const formatted = new Intl.NumberFormat('tr-TR', {
    maximumFractionDigits: 0,
  }).format(Number(numeric));
  const currencyLabel = currency || 'EUR';
  return priceType === 'HOURLY'
    ? `${formatted} ${currencyLabel} / saat`
    : `${formatted} ${currencyLabel}`;
};

const slugify = (text) => {
  return text
    .toString()
    .toLowerCase()
    .replace(/\s+/g, '-')     // Replace spaces with -
    .replace(/[^\w\-]+/g, '') // Remove all non-word chars
    .replace(/\-\-+/g, '-')   // Replace multiple - with single -
    .replace(/^-+/, '')       // Trim - from start
    .replace(/-+$/, '');      // Trim - from end
};

export default function SearchPage() {
  const navigate = useNavigate();
  const [searchState, setSearchState] = useSearchState();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState({ items: [], facets: {}, pagination: {} });
  const [facetMeta, setFacetMeta] = useState({}); // To store types/labels
  const facetsEnabled = Object.keys(facetMeta || {}).length > 0;
  const [categories, setCategories] = useState([]); // Flat list of categories
  const [makes, setMakes] = useState([]);
  const [models, setModels] = useState([]);
  const [loadingMakes, setLoadingMakes] = useState(false);
  const [loadingModels, setLoadingModels] = useState(false);

  // Initial Bootstrap: Fetch Categories + Make/Model options
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const country = (localStorage.getItem('selected_country') || 'DE').toUpperCase();
        const res = await fetch(`${API}/categories?module=vehicle&country=${country}`);
        if (res.ok) {
          const json = await res.json();
          setCategories(json);
        }
      } catch (e) {
        console.error("Category fetch error", e);
      }
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
        if (res.ok) {
          const json = await res.json();
          if (alive) setMakes(json.items || []);
        }
      } catch (e) {
        console.error('Make fetch error', e);
      } finally {
        if (alive) setLoadingMakes(false);
      }
    };
    fetchMakes();
    return () => { alive = false; };
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
        if (res.ok) {
          const json = await res.json();
          if (alive) setModels(json.items || []);
        }
      } catch (e) {
        console.error('Model fetch error', e);
      } finally {
        if (alive) setLoadingModels(false);
      }
    };
    fetchModels();
    return () => { alive = false; };
  }, [searchState.make]);

  // Fetch Data
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const queryParams = new URLSearchParams();
        
        // Map State to API Params
        const country = (localStorage.getItem('selected_country') || 'DE').toUpperCase();
        queryParams.set('country', country);

        if (searchState.q) queryParams.set('q', searchState.q);
        if (searchState.category) queryParams.set('category', searchState.category);
        if (searchState.make) queryParams.set('make', searchState.make);
        if (searchState.model) queryParams.set('model', searchState.model);
        if (searchState.doping) queryParams.set('doping_type', searchState.doping);
        if (searchState.sort) queryParams.set('sort', searchState.sort);
        queryParams.set('page', searchState.page);
        queryParams.set('limit', searchState.limit);
        
        // Handle Price
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
            if (value.min !== undefined && value.min !== null) {
              queryParams.set(`attr[${key}]_min`, String(value.min));
            }
            if (value.max !== undefined && value.max !== null) {
              queryParams.set(`attr[${key}]_max`, String(value.max));
            }
            return;
          }
          if (typeof value === 'boolean') {
            queryParams.set(`attr[${key}]`, value ? 'true' : 'false');
          }
        });

        const res = await fetch(`${API}/v2/search?${queryParams.toString()}`);
        
        if (!res.ok) {
           throw new Error('Search failed');
        }

        const json = await res.json();
        setData(json);
        
        setFacetMeta(json.facet_meta || {});

      } catch (err) {
        console.error(err);
        setError('İlanlar yüklenirken bir hata oluştu.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [searchState]); // Re-run when URL state changes

  const handleCategoryChange = (categoryId) => {
    // Reset filters on category change (Architecture Decision 3)
    setSearchState({ category: categoryId, filters: {}, page: 1 });
  };

  const searchTitle = (() => {
    if (searchState.doping === 'urgent') return 'Acil İlanlar';
    if (searchState.doping === 'showcase') return 'Vitrin İlanları';
    if (searchState.category) {
      return `Kategori: ${categories.find(c => c.id === searchState.category || c.slug === searchState.category)?.name || searchState.category}`;
    }
    return 'Tüm İlanlar';
  })();

  const handleMakeChange = (makeKey) => {
    const nextMake = makeKey === 'all' ? null : makeKey;
    setSearchState({ make: nextMake, model: null, page: 1 });
  };

  const handleModelChange = (modelKey) => {
    const nextModel = modelKey === 'all' ? null : modelKey;
    setSearchState({ model: nextModel, page: 1 });
  };

  const handleFilterChange = (newFilters) => {
    // Reset page to 1 when filters change
    setSearchState({ filters: newFilters, page: 1 });
  };

  const handleSortChange = (val) => {
    setSearchState({ sort: val });
  };

  const handlePageChange = (newPage) => {
    setSearchState({ page: newPage });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div>
      <div className="container mx-auto px-4 py-6">
        <div className="mb-6" data-testid="search-ad-slot">
          <AdSlot placement="AD_SEARCH_TOP" />
        </div>
        
        {/* Breadcrumb */}
        {searchState.category && (
          <div className="flex items-center text-sm text-muted-foreground mb-4">
            <span 
              className="hover:text-foreground cursor-pointer"
              onClick={() => handleCategoryChange(null)}
            >
              Ana Sayfa
            </span>
            <ChevronRight className="h-4 w-4 mx-1" />
            <span className="font-medium text-foreground" data-testid="search-breadcrumb-category">
              {categories.find(c => c.id === searchState.category || c.slug === searchState.category)?.name || searchState.category}
            </span>
          </div>
        )}

        {/* Header & Mobile Filter Toggle */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight" data-testid="search-results-title">
               {searchTitle}
            </h1>
            <p className="text-muted-foreground text-sm mt-1">
              {data.pagination.total || 0} sonuç bulundu
            </p>
            {(searchState.filters?.price_min || searchState.filters?.price_max) && (
              <p className="text-xs text-muted-foreground mt-1" data-testid="search-price-filter-note">
                Not: Saatlik ücretli ilanlar fiyat filtresinde gösterilmez.
              </p>
            )}
          </div>

          <div className="flex items-center gap-2 w-full md:w-auto">
            <Select value={searchState.sort} onValueChange={handleSortChange} data-testid="search-sort-select">
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

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          
          {/* Sidebar - Filters */}
          <div className="hidden md:block md:col-span-1 space-y-6">
             <Card>
               <CardContent className="p-4">
                 <CategorySidebar 
                   categories={categories}
                   activeCategorySlug={searchState.category}
                   onCategoryChange={handleCategoryChange}
                 />

          <div className="my-4 border-t border-border" />
          <div className="space-y-3" data-testid="search-make-model-filters">
            <div>
              <div className="text-sm font-medium text-muted-foreground mb-1">Marka</div>
              <Select
                value={searchState.make || 'all'}
                onValueChange={handleMakeChange}
                data-testid="search-make-select"
              >
                <SelectTrigger>
                  <SelectValue placeholder={loadingMakes ? 'Yükleniyor...' : 'Tüm Markalar'} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tümü</SelectItem>
                  {makes.map((make) => (
                    <SelectItem key={make.id} value={make.key} data-testid={`search-make-option-${make.key}`}>
                      {make.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <div className="text-sm font-medium text-muted-foreground mb-1">Model</div>
              <Select
                value={searchState.model || 'all'}
                onValueChange={handleModelChange}
                disabled={!searchState.make || loadingModels}
                data-testid="search-model-select"
              >
                <SelectTrigger>
                  <SelectValue placeholder={!searchState.make ? 'Önce marka seçin' : (loadingModels ? 'Yükleniyor...' : 'Tüm Modeller')} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tümü</SelectItem>
                  {models.map((model) => (
                    <SelectItem key={model.id} value={model.key} data-testid={`search-model-option-${model.key}`}>
                      {model.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

                 {facetsEnabled && (
                   <>
                     <div className="my-4 border-t" />
                     <FacetRenderer 
                        facets={data.facets} 
                        facetMeta={facetMeta}
                        selections={searchState.filters}
                        onFilterChange={handleFilterChange}
                     />
                   </>
                 )}
               </CardContent>
             </Card>
          </div>

          {/* Results Grid */}
          <div className="md:col-span-3">
             {loading ? (
                <div className="flex justify-center items-center h-64">
                   <Loader2 className="h-8 w-8 animate-spin text-primary" />
                </div>
             ) : error ? (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>Hata</AlertTitle>
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
             ) : data.items.length === 0 ? (
                <div className="text-center py-12 bg-muted/30 rounded-lg">
                   <div className="bg-muted rounded-full p-4 w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                     <Search className="h-8 w-8 text-muted-foreground" />
                   </div>
                   <h3 className="text-lg font-medium">Sonuç bulunamadı</h3>
                   <p className="text-muted-foreground mt-2">
                     Arama kriterlerinizi değiştirerek tekrar deneyin.
                   </p>
                   <Button 
                     variant="outline" 
                     className="mt-4"
                     onClick={() => handleFilterChange({})}
                   >
                     Filtreleri Temizle
                   </Button>
                </div>
             ) : (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {data.items.map((item) => (
                      <Card 
                        key={item.id} 
                        className="overflow-hidden hover:shadow-md transition-shadow group cursor-pointer"
                        style={{
                          borderColor: item.is_featured ? '#4f46e5' : (item.is_urgent ? '#e11d48' : undefined),
                          borderWidth: item.is_featured || item.is_urgent ? 2 : 1,
                        }}
                        onClick={() => navigate(`/ilan/${slugify(item.title)}-${item.id}`)}
                        data-testid={`search-result-card-${item.id}`}
                      >
                        <div className="aspect-[4/3] relative bg-gray-100 overflow-hidden">
                          {item.image ? (
                             <img 
                               src={item.image} 
                               alt={item.title} 
                               className="object-cover w-full h-full group-hover:scale-105 transition-transform duration-300"
                             />
                          ) : (
                             <div className="w-full h-full flex items-center justify-center text-muted-foreground">
                               <Car className="h-12 w-12 opacity-20" />
                             </div>
                          )}
                          <Badge className="absolute top-2 right-2 bg-black/50 hover:bg-black/70 backdrop-blur-sm border-none">
                            {formatPrice(item.price_amount ?? item.price, item.currency, item.price_type, item.hourly_rate)}
                          </Badge>
                        </div>
                        <CardHeader className="p-4 pb-2">
                          <div className="mb-1 flex flex-wrap items-center gap-1" data-testid={`search-result-doping-badges-${item.id}`}>
                            {item.is_featured ? (
                              <span className="rounded-full bg-indigo-100 px-2 py-0.5 text-[11px] font-semibold text-indigo-700" data-testid={`search-result-featured-badge-${item.id}`}>Vitrin</span>
                            ) : null}
                            {item.is_urgent ? (
                              <span className="rounded-full bg-rose-100 px-2 py-0.5 text-[11px] font-semibold text-rose-700" data-testid={`search-result-urgent-badge-${item.id}`}>Acil</span>
                            ) : null}
                          </div>
                          <CardTitle className="text-base line-clamp-2 leading-tight">
                            {item.title}
                          </CardTitle>
                        </CardHeader>
                        <CardFooter className="p-4 pt-0 text-sm text-muted-foreground flex justify-between">
                           <span>{item.city || 'Konum yok'}</span>
                           <span>{format(new Date(), 'd MMM', { locale: tr })}</span>
                        </CardFooter>
                      </Card>
                    ))}
                  </div>

                  {/* Pagination */}
                  {data.pagination.pages > 1 && (
                    <div className="flex justify-center gap-2 mt-8">
                       <Button 
                         variant="outline" 
                         size="sm" 
                         disabled={searchState.page <= 1}
                         onClick={() => handlePageChange(searchState.page - 1)}
                       >
                         Önceki
                       </Button>
                       <span className="flex items-center px-4 text-sm font-medium">
                         Sayfa {searchState.page} / {data.pagination.pages}
                       </span>
                       <Button 
                         variant="outline" 
                         size="sm" 
                         disabled={searchState.page >= data.pagination.pages}
                         onClick={() => handlePageChange(searchState.page + 1)}
                       >
                         Sonraki
                       </Button>
                    </div>
                  )}
                </div>
             )}
          </div>

        </div>
      </div>
    </div>
  );
}
