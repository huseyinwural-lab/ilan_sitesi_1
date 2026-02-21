import React, { useEffect, useMemo, useState } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const formatPrice = (value) => {
  if (value === null || value === undefined || value === '') return '-';
  const number = Number(value);
  if (Number.isNaN(number)) return '-';
  return new Intl.NumberFormat('tr-TR').format(number);
};

export default function DealerListings() {
  const [items, setItems] = useState([]);
  const [quota, setQuota] = useState({ limit: 0, used: 0, remaining: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [createOpen, setCreateOpen] = useState(false);
  const [form, setForm] = useState({ title: '', price: '' });
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState('');

  const authHeader = useMemo(
    () => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` }),
    []
  );

  const fetchListings = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API}/dealer/listings`, { headers: authHeader });
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
    fetchListings();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleOpenCreate = () => {
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
          onClick={fetchListings}
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

      {items.length === 0 ? (
        <div className="rounded-lg border bg-white p-6 text-sm text-muted-foreground" data-testid="dealer-listings-empty">
          Henüz ilanınız yok. "Yeni İlan Oluştur" ile başlayın.
        </div>
      ) : (
        <div className="rounded-lg border bg-white overflow-hidden" data-testid="dealer-listings-table">
          <div className="grid grid-cols-4 gap-4 bg-muted text-sm font-medium px-3 py-2" data-testid="dealer-listings-table-header">
            <div data-testid="dealer-listings-header-title">İlan</div>
            <div data-testid="dealer-listings-header-price">Fiyat</div>
            <div data-testid="dealer-listings-header-status">Durum</div>
            <div data-testid="dealer-listings-header-created">Oluşturma</div>
          </div>
          <div className="divide-y" data-testid="dealer-listings-table-body">
            {items.map((item) => (
              <div
                key={item.id}
                className="grid grid-cols-4 gap-4 px-3 py-3 text-sm"
                data-testid={`dealer-listings-row-${item.id}`}
              >
                <div data-testid={`dealer-listings-title-${item.id}`}>{item.title}</div>
                <div data-testid={`dealer-listings-price-${item.id}`}>{formatPrice(item.price)}</div>
                <div data-testid={`dealer-listings-status-${item.id}`}>{item.status}</div>
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
