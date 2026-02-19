import { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import isoCountries from '../../data/isoCountries';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const formatName = (name) => {
  if (!name) return '';
  if (typeof name === 'string') return name;
  if (typeof name === 'object') {
    return name.tr || name.en || name.de || name.fr || Object.values(name)[0] || '';
  }
  return String(name);
};

export default function AdminCountriesPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({
    country_code: '',
    name: '',
    default_currency: 'EUR',
    default_language: '',
    active_flag: true,
  });
  const [isoSearch, setIsoSearch] = useState('');
  const [error, setError] = useState(null);

  const authHeader = useMemo(() => ({
    Authorization: `Bearer ${localStorage.getItem('access_token')}`,
  }), []);

  const filteredIsoCountries = useMemo(() => {
    const term = isoSearch.trim().toLowerCase();
    if (!term) return isoCountries.slice(0, 50);
    return isoCountries
      .filter((country) =>
        country.code.toLowerCase().includes(term) || (country.name || '').toLowerCase().includes(term)
      )
      .slice(0, 50);
  }, [isoSearch]);

  const handleIsoSelect = (code) => {
    const selected = isoCountries.find((country) => country.code === code);
    if (!selected) return;
    setForm((prev) => ({
      ...prev,
      country_code: selected.code,
      name: selected.name,
      default_currency: selected.currency || prev.default_currency || 'EUR',
      default_language: selected.locale || prev.default_language || '',
    }));
  };

  const fetchCountries = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/admin/countries`, { headers: authHeader });
      setItems(res.data.items || []);
    } catch (e) {
      console.error('Failed to fetch countries', e);
    } finally {
      setLoading(false);
    }
  };

  const openCreate = () => {
    setEditing(null);
    setForm({
      country_code: '',
      name: '',
      default_currency: 'EUR',
      default_language: '',
      active_flag: true,
    });
    setIsoSearch('');
    setError(null);
    setModalOpen(true);
  };

  const openEdit = (item) => {
    setEditing(item);
    setForm({
      country_code: item.country_code,
      name: formatName(item.name),
      default_currency: item.default_currency,
      default_language: item.default_language || '',
      active_flag: item.active_flag,
    });
    setIsoSearch('');
    setError(null);
    setModalOpen(true);
  };

  const submitForm = async () => {
    if (!form.country_code || !form.name) {
      setError('Country code ve name zorunlu');
      return;
    }
    try {
      if (editing) {
        await axios.patch(
          `${API}/admin/countries/${editing.country_code}`,
          {
            name: form.name,
            default_currency: form.default_currency,
            default_language: form.default_language || null,
            active_flag: form.active_flag,
          },
          { headers: authHeader }
        );
      } else {
        await axios.post(
          `${API}/admin/countries`,
          {
            country_code: form.country_code,
            name: form.name,
            default_currency: form.default_currency,
            default_language: form.default_language || null,
            active_flag: form.active_flag,
          },
          { headers: authHeader }
        );
      }
      setModalOpen(false);
      fetchCountries();
    } catch (e) {
      setError(e.response?.data?.detail || 'Kaydedilemedi');
    }
  };

  const deactivateCountry = async (item) => {
    if (!window.confirm('Ülke pasif edilsin mi?')) return;
    try {
      await axios.delete(`${API}/admin/countries/${item.country_code}`, { headers: authHeader });
      fetchCountries();
    } catch (e) {
      console.error('Delete failed', e);
    }
  };

  useEffect(() => {
    fetchCountries();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="space-y-6" data-testid="admin-countries-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold" data-testid="admin-countries-title">Countries</h1>
        </div>
        <button
          onClick={openCreate}
          className="h-9 px-3 rounded-md bg-primary text-primary-foreground text-sm"
          data-testid="countries-create-open"
        >
          Yeni Ülke
        </button>
      </div>

      <div className="rounded-md border bg-card overflow-hidden" data-testid="countries-table">
        <div className="hidden lg:grid grid-cols-[0.8fr_1.4fr_0.8fr_0.8fr_0.6fr_0.8fr] gap-4 bg-muted px-4 py-3 text-sm font-medium">
          <div>Code</div>
          <div>Name</div>
          <div>Currency</div>
          <div>Language</div>
          <div>Active</div>
          <div className="text-right">Aksiyon</div>
        </div>
        <div className="divide-y">
          {loading ? (
            <div className="p-6 text-center" data-testid="countries-loading">Yükleniyor…</div>
          ) : items.length === 0 ? (
            <div className="p-6 text-center text-muted-foreground" data-testid="countries-empty">Kayıt yok</div>
          ) : (
            items.map((item) => (
              <div
                key={item.country_code}
                className="grid grid-cols-1 gap-4 px-4 py-4 lg:grid-cols-[0.8fr_1.4fr_0.8fr_0.8fr_0.6fr_0.8fr]"
                data-testid={`country-row-${item.country_code}`}
              >
                <div>{item.country_code}</div>
                <div>{formatName(item.name)}</div>
                <div>{item.default_currency}</div>
                <div>{item.default_language || '—'}</div>
                <div>{item.active_flag ? 'yes' : 'no'}</div>
                <div className="flex gap-2 justify-end">
                  <button
                    onClick={() => openEdit(item)}
                    className="h-8 px-2.5 rounded-md border text-xs"
                    data-testid={`country-edit-${item.country_code}`}
                  >
                    Düzenle
                  </button>
                  <button
                    onClick={() => deactivateCountry(item)}
                    className="h-8 px-2.5 rounded-md border text-xs text-rose-600"
                    data-testid={`country-deactivate-${item.country_code}`}
                  >
                    Pasif Et
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {modalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" data-testid="countries-modal">
          <div className="bg-card rounded-lg border shadow-xl w-full max-w-lg">
            <div className="p-4 border-b flex items-center justify-between">
              <h3 className="text-lg font-semibold" data-testid="countries-modal-title">{editing ? 'Country Güncelle' : 'Country Oluştur'}</h3>
              <button
                onClick={() => setModalOpen(false)}
                className="h-8 px-2.5 rounded-md border text-xs"
                data-testid="countries-modal-close"
              >
                Kapat
              </button>
            </div>
            <div className="p-4 space-y-3">
              {!editing && (
                <div className="space-y-2" data-testid="countries-iso-picker">
                  <div className="text-xs text-muted-foreground">ISO 3166 ülke seç</div>
                  <input
                    value={isoSearch}
                    onChange={(e) => setIsoSearch(e.target.value)}
                    placeholder="Ülke ara (örn: Germany, DE)"
                    className="h-9 px-3 rounded-md border bg-background text-sm w-full"
                    data-testid="countries-iso-search"
                  />
                  <select
                    className="h-9 rounded-md border bg-background px-3 text-sm w-full"
                    onChange={(e) => handleIsoSelect(e.target.value)}
                    data-testid="countries-iso-select"
                  >
                    <option value="">Ülke seç</option>
                    {filteredIsoCountries.map((country) => (
                      <option key={country.code} value={country.code}>
                        {country.code} · {country.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}
              <input
                value={form.country_code}
                onChange={(e) => setForm({ ...form, country_code: e.target.value.toUpperCase() })}
                placeholder="Country Code"
                className="h-9 px-3 rounded-md border bg-background text-sm w-full"
                disabled={!!editing}
                readOnly={!editing}
                data-testid="countries-form-code"
              />
              <input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="Name"
                className="h-9 px-3 rounded-md border bg-background text-sm w-full"
                data-testid="countries-form-name"
              />
              <input
                value={form.default_currency}
                onChange={(e) => setForm({ ...form, default_currency: e.target.value.toUpperCase() })}
                placeholder="Default Currency"
                className="h-9 px-3 rounded-md border bg-background text-sm w-full"
                data-testid="countries-form-currency"
              />
              <input
                value={form.default_language}
                onChange={(e) => setForm({ ...form, default_language: e.target.value })}
                placeholder="Locale (örn: de-DE)"
                className="h-9 px-3 rounded-md border bg-background text-sm w-full"
                data-testid="countries-form-language"
              />
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={form.active_flag}
                  onChange={(e) => setForm({ ...form, active_flag: e.target.checked })}
                  data-testid="countries-form-active"
                />
                Active
              </label>
              {error && (
                <div className="text-xs text-destructive" data-testid="countries-form-error">{error}</div>
              )}
              <button
                onClick={submitForm}
                className="h-9 px-3 rounded-md bg-primary text-primary-foreground text-sm"
                data-testid="countries-form-submit"
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
