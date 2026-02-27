import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const DEFAULT_CONFIG = {
  homepage: { enabled: true, rows: 9, columns: 7, listing_count: 63 },
  category_showcase: {
    enabled: true,
    default: { rows: 2, columns: 4, listing_count: 8 },
    categories: [],
  },
};

const clamp = (value, min, max, fallback) => {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return fallback;
  return Math.min(max, Math.max(min, Math.floor(parsed)));
};

const normalizeConfig = (raw) => {
  const source = raw || {};
  const homepage = source.homepage || {};
  const categoryShowcase = source.category_showcase || {};
  const defaultBlock = categoryShowcase.default || {};
  return {
    homepage: {
      enabled: homepage.enabled !== false,
      rows: clamp(homepage.rows, 1, 12, 9),
      columns: clamp(homepage.columns, 1, 8, 7),
      listing_count: clamp(homepage.listing_count, 1, 120, 63),
    },
    category_showcase: {
      enabled: categoryShowcase.enabled !== false,
      default: {
        rows: clamp(defaultBlock.rows, 1, 12, 2),
        columns: clamp(defaultBlock.columns, 1, 8, 4),
        listing_count: clamp(defaultBlock.listing_count, 1, 120, 8),
      },
      categories: Array.isArray(categoryShowcase.categories)
        ? categoryShowcase.categories.map((item) => ({
          enabled: item?.enabled !== false,
          category_id: item?.category_id || '',
          category_slug: item?.category_slug || '',
          category_name: item?.category_name || '',
          rows: clamp(item?.rows, 1, 12, 2),
          columns: clamp(item?.columns, 1, 8, 4),
          listing_count: clamp(item?.listing_count, 1, 120, 8),
        }))
        : [],
    },
  };
};

const effectiveTileCount = (block) => Math.min(Number(block?.listing_count || 0), Number(block?.rows || 0) * Number(block?.columns || 0));

