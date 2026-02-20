import React, { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { LoadingState, ErrorState, EmptyState } from '@/components/account/AccountStates';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const tabs = [
  { key: 'all', label: 'Tümü' },
  { key: 'active', label: 'Yayında' },
  { key: 'draft', label: 'Taslak' },
  { key: 'rejected', label: 'Reddedildi' },
  { key: 'expired', label: 'Süresi Doldu' },
];

const statusLabel = (status) => {
  switch (status) {
    case 'published':
      return { label: 'Yayında', color: 'bg-emerald-100 text-emerald-700' };
    case 'pending_moderation':
      return { label: 'Moderasyon', color: 'bg-amber-100 text-amber-700' };
    case 'needs_revision':
      return { label: 'Revize', color: 'bg-amber-100 text-amber-700' };
    case 'rejected':
      return { label: 'Reddedildi', color: 'bg-rose-100 text-rose-700' };
    case 'unpublished':
      return { label: 'Yayından Kaldırıldı', color: 'bg-slate-100 text-slate-700' };
    case 'archived':
      return { label: 'Arşiv', color: 'bg-slate-100 text-slate-700' };
    default:
      return { label: 'Taslak', color: 'bg-slate-100 text-slate-700' };
  }
};

const formatDate = (value) => {
  if (!value) return '-';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return '-';
  return d.toLocaleDateString('tr-TR');
};

export default function MyListings() {
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [tab, setTab] = useState('all');
  const [search, setSearch] = useState('');

  const fetchListings = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (tab !== 'all') params.set('status', tab);
      if (search.trim()) params.set('q', search.trim());
      const res = await fetch(`${API}/v1/listings/my?${params.toString()}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      });
      if (!res.ok) {
        throw new Error('İlanlar yüklenemedi');
      }
      const data = await res.json();
      setItems(data.items || []);
      setError('');
    } catch (err) {
      setError('İlanlar yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchListings();
  }, [tab]);

  const handleSearch = (e) => {
    e.preventDefault();
    fetchListings();
  };

  const handleArchive = async (listingId) => {
    if (!window.confirm('İlanı arşivlemek istiyor musunuz?')) return;
    await fetch(`${API}/v1/listings/vehicle/${listingId}/archive`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
    });
    fetchListings();
  };

  const handlePublish = async (listingId) => {
    if (!window.confirm('İlanı yayına almak istiyor musunuz?')) return;
    await fetch(`${API}/v1/listings/vehicle/${listingId}/request-publish`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
    });
    fetchListings();
  };

  const handleUnpublish = async (listingId) => {
    if (!window.confirm('İlanı yayından kaldırmak istiyor musunuz?')) return;
    await fetch(`${API}/v1/listings/vehicle/${listingId}/unpublish`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
    });
    fetchListings();
  };

  const handleExtend = async (listingId) => {
    await fetch(`${API}/v1/listings/vehicle/${listingId}/extend`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ days: 30 }),
    });
    fetchListings();
  };

  if (loading) {
    return <LoadingState label="İlanlar yükleniyor..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchListings} testId="account-listings-error" />;
  }

  if (items.length === 0) {
    return (
      <EmptyState
        title="İlanınız yok"
        description="Yeni ilan oluşturmak için sihirbazı başlatın."
        actionLabel="Yeni İlan Oluştur"
        onAction={() => navigate('/account/create/vehicle-wizard')}
        testId="account-listings-empty"
      />
    );
  }

  return (
    <div className="space-y-4" data-testid="account-listings">
      <div className="flex flex-wrap items-center justify-between gap-3" data-testid="account-listings-header">
        <div>
          <h2 className="text-2xl font-bold" data-testid="account-listings-title">İlanlarım</h2>
          <p className="text-sm text-muted-foreground" data-testid="account-listings-subtitle">İlan durumlarınızı yönetin.</p>
        </div>
        <Link
          to="/account/create/vehicle-wizard"
          className="h-10 px-4 rounded-md bg-primary text-primary-foreground text-sm inline-flex items-center"
          data-testid="account-listings-create"
        >
          Yeni İlan
        </Link>
      </div>

      <div className="flex flex-wrap items-center gap-3" data-testid="account-listings-controls">
        <div className="flex flex-wrap gap-2" data-testid="account-listings-tabs">
          {tabs.map((item) => (
            <button
              key={item.key}
              type="button"
              onClick={() => setTab(item.key)}
              className={`h-9 px-3 rounded-md border text-sm ${tab === item.key ? 'bg-muted' : ''}`}
              data-testid={`account-listings-tab-${item.key}`}
            >
              {item.label}
            </button>
          ))}
        </div>
        <form onSubmit={handleSearch} className="flex items-center gap-2" data-testid="account-listings-search">
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-9 rounded-md border px-3 text-sm"
            placeholder="İlan ara"
            data-testid="account-listings-search-input"
          />
          <button type="submit" className="h-9 px-3 rounded-md border text-sm" data-testid="account-listings-search-submit">
            Ara
          </button>
        </form>
      </div>

      <div className="rounded-lg border bg-white overflow-hidden" data-testid="account-listings-table">
        <table className="w-full text-sm">
          <thead className="bg-muted">
            <tr>
              <th className="text-left p-3">İlan</th>
              <th className="text-left p-3">Durum</th>
              <th className="text-left p-3">Fiyat</th>
              <th className="text-left p-3">Oluşturma</th>
              <th className="text-left p-3">Bitiş</th>
              <th className="text-right p-3">Aksiyonlar</th>
            </tr>
          </thead>
          <tbody>
            {items.map((listing) => {
              const status = statusLabel(listing.status);
              const canPublish = ['draft', 'needs_revision', 'unpublished'].includes(listing.status);
              return (
                <tr key={listing.id} className="border-t" data-testid={`account-listings-row-${listing.id}`}>
                  <td className="p-3">
                    <div className="font-medium" data-testid={`account-listings-title-${listing.id}`}>{listing.title || listing.id}</div>
                    {listing.moderation_note && (
                      <div className="text-xs text-rose-600" data-testid={`account-listings-moderation-${listing.id}`}>
                        {listing.moderation_note}
                      </div>
                    )}
                  </td>
                  <td className="p-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${status.color}`} data-testid={`account-listings-status-${listing.id}`}>
                      {status.label}
                    </span>
                  </td>
                  <td className="p-3" data-testid={`account-listings-price-${listing.id}`}>
                    {listing.price?.amount || listing.attributes?.price_eur || '-'}
                  </td>
                  <td className="p-3" data-testid={`account-listings-created-${listing.id}`}>
                    {formatDate(listing.created_at)}
                  </td>
                  <td className="p-3" data-testid={`account-listings-expires-${listing.id}`}>
                    {formatDate(listing.expires_at)}
                  </td>
                  <td className="p-3 text-right">
                    <div className="flex flex-wrap items-center justify-end gap-2">
                      <button
                        type="button"
                        onClick={() => navigate(`/account/create/vehicle-wizard?edit=${listing.id}`)}
                        className="h-8 px-3 rounded-md border text-xs"
                        data-testid={`account-listings-edit-${listing.id}`}
                      >
                        Düzenle
                      </button>
                      {listing.status === 'published' ? (
                        <button
                          type="button"
                          onClick={() => handleUnpublish(listing.id)}
                          className="h-8 px-3 rounded-md border text-xs"
                          data-testid={`account-listings-unpublish-${listing.id}`}
                        >
                          Yayından Kaldır
                        </button>
                      ) : (
                        <button
                          type="button"
                          onClick={() => handlePublish(listing.id)}
                          disabled={!canPublish}
                          className="h-8 px-3 rounded-md border text-xs disabled:opacity-50"
                          data-testid={`account-listings-publish-${listing.id}`}
                        >
                          Yayına Al
                        </button>
                      )}
                      <button
                        type="button"
                        onClick={() => handleExtend(listing.id)}
                        className="h-8 px-3 rounded-md border text-xs"
                        data-testid={`account-listings-extend-${listing.id}`}
                      >
                        Süre Uzat
                      </button>
                      <button
                        type="button"
                        onClick={() => handleArchive(listing.id)}
                        className="h-8 px-3 rounded-md border text-xs text-rose-600 border-rose-200"
                        data-testid={`account-listings-archive-${listing.id}`}
                      >
                        Sil
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
