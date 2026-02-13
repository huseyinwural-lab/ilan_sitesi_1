import React, { useEffect, useState } from 'react';
import { useSearchState } from '@/hooks/useSearchState';
import { FacetRenderer } from '@/components/search/FacetRenderer';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import Layout from '@/components/Layout';
import { Loader2, AlertCircle, ShoppingCart, Home, Car, Search } from 'lucide-react';
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

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// Helper to format currency
const formatPrice = (price, currency) => {
  return new Intl.NumberFormat('tr-TR', {
    style: 'currency',
    currency: currency || 'EUR',
    maximumFractionDigits: 0,
  }).format(price);
};

export default function SearchPage() {
  const [searchState, setSearchState] = useSearchState();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState({ items: [], facets: {}, pagination: {} });
  const [facetMeta, setFacetMeta] = useState({}); // To store types/labels

  // Fetch Data
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const queryParams = new URLSearchParams();
        
        // Map State to API Params
        if (searchState.q) queryParams.set('q', searchState.q);
        if (searchState.category) queryParams.set('category_slug', searchState.category);
        if (searchState.sort) queryParams.set('sort', searchState.sort);
        queryParams.set('page', searchState.page);
        queryParams.set('limit', searchState.limit);
        
        // Handle Price
        if (searchState.filters.price_min) queryParams.set('price_min', searchState.filters.price_min);
        if (searchState.filters.price_max) queryParams.set('price_max', searchState.filters.price_max);

        // Handle Attributes (JSON encoded for API v2)
        const attrFilters = {};
        Object.entries(searchState.filters).forEach(([key, val]) => {
           if (key === 'price_min' || key === 'price_max') return;
           attrFilters[key] = val;
        });
        
        if (Object.keys(attrFilters).length > 0) {
           queryParams.set('attrs', JSON.stringify(attrFilters));
        }

        const res = await fetch(`${API_URL}/api/v2/search?${queryParams.toString()}`);
        
        if (!res.ok) {
           throw new Error('Search failed');
        }

        const json = await res.json();
        setData(json);
        
        await fetchFacetMeta(Object.keys(json.facets));

      } catch (err) {
        console.error(err);
        setError('İlanlar yüklenirken bir hata oluştu.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [searchState]); // Re-run when URL state changes

  // Fetch Meta Data for Facets (Label, Type, etc.)
  const fetchFacetMeta = async (keys) => {
    try {
        const res = await fetch(`${API_URL}/api/attributes?filterable_only=true`);
        if (res.ok) {
            const attrs = await res.json();
            const meta = {};
            attrs.forEach(a => {
                meta[a.key] = {
                    label: a.name.tr || a.name.en || a.key,
                    type: a.attribute_type,
                    unit: a.unit,
                    min: 0, // Default
                    max: 1000000 // Default
                };
            });
            // Manual overrides for Price
            meta['price'] = { label: 'Fiyat', type: 'range', unit: 'EUR' }; // currency dynamic?
            setFacetMeta(meta);
        }
    } catch (e) {
        console.error("Meta fetch error", e);
    }
  };

  const handlePageChange = (newPage) => {
    setSearchState({ page: newPage });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleFilterChange = (newFilters) => {
    // Reset page to 1 when filters change
    setSearchState({ filters: newFilters, page: 1 });
  };

  const handleSortChange = (val) => {
    setSearchState({ sort: val });
  };

  return (
    <Layout>
      <div className="container mx-auto px-4 py-6">
        
        {/* Header & Mobile Filter Toggle */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
               {searchState.category ? `Kategori: ${searchState.category}` : 'Tüm İlanlar'}
            </h1>
            <p className="text-muted-foreground text-sm mt-1">
              {data.pagination.total || 0} sonuç bulundu
            </p>
          </div>

          <div className="flex items-center gap-2 w-full md:w-auto">
            <Select value={searchState.sort} onValueChange={handleSortChange}>
              <SelectTrigger className="w-full md:w-[180px]">
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
                 <FacetRenderer 
                    facets={data.facets} 
                    facetMeta={facetMeta}
                    selections={searchState.filters}
                    onFilterChange={handleFilterChange}
                 />
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
                      <Card key={item.id} className="overflow-hidden hover:shadow-md transition-shadow group cursor-pointer">
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
                            {formatPrice(item.price, item.currency)}
                          </Badge>
                        </div>
                        <CardHeader className="p-4 pb-2">
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
    </Layout>
  );
}
