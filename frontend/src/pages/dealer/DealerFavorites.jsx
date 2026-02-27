import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const tabOptions = [
  { key: 'listings', label: 'Favori İlanlar' },
  { key: 'searches', label: 'Favori Aramalar' },
  { key: 'sellers', label: 'Favori Satıcılar' },
];

const formatDate = (value) => {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '-';
  return date.toLocaleString('tr-TR');
};

export default function DealerFavorites() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [summary, setSummary] = useState({
    favorite_listings_count: 0,
    favorite_searches_count: 0,
    favorite_sellers_count: 0,
  });
  const [favoriteListings, setFavoriteListings] = useState([]);
  const [favoriteSearches, setFavoriteSearches] = useState([]);
  const [favoriteSellers, setFavoriteSellers] = useState([]);
  const [query, setQuery] = useState('');

  const activeTab = useMemo(() => {
    const raw = searchParams.get('tab') || 'listings';
    if (tabOptions.some((item) => item.key === raw)) return raw;
    return 'listings';
  }, [searchParams]);

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`${API}/dealer/favorites`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(payload?.detail || 'Favoriler alınamadı');
      setSummary(payload?.summary || {});
      setFavoriteListings(Array.isArray(payload?.favorite_listings) ? payload.favorite_listings : []);
      setFavoriteSearches(Array.isArray(payload?.favorite_searches) ? payload.favorite_searches : []);
      setFavoriteSellers(Array.isArray(payload?.favorite_sellers) ? payload.favorite_sellers : []);
    } catch (err) {
      setError(err?.message || 'Favoriler alınamadı');
      setSummary({
        favorite_listings_count: 0,
        favorite_searches_count: 0,
        favorite_sellers_count: 0,
      });
      setFavoriteListings([]);
      setFavoriteSearches([]);
      setFavoriteSellers([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const filteredListings = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return favoriteListings;
    return favoriteListings.filter((item) => `${item.title || ''} ${item.city || ''}`.toLowerCase().includes(q));
  }, [favoriteListings, query]);

  const filteredSearches = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return favoriteSearches;
    return favoriteSearches.filter((item) => `${item.label || ''}`.toLowerCase().includes(q));
  }, [favoriteSearches, query]);

  const filteredSellers = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return favoriteSellers;
    return favoriteSellers.filter((item) => `${item.full_name || ''} ${item.email || ''}`.toLowerCase().includes(q));
  }, [favoriteSellers, query]);

  const changeTab = (tabKey) => {
    setSearchParams({ tab: tabKey });
  };

  return (
    <div className="space-y-4" data-testid="dealer-favorites-page">
      <div className="flex flex-wrap items-center justify-between gap-3" data-testid="dealer-favorites-header">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900" data-testid="dealer-favorites-title">Favoriler</h1>
          <p className="text-sm font-medium text-slate-700" data-testid="dealer-favorites-subtitle">Favori ilan, arama ilgisi ve favorileyen kullanıcı görünümü.</p>
        </div>
        <button
          type="button"
          onClick={fetchData}
          className="h-9 rounded-md border border-slate-300 px-3 text-sm font-semibold text-slate-900"
          data-testid="dealer-favorites-refresh-button"
        >
          Yenile
        </button>
      </div>

      {error ? (
        <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700" data-testid="dealer-favorites-error">
          {error}
        </div>
      ) : null}

      <div className="rounded-lg border border-slate-200 bg-white p-4" data-testid="dealer-favorites-toolbar">
        <div className="flex flex-wrap items-center gap-2" data-testid="dealer-favorites-tabs">
          <button
            type="button"
            onClick={() => changeTab('listings')}
            className={`rounded-full border px-3 py-1.5 text-xs font-semibold ${activeTab === 'listings' ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-300 text-slate-800'}`}
            data-testid="dealer-favorites-tab-listings"
          >
            Favori İlanlar ({summary.favorite_listings_count || 0})
          </button>
          <button
            type="button"
            onClick={() => changeTab('searches')}
            className={`rounded-full border px-3 py-1.5 text-xs font-semibold ${activeTab === 'searches' ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-300 text-slate-800'}`}
            data-testid="dealer-favorites-tab-searches"
          >
            Favori Aramalar ({summary.favorite_searches_count || 0})
          </button>
          <button
            type="button"
            onClick={() => changeTab('sellers')}
            className={`rounded-full border px-3 py-1.5 text-xs font-semibold ${activeTab === 'sellers' ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-300 text-slate-800'}`}
            data-testid="dealer-favorites-tab-sellers"
          >
            Favori Satıcılar ({summary.favorite_sellers_count || 0})
          </button>
        </div>

        <div className="mt-3" data-testid="dealer-favorites-search-row">
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            className="h-10 w-full max-w-md rounded-md border border-slate-300 px-3 text-sm text-slate-900"
            placeholder="Ara"
            data-testid="dealer-favorites-search-input"
          />
        </div>
      </div>

      {loading ? (
        <div className="rounded-md border border-slate-200 bg-white p-4 text-sm text-slate-600" data-testid="dealer-favorites-loading">
          Yükleniyor...
        </div>
      ) : null}

      {!loading && activeTab === 'listings' ? (
        <div className="rounded-md border border-slate-200 overflow-x-auto" data-testid="dealer-favorites-table-listings-wrap">
          <table className="w-full text-sm" data-testid="dealer-favorites-table-listings">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-3 py-2 text-left text-slate-800">İlan</th>
                <th className="px-3 py-2 text-left text-slate-800">Şehir</th>
                <th className="px-3 py-2 text-left text-slate-800">Fiyat</th>
                <th className="px-3 py-2 text-left text-slate-800">Favori Sayısı</th>
                <th className="px-3 py-2 text-left text-slate-800">Son Favorileme</th>
                <th className="px-3 py-2 text-left text-slate-800">İşlem</th>
              </tr>
            </thead>
            <tbody>
              {filteredListings.length === 0 ? (
                <tr><td className="px-3 py-4 text-slate-600" colSpan={6} data-testid="dealer-favorites-empty-listings">Kayıt yok</td></tr>
              ) : filteredListings.map((item) => (
                <tr key={item.listing_id} className="border-t" data-testid={`dealer-favorites-listing-row-${item.listing_id}`}>
                  <td className="px-3 py-2 font-medium text-slate-900" data-testid={`dealer-favorites-listing-title-${item.listing_id}`}>{item.title || '-'}</td>
                  <td className="px-3 py-2" data-testid={`dealer-favorites-listing-city-${item.listing_id}`}>{item.city || '-'}</td>
                  <td className="px-3 py-2" data-testid={`dealer-favorites-listing-price-${item.listing_id}`}>{new Intl.NumberFormat('tr-TR').format(Number(item.price || 0))} TL</td>
                  <td className="px-3 py-2 font-semibold" data-testid={`dealer-favorites-listing-count-${item.listing_id}`}>{item.favorite_count || 0}</td>
                  <td className="px-3 py-2" data-testid={`dealer-favorites-listing-last-${item.listing_id}`}>{formatDate(item.last_favorited_at)}</td>
                  <td className="px-3 py-2" data-testid={`dealer-favorites-listing-action-${item.listing_id}`}>
                    <button
                      type="button"
                      onClick={() => navigate(item.route || '/dealer/listings')}
                      className="rounded border border-slate-300 px-2 py-1 text-xs font-semibold text-slate-900"
                      data-testid={`dealer-favorites-listing-open-${item.listing_id}`}
                    >
                      Aç
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {!loading && activeTab === 'searches' ? (
        <div className="rounded-md border border-slate-200 overflow-x-auto" data-testid="dealer-favorites-table-searches-wrap">
          <table className="w-full text-sm" data-testid="dealer-favorites-table-searches">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-3 py-2 text-left text-slate-800">Arama Tanımı</th>
                <th className="px-3 py-2 text-left text-slate-800">Arama Sayısı</th>
                <th className="px-3 py-2 text-left text-slate-800">Son Görülme</th>
                <th className="px-3 py-2 text-left text-slate-800">İşlem</th>
              </tr>
            </thead>
            <tbody>
              {filteredSearches.length === 0 ? (
                <tr><td className="px-3 py-4 text-slate-600" colSpan={4} data-testid="dealer-favorites-empty-searches">Kayıt yok</td></tr>
              ) : filteredSearches.map((item) => (
                <tr key={item.search_key} className="border-t" data-testid={`dealer-favorites-search-row-${item.search_key}`}>
                  <td className="px-3 py-2 font-medium text-slate-900" data-testid={`dealer-favorites-search-label-${item.search_key}`}>{item.label}</td>
                  <td className="px-3 py-2 font-semibold" data-testid={`dealer-favorites-search-count-${item.search_key}`}>{item.search_count || 0}</td>
                  <td className="px-3 py-2" data-testid={`dealer-favorites-search-last-${item.search_key}`}>{formatDate(item.last_seen_at)}</td>
                  <td className="px-3 py-2" data-testid={`dealer-favorites-search-action-${item.search_key}`}>
                    <button
                      type="button"
                      onClick={() => navigate(item.route || '/dealer/reports')}
                      className="rounded border border-slate-300 px-2 py-1 text-xs font-semibold text-slate-900"
                      data-testid={`dealer-favorites-search-open-${item.search_key}`}
                    >
                      Aç
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {!loading && activeTab === 'sellers' ? (
        <div className="rounded-md border border-slate-200 overflow-x-auto" data-testid="dealer-favorites-table-sellers-wrap">
          <table className="w-full text-sm" data-testid="dealer-favorites-table-sellers">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-3 py-2 text-left text-slate-800">Ad Soyad</th>
                <th className="px-3 py-2 text-left text-slate-800">E-Posta</th>
                <th className="px-3 py-2 text-left text-slate-800">Favori Sayısı</th>
                <th className="px-3 py-2 text-left text-slate-800">Son Favorileme</th>
                <th className="px-3 py-2 text-left text-slate-800">İşlem</th>
              </tr>
            </thead>
            <tbody>
              {filteredSellers.length === 0 ? (
                <tr><td className="px-3 py-4 text-slate-600" colSpan={5} data-testid="dealer-favorites-empty-sellers">Kayıt yok</td></tr>
              ) : filteredSellers.map((item) => (
                <tr key={item.user_id} className="border-t" data-testid={`dealer-favorites-seller-row-${item.user_id}`}>
                  <td className="px-3 py-2 font-medium text-slate-900" data-testid={`dealer-favorites-seller-name-${item.user_id}`}>{item.full_name || '-'}</td>
                  <td className="px-3 py-2" data-testid={`dealer-favorites-seller-email-${item.user_id}`}>{item.email || '-'}</td>
                  <td className="px-3 py-2 font-semibold" data-testid={`dealer-favorites-seller-count-${item.user_id}`}>{item.favorite_count || 0}</td>
                  <td className="px-3 py-2" data-testid={`dealer-favorites-seller-last-${item.user_id}`}>{formatDate(item.last_favorited_at)}</td>
                  <td className="px-3 py-2" data-testid={`dealer-favorites-seller-action-${item.user_id}`}>
                    <button
                      type="button"
                      onClick={() => navigate(item.route || '/dealer/customers')}
                      className="rounded border border-slate-300 px-2 py-1 text-xs font-semibold text-slate-900"
                      data-testid={`dealer-favorites-seller-open-${item.user_id}`}
                    >
                      Aç
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  );
}