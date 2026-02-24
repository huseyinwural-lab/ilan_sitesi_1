import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { useSearchParams } from 'react-router-dom';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

const COUNTRY_OPTIONS = [
  { code: 'DE', label: 'DE', currency: 'EUR' },
  { code: 'AT', label: 'AT', currency: 'EUR' },
  { code: 'FR', label: 'FR', currency: 'EUR' },
  { code: 'CH', label: 'CH', currency: 'CHF' },
];

const PLAN_QUOTA_MIN = 0;
const PLAN_QUOTA_MAX = 10000;

const resolveCurrency = (scope, countryCode) => {
  if (scope === 'global') return 'EUR';
  const match = COUNTRY_OPTIONS.find((item) => item.code === countryCode);
  return match?.currency || 'EUR';
};

const slugify = (value) => {
  return String(value || '')
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
};

const formatDate = (value) => {
  if (!value) return '-';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return '-';
  return parsed.toLocaleString('tr-TR', { year: 'numeric', month: '2-digit', day: '2-digit' });
};

const emptyForm = {
  name: '',
  scope: 'global',
  country_code: '',
  period: 'monthly',
  price_amount: '',
  currency_code: 'EUR',
  listing_quota: '',
  showcase_quota: '',
  active_flag: true,
};

export default function AdminPlans() {
  const [searchParams] = useSearchParams();
  const urlCountry = searchParams.get('country') || '';
  const defaultCountry = urlCountry ? urlCountry.toUpperCase() : 'DE';

  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [dbReady, setDbReady] = useState(false);

  const [filterScope, setFilterScope] = useState('all');
  const [filterCountry, setFilterCountry] = useState('');
  const [filterStatus, setFilterStatus] = useState('active');
  const [searchInput, setSearchInput] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortOrder, setSortOrder] = useState('desc');

  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [editing, setEditing] = useState(null);
  const [saving, setSaving] = useState(false);

  const authHeader = useMemo(() => {
    const token = localStorage.getItem('access_token');
    return { Authorization: `Bearer ${token}` };
  }, []);

  const sortedItems = useMemo(() => {
    const list = [...items];
    list.sort((a, b) => {
      const dateA = new Date(a.updated_at || a.created_at || 0).getTime();
      const dateB = new Date(b.updated_at || b.created_at || 0).getTime();
      if (sortOrder === 'asc') return dateA - dateB;
      return dateB - dateA;
    });
    return list;
  }, [items, sortOrder]);

  const disabled = !dbReady;

  const checkDb = async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/api/health/db`);
      const isReady = res.data?.db_status === 'ok' || res.data?.status === 'healthy';
      setDbReady(isReady);
      if (isReady) {
        setError('');
      }
    } catch (err) {
      setDbReady(false);
      setError('');
    }
  };

  const fetchItems = async () => {
    if (!dbReady) {
      setItems([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filterScope !== 'all') params.set('scope', filterScope);
      if (filterScope === 'country' && filterCountry) params.set('country_code', filterCountry);
      if (filterStatus !== 'all') params.set('status', filterStatus);
      if (searchQuery) params.set('q', searchQuery);
      const query = params.toString();
      const res = await axios.get(`${API_BASE_URL}/api/admin/plans${query ? `?${query}` : ''}`, {
        headers: authHeader,
      });
      setItems(res.data.items || []);
      setError('');
    } catch (err) {
      setError('Planlar yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkDb();
  }, []);

  useEffect(() => {
    if (urlCountry) {
      setFilterScope('country');
      setFilterCountry(urlCountry.toUpperCase());
    }
  }, [urlCountry]);

  useEffect(() => {
    fetchItems();
  }, [dbReady, filterScope, filterCountry, filterStatus, searchQuery]);

  const openCreate = () => {
    setEditing(null);
    const scope = filterScope === 'country' ? 'country' : 'global';
    const country = scope === 'country' ? filterCountry : '';
    const currency = resolveCurrency(scope, country || 'DE');
    setForm({
      ...emptyForm,
      scope,
      country_code: country,
      period: 'monthly',
      currency_code: currency,
    });
    setShowForm(true);
  };

  const openEdit = (item) => {
    setEditing(item);
    const scope = item.country_scope || 'global';
    const country = scope === 'country' ? item.country_code || '' : '';
    setForm({
      name: item.name || '',
      scope,
      country_code: country,
      period: item.period || 'monthly',
      price_amount: item.price_amount ?? '',
      currency_code: item.currency_code || resolveCurrency(scope, country || 'DE'),
      listing_quota: item.listing_quota ?? '',
      showcase_quota: item.showcase_quota ?? '',
      active_flag: item.active_flag !== false,
    });
    setShowForm(true);
  };

  const closeForm = () => {
    setShowForm(false);
    setForm(emptyForm);
    setEditing(null);
  };

  const validateForm = () => {
    if (!form.name.trim()) return 'Name zorunlu';
    if (!form.period) return 'Period zorunlu';
    if (form.scope === 'country' && !form.country_code) return 'Country zorunlu';
    if (Number(form.price_amount) < 0) return 'Price 0 veya daha büyük olmalı';
    if (Number(form.listing_quota) < 0) return 'Listing quota 0 veya daha büyük olmalı';
    if (Number(form.showcase_quota) < 0) return 'Showcase quota 0 veya daha büyük olmalı';
    return '';
  };

  const submitForm = async ({ forceActive = false } = {}) => {
    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setSaving(true);
    try {
      const payload = {
        name: form.name.trim(),
        slug: editing ? editing.slug : slugify(form.name),
        country_scope: form.scope,
        country_code: form.scope === 'country' ? form.country_code : undefined,
        period: form.period,
        price_amount: Number(form.price_amount),
        currency_code: resolveCurrency(form.scope, form.country_code || 'DE'),
        listing_quota: Number(form.listing_quota),
        showcase_quota: Number(form.showcase_quota),
        active_flag: forceActive ? true : form.active_flag,
      };

      if (editing) {
        await axios.put(`${API_BASE_URL}/api/admin/plans/${editing.id}`, payload, { headers: authHeader });
      } else {
        await axios.post(`${API_BASE_URL}/api/admin/plans`, payload, { headers: authHeader });
      }
      closeForm();
      fetchItems();
    } catch (err) {
      setError('Plan kaydedilemedi');
    } finally {
      setSaving(false);
    }
  };

  const toggleActive = async (item) => {
    if (disabled) return;
    try {
      await axios.post(`${API_BASE_URL}/api/admin/plans/${item.id}/toggle-active`, {}, { headers: authHeader });
      fetchItems();
    } catch (err) {
      setError('Aktif/Pasif güncellenemedi');
    }
  };

  const archivePlan = async (item) => {
    if (disabled) return;
    const confirmed = window.confirm('Bu planı arşivlemek mevcut abonelikleri etkilemez. Devam edilsin mi?');
    if (!confirmed) return;
    try {
      await axios.post(`${API_BASE_URL}/api/admin/plans/${item.id}/archive`, {}, { headers: authHeader });
      fetchItems();
    } catch (err) {
      setError('Plan arşivlenemedi');
    }
  };

  const handleScopeChange = (scope) => {
    const country = scope === 'country' ? (form.country_code || filterCountry || 'DE') : '';
    const currency = resolveCurrency(scope, country || 'DE');
    setForm((prev) => ({
      ...prev,
      scope,
      country_code: country,
      currency_code: currency,
    }));
  };

  const handleCountryChange = (code) => {
    const currency = resolveCurrency(form.scope, code || 'DE');
    setForm((prev) => ({
      ...prev,
      country_code: code,
      currency_code: currency,
    }));
  };

  return (
    <div className="p-6 space-y-6" data-testid="plans-page">
      <div className="flex items-start justify-between gap-4" data-testid="plans-header">
        <div>
          <h1 className="text-2xl font-semibold" data-testid="plans-title">Planlar</h1>
          <p className="text-sm text-muted-foreground" data-testid="plans-subtitle">Country: {urlCountry || 'Global'}</p>
        </div>
        <button
          className="px-4 py-2 rounded bg-primary text-white disabled:opacity-60"
          onClick={openCreate}
          disabled={disabled}
          title={disabled ? 'DB hazır değil' : 'Yeni Plan'}
          data-testid="plans-create-button"
        >
          Yeni Plan
        </button>
      </div>

      {!dbReady && (
        <div className="border border-amber-200 bg-amber-50 text-amber-900 rounded-md p-4" data-testid="plans-db-banner">
          DB hazır değil → işlemler devre dışı. Ops ekibine DATABASE_URL + migration kontrolü gerekiyor.
        </div>
      )}

      {error && (
        <div className="border border-red-200 bg-red-50 text-red-700 rounded-md p-3" data-testid="plans-error">
          {error}
        </div>
      )}

      <div className="flex flex-wrap items-end gap-3" data-testid="plans-filters">
        <div className="flex items-center gap-2" data-testid="plans-filter-chips">
          <button
            className={`px-3 py-1 rounded-full border text-sm ${filterScope === 'global' ? 'bg-primary text-white border-primary' : 'bg-white'}`}
            onClick={() => {
              setFilterScope('global');
              setFilterCountry('');
            }}
            data-testid="plans-filter-chip-global"
          >
            Global
          </button>
          <button
            className={`px-3 py-1 rounded-full border text-sm ${filterScope === 'country' ? 'bg-primary text-white border-primary' : 'bg-white'}`}
            onClick={() => {
              setFilterScope('country');
              if (!filterCountry) setFilterCountry(defaultCountry);
            }}
            data-testid="plans-filter-chip-country"
          >
            Country
          </button>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-muted-foreground" data-testid="plans-filter-scope-label">Scope</label>
          <select
            className="border rounded p-2"
            value={filterScope}
            onChange={(e) => {
              const value = e.target.value;
              setFilterScope(value);
              if (value !== 'country') setFilterCountry('');
            }}
            data-testid="plans-filter-scope"
          >
            <option value="all">Tümü</option>
            <option value="global">Global</option>
            <option value="country">Country</option>
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-muted-foreground" data-testid="plans-filter-country-label">Country</label>
          <select
            className="border rounded p-2"
            value={filterCountry}
            onChange={(e) => setFilterCountry(e.target.value)}
            disabled={filterScope !== 'country'}
            data-testid="plans-filter-country"
          >
            <option value="">Tümü</option>
            {COUNTRY_OPTIONS.map((item) => (
              <option key={item.code} value={item.code}>{item.label}</option>
            ))}
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-muted-foreground" data-testid="plans-filter-status-label">Active</label>
          <select
            className="border rounded p-2"
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            data-testid="plans-filter-status"
          >
            <option value="all">Tümü</option>
            <option value="active">Aktif</option>
            <option value="inactive">Pasif</option>
            <option value="archived">Arşiv</option>
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-muted-foreground" data-testid="plans-filter-search-label">Search</label>
          <input
            className="border rounded p-2"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Plan adı"
            data-testid="plans-filter-search-input"
          />
        </div>
        <button
          className="px-4 py-2 rounded border"
          onClick={() => setSearchQuery(searchInput.trim())}
          disabled={disabled}
          data-testid="plans-filter-search-button"
        >
          Ara
        </button>
        <button
          className="px-4 py-2 rounded border"
          onClick={() => setSortOrder('desc')}
          disabled={disabled}
          data-testid="plans-sort-newest"
        >
          Sırala: En yeni
        </button>
      </div>

      <div className="border rounded-lg overflow-hidden" data-testid="plans-table">
        <table className="w-full text-sm">
          <thead className="bg-muted">
            <tr>
              <th className="text-left px-3 py-2" data-testid="plans-header-name">Name</th>
              <th className="text-left px-3 py-2" data-testid="plans-header-scope">Scope/Country</th>
              <th className="text-left px-3 py-2" data-testid="plans-header-period">Period</th>
              <th className="text-left px-3 py-2" data-testid="plans-header-price">Price</th>
              <th className="text-left px-3 py-2" data-testid="plans-header-listing">Listing</th>
              <th className="text-left px-3 py-2" data-testid="plans-header-showcase">Showcase</th>
              <th className="text-left px-3 py-2" data-testid="plans-header-active">Active</th>
              <th className="text-left px-3 py-2" data-testid="plans-header-updated">
                <button
                  type="button"
                  className="flex flex-col items-start"
                  onClick={() => setSortOrder((prev) => (prev === 'desc' ? 'asc' : 'desc'))}
                  data-testid="plans-sort-toggle"
                >
                  <span>Updated</span>
                  <span className="text-xs text-muted-foreground" data-testid="plans-sort-direction">
                    {sortOrder === 'desc' ? 'En yeni' : 'En eski'}
                  </span>
                </button>
              </th>
              <th className="text-right px-3 py-2" data-testid="plans-header-actions">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td className="px-3 py-4" colSpan="9">Yükleniyor...</td></tr>
            ) : sortedItems.length === 0 ? (
              <tr><td className="px-3 py-4" colSpan="9">Kayıt yok</td></tr>
            ) : (
              sortedItems.map((item) => (
                <tr key={item.id} className="border-t" data-testid={`plans-row-${item.id}`}>
                  <td className="px-3 py-2" data-testid={`plans-name-${item.id}`}>{item.name}</td>
                  <td className="px-3 py-2" data-testid={`plans-scope-${item.id}`}>
                    {item.country_scope === 'country' ? `Country / ${item.country_code || '-'}` : 'Global / —'}
                  </td>
                  <td className="px-3 py-2" data-testid={`plans-period-${item.id}`}>
                    {item.period || '-'}
                  </td>
                  <td className="px-3 py-2" data-testid={`plans-price-${item.id}`}>
                    {item.price_amount} {item.currency_code || 'EUR'}
                  </td>
                  <td className="px-3 py-2" data-testid={`plans-listing-${item.id}`}>{item.listing_quota}</td>
                  <td className="px-3 py-2" data-testid={`plans-showcase-${item.id}`}>{item.showcase_quota}</td>
                  <td className="px-3 py-2" data-testid={`plans-active-${item.id}`}>
                    {item.active_flag ? 'yes' : 'no'}
                  </td>
                  <td className="px-3 py-2" data-testid={`plans-updated-${item.id}`}>
                    {formatDate(item.updated_at || item.created_at)}
                  </td>
                  <td className="px-3 py-2 text-right space-x-2" data-testid={`plans-actions-${item.id}`}>
                    <button
                      className="px-2 py-1 border rounded"
                      onClick={() => openEdit(item)}
                      disabled={disabled}
                      title={disabled ? 'DB hazır değil' : 'Düzenle'}
                      data-testid={`plans-edit-${item.id}`}
                    >
                      Düzenle
                    </button>
                    <button
                      className="px-2 py-1 border rounded"
                      onClick={() => toggleActive(item)}
                      disabled={disabled}
                      title={disabled ? 'DB hazır değil' : 'Aktif/Pasif'}
                      data-testid={`plans-toggle-${item.id}`}
                    >
                      {item.active_flag ? 'Pasif Yap' : 'Aktif Yap'}
                    </button>
                    <button
                      className="px-2 py-1 border rounded text-red-600"
                      onClick={() => archivePlan(item)}
                      disabled={disabled}
                      title={disabled ? 'DB hazır değil' : 'Arşivle'}
                      data-testid={`plans-archive-${item.id}`}
                    >
                      Arşivle
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {showForm && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" data-testid="plans-form-modal">
          <div className="bg-white rounded-lg shadow-lg w-full max-w-xl p-6 space-y-4" data-testid="plans-form-card">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold" data-testid="plans-form-title">{editing ? 'Plan Düzenle' : 'Yeni Plan'}</h2>
              <button className="text-sm text-muted-foreground" onClick={closeForm} data-testid="plans-form-close">Kapat</button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-xs text-muted-foreground" data-testid="plans-form-name-label">Name</label>
                <input
                  className="w-full border rounded p-2"
                  value={form.name}
                  onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
                  data-testid="plans-form-name"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs text-muted-foreground" data-testid="plans-form-scope-label">Scope</label>
                <select
                  className="w-full border rounded p-2"
                  value={form.scope}
                  onChange={(e) => handleScopeChange(e.target.value)}
                  data-testid="plans-form-scope"
                >
                  <option value="global">Global</option>
                  <option value="country">Country</option>
                </select>
              </div>
              <div className="space-y-1">
                <label className="text-xs text-muted-foreground" data-testid="plans-form-country-label">Country</label>
                <select
                  className="w-full border rounded p-2"
                  value={form.country_code}
                  onChange={(e) => handleCountryChange(e.target.value)}
                  disabled={form.scope !== 'country'}
                  data-testid="plans-form-country"
                >
                  <option value="">Seç</option>
                  {COUNTRY_OPTIONS.map((item) => (
                    <option key={item.code} value={item.code}>{item.label}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-1">
                <label className="text-xs text-muted-foreground" data-testid="plans-form-period-label">Period</label>
                <select
                  className="w-full border rounded p-2"
                  value={form.period}
                  onChange={(e) => setForm((prev) => ({ ...prev, period: e.target.value }))}
                  data-testid="plans-form-period"
                >
                  <option value="monthly">Monthly</option>
                  <option value="yearly">Yearly</option>
                </select>
              </div>
              <div className="space-y-1">
                <label className="text-xs text-muted-foreground" data-testid="plans-form-currency-label">Currency</label>
                <input
                  className="w-full border rounded p-2 bg-muted"
                  value={resolveCurrency(form.scope, form.country_code || 'DE')}
                  readOnly
                  data-testid="plans-form-currency"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs text-muted-foreground" data-testid="plans-form-price-label">Price</label>
                <input
                  className="w-full border rounded p-2"
                  type="number"
                  value={form.price_amount}
                  onChange={(e) => setForm((prev) => ({ ...prev, price_amount: e.target.value }))}
                  data-testid="plans-form-price"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs text-muted-foreground" data-testid="plans-form-listing-label">Listing quota</label>
                <input
                  className="w-full border rounded p-2"
                  type="number"
                  value={form.listing_quota}
                  onChange={(e) => setForm((prev) => ({ ...prev, listing_quota: e.target.value }))}
                  data-testid="plans-form-listing"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs text-muted-foreground" data-testid="plans-form-showcase-label">Showcase quota</label>
                <input
                  className="w-full border rounded p-2"
                  type="number"
                  value={form.showcase_quota}
                  onChange={(e) => setForm((prev) => ({ ...prev, showcase_quota: e.target.value }))}
                  data-testid="plans-form-showcase"
                />
              </div>
              <div className="flex items-center gap-2" data-testid="plans-form-active">
                <input
                  type="checkbox"
                  checked={form.active_flag}
                  onChange={(e) => setForm((prev) => ({ ...prev, active_flag: e.target.checked }))}
                  data-testid="plans-form-active-checkbox"
                />
                <span>Aktif</span>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2">
              <button className="px-3 py-2 border rounded" onClick={closeForm} data-testid="plans-form-cancel">
                Vazgeç
              </button>
              <button
                className="px-3 py-2 border rounded"
                onClick={() => submitForm({ forceActive: true })}
                disabled={saving || disabled}
                data-testid="plans-form-save-activate"
              >
                Kaydet + Aktifleştir
              </button>
              <button
                className="px-3 py-2 rounded bg-primary text-white"
                onClick={() => submitForm({ forceActive: false })}
                disabled={saving || disabled}
                data-testid="plans-form-save"
              >
                Kaydet
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
