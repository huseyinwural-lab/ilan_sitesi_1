import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { LoadingState, ErrorState, EmptyState } from '@/components/account/AccountStates';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AccountFavorites() {
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchFavorites = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/v1/favorites`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      });
      if (!res.ok) {
        throw new Error('Favoriler yüklenemedi');
      }
      const data = await res.json();
      setFavorites(data.items || []);
      setError('');
    } catch (err) {
      setError('Favoriler yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFavorites();
  }, []);

  const handleRemove = async (listingId) => {
    try {
      await fetch(`${API}/v1/favorites/${listingId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      });
      await fetchFavorites();
    } catch (err) {
      setError('Favori silinemedi');
    }
  };

  if (loading) {
    return <LoadingState label="Favoriler yükleniyor..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchFavorites} testId="account-favorites-error" />;
  }

  if (favorites.length === 0) {
    return (
      <EmptyState
        title="Favoriniz yok"
        description="Beğendiğiniz ilanları favoriye ekleyebilirsiniz."
        actionLabel="İlanlara Git"
        onAction={() => window.location.assign('/search')}
        testId="account-favorites-empty"
      />
    );
  }

  return (
    <div className="space-y-4" data-testid="account-favorites">
      <div className="flex items-center justify-between" data-testid="account-favorites-header">
        <h1 className="text-2xl font-bold" data-testid="account-favorites-title">Favoriler</h1>
        <span className="text-sm text-muted-foreground" data-testid="account-favorites-count">{favorites.length} ilan</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4" data-testid="account-favorites-grid">
        {favorites.map((item) => (
          <div key={item.listing_id} className="rounded-lg border bg-white overflow-hidden" data-testid={`account-favorite-card-${item.listing_id}`}>
            <div className="h-40 bg-slate-100" data-testid={`account-favorite-image-${item.listing_id}`}>
              {item.listing_image ? (
                <img src={item.listing_image} alt={item.listing_title} className="h-full w-full object-cover" />
              ) : (
                <div className="h-full w-full flex items-center justify-center text-sm text-muted-foreground">
                  Görsel yok
                </div>
              )}
            </div>
            <div className="p-4 space-y-2">
              <div className="text-sm text-muted-foreground" data-testid={`account-favorite-location-${item.listing_id}`}>{item.listing_location || '-'}</div>
              <div className="font-semibold" data-testid={`account-favorite-title-${item.listing_id}`}>{item.listing_title || item.listing_id}</div>
              <div className="text-sm font-medium" data-testid={`account-favorite-price-${item.listing_id}`}>{item.listing_price || '-'}</div>
              <div className="flex items-center gap-2">
                <Link
                  to={`/ilan/${item.listing_id}`}
                  className="h-9 px-3 rounded-md border text-sm"
                  data-testid={`account-favorite-view-${item.listing_id}`}
                >
                  İlana Git
                </Link>
                <button
                  type="button"
                  onClick={() => handleRemove(item.listing_id)}
                  className="h-9 px-3 rounded-md text-sm text-rose-600 border border-rose-200"
                  data-testid={`account-favorite-remove-${item.listing_id}`}
                >
                  Kaldır
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
