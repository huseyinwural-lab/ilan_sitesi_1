import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { LoadingState, ErrorState, EmptyState } from '@/components/account/AccountStates';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const buildSummary = (item) => {
  const filters = item?.filters_json || {};
  const summaryParts = [];
  if (filters.q) summaryParts.push(`Arama: ${filters.q}`);
  if (filters.category) summaryParts.push(`Kategori: ${filters.category}`);
  if (filters.make) summaryParts.push(`Marka: ${filters.make}`);
  if (filters.model) summaryParts.push(`Model: ${filters.model}`);
  if (filters.sort) summaryParts.push(`Sıralama: ${filters.sort}`);
  const attrCount = filters.filters && typeof filters.filters === 'object' ? Object.keys(filters.filters).length : 0;
  if (attrCount > 0) summaryParts.push(`Detay filtre: ${attrCount}`);
  return summaryParts.length > 0 ? summaryParts.join(' • ') : 'Filtre özeti yok';
};

export default function AccountSavedSearches() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionLoading, setActionLoading] = useState('');

  const authHeaders = useMemo(() => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` }), []);

  const fetchSavedSearches = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/v1/saved-searches`, { headers: authHeaders });
      if (!res.ok) throw new Error('Kayıtlı aramalar yüklenemedi');
      const data = await res.json();
      setItems(Array.isArray(data?.items) ? data.items : []);
      setError('');
    } catch (_err) {
      setError('Kayıtlı aramalar yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSavedSearches();
  }, []);

  const handleDelete = async (id) => {
    setActionLoading(`delete-${id}`);
    try {
      const res = await fetch(`${API}/v1/saved-searches/${id}`, {
        method: 'DELETE',
        headers: authHeaders,
      });
      if (!res.ok) throw new Error('Silinemedi');
      await fetchSavedSearches();
    } catch (_err) {
      setError('Kayıtlı arama silinemedi');
    } finally {
      setActionLoading('');
    }
  };

  const handleToggle = async (id, patch) => {
    setActionLoading(`toggle-${id}`);
    try {
      const res = await fetch(`${API}/v1/saved-searches/${id}/notifications`, {
        method: 'PATCH',
        headers: {
          ...authHeaders,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(patch),
      });
      if (!res.ok) throw new Error('Toggle kaydedilemedi');
      const data = await res.json();
      setItems((prev) => prev.map((row) => (row.id === id ? data.item : row)));
    } catch (_err) {
      setError('Bildirim tercihi kaydedilemedi');
    } finally {
      setActionLoading('');
    }
  };

  if (loading) return <LoadingState label="Kayıtlı aramalar yükleniyor..." />;
  if (error) return <ErrorState message={error} onRetry={fetchSavedSearches} testId="account-saved-searches-error" />;

  if (items.length === 0) {
    return (
      <EmptyState
        title="Kayıtlı arama yok"
        description="Arama ekranından filtrelerinizi kaydedebilirsiniz."
        actionLabel="Aramaya Git"
        onAction={() => window.location.assign('/search')}
        testId="account-saved-searches-empty"
      />
    );
  }

  return (
    <div className="space-y-4" data-testid="account-saved-searches-page">
      <div className="flex items-center justify-between" data-testid="account-saved-searches-header">
        <h1 className="text-2xl font-bold" data-testid="account-saved-searches-title">Kayıtlı Aramalar</h1>
        <span className="text-sm text-muted-foreground" data-testid="account-saved-searches-count">{items.length} kayıt</span>
      </div>

      <div className="space-y-3" data-testid="account-saved-searches-list">
        {items.map((item) => {
          const query = item.query_string ? `?${item.query_string}` : '';
          return (
            <div key={item.id} className="rounded-lg border bg-white p-4" data-testid={`account-saved-search-row-${item.id}`}>
              <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-3">
                <div className="space-y-1">
                  <div className="font-semibold" data-testid={`account-saved-search-name-${item.id}`}>{item.name}</div>
                  <div className="text-sm text-muted-foreground" data-testid={`account-saved-search-summary-${item.id}`}>{buildSummary(item)}</div>
                  <div className="text-xs text-slate-500" data-testid={`account-saved-search-date-${item.id}`}>
                    Oluşturulma: {item.created_at ? new Date(item.created_at).toLocaleString('tr-TR') : '-'}
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-3">
                  <label className="inline-flex items-center gap-2 text-xs" data-testid={`account-saved-search-email-wrap-${item.id}`}>
                    <input
                      type="checkbox"
                      checked={Boolean(item.email_enabled)}
                      onChange={(e) => handleToggle(item.id, { email_enabled: e.target.checked })}
                      data-testid={`account-saved-search-email-toggle-${item.id}`}
                    />
                    Email
                  </label>

                  <label className="inline-flex items-center gap-2 text-xs" data-testid={`account-saved-search-push-wrap-${item.id}`}>
                    <input
                      type="checkbox"
                      checked={Boolean(item.push_enabled)}
                      onChange={(e) => handleToggle(item.id, { push_enabled: e.target.checked })}
                      data-testid={`account-saved-search-push-toggle-${item.id}`}
                    />
                    Push
                  </label>

                  <Link
                    to={`/search${query}`}
                    className="h-9 px-3 rounded-md border text-sm inline-flex items-center"
                    data-testid={`account-saved-search-open-${item.id}`}
                  >
                    Bu aramayla devam et
                  </Link>

                  <button
                    type="button"
                    onClick={() => handleDelete(item.id)}
                    disabled={actionLoading === `delete-${item.id}`}
                    className="h-9 px-3 rounded-md border border-rose-200 text-rose-600 text-sm"
                    data-testid={`account-saved-search-delete-${item.id}`}
                  >
                    Sil
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
