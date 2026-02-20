import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { EmptyState } from '@/components/account/AccountStates';

const readFavorites = () => {
  try {
    return JSON.parse(localStorage.getItem('account_favorites') || '[]');
  } catch (e) {
    return [];
  }
};

export default function AccountFavorites() {
  const [favorites, setFavorites] = useState([]);

  useEffect(() => {
    setFavorites(readFavorites());
  }, []);

  const handleRemove = (listingId) => {
    const next = favorites.filter((item) => item.id !== listingId);
    localStorage.setItem('account_favorites', JSON.stringify(next));
    setFavorites(next);
  };

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
          <div key={item.id} className="rounded-lg border bg-white overflow-hidden" data-testid={`account-favorite-card-${item.id}`}>
            <div className="h-40 bg-slate-100" data-testid={`account-favorite-image-${item.id}`}>
              {item.image ? (
                <img src={item.image} alt={item.title} className="h-full w-full object-cover" />
              ) : (
                <div className="h-full w-full flex items-center justify-center text-sm text-muted-foreground">
                  Görsel yok
                </div>
              )}
            </div>
            <div className="p-4 space-y-2">
              <div className="text-sm text-muted-foreground" data-testid={`account-favorite-location-${item.id}`}>{item.location || '-'}</div>
              <div className="font-semibold" data-testid={`account-favorite-title-${item.id}`}>{item.title}</div>
              <div className="text-sm font-medium" data-testid={`account-favorite-price-${item.id}`}>{item.price || '-'}</div>
              <div className="flex items-center gap-2">
                <Link
                  to={`/ilan/${item.id}`}
                  className="h-9 px-3 rounded-md border text-sm"
                  data-testid={`account-favorite-view-${item.id}`}
                >
                  İlana Git
                </Link>
                <button
                  type="button"
                  onClick={() => handleRemove(item.id)}
                  className="h-9 px-3 rounded-md text-sm text-rose-600 border border-rose-200"
                  data-testid={`account-favorite-remove-${item.id}`}
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
