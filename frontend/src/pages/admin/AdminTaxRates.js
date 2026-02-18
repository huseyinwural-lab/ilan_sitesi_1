import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AdminTaxRatesPage() {
  const [searchParams] = useSearchParams();
  const urlCountry = (searchParams.get('country') || '').toUpperCase();

  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({
    country_code: urlCountry,
    rate: '',
    effective_date: '',
    active_flag: true,
  });
  const [error, setError] = useState(null);

  const authHeader = useMemo(() => ({
    Authorization: `Bearer ${localStorage.getItem('access_token')}`,
  }), []);

  const fetchTaxRates = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (urlCountry) params.set('country', urlCountry);
      const res = await axios.get(`${API}/admin/tax-rates?${params.toString()}`, {
        headers: authHeader,
      });
      setItems(res.data.items || []);
    } catch (e) {
      console.error('Failed to fetch tax rates', e);
    } finally {
      setLoading(false);
    }
  };

  const openCreate = () => {
    setEditing(null);
    setForm({ country_code: urlCountry, rate: '', effective_date: '', active_flag: true });
    setError(null);
    setModalOpen(true);
  };

  const openEdit = (item) => {
    setEditing(item);
    setForm({
      country_code: item.country_code,
      rate: item.rate,
      effective_date: item.effective_date,
      active_flag: item.active_flag,
    });
    setError(null);
    setModalOpen(true);
  };

  const submitForm = async () => {
    if (!form.country_code) {
      setError('Country zorunlu');
      return;
    }
    if (form.rate === '') {
      setError('Rate zorunlu');
      return;
    }
    try {
      if (editing) {
        await axios.patch(
          `${API}/admin/tax-rates/${editing.id}`,
          {
            rate: Number(form.rate),
            effective_date: form.effective_date,
            active_flag: form.active_flag,
          },
          { headers: authHeader }
        );
      } else {
        await axios.post(
          `${API}/admin/tax-rates`,
          {
            country_code: form.country_code,
            rate: Number(form.rate),
            effective_date: form.effective_date,
            active_flag: form.active_flag,
          },
          { headers: authHeader }
        );
      }
      setModalOpen(false);
      fetchTaxRates();
    } catch (e) {
      setError(e.response?.data?.detail || 'Kaydedilemedi');
    }
  };

  const deleteTaxRate = async (item) => {
    if (!window.confirm('Tax rate silinsin mi?')) return;
    try {
      await axios.delete(`${API}/admin/tax-rates/${item.id}`, { headers: authHeader });
      fetchTaxRates();
    } catch (e) {
      console.error('Delete failed', e);
    }
  };

  useEffect(() => {
    fetchTaxRates();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [urlCountry]);

  return (
    <div className="space-y-6" data-testid="admin-tax-rates-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold" data-testid="admin-tax-title">Tax Rates</h1>
          <div className="text-xs text-muted-foreground" data-testid="admin-tax-context">
            Country: <span className="font-semibold">{urlCountry || 'Global'}</span>
          </div>
        </div>
        <button
          onClick={openCreate}
          className="h-9 px-3 rounded-md bg-primary text-primary-foreground text-sm"
          data-testid="tax-create-open"
        >
          Yeni Tax Rate
        </button>
      </div>

      <div className="rounded-md border bg-card overflow-hidden" data-testid="tax-table">
        <div className="hidden lg:grid grid-cols-[1fr_1fr_1fr_0.5fr_0.7fr] gap-4 bg-muted px-4 py-3 text-sm font-medium">
          <div>Country</div>
          <div>Rate</div>
          <div>Effective Date</div>
          <div>Active</div>
          <div className="text-right">Aksiyon</div>
        </div>
        <div className="divide-y">
          {loading ? (
            <div className="p-6 text-center" data-testid="tax-loading">Yükleniyor…</div>
          ) : items.length === 0 ? (
            <div className="p-6 text-center text-muted-foreground" data-testid="tax-empty">Kayıt yok</div>
          ) : (
            items.map((item) => (
              <div
                key={item.id}
                className="grid grid-cols-1 gap-4 px-4 py-4 lg:grid-cols-[1fr_1fr_1fr_0.5fr_0.7fr]"
                data-testid={`tax-row-${item.id}`}
              >
                <div>{item.country_code}</div>
                <div>{item.rate}%</div>
                <div>{item.effective_date}</div>
                <div>{item.active_flag ? 'yes' : 'no'}</div>
                <div className="flex gap-2 justify-end">
                  <button
                    onClick={() => openEdit(item)}
                    className="h-8 px-2.5 rounded-md border text-xs"
                    data-testid={`tax-edit-${item.id}`}
                  >
                    Düzenle
                  </button>
                  <button
                    onClick={() => deleteTaxRate(item)}
                    className="h-8 px-2.5 rounded-md border text-xs text-rose-600"
                    data-testid={`tax-delete-${item.id}`}
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
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" data-testid="tax-modal">
          <div className="bg-card rounded-lg border shadow-xl w-full max-w-lg">
            <div className="p-4 border-b flex items-center justify-between">
              <h3 className="text-lg font-semibold" data-testid="tax-modal-title">{editing ? 'Tax Rate Güncelle' : 'Tax Rate Oluştur'}</h3>
              <button
                onClick={() => setModalOpen(false)}
                className="h-8 px-2.5 rounded-md border text-xs"
                data-testid="tax-modal-close"
              >
                Kapat
              </button>
            </div>
            <div className="p-4 space-y-3">
              <input
                value={form.country_code}
                onChange={(e) => setForm({ ...form, country_code: e.target.value.toUpperCase() })}
                placeholder="Country Code"
                className="h-9 px-3 rounded-md border bg-background text-sm w-full"
                data-testid="tax-form-country"
              />
              <input
                value={form.rate}
                onChange={(e) => setForm({ ...form, rate: e.target.value })}
                placeholder="Rate (0-100)"
                className="h-9 px-3 rounded-md border bg-background text-sm w-full"
                data-testid="tax-form-rate"
              />
              <input
                value={form.effective_date}
                onChange={(e) => setForm({ ...form, effective_date: e.target.value })}
                placeholder="Effective Date (ISO)"
                className="h-9 px-3 rounded-md border bg-background text-sm w-full"
                data-testid="tax-form-effective"
              />
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={form.active_flag}
                  onChange={(e) => setForm({ ...form, active_flag: e.target.checked })}
                  data-testid="tax-form-active"
                />
                Active
              </label>
              {error && (
                <div className="text-xs text-destructive" data-testid="tax-form-error">{error}</div>
              )}
              <button
                onClick={submitForm}
                className="h-9 px-3 rounded-md bg-primary text-primary-foreground text-sm"
                data-testid="tax-form-submit"
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
