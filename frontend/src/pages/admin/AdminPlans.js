import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AdminPlansPage() {
  const [searchParams] = useSearchParams();
  const urlCountry = (searchParams.get('country') || '').toUpperCase();

  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({
    name: '',
    country_code: urlCountry,
    price: '',
    currency: 'EUR',
    listing_quota: '',
    showcase_quota: '',
    active_flag: true,
  });
  const [error, setError] = useState(null);

  const authHeader = useMemo(() => ({
    Authorization: `Bearer ${localStorage.getItem('access_token')}`,
  }), []);

  const fetchPlans = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (urlCountry) params.set('country', urlCountry);
      const res = await axios.get(`${API}/admin/plans?${params.toString()}`, {
        headers: authHeader,
      });
      setItems(res.data.items || []);
    } catch (e) {
      console.error('Failed to fetch plans', e);
    } finally {
      setLoading(false);
    }
  };

  const openCreate = () => {
    setEditing(null);
    setForm({
      name: '',
      country_code: urlCountry,
      price: '',
      currency: 'EUR',
      listing_quota: '',
      showcase_quota: '',
      active_flag: true,
    });
    setError(null);
    setModalOpen(true);
  };

  const openEdit = (item) => {
    setEditing(item);
    setForm({
      name: item.name,
      country_code: item.country_code,
      price: item.price,
      currency: item.currency,
      listing_quota: item.listing_quota,
      showcase_quota: item.showcase_quota,
      active_flag: item.active_flag,
    });
    setError(null);
    setModalOpen(true);
  };

  const submitForm = async () => {
    if (!form.name || !form.country_code) {
      setError('Name ve country zorunlu');
      return;
    }
    try {
      if (editing) {
        await axios.patch(
          `${API}/admin/plans/${editing.id}`,
          {
            name: form.name,
            country_code: form.country_code,
            price: Number(form.price),
            currency: form.currency,
            listing_quota: Number(form.listing_quota),
            showcase_quota: Number(form.showcase_quota),
            active_flag: form.active_flag,
          },
          { headers: authHeader }
        );
      } else {
        await axios.post(
          `${API}/admin/plans`,
          {
            name: form.name,
            country_code: form.country_code,
            price: Number(form.price),
            currency: form.currency,
            listing_quota: Number(form.listing_quota),
            showcase_quota: Number(form.showcase_quota),
            active_flag: form.active_flag,
          },
          { headers: authHeader }
        );
      }
      setModalOpen(false);
      fetchPlans();
    } catch (e) {
      setError(e.response?.data?.detail || 'Kaydedilemedi');
    }
  };

  const deletePlan = async (item) => {
    if (!window.confirm('Plan silinsin mi?')) return;
    try {
      await axios.delete(`${API}/admin/plans/${item.id}`, { headers: authHeader });
      fetchPlans();
    } catch (e) {
      console.error('Delete failed', e);
    }
  };

  useEffect(() => {
    fetchPlans();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [urlCountry]);

  return (
    <div className="space-y-6" data-testid="admin-plans-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold" data-testid="admin-plans-title">Plans</h1>
          <div className="text-xs text-muted-foreground" data-testid="admin-plans-context">
            Country: <span className="font-semibold">{urlCountry || 'Global'}</span>
          </div>
        </div>
        <button
          onClick={openCreate}
          className="h-9 px-3 rounded-md bg-primary text-primary-foreground text-sm"
          data-testid="plan-create-open"
        >
          Yeni Plan
        </button>
      </div>

      <div className="rounded-md border bg-card overflow-hidden" data-testid="plan-table">
        <div className="hidden lg:grid grid-cols-[1.2fr_0.6fr_0.6fr_0.6fr_0.6fr_0.5fr_0.7fr] gap-4 bg-muted px-4 py-3 text-sm font-medium">
          <div>Name</div>
          <div>Country</div>
          <div>Price</div>
          <div>Listing</div>
          <div>Showcase</div>
          <div>Active</div>
          <div className="text-right">Aksiyon</div>
        </div>
        <div className="divide-y">
          {loading ? (
            <div className="p-6 text-center" data-testid="plan-loading">Yükleniyor…</div>
          ) : items.length === 0 ? (
            <div className="p-6 text-center text-muted-foreground" data-testid="plan-empty">Kayıt yok</div>
          ) : (
            items.map((item) => (
              <div
                key={item.id}
                className="grid grid-cols-1 gap-4 px-4 py-4 lg:grid-cols-[1.2fr_0.6fr_0.6fr_0.6fr_0.6fr_0.5fr_0.7fr]"
                data-testid={`plan-row-${item.id}`}
              >
                <div>{item.name}</div>
                <div>{item.country_code}</div>
                <div>{item.price} {item.currency}</div>
                <div>{item.listing_quota}</div>
                <div>{item.showcase_quota}</div>
                <div>{item.active_flag ? 'yes' : 'no'}</div>
                <div className="flex gap-2 justify-end">
                  <button
                    onClick={() => openEdit(item)}
                    className="h-8 px-2.5 rounded-md border text-xs"
                    data-testid={`plan-edit-${item.id}`}
                  >
                    Düzenle
                  </button>
                  <button
                    onClick={() => deletePlan(item)}
                    className="h-8 px-2.5 rounded-md border text-xs text-rose-600"
                    data-testid={`plan-delete-${item.id}`}
                  >
                    Sil
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {modalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" data-testid="plan-modal">
          <div className="bg-card rounded-lg border shadow-xl w-full max-w-lg">
            <div className="p-4 border-b flex items-center justify-between">
              <h3 className="text-lg font-semibold" data-testid="plan-modal-title">{editing ? 'Plan Güncelle' : 'Plan Oluştur'}</h3>
              <button
                onClick={() => setModalOpen(false)}
                className="h-8 px-2.5 rounded-md border text-xs"
                data-testid="plan-modal-close"
              >
                Kapat
              </button>
            </div>
            <div className="p-4 space-y-3">
              <input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="Plan Name"
                className="h-9 px-3 rounded-md border bg-background text-sm w-full"
                data-testid="plan-form-name"
              />
              <input
                value={form.country_code}
                onChange={(e) => setForm({ ...form, country_code: e.target.value.toUpperCase() })}
                placeholder="Country Code"
                className="h-9 px-3 rounded-md border bg-background text-sm w-full"
                data-testid="plan-form-country"
              />
              <input
                value={form.price}
                onChange={(e) => setForm({ ...form, price: e.target.value })}
                placeholder="Price"
                className="h-9 px-3 rounded-md border bg-background text-sm w-full"
                data-testid="plan-form-price"
              />
              <input
                value={form.currency}
                onChange={(e) => setForm({ ...form, currency: e.target.value })}
                placeholder="Currency"
                className="h-9 px-3 rounded-md border bg-background text-sm w-full"
                data-testid="plan-form-currency"
              />
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <input
                  value={form.listing_quota}
                  onChange={(e) => setForm({ ...form, listing_quota: e.target.value })}
                  placeholder="Listing Quota"
                  className="h-9 px-3 rounded-md border bg-background text-sm"
                  data-testid="plan-form-listing"
                />
                <input
                  value={form.showcase_quota}
                  onChange={(e) => setForm({ ...form, showcase_quota: e.target.value })}
                  placeholder="Showcase Quota"
                  className="h-9 px-3 rounded-md border bg-background text-sm"
                  data-testid="plan-form-showcase"
                />
              </div>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={form.active_flag}
                  onChange={(e) => setForm({ ...form, active_flag: e.target.checked })}
                  data-testid="plan-form-active"
                />
                Active
              </label>
              {error && (
                <div className="text-xs text-destructive" data-testid="plan-form-error">{error}</div>
              )}
              <button
                onClick={submitForm}
                className="h-9 px-3 rounded-md bg-primary text-primary-foreground text-sm"
                data-testid="plan-form-submit"
              >
                {editing ? 'Güncelle' : 'Oluştur'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
