import React, { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { toast } from '@/components/ui/use-toast';
import { trackDealerEvent } from '@/lib/dealerAnalytics';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const formatPrice = (value) => {
  if (value === null || value === undefined || value === '') return '-';
  const number = Number(value);
  if (Number.isNaN(number)) return '-';
  return new Intl.NumberFormat('tr-TR').format(number);
};

const statusLabels = {
  active: 'Aktif',
  draft: 'Taslak',
  archived: 'Arşiv',
};

const computeExpiry = (createdAt) => {
  if (!createdAt) return '-';
  const date = new Date(createdAt);
  if (Number.isNaN(date.getTime())) return '-';
  date.setDate(date.getDate() + 90);
  return date.toLocaleDateString('tr-TR');
};

const inactiveStatuses = new Set(['draft', 'archived']);

export default function DealerListings() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [allItems, setAllItems] = useState([]);
  const [quota, setQuota] = useState({ limit: 0, used: 0, remaining: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [createOpen, setCreateOpen] = useState(false);
  const [form, setForm] = useState({ title: '', price: '' });
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState('');
  const [statusFilter, setStatusFilter] = useState('active');
  const [query, setQuery] = useState('');
  const [selectedIds, setSelectedIds] = useState([]);
  const [bulkLoading, setBulkLoading] = useState(false);
  const [lastBulkAction, setLastBulkAction] = useState(null);

  const authHeader = useMemo(
    () => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` }),
    []
  );

  const fetchListings = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API}/dealer/listings?status=all`, { headers: authHeader });
      if (!res.ok) {
        throw new Error('İlanlar yüklenemedi');
      }
      const data = await res.json();
      setAllItems(data.items || []);
      setQuota(data.quota || { limit: 0, used: 0, remaining: 0 });
    } catch (err) {
      setError('İlanlar yüklenemedi.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchListings();
  }, []);

  useEffect(() => {
    if (searchParams.get('create') === '1') {
      setCreateOpen(true);
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        next.delete('create');
        return next;
      }, { replace: true });
    }
  }, [searchParams, setSearchParams]);

  useEffect(() => {
    setSelectedIds((prev) => prev.filter((id) => allItems.some((item) => item.id === id)));
  }, [allItems]);

  const counters = useMemo(() => {
    const active = allItems.filter((item) => item.status === 'active').length;
    const inactive = allItems.filter((item) => inactiveStatuses.has(item.status)).length;
    return { active, inactive, total: allItems.length };
  }, [allItems]);

  const filteredItems = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return allItems.filter((item) => {
      const statusMatched =
        statusFilter === 'all'
          ? true
          : statusFilter === 'inactive'
            ? inactiveStatuses.has(item.status)
            : item.status === statusFilter;
      if (!statusMatched) return false;
      if (!normalizedQuery) return true;
      return `${item.title || ''}`.toLowerCase().includes(normalizedQuery);
    });
  }, [allItems, statusFilter, query]);

  const handleOpenCreate = () => {
    trackDealerEvent('dealer_listing_create_start', { source: 'dealer_listings' });
    setForm({ title: '', price: '' });
    setFormError('');
    setCreateOpen(true);
  };

  const handleCreate = async (event) => {
    event.preventDefault();
    setFormError('');
    if (!form.title.trim()) {
      setFormError('Başlık gerekli.');
      return;
    }

    setSaving(true);
    try {
      const payload = {
        title: form.title.trim(),
        price: form.price ? Number(form.price) : null,
      };
      const res = await fetch(`${API}/dealer/listings`, {
        method: 'POST',
        headers: {
          ...authHeader,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const detail = await res.json();
        throw new Error(detail?.detail || 'İlan oluşturulamadı');
      }
      setCreateOpen(false);
      fetchListings();
    } catch (err) {
      setFormError(err?.message || 'İlan oluşturulamadı');
    } finally {
      setSaving(false);
    }
  };

  const allSelected = filteredItems.length > 0 && selectedIds.length === filteredItems.length;
  const bulkDisabled = selectedIds.length === 0 || bulkLoading;

  const handleSelectAll = () => {
    if (allSelected) {
      setSelectedIds([]);
    } else {
      setSelectedIds(filteredItems.map((item) => item.id));
    }
  };

  const handleToggleSelect = (id) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((itemId) => itemId !== id) : [...prev, id]
    );
  };

  const handleBulkAction = async (action, idsOverride) => {
    const ids = idsOverride || selectedIds;
    if (!ids.length || bulkLoading) return;
    setBulkLoading(true);

    try {
      const res = await fetch(`${API}/dealer/listings/bulk`, {
        method: 'POST',
        headers: {
          ...authHeader,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ids, action }),
      });
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail?.detail || 'Toplu işlem başarısız');
      }

      const data = await res.json();
      const updatedCount = (data.updated || 0) + (data.deleted || 0);
      const failedCount = data.failed || 0;

      if (updatedCount > 0) {
        toast({ title: `${updatedCount} ilan güncellendi` });
      }
      if (failedCount > 0) {
        toast({ title: `${failedCount} ilan güncellenemedi`, variant: 'destructive' });
        setLastBulkAction({ action, ids });
      } else {
        setLastBulkAction(null);
      }

      await fetchListings();
      setSelectedIds([]);
    } catch (err) {
      toast({ title: err?.message || 'Toplu işlem başarısız', variant: 'destructive' });
      setLastBulkAction({ action, ids });
    } finally {
      setBulkLoading(false);
    }
  };

  const handleRetry = () => {
    if (!lastBulkAction) return;
    handleBulkAction(lastBulkAction.action, lastBulkAction.ids);
  };

  const handleStatusUpdate = async (listingId, status) => {
    try {
      const res = await fetch(`${API}/dealer/listings/${listingId}/status`, {
        method: 'POST',
        headers: {
          ...authHeader,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status }),
      });
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail?.detail || 'İlan güncellenemedi');
      }
      toast({ title: 'İlan durumu güncellendi' });
      await fetchListings();
    } catch (err) {
      toast({ title: err?.message || 'İlan güncellenemedi', variant: 'destructive' });
    }
  };

  if (loading) {
    return (
      <div className="text-sm text-muted-foreground" data-testid="dealer-listings-loading">
        İlanlar yükleniyor...
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-3" data-testid="dealer-listings-error">
        <p className="text-sm text-rose-600" data-testid="dealer-listings-error-message">
          {error}
        </p>
        <button
          type="button"
          onClick={() => fetchListings()}
          className="h-9 px-3 rounded-md border text-sm"
          data-testid="dealer-listings-retry"
        >
          Tekrar Dene
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="dealer-listings">
      <div className="flex flex-wrap items-start justify-between gap-3" data-testid="dealer-listings-header">
        <div>
          <h2 className="text-2xl font-bold text-slate-900" data-testid="dealer-listings-title">
            Yayında Olan İlanlar ({counters.active})
          </h2>
          <p className="text-sm font-medium text-slate-700" data-testid="dealer-listings-subtitle">
            PDF akışına uygun kurumsal ilan yönetimi.
          </p>
        </div>
        <div className="flex items-center gap-3" data-testid="dealer-listings-actions">
          <div className="rounded-md border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-800" data-testid="dealer-listings-quota">
            Kota: <span data-testid="dealer-listings-quota-used">{quota.used}</span> /{' '}
            <span data-testid="dealer-listings-quota-limit">{quota.limit}</span>
            {quota.remaining !== undefined && (
              <span className="ml-2 text-slate-600" data-testid="dealer-listings-quota-remaining">
                Kalan {quota.remaining}
              </span>
            )}
          </div>
          <button
            type="button"
            onClick={handleOpenCreate}
            className="h-10 px-4 rounded-md bg-slate-900 text-white text-sm"
            data-testid="dealer-listings-create"
          >
            Yeni İlan Oluştur
          </button>
        </div>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-4" data-testid="dealer-listings-toolbar">
        <div className="flex flex-wrap items-center justify-between gap-3" data-testid="dealer-listings-search-row">
          <div className="relative w-full max-w-md" data-testid="dealer-listings-search-wrap">
            <input
              type="text"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="İlan başlığı ile ara"
              className="h-10 w-full rounded-md border border-slate-300 px-3 text-sm text-slate-900"
              data-testid="dealer-listings-search-input"
            />
          </div>
          <span className="text-xs font-semibold text-slate-700" data-testid="dealer-listings-sort-info">Sıralama: Yeni → Eski</span>
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-2" data-testid="dealer-listings-status-tabs">
          <button
            type="button"
            onClick={() => setStatusFilter('active')}
            className={`rounded-full border px-3 py-1.5 text-xs font-semibold ${statusFilter === 'active' ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-300 text-slate-800'}`}
            data-testid="dealer-listings-status-tab-active"
          >
            Yayında ({counters.active})
          </button>
          <button
            type="button"
            onClick={() => setStatusFilter('inactive')}
            className={`rounded-full border px-3 py-1.5 text-xs font-semibold ${statusFilter === 'inactive' ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-300 text-slate-800'}`}
            data-testid="dealer-listings-status-tab-inactive"
          >
            Yayında Değil ({counters.inactive})
          </button>
          <button
            type="button"
            onClick={() => setStatusFilter('all')}
            className={`rounded-full border px-3 py-1.5 text-xs font-semibold ${statusFilter === 'all' ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-300 text-slate-800'}`}
            data-testid="dealer-listings-status-tab-all"
          >
            Tümü ({counters.total})
          </button>
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-2" data-testid="dealer-listings-bulk-actions">
            <span className="text-xs font-medium text-slate-700" data-testid="dealer-listings-selected-count">
              Seçili: {selectedIds.length}
            </span>
            <button
              type="button"
              onClick={() => handleBulkAction('archive')}
              disabled={bulkDisabled}
              className="h-9 px-3 rounded-md border text-xs disabled:opacity-60"
              data-testid="dealer-listings-bulk-archive"
            >
              Arşivle
            </button>
            <button
              type="button"
              onClick={() => handleBulkAction('delete')}
              disabled={bulkDisabled}
              className="h-9 px-3 rounded-md border border-rose-200 text-rose-600 text-xs disabled:opacity-60"
              data-testid="dealer-listings-bulk-delete"
            >
              Soft Delete
            </button>
            <button
              type="button"
              onClick={() => handleBulkAction('restore')}
              disabled={bulkDisabled}
              className="h-9 px-3 rounded-md border text-xs disabled:opacity-60"
              data-testid="dealer-listings-bulk-restore"
            >
              Restore
            </button>
            {lastBulkAction && (
              <button
                type="button"
                onClick={handleRetry}
                className="h-9 px-3 rounded-md bg-slate-900 text-white text-xs"
                data-testid="dealer-listings-bulk-retry"
              >
                Tekrar Dene
              </button>
            )}
        </div>
      </div>

      {filteredItems.length === 0 ? (
        <div className="rounded-lg border border-slate-200 bg-white p-6 text-sm font-medium text-slate-700" data-testid="dealer-listings-empty">
          Bu filtrede ilan bulunamadı. Farklı bir durum seçin veya yeni ilan oluşturun.
        </div>
      ) : (
        <div className="rounded-lg border border-slate-200 bg-white overflow-hidden" data-testid="dealer-listings-table">
          <div className="grid grid-cols-[60px_1fr_120px_120px_120px_120px_120px_110px] gap-3 bg-slate-50 text-sm font-semibold px-3 py-2 text-slate-800" data-testid="dealer-listings-table-header">
            <div className="flex items-center" data-testid="dealer-listings-header-select">
              <input
                type="checkbox"
                checked={allSelected}
                onChange={handleSelectAll}
                className="h-4 w-4"
                data-testid="dealer-listings-select-all"
              />
            </div>
            <div data-testid="dealer-listings-header-title">İlan</div>
            <div data-testid="dealer-listings-header-price">Fiyat</div>
            <div data-testid="dealer-listings-header-views">Görüntülenme</div>
            <div data-testid="dealer-listings-header-favorites">Favori</div>
            <div data-testid="dealer-listings-header-messages">Mesaj</div>
            <div data-testid="dealer-listings-header-expiry">Bitiş</div>
            <div data-testid="dealer-listings-header-actions">İşlem</div>
          </div>
          <div className="divide-y" data-testid="dealer-listings-table-body">
            {filteredItems.map((item) => (
              <div
                key={item.id}
                className="grid grid-cols-[60px_1fr_120px_120px_120px_120px_120px_110px] gap-3 px-3 py-3 text-sm"
                data-testid={`dealer-listings-row-${item.id}`}
              >
                <div className="flex items-center" data-testid={`dealer-listings-select-cell-${item.id}`}>
                  <input
                    type="checkbox"
                    checked={selectedIds.includes(item.id)}
                    onChange={() => handleToggleSelect(item.id)}
                    className="h-4 w-4"
                    data-testid={`dealer-listings-select-${item.id}`}
                  />
                </div>
                <div data-testid={`dealer-listings-title-${item.id}`}>
                  <div className="font-semibold text-slate-900">{item.title}</div>
                  <div className="mt-1 inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-semibold text-slate-700" data-testid={`dealer-listings-status-pill-${item.id}`}>
                    {statusLabels[item.status] || item.status}
                  </div>
                </div>
                <div className="font-semibold text-slate-900" data-testid={`dealer-listings-price-${item.id}`}>{formatPrice(item.price)}</div>
                <div className="font-semibold text-slate-900" data-testid={`dealer-listings-views-${item.id}`}>0</div>
                <div className="font-semibold text-slate-900" data-testid={`dealer-listings-favorites-${item.id}`}>0</div>
                <div className="font-semibold text-slate-900" data-testid={`dealer-listings-messages-${item.id}`}>0</div>
                <div className="font-medium text-slate-700" data-testid={`dealer-listings-expiry-${item.id}`}>{computeExpiry(item.created_at)}</div>
                <div data-testid={`dealer-listings-status-${item.id}`}>
                  <div className="flex flex-wrap items-center gap-1" data-testid={`dealer-listings-actions-${item.id}`}>
                    {item.status !== 'active' ? (
                      <button
                        type="button"
                        onClick={() => handleStatusUpdate(item.id, 'active')}
                        className="rounded border border-emerald-200 px-2 py-1 text-[11px] font-semibold text-emerald-700"
                        data-testid={`dealer-listings-action-publish-${item.id}`}
                      >
                        Yayına Al
                      </button>
                    ) : (
                      <button
                        type="button"
                        onClick={() => handleStatusUpdate(item.id, 'archived')}
                        className="rounded border border-slate-300 px-2 py-1 text-[11px] font-semibold text-slate-700"
                        data-testid={`dealer-listings-action-archive-${item.id}`}
                      >
                        Arşivle
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {createOpen && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" data-testid="dealer-listings-modal">
          <div className="bg-white w-full max-w-lg rounded-xl shadow-lg p-6" data-testid="dealer-listings-modal-card">
            <div className="flex items-center justify-between" data-testid="dealer-listings-modal-header">
              <h3 className="text-lg font-semibold" data-testid="dealer-listings-modal-title">Yeni İlan</h3>
              <button
                type="button"
                onClick={() => setCreateOpen(false)}
                className="text-sm text-muted-foreground"
                data-testid="dealer-listings-modal-close"
              >
                Kapat
              </button>
            </div>
            <form className="mt-4 space-y-4" onSubmit={handleCreate} data-testid="dealer-listings-form">
              <div className="space-y-2" data-testid="dealer-listings-form-title">
                <label className="text-sm font-medium" htmlFor="dealer-title">İlan Başlığı</label>
                <input
                  id="dealer-title"
                  value={form.title}
                  onChange={(event) => setForm((prev) => ({ ...prev, title: event.target.value }))}
                  className="w-full border rounded-md px-3 py-2 text-sm"
                  placeholder="Örn: 2020 BMW 320i"
                  data-testid="dealer-listings-input-title"
                />
              </div>
              <div className="space-y-2" data-testid="dealer-listings-form-price">
                <label className="text-sm font-medium" htmlFor="dealer-price">Fiyat</label>
                <input
                  id="dealer-price"
                  type="number"
                  value={form.price}
                  onChange={(event) => setForm((prev) => ({ ...prev, price: event.target.value }))}
                  className="w-full border rounded-md px-3 py-2 text-sm"
                  placeholder="Örn: 950000"
                  data-testid="dealer-listings-input-price"
                />
              </div>

              {formError && (
                <div className="text-sm text-rose-600" data-testid="dealer-listings-form-error">
                  {formError}
                </div>
              )}

              <div className="flex items-center justify-end gap-2" data-testid="dealer-listings-form-actions">
                <button
                  type="button"
                  onClick={() => setCreateOpen(false)}
                  className="h-9 px-3 rounded-md border text-sm"
                  data-testid="dealer-listings-form-cancel"
                >
                  Vazgeç
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="h-9 px-4 rounded-md bg-slate-900 text-white text-sm disabled:opacity-60"
                  data-testid="dealer-listings-form-submit"
                >
                  {saving ? 'Kaydediliyor...' : 'Kaydet'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
