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

export default function DealerListings() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [items, setItems] = useState([]);
  const [quota, setQuota] = useState({ limit: 0, used: 0, remaining: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [createOpen, setCreateOpen] = useState(false);
  const [form, setForm] = useState({ title: '', price: '' });
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState('');
  const [statusFilter, setStatusFilter] = useState('active');
  const [selectedIds, setSelectedIds] = useState([]);
  const [bulkLoading, setBulkLoading] = useState(false);
  const [lastBulkAction, setLastBulkAction] = useState(null);

  const authHeader = useMemo(
    () => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` }),
    []
  );

  const fetchListings = async (statusValue = statusFilter) => {
    setLoading(true);
    setError('');
    try {
      const query = statusValue && statusValue !== 'all' ? `?status=${statusValue}` : '';
      const res = await fetch(`${API}/dealer/listings${query}`, { headers: authHeader });
      if (!res.ok) {
        throw new Error('İlanlar yüklenemedi');
      }
      const data = await res.json();
      setItems(data.items || []);
      setQuota(data.quota || { limit: 0, used: 0, remaining: 0 });
    } catch (err) {
      setError('İlanlar yüklenemedi.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchListings(statusFilter);
  }, [statusFilter]);

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
    setSelectedIds((prev) => prev.filter((id) => items.some((item) => item.id === id)));
  }, [items]);

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
      fetchListings(statusFilter);
    } catch (err) {
      setFormError(err?.message || 'İlan oluşturulamadı');
    } finally {
      setSaving(false);
    }
  };

  const allSelected = items.length > 0 && selectedIds.length === items.length;
  const bulkDisabled = selectedIds.length === 0 || bulkLoading;

  const handleSelectAll = () => {
    if (allSelected) {
      setSelectedIds([]);
    } else {
      setSelectedIds(items.map((item) => item.id));
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

      await fetchListings(statusFilter);
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
          onClick={() => fetchListings(statusFilter)}
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
          <h2 className="text-2xl font-bold" data-testid="dealer-listings-title">İlanlarım</h2>
          <p className="text-sm text-muted-foreground" data-testid="dealer-listings-subtitle">
            Kurumsal ilanlarınızı yönetin.
          </p>
        </div>
        <div className="flex items-center gap-3" data-testid="dealer-listings-actions">
          <div className="rounded-md border bg-white px-3 py-2 text-xs" data-testid="dealer-listings-quota">
            Kota: <span data-testid="dealer-listings-quota-used">{quota.used}</span> /{' '}
            <span data-testid="dealer-listings-quota-limit">{quota.limit}</span>
            {quota.remaining !== undefined && (
              <span className="ml-2 text-muted-foreground" data-testid="dealer-listings-quota-remaining">
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

      <div className="rounded-lg border bg-white p-4" data-testid="dealer-listings-toolbar">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-4" data-testid="dealer-listings-filters">
            <div className="flex items-center gap-2" data-testid="dealer-listings-filter-status">
              <label className="text-xs font-medium text-muted-foreground" htmlFor="dealer-status-filter">
                Durum
              </label>
              <select
                id="dealer-status-filter"
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value)}
                className="h-9 rounded-md border px-3 text-sm"
                data-testid="dealer-listings-status-select"
              >
                <option value="active">Aktif</option>
                <option value="draft">Taslak</option>
                <option value="archived">Arşiv</option>
                <option value="all">Tümü</option>
              </select>
            </div>
            <span className="text-xs text-muted-foreground" data-testid="dealer-listings-sort-info">
              Sıralama: Yeni → Eski
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-2" data-testid="dealer-listings-bulk-actions">
            <span className="text-xs text-muted-foreground" data-testid="dealer-listings-selected-count">
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
      </div>

      {items.length === 0 ? (
        <div className="rounded-lg border bg-white p-6 text-sm text-muted-foreground" data-testid="dealer-listings-empty">
          Bu filtrede ilan bulunamadı. Farklı bir durum seçin veya yeni ilan oluşturun.
        </div>
      ) : (
        <div className="rounded-lg border bg-white overflow-hidden" data-testid="dealer-listings-table">
          <div className="grid grid-cols-5 gap-4 bg-muted text-sm font-medium px-3 py-2" data-testid="dealer-listings-table-header">
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
            <div data-testid="dealer-listings-header-status">Durum</div>
            <div data-testid="dealer-listings-header-created">Oluşturma</div>
          </div>
          <div className="divide-y" data-testid="dealer-listings-table-body">
            {items.map((item) => (
              <div
                key={item.id}
                className="grid grid-cols-5 gap-4 px-3 py-3 text-sm"
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
                <div data-testid={`dealer-listings-title-${item.id}`}>{item.title}</div>
                <div data-testid={`dealer-listings-price-${item.id}`}>{formatPrice(item.price)}</div>
                <div data-testid={`dealer-listings-status-${item.id}`}>
                  {statusLabels[item.status] || item.status}
                </div>
                <div data-testid={`dealer-listings-created-${item.id}`}>
                  {item.created_at ? new Date(item.created_at).toLocaleDateString('tr-TR') : '-'}
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
