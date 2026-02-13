import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Layout from '@/components/Layout';
import { SEO } from '@/components/common/SEO';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { Loader2, MapPin, Calendar, Phone, Share2, Heart, ShieldCheck, User } from 'lucide-react';
import { format } from 'date-fns';
import { tr } from 'date-fns/locale';

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const formatPrice = (price, currency) => {
  return new Intl.NumberFormat('tr-TR', {
    style: 'currency',
    currency: currency || 'TRY',
    maximumFractionDigits: 0,
  }).format(price);
};

export default function DetailPage() {
  const { id } = useParams(); // URL format: :slug-:id
  
  // Extract UUID from end of string (Standard UUID has 36 chars)
  const realId = id.substr(-36); 

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const res = await fetch(`${API_URL}/api/v2/listings/${realId}`);
        if (!res.ok) {
          if (res.status === 404) throw new Error('İlan bulunamadı (404)');
          throw new Error('Bir hata oluştu');
        }
        const json = await res.json();
        setData(json);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [realId]);

  if (error) {
    return (
      <Layout>
        <div className="container mx-auto py-20 text-center">
          <h1 className="text-4xl font-bold mb-4">404</h1>
          <p className="text-muted-foreground text-lg">{error}</p>
          <Button variant="link" href="/search" className="mt-4">Aramaya Dön</Button>
        </div>
      </Layout>
    );
  }

  if (loading || !data) {
    return (
      <Layout>
        <div className="container mx-auto py-8 space-y-8">
          <Skeleton className="h-12 w-3/4" />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <Skeleton className="h-96 md:col-span-2 rounded-xl" />
            <div className="space-y-4">
              <Skeleton className="h-32 rounded-xl" />
              <Skeleton className="h-64 rounded-xl" />
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  const { listing, related } = data;

  return (
    <Layout>
      <SEO 
        title={`${listing.title} - ${formatPrice(listing.price, listing.currency)}`}
        description={listing.description ? listing.description.substring(0, 160) : listing.title}
        image={listing.media[0]?.url}
        price={listing.price}
        currency={listing.currency}
      />

      <div className="container mx-auto px-4 py-6">
        
        {/* Breadcrumb */}
        <div className="flex items-center text-sm text-muted-foreground mb-4 overflow-x-auto whitespace-nowrap pb-2">
          {listing.breadcrumbs.map((b, i) => (
            <React.Fragment key={i}>
              <a href={b.slug ? `/search?category=${b.slug}` : '/'} className="hover:text-foreground">
                {b.label}
              </a>
              {i < listing.breadcrumbs.length - 1 && <span className="mx-2">/</span>}
            </React.Fragment>
          ))}
        </div>

        {/* Title Section */}
        <div className="flex flex-col md:flex-row justify-between items-start gap-4 mb-6">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold leading-tight">{listing.title}</h1>
            <div className="flex items-center gap-4 mt-2 text-muted-foreground text-sm">
              <span className="flex items-center gap-1">
                <MapPin className="h-4 w-4" /> 
                {listing.location.city}, {listing.location.country}
              </span>
              <span className="flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                {format(new Date(listing.created_at), 'd MMMM yyyy', { locale: tr })}
              </span>
              <span className="text-xs px-2 py-0.5 bg-muted rounded">
                İlan No: {listing.id.split('-')[0]}
              </span>
            </div>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-primary">
              {formatPrice(listing.price, listing.currency)}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-8">
            
            {/* Gallery */}
            <div className="space-y-4">
              <div className="aspect-video bg-black rounded-xl overflow-hidden relative group">
                <img 
                  src={listing.media[activeImage]?.url} 
                  alt={listing.title} 
                  className="w-full h-full object-contain"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-4">
                  <p className="text-white text-sm">
                    {activeImage + 1} / {listing.media.length}
                  </p>
                </div>
              </div>
              
              {/* Thumbs */}
              <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
                {listing.media.map((m, i) => (
                  <button 
                    key={i}
                    onClick={() => setActiveImage(i)}
                    className={`relative w-20 h-16 flex-shrink-0 rounded-md overflow-hidden border-2 ${activeImage === i ? 'border-primary' : 'border-transparent'}`}
                  >
                    <img src={m.url} alt="" className="w-full h-full object-cover" />
                  </button>
                ))}
              </div>
            </div>

            {/* Description */}
            <Card>
              <CardContent className="p-6">
                <h2 className="text-xl font-semibold mb-4">Açıklama</h2>
                <div className="prose prose-sm max-w-none text-foreground/90 whitespace-pre-wrap">
                  {listing.description}
                </div>
              </CardContent>
            </Card>

            {/* Attributes */}
            <Card>
              <CardContent className="p-6">
                <h2 className="text-xl font-semibold mb-6">Özellikler</h2>
                {listing.attributes.map((group, i) => (
                  <div key={i} className="mb-6 last:mb-0">
                    {/* <h3 className="font-medium text-muted-foreground mb-3">{group.group}</h3> */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-y-4 gap-x-8">
                      {group.items.map((item) => (
                        <div key={item.key} className="flex justify-between border-b pb-2">
                          <span className="text-muted-foreground">{item.label}</span>
                          <span className="font-medium text-right">
                            {item.value === true ? 'Evet' : item.value === false ? 'Hayır' : item.value} 
                            {item.unit && ` ${item.unit}`}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            
            {/* Seller Card */}
            <Card className="border-l-4 border-l-primary">
              <CardContent className="p-6 space-y-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
                    <User className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-bold text-lg">{listing.seller.name}</h3>
                    <p className="text-sm text-muted-foreground capitalize">
                      {listing.seller.type === 'dealer' ? listing.seller.dealer_name : 'Bireysel Satıcı'}
                    </p>
                  </div>
                </div>

                <div className="space-y-3">
                  <Button className="w-full h-12 text-lg gap-2">
                    <Phone className="h-5 w-5" />
                    Ara
                  </Button>
                  <Button variant="outline" className="w-full h-12 gap-2">
                    Mesaj Gönder
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Safety Tips */}
            <Card className="bg-muted/30 border-none shadow-none">
              <CardContent className="p-4 flex gap-3">
                <ShieldCheck className="h-6 w-6 text-green-600 shrink-0" />
                <div className="text-sm text-muted-foreground">
                  <p className="font-medium text-foreground mb-1">Güvenli Alışveriş İpuçları</p>
                  <p>Kapora göndermeyin. Ürünü görmeden ödeme yapmayın.</p>
                </div>
              </CardContent>
            </Card>

            {/* Actions */}
            <div className="flex gap-2">
              <Button variant="outline" className="flex-1 gap-2">
                <Heart className="h-4 w-4" /> Favorile
              </Button>
              <Button variant="outline" className="flex-1 gap-2">
                <Share2 className="h-4 w-4" /> Paylaş
              </Button>
            </div>

          </div>

        </div>
      </div>
    </Layout>
  );
}