export default function AdminShowcaseManagement() {
  const [config, setConfig] = useState(DEFAULT_CONFIG);
  const [versions, setVersions] = useState([]);
  const [categories, setCategories] = useState([]);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const authHeader = useMemo(() => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` }), []);
  const countryCode = useMemo(() => (localStorage.getItem('selected_country') || 'DE').toUpperCase(), []);

  const categoryOptions = useMemo(
    () => categories
      .filter((item) => !item.parent_id)
      .map((item) => ({
        id: item.id,
        slug: item.slug || '',
        name: item.name || item.slug || item.id,
      })),
    [categories]
  );

  const fetchConfig = async () => {
    try {
      const res = await axios.get(`${API}/admin/site/showcase-layout`, { headers: authHeader });
      setConfig(normalizeConfig(res.data?.config));
    } catch (_err) {
      setConfig(DEFAULT_CONFIG);
    }
  };

  const fetchVersions = async () => {
    try {
      const res = await axios.get(`${API}/admin/site/showcase-layout/configs`, { headers: authHeader });
      setVersions(res.data?.items || []);
    } catch (_err) {
      setVersions([]);
    }
  };

  const fetchCategories = async () => {
    try {
      const res = await axios.get(`${API}/categories?module=vehicle&country=${countryCode}`);
      setCategories(Array.isArray(res.data) ? res.data : []);
    } catch (_err) {
      setCategories([]);
    }
  };

  useEffect(() => {
    fetchConfig();
    fetchVersions();
    fetchCategories();
  }, []);

  const updateHomeField = (key, value) => {
    setConfig((prev) => ({
      ...prev,
      homepage: {
        ...prev.homepage,
        [key]: key === 'enabled' ? Boolean(value) : clamp(value, 1, key === 'columns' ? 8 : key === 'rows' ? 12 : 120, prev.homepage[key]),
      },
    }));
  };

  const updateCategoryDefaultField = (key, value) => {
    setConfig((prev) => ({
      ...prev,
      category_showcase: {
        ...prev.category_showcase,
        default: {
          ...prev.category_showcase.default,
          [key]: key === 'enabled' ? Boolean(value) : clamp(value, 1, key === 'columns' ? 8 : key === 'rows' ? 12 : 120, prev.category_showcase.default[key]),
        },
      },
    }));
  };

  const updateCategoryItem = (index, updates) => {
    setConfig((prev) => {
      const nextItems = [...(prev.category_showcase.categories || [])];
      nextItems[index] = { ...nextItems[index], ...updates };
      return {
        ...prev,
        category_showcase: {
          ...prev.category_showcase,
          categories: nextItems,
        },
      };
    });
  };

  const addCategoryLayout = () => {
    const defaultBlock = config.category_showcase.default;
    const usedIds = new Set((config.category_showcase.categories || []).map((item) => item.category_id).filter(Boolean));
    const firstAvailable = categoryOptions.find((option) => !usedIds.has(option.id)) || categoryOptions[0];
    setConfig((prev) => ({
      ...prev,
      category_showcase: {
        ...prev.category_showcase,
        categories: [
          ...(prev.category_showcase.categories || []),
          {
            enabled: true,
            category_id: firstAvailable?.id || '',
            category_slug: firstAvailable?.slug || '',
            category_name: firstAvailable?.name || '',
            rows: defaultBlock.rows,
            columns: defaultBlock.columns,
            listing_count: defaultBlock.listing_count,
          },
        ],
      },
    }));
  };

  const removeCategoryLayout = (index) => {
    setConfig((prev) => ({
      ...prev,
      category_showcase: {
        ...prev.category_showcase,
        categories: (prev.category_showcase.categories || []).filter((_, idx) => idx !== index),
      },
    }));
  };

  const saveDraft = async () => {
    setSaving(true);
    setStatus('');
    setError('');
    try {
      const payload = normalizeConfig(config);
      const res = await axios.put(
        `${API}/admin/site/showcase-layout/config`,
        { config: payload, status: 'draft' },
        { headers: authHeader }
      );
      setStatus(`Taslak kaydedildi (v${res.data?.version || '-'})`);
      await fetchVersions();
      return res.data;
    } catch (err) {
      setError(err?.response?.data?.detail?.message || 'Kaydetme başarısız');
      return null;
    } finally {
      setSaving(false);
    }
  };

  const handlePublish = async () => {
    const saved = await saveDraft();
    if (!saved?.id) return;
    try {
      await axios.post(`${API}/admin/site/showcase-layout/config/${saved.id}/publish`, {}, { headers: authHeader });
      setStatus(`Yayına alındı (v${saved.version || '-'})`);
      await fetchVersions();
      await fetchConfig();
    } catch (err) {
      setError(err?.response?.data?.detail?.message || 'Yayınlama başarısız');
    }
  };

  const loadVersion = async (id) => {
    try {
      const res = await axios.get(`${API}/admin/site/showcase-layout/config/${id}`, { headers: authHeader });
      setConfig(normalizeConfig(res.data?.config));
      setStatus(`Versiyon yüklendi (v${res.data?.version || '-'})`);
      setError('');
    } catch (_err) {
      setError('Versiyon yüklenemedi');
    }
  };

  const publishVersion = async (id) => {
    try {
      await axios.post(`${API}/admin/site/showcase-layout/config/${id}/publish`, {}, { headers: authHeader });
      setStatus('Seçilen versiyon yayına alındı');
      await fetchVersions();
      await fetchConfig();
      setError('');
    } catch (_err) {
      setError('Versiyon yayınlanamadı');
    }
  };

  return (
    <div className="space-y-6" data-testid="admin-showcase-management-page">
      <div className="flex flex-wrap items-start justify-between gap-4" data-testid="admin-showcase-management-header">
        <div>
          <h1 className="text-2xl font-semibold" data-testid="admin-showcase-management-title">Vitrin Yönetimi</h1>
          <p className="text-sm text-muted-foreground" data-testid="admin-showcase-management-subtitle">
            Ana sayfa ve ana kategori vitrin düzenini satır/sütun/ilan alanı ile yönetin.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2" data-testid="admin-showcase-management-actions">
          <button type="button" onClick={saveDraft} className="h-9 rounded-md border px-4 text-sm" disabled={saving} data-testid="admin-showcase-save-draft">
            Taslağı Kaydet
          </button>
          <button type="button" onClick={handlePublish} className="h-9 rounded-md bg-primary px-4 text-sm text-primary-foreground" disabled={saving} data-testid="admin-showcase-publish">
            Yayınla
          </button>
        </div>
      </div>

      {status ? <div className="text-xs text-emerald-600" data-testid="admin-showcase-status">{status}</div> : null}
      {error ? <div className="text-xs text-rose-600" data-testid="admin-showcase-error">{error}</div> : null}

      <div className="rounded-lg border bg-white p-4 space-y-4" data-testid="admin-showcase-home-block">
        <div className="flex items-center justify-between gap-4">
          <h2 className="text-base font-semibold" data-testid="admin-showcase-home-title">1. Ana Sayfa Vitrin</h2>
          <label className="inline-flex items-center gap-2 text-xs" data-testid="admin-showcase-home-enabled-wrap">
            <input type="checkbox" checked={config.homepage.enabled} onChange={(e) => updateHomeField('enabled', e.target.checked)} data-testid="admin-showcase-home-enabled" />
            Aktif
          </label>
        </div>
        <div className="grid gap-3 md:grid-cols-3">
          <label className="text-xs">Satır
            <input type="number" min={1} max={12} value={config.homepage.rows} onChange={(e) => updateHomeField('rows', e.target.value)} className="mt-1 h-9 w-full rounded-md border px-2 text-sm" data-testid="admin-showcase-home-rows" />
          </label>
          <label className="text-xs">Sütun
            <input type="number" min={1} max={8} value={config.homepage.columns} onChange={(e) => updateHomeField('columns', e.target.value)} className="mt-1 h-9 w-full rounded-md border px-2 text-sm" data-testid="admin-showcase-home-columns" />
          </label>
          <label className="text-xs">İlan Alanı
            <input type="number" min={1} max={120} value={config.homepage.listing_count} onChange={(e) => updateHomeField('listing_count', e.target.value)} className="mt-1 h-9 w-full rounded-md border px-2 text-sm" data-testid="admin-showcase-home-listing-count" />
          </label>
        </div>
        <div className="text-xs text-muted-foreground" data-testid="admin-showcase-home-effective-count">
          Aktif gösterim: {effectiveTileCount(config.homepage)} ilan (satır×sütun ve ilan alanı birlikte uygulanır)
        </div>
      </div>

      <div className="rounded-lg border bg-white p-4 space-y-4" data-testid="admin-showcase-category-block">
        <div className="flex items-center justify-between gap-4">
          <h2 className="text-base font-semibold" data-testid="admin-showcase-category-title">2. Ana Kategori Vitrin</h2>
          <label className="inline-flex items-center gap-2 text-xs" data-testid="admin-showcase-category-enabled-wrap">
            <input type="checkbox" checked={config.category_showcase.enabled} onChange={(e) => setConfig((prev) => ({ ...prev, category_showcase: { ...prev.category_showcase, enabled: e.target.checked } }))} data-testid="admin-showcase-category-enabled" />
            Aktif
          </label>
        </div>

        <div className="grid gap-3 rounded-md border border-dashed p-3 md:grid-cols-3" data-testid="admin-showcase-category-default-grid">
          <label className="text-xs">Varsayılan Satır
            <input type="number" min={1} max={12} value={config.category_showcase.default.rows} onChange={(e) => updateCategoryDefaultField('rows', e.target.value)} className="mt-1 h-9 w-full rounded-md border px-2 text-sm" data-testid="admin-showcase-category-default-rows" />
          </label>
          <label className="text-xs">Varsayılan Sütun
            <input type="number" min={1} max={8} value={config.category_showcase.default.columns} onChange={(e) => updateCategoryDefaultField('columns', e.target.value)} className="mt-1 h-9 w-full rounded-md border px-2 text-sm" data-testid="admin-showcase-category-default-columns" />
          </label>
          <label className="text-xs">Varsayılan İlan Alanı
            <input type="number" min={1} max={120} value={config.category_showcase.default.listing_count} onChange={(e) => updateCategoryDefaultField('listing_count', e.target.value)} className="mt-1 h-9 w-full rounded-md border px-2 text-sm" data-testid="admin-showcase-category-default-listing-count" />
          </label>
        </div>

        <div className="flex items-center justify-between" data-testid="admin-showcase-category-list-header">
          <div className="text-xs text-muted-foreground">Birden fazla ana kategori için ayrı vitrin düzeni tanımlayabilirsiniz.</div>
          <button type="button" onClick={addCategoryLayout} className="h-8 rounded-md border px-3 text-xs" data-testid="admin-showcase-category-add">
            Ana Kategori Ekle
          </button>
        </div>

        <div className="space-y-3" data-testid="admin-showcase-category-list">
          {(config.category_showcase.categories || []).length === 0 ? (
            <div className="text-xs text-muted-foreground" data-testid="admin-showcase-category-empty">Henüz kategori vitrini eklenmedi.</div>
          ) : (config.category_showcase.categories || []).map((item, index) => (
            <div key={`${item.category_id || item.category_slug || 'item'}-${index}`} className="rounded-md border p-3 space-y-3" data-testid={`admin-showcase-category-item-${index}`}>
              <div className="grid gap-3 md:grid-cols-[2fr_1fr]">
                <label className="text-xs">Ana Kategori
                  <select
                    value={item.category_id || ''}
                    onChange={(e) => {
                      const selected = categoryOptions.find((option) => option.id === e.target.value);
                      updateCategoryItem(index, {
                        category_id: selected?.id || '',
                        category_slug: selected?.slug || '',
                        category_name: selected?.name || '',
                      });
                    }}
                    className="mt-1 h-9 w-full rounded-md border px-2 text-sm"
                    data-testid={`admin-showcase-category-select-${index}`}
                  >
                    <option value="">Kategori seç</option>
                    {categoryOptions.map((option) => (
                      <option key={option.id} value={option.id}>{option.name}</option>
                    ))}
                  </select>
                </label>
                <label className="inline-flex items-end gap-2 text-xs" data-testid={`admin-showcase-category-enabled-wrap-${index}`}>
                  <input type="checkbox" checked={item.enabled !== false} onChange={(e) => updateCategoryItem(index, { enabled: e.target.checked })} data-testid={`admin-showcase-category-enabled-${index}`} />
                  Aktif
                </label>
              </div>
              <div className="grid gap-3 md:grid-cols-3">
                <label className="text-xs">Satır
                  <input type="number" min={1} max={12} value={item.rows} onChange={(e) => updateCategoryItem(index, { rows: clamp(e.target.value, 1, 12, item.rows) })} className="mt-1 h-9 w-full rounded-md border px-2 text-sm" data-testid={`admin-showcase-category-rows-${index}`} />
                </label>
                <label className="text-xs">Sütun
                  <input type="number" min={1} max={8} value={item.columns} onChange={(e) => updateCategoryItem(index, { columns: clamp(e.target.value, 1, 8, item.columns) })} className="mt-1 h-9 w-full rounded-md border px-2 text-sm" data-testid={`admin-showcase-category-columns-${index}`} />
                </label>
                <label className="text-xs">İlan Alanı
                  <input type="number" min={1} max={120} value={item.listing_count} onChange={(e) => updateCategoryItem(index, { listing_count: clamp(e.target.value, 1, 120, item.listing_count) })} className="mt-1 h-9 w-full rounded-md border px-2 text-sm" data-testid={`admin-showcase-category-listing-count-${index}`} />
                </label>
              </div>
              <div className="flex items-center justify-between gap-3">
                <div className="text-xs text-muted-foreground" data-testid={`admin-showcase-category-effective-count-${index}`}>
                  Aktif gösterim: {effectiveTileCount(item)} ilan
                </div>
                <button type="button" onClick={() => removeCategoryLayout(index)} className="text-xs text-rose-600 underline" data-testid={`admin-showcase-category-remove-${index}`}>
                  Kaldır
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-lg border bg-white p-4" data-testid="admin-showcase-versions-card">
        <div className="text-sm font-semibold">Versiyonlar</div>
        <div className="mt-3 space-y-2" data-testid="admin-showcase-versions-list">
          {versions.length === 0 ? <div className="text-xs text-muted-foreground" data-testid="admin-showcase-version-empty">Kayıtlı versiyon yok.</div> : null}
          {versions.map((item) => (
            <div key={item.id} className="flex items-center justify-between gap-2 rounded-md border px-3 py-2 text-xs" data-testid={`admin-showcase-version-${item.id}`}>
              <div>
                <div className="font-semibold">v{item.version}</div>
                <div className="text-muted-foreground">{item.status}</div>
              </div>
              <div className="flex items-center gap-2">
                <button type="button" className="rounded-md border px-2 py-1" onClick={() => loadVersion(item.id)} data-testid={`admin-showcase-version-load-${item.id}`}>
                  Yükle
                </button>
                {item.status !== 'published' ? (
                  <button type="button" className="rounded-md bg-primary px-2 py-1 text-primary-foreground" onClick={() => publishVersion(item.id)} data-testid={`admin-showcase-version-publish-${item.id}`}>
                    Yayınla
                  </button>
                ) : (
                  <span className="rounded-full bg-emerald-100 px-2 py-1 text-emerald-700" data-testid={`admin-showcase-version-live-${item.id}`}>Aktif</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
