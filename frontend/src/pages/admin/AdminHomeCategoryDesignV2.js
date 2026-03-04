import React, { useEffect, useMemo, useState } from 'react';
import { useLanguage } from '@/contexts/LanguageContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const MODULES = [
  { key: 'real_estate', label: 'Emlak' },
  { key: 'vehicle', label: 'Vasıta' },
  { key: 'other', label: 'Diğer' },
];

const DEFAULT_CONFIG = {
  column_width: 304,
  l1_initial_limit: 6,
  module_order_mode: 'manual',
  module_order: MODULES.map((item) => item.key),
  module_l1_order_mode: {},
  module_l1_order: {},
  listing_module_grid_rows: 2,
  listing_module_grid_columns: 4,
  listing_lx_limit: 8,
};

const EMPTY_CATEGORY_FORM = {
  id: null,
  name: '',
  slug: '',
  module: 'real_estate',
  parent_id: '',
  sort_order: 1,
  active_flag: true,
  icon_svg: '',
};

const LANGUAGE_LOCALE_MAP = {
  tr: 'tr-TR',
  de: 'de-DE',
  fr: 'fr-FR',
};

const clamp = (value, min, max, fallback) => {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return fallback;
  return Math.max(min, Math.min(max, Math.floor(parsed)));
};

const normalizeConfig = (raw) => {
  const source = raw || {};
  const moduleOrder = [];
  const seen = new Set();
  const rawOrder = Array.isArray(source.module_order) ? source.module_order : [];
  rawOrder.forEach((value) => {
    const key = String(value || '').trim();
    if (!key || seen.has(key)) return;
    moduleOrder.push(key);
    seen.add(key);
  });
  MODULES.forEach((item) => {
    if (!moduleOrder.includes(item.key)) moduleOrder.push(item.key);
  });

  return {
    column_width: clamp(source.column_width, 240, 420, DEFAULT_CONFIG.column_width),
    l1_initial_limit: clamp(source.l1_initial_limit, 1, 20, DEFAULT_CONFIG.l1_initial_limit),
    module_order_mode: source.module_order_mode === 'alphabetical' ? 'alphabetical' : 'manual',
    module_order: moduleOrder,
    module_l1_order_mode: typeof source.module_l1_order_mode === 'object' && source.module_l1_order_mode ? source.module_l1_order_mode : {},
    module_l1_order: typeof source.module_l1_order === 'object' && source.module_l1_order ? source.module_l1_order : {},
    listing_module_grid_rows: clamp(source.listing_module_grid_rows, 1, 6, DEFAULT_CONFIG.listing_module_grid_rows),
    listing_module_grid_columns: clamp(source.listing_module_grid_columns, 2, 6, DEFAULT_CONFIG.listing_module_grid_columns),
    listing_lx_limit: clamp(source.listing_lx_limit, 4, 20, DEFAULT_CONFIG.listing_lx_limit),
  };
};

const moveItem = (list, fromIndex, toIndex) => {
  const next = [...list];
  const [moved] = next.splice(fromIndex, 1);
  next.splice(toIndex, 0, moved);
  return next;
};

const slugify = (value) => String(value || '')
  .toLowerCase()
  .normalize('NFKD')
  .replace(/[\u0300-\u036f]/g, '')
  .replace(/ı/g, 'i')
  .replace(/ş/g, 's')
  .replace(/ğ/g, 'g')
  .replace(/ç/g, 'c')
  .replace(/ö/g, 'o')
  .replace(/ü/g, 'u')
  .replace(/[^a-z0-9\s-]/g, '')
  .replace(/\s+/g, '-')
  .replace(/-+/g, '-')
  .replace(/^-|-$/g, '');

const parseApiError = async (response) => {
  const payload = await response.json().catch(() => ({}));
  const detail = payload?.detail;
  if (typeof detail === 'string') return detail;
  if (detail && typeof detail === 'object') return detail.message || detail.error_code || 'İşlem başarısız';
  return payload?.message || 'İşlem başarısız';
};

const readFileAsText = (file) => new Promise((resolve, reject) => {
  const reader = new FileReader();
  reader.onload = () => resolve(String(reader.result || ''));
  reader.onerror = () => reject(new Error('Dosya okunamadı'));
  reader.readAsText(file);
});

const readFileAsDataUrl = (file) => new Promise((resolve, reject) => {
  const reader = new FileReader();
  reader.onload = () => resolve(String(reader.result || ''));
  reader.onerror = () => reject(new Error('Dosya okunamadı'));
  reader.readAsDataURL(file);
});

const wrapDataUrlAsSvg = (dataUrl) => {
  const safeDataUrl = String(dataUrl || '').replace(/"/g, '&quot;');
  return `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><image href="${safeDataUrl}" x="0" y="0" width="24" height="24" preserveAspectRatio="xMidYMid slice"/></svg>`;
};

const CategoryIconPreview = ({ iconSvg, testId }) => {
  if (iconSvg) {
    return <span className="h-7 w-7 rounded-full border bg-white p-1" dangerouslySetInnerHTML={{ __html: iconSvg }} data-testid={testId} />;
  }
  return <span className="h-7 w-7 rounded-full border bg-slate-100" data-testid={testId} />;
};

export default function AdminHomeCategoryDesignV2() {
  const { language } = useLanguage();
  const [config, setConfig] = useState(DEFAULT_CONFIG);
  const [categoriesByModule, setCategoriesByModule] = useState({});
  const [adminCategories, setAdminCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');

  const [crudModule, setCrudModule] = useState('real_estate');
  const [crudStatus, setCrudStatus] = useState('');
  const [crudError, setCrudError] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [categorySaving, setCategorySaving] = useState(false);
  const [categoryForm, setCategoryForm] = useState(EMPTY_CATEGORY_FORM);
  const [iconUploadStatus, setIconUploadStatus] = useState('');
  const [iconUploadError, setIconUploadError] = useState('');

  const authHeader = useMemo(() => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` }), []);
  const countryCode = useMemo(() => (localStorage.getItem('selected_country') || 'DE').toUpperCase(), []);

  const moduleLabelMap = useMemo(() => new Map(MODULES.map((item) => [item.key, item.label])), []);

  const moduleOrder = useMemo(() => {
    const rawOrder = Array.isArray(config.module_order) ? config.module_order : [];
    if (config.module_order_mode === 'alphabetical') {
      return MODULES
        .map((item) => item.key)
        .sort((a, b) => {
          const labelA = moduleLabelMap.get(a) || a;
          const labelB = moduleLabelMap.get(b) || b;
          return labelA.localeCompare(labelB, LANGUAGE_LOCALE_MAP[language] || 'tr-TR');
        });
    }
    const unique = [];
    const seen = new Set();
    rawOrder.forEach((item) => {
      const value = String(item || '').trim();
      if (!value || seen.has(value)) return;
      unique.push(value);
      seen.add(value);
    });
    MODULES.forEach((item) => {
      if (!unique.includes(item.key)) unique.push(item.key);
    });
    return unique;
  }, [config.module_order, config.module_order_mode, language, moduleLabelMap]);

  const moduleSections = useMemo(() => moduleOrder.map((moduleKey) => {
    const moduleLabel = moduleLabelMap.get(moduleKey) || moduleKey;
    const categories = categoriesByModule[moduleKey] || [];
    const roots = categories.filter((item) => !item.parent_id);
    const orderList = Array.isArray(config.module_l1_order?.[moduleKey]) ? config.module_l1_order[moduleKey] : [];
    const orderIndex = new Map(orderList.map((item, index) => [item, index]));
    const l1Mode = config.module_l1_order_mode?.[moduleKey] || 'alphabetical';
    const orderedRoots = [...roots].sort((a, b) => {
      if (l1Mode === 'alphabetical') {
        return String(a.name || a.slug || '').localeCompare(String(b.name || b.slug || ''), LANGUAGE_LOCALE_MAP[language] || 'tr-TR');
      }
      const ai = orderIndex.get(a.id) ?? orderIndex.get(a.slug) ?? Number(a.sort_order || 9999);
      const bi = orderIndex.get(b.id) ?? orderIndex.get(b.slug) ?? Number(b.sort_order || 9999);
      return ai - bi;
    });
    return {
      moduleKey,
      moduleLabel,
      roots: orderedRoots,
      l1Mode,
    };
  }), [categoriesByModule, config.module_l1_order, config.module_l1_order_mode, language, moduleLabelMap, moduleOrder]);

  const moduleCrudRows = useMemo(() => {
    const scoped = adminCategories.filter((item) => item.module === crudModule);
    const byParent = new Map();
    scoped.forEach((item) => {
      const key = item.parent_id || '__root__';
      if (!byParent.has(key)) byParent.set(key, []);
      byParent.get(key).push(item);
    });

    const sortRows = (rows) => [...rows].sort((a, b) => Number(a.sort_order || 0) - Number(b.sort_order || 0));
    const roots = sortRows(byParent.get('__root__') || []).map((root) => ({
      ...root,
      children: sortRows(byParent.get(root.id) || []),
    }));

    return roots;
  }, [adminCategories, crudModule]);

  const findCategoryById = (categoryId) => adminCategories.find((item) => item.id === categoryId) || null;

  const getSiblingNextSortOrder = (moduleKey, parentId) => {
    const siblings = adminCategories.filter((item) => item.module === moduleKey && (item.parent_id || '') === (parentId || ''));
    const maxSort = siblings.reduce((maxValue, item) => Math.max(maxValue, Number(item.sort_order || 0)), 0);
    return maxSort + 1;
  };

  const fetchConfig = async () => {
    const response = await fetch(`${API}/admin/site/home-category-layout?country=${countryCode}`, { headers: authHeader });
    const payload = await response.json().catch(() => ({}));
    setConfig(normalizeConfig(payload?.config));
  };

  const fetchPublicCategories = async () => {
    const responses = await Promise.allSettled(
      MODULES.map((moduleItem) => fetch(`${API}/categories?module=${moduleItem.key}&country=${countryCode}`))
    );
    const next = {};
    for (let index = 0; index < responses.length; index += 1) {
      const result = responses[index];
      const moduleKey = MODULES[index].key;
      if (result.status === 'fulfilled') {
        const payload = await result.value.json().catch(() => []);
        next[moduleKey] = Array.isArray(payload) ? payload : [];
      } else {
        next[moduleKey] = [];
      }
    }
    setCategoriesByModule(next);
  };

  const fetchAdminCategories = async () => {
    const response = await fetch(`${API}/admin/categories?country=${countryCode}`, { headers: authHeader });
    const payload = await response.json().catch(() => ({}));
    const rows = Array.isArray(payload?.items) ? payload.items : [];
    setAdminCategories(rows);
  };

  const refreshAll = async () => {
    setLoading(true);
    setError('');
    try {
      await Promise.all([fetchConfig(), fetchPublicCategories(), fetchAdminCategories()]);
    } catch (_e) {
      setError('Veriler yüklenemedi. Lütfen tekrar deneyin.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshAll();
  }, []);

  const handleModuleMove = (index, direction) => {
    if (config.module_order_mode === 'alphabetical') return;
    setConfig((prev) => {
      const nextIndex = index + direction;
      if (nextIndex < 0 || nextIndex >= moduleOrder.length) return prev;
      return {
        ...prev,
        module_order: moveItem(moduleOrder, index, nextIndex),
      };
    });
  };

  const handleL1Move = (moduleKey, index, direction) => {
    if ((config.module_l1_order_mode?.[moduleKey] || 'alphabetical') === 'alphabetical') return;
    setConfig((prev) => {
      const roots = (categoriesByModule[moduleKey] || []).filter((item) => !item.parent_id);
      const orderList = Array.isArray(prev.module_l1_order?.[moduleKey]) ? prev.module_l1_order[moduleKey] : [];
      const orderIndex = new Map(orderList.map((item, idx) => [item, idx]));
      const orderedRoots = [...roots].sort((a, b) => {
        const ai = orderIndex.get(a.id) ?? orderIndex.get(a.slug) ?? Number(a.sort_order || 9999);
        const bi = orderIndex.get(b.id) ?? orderIndex.get(b.slug) ?? Number(b.sort_order || 9999);
        return ai - bi;
      });
      const nextIndex = index + direction;
      if (nextIndex < 0 || nextIndex >= orderedRoots.length) return prev;
      const nextOrderIds = moveItem(orderedRoots.map((item) => item.id), index, nextIndex);
      return {
        ...prev,
        module_l1_order: {
          ...prev.module_l1_order,
          [moduleKey]: nextOrderIds,
        },
      };
    });
  };

  const handleSaveLayout = async () => {
    setSaving(true);
    setStatus('');
    setError('');
    try {
      const response = await fetch(`${API}/admin/site/home-category-layout`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...authHeader,
        },
        body: JSON.stringify({ config, country_code: countryCode }),
      });
      if (!response.ok) {
        throw new Error(await parseApiError(response));
      }
      const payload = await response.json();
      setConfig(normalizeConfig(payload?.config || config));
      setStatus('Ana sayfa kategori layout ayarları kaydedildi.');
    } catch (saveError) {
      setError(saveError?.message || 'Kaydetme başarısız.');
    } finally {
      setSaving(false);
    }
  };

  const openCreateModal = ({ moduleKey, parentId = '' }) => {
    setCrudError('');
    setCrudStatus('');
    setIconUploadStatus('');
    setIconUploadError('');
    setCategoryForm({
      ...EMPTY_CATEGORY_FORM,
      module: moduleKey,
      parent_id: parentId,
      sort_order: getSiblingNextSortOrder(moduleKey, parentId),
    });
    setModalOpen(true);
  };

  const openEditModal = (item) => {
    setCrudError('');
    setCrudStatus('');
    setIconUploadStatus('');
    setIconUploadError('');
    setCategoryForm({
      id: item.id,
      name: item.name || '',
      slug: item.slug || '',
      module: item.module || 'real_estate',
      parent_id: item.parent_id || '',
      sort_order: Number(item.sort_order || 1),
      active_flag: Boolean(item.active_flag),
      icon_svg: item.icon_svg || '',
    });
    setModalOpen(true);
  };

  const closeModal = () => {
    if (categorySaving) return;
    setModalOpen(false);
    setCategoryForm(EMPTY_CATEGORY_FORM);
    setIconUploadStatus('');
    setIconUploadError('');
  };

  const handleIconFileUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIconUploadStatus('');
    setIconUploadError('');

    try {
      const isSvg = file.type === 'image/svg+xml' || String(file.name || '').toLowerCase().endsWith('.svg');
      const isRaster = file.type.startsWith('image/');

      if (!isSvg && !isRaster) {
        throw new Error('Sadece SVG/PNG/JPG/WEBP ikon dosyası yükleyebilirsiniz.');
      }

      if (isSvg) {
        const svgText = (await readFileAsText(file)).trim();
        if (!svgText.toLowerCase().includes('<svg')) {
          throw new Error('Yüklenen SVG dosyası geçerli değil.');
        }
        setCategoryForm((prev) => ({ ...prev, icon_svg: svgText }));
        setIconUploadStatus('SVG dosyası yüklendi.');
      } else {
        const dataUrl = await readFileAsDataUrl(file);
        setCategoryForm((prev) => ({ ...prev, icon_svg: wrapDataUrlAsSvg(dataUrl) }));
        setIconUploadStatus('Görsel yüklendi ve SVG ikon formatına dönüştürüldü.');
      }
    } catch (uploadError) {
      setIconUploadError(uploadError?.message || 'İkon dosyası yüklenemedi.');
    } finally {
      event.target.value = '';
    }
  };

  const handleCategorySave = async () => {
    setCategorySaving(true);
    setCrudError('');
    setCrudStatus('');
    try {
      const payload = {
        name: categoryForm.name.trim(),
        slug: slugify(categoryForm.slug || categoryForm.name),
        module: categoryForm.module,
        parent_id: categoryForm.parent_id || null,
        country_code: countryCode,
        sort_order: Number(categoryForm.sort_order || 1),
        active_flag: Boolean(categoryForm.active_flag),
        icon_svg: categoryForm.icon_svg,
      };

      if (!payload.name) throw new Error('Kategori adı zorunludur.');
      if (!payload.slug) throw new Error('Geçerli bir slug zorunludur.');

      const isEdit = Boolean(categoryForm.id);
      const endpoint = isEdit ? `${API}/admin/categories/${categoryForm.id}` : `${API}/admin/categories`;
      const method = isEdit ? 'PATCH' : 'POST';

      const response = await fetch(endpoint, {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...authHeader,
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(await parseApiError(response));
      }

      await Promise.all([fetchAdminCategories(), fetchPublicCategories()]);
      setCrudStatus(isEdit ? 'Kategori güncellendi.' : 'Kategori oluşturuldu.');
      closeModal();
    } catch (saveError) {
      setCrudError(saveError?.message || 'Kategori kaydedilemedi.');
    } finally {
      setCategorySaving(false);
    }
  };

  const handleDeleteCategory = async (category) => {
    const confirmed = window.confirm(`"${category.name}" kategorisini silmek istediğinizden emin misiniz?`);
    if (!confirmed) return;
    setCrudError('');
    setCrudStatus('');
    try {
      const response = await fetch(`${API}/admin/categories/${category.id}`, {
        method: 'DELETE',
        headers: authHeader,
      });
      if (!response.ok) {
        throw new Error(await parseApiError(response));
      }
      await Promise.all([fetchAdminCategories(), fetchPublicCategories()]);
      setCrudStatus('Kategori silindi.');
    } catch (deleteError) {
      setCrudError(deleteError?.message || 'Kategori silinemedi.');
    }
  };

  return (
    <div className="space-y-6" data-testid="home-category-design-v2-page">
      <div className="flex flex-wrap items-center justify-between gap-3" data-testid="home-category-design-v2-header">
        <div>
          <h1 className="text-2xl font-semibold" data-testid="home-category-design-v2-title">Ana Sayfa Kategori & Tasarım Yönetimi</h1>
          <p className="text-sm text-slate-600" data-testid="home-category-design-v2-subtitle">
            Homepage kategori görünümü, modül sıraları ve kategori CRUD işlemlerini bu ekrandan yönetebilirsiniz.
          </p>
        </div>
        <div className="flex items-center gap-2" data-testid="home-category-design-v2-actions">
          <button
            type="button"
            className="h-10 rounded-md border px-4 text-sm"
            onClick={refreshAll}
            data-testid="home-category-design-v2-refresh"
          >
            Yenile
          </button>
          <button
            type="button"
            className="h-10 rounded-md bg-slate-900 px-5 text-sm text-white disabled:opacity-60"
            onClick={handleSaveLayout}
            disabled={saving}
            data-testid="home-category-design-v2-save-layout"
          >
            {saving ? 'Kaydediliyor...' : 'Layout Kaydet'}
          </button>
        </div>
      </div>

      {status ? <div className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700" data-testid="home-category-design-v2-status">{status}</div> : null}
      {error ? <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700" data-testid="home-category-design-v2-error">{error}</div> : null}

      <div className="rounded-xl border bg-white p-4" data-testid="home-category-layout-controls-card">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <label className="space-y-1" data-testid="home-category-layout-column-width-block">
            <span className="text-xs font-semibold text-slate-600">Kategori Kolon Genişliği</span>
            <input
              type="number"
              min={240}
              max={420}
              value={config.column_width}
              onChange={(event) => setConfig((prev) => ({ ...prev, column_width: clamp(event.target.value, 240, 420, prev.column_width) }))}
              className="h-10 w-full rounded-md border px-3 text-sm"
              data-testid="home-category-layout-column-width-input"
            />
          </label>

          <label className="space-y-1" data-testid="home-category-layout-root-limit-block">
            <span className="text-xs font-semibold text-slate-600">L1 İlk Gösterim Adedi</span>
            <input
              type="number"
              min={1}
              max={20}
              value={config.l1_initial_limit}
              onChange={(event) => setConfig((prev) => ({ ...prev, l1_initial_limit: clamp(event.target.value, 1, 20, prev.l1_initial_limit) }))}
              className="h-10 w-full rounded-md border px-3 text-sm"
              data-testid="home-category-layout-root-limit-input"
            />
          </label>

          <label className="space-y-1" data-testid="home-category-layout-grid-columns-block">
            <span className="text-xs font-semibold text-slate-600">Kart Grid Sütun</span>
            <input
              type="number"
              min={2}
              max={6}
              value={config.listing_module_grid_columns}
              onChange={(event) => setConfig((prev) => ({ ...prev, listing_module_grid_columns: clamp(event.target.value, 2, 6, prev.listing_module_grid_columns) }))}
              className="h-10 w-full rounded-md border px-3 text-sm"
              data-testid="home-category-layout-grid-columns-input"
            />
          </label>

          <label className="space-y-1" data-testid="home-category-layout-grid-limit-block">
            <span className="text-xs font-semibold text-slate-600">Kart Gösterim Limiti</span>
            <input
              type="number"
              min={4}
              max={20}
              value={config.listing_lx_limit}
              onChange={(event) => setConfig((prev) => ({ ...prev, listing_lx_limit: clamp(event.target.value, 4, 20, prev.listing_lx_limit) }))}
              className="h-10 w-full rounded-md border px-3 text-sm"
              data-testid="home-category-layout-grid-limit-input"
            />
          </label>
        </div>
      </div>

      <div className="grid gap-4" data-testid="home-category-layout-module-order-list">
        {loading ? (
          <div className="rounded-md border bg-white p-3 text-sm text-slate-600" data-testid="home-category-layout-loading">Yükleniyor...</div>
        ) : moduleSections.map((section, index) => (
          <div key={section.moduleKey} className="rounded-xl border bg-white p-4" data-testid={`home-category-layout-module-${section.moduleKey}`}>
            <div className="flex flex-wrap items-center justify-between gap-3" data-testid={`home-category-layout-module-header-${section.moduleKey}`}>
              <div>
                <div className="text-xs text-slate-500">Modül</div>
                <div className="text-lg font-semibold" data-testid={`home-category-layout-module-title-${section.moduleKey}`}>{section.moduleLabel}</div>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <select
                  className="h-9 rounded-md border px-3 text-sm"
                  value={section.l1Mode}
                  onChange={(event) => setConfig((prev) => ({
                    ...prev,
                    module_l1_order_mode: {
                      ...prev.module_l1_order_mode,
                      [section.moduleKey]: event.target.value === 'alphabetical' ? 'alphabetical' : 'manual',
                    },
                  }))}
                  data-testid={`home-category-layout-module-l1-mode-${section.moduleKey}`}
                >
                  <option value="manual">L1 Manuel</option>
                  <option value="alphabetical">L1 Alfabetik</option>
                </select>
                <button
                  type="button"
                  onClick={() => handleModuleMove(index, -1)}
                  disabled={index === 0 || config.module_order_mode === 'alphabetical'}
                  className="h-9 rounded-md border px-3 text-sm disabled:opacity-50"
                  data-testid={`home-category-layout-module-up-${section.moduleKey}`}
                >
                  Yukarı
                </button>
                <button
                  type="button"
                  onClick={() => handleModuleMove(index, 1)}
                  disabled={index === moduleSections.length - 1 || config.module_order_mode === 'alphabetical'}
                  className="h-9 rounded-md border px-3 text-sm disabled:opacity-50"
                  data-testid={`home-category-layout-module-down-${section.moduleKey}`}
                >
                  Aşağı
                </button>
              </div>
            </div>

            <div className="mt-3 grid gap-2" data-testid={`home-category-layout-module-roots-${section.moduleKey}`}>
              {section.roots.length === 0 ? (
                <div className="rounded-md border border-dashed px-3 py-2 text-sm text-slate-500" data-testid={`home-category-layout-module-empty-${section.moduleKey}`}>L1 kategori bulunamadı.</div>
              ) : section.roots.map((root, rootIndex) => (
                <div key={root.id} className="flex items-center justify-between gap-2 rounded-md border px-3 py-2" data-testid={`home-category-layout-root-${root.id}`}>
                  <div className="text-sm font-semibold" data-testid={`home-category-layout-root-title-${root.id}`}>{root.name || root.slug || root.id}</div>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => handleL1Move(section.moduleKey, rootIndex, -1)}
                      disabled={rootIndex === 0 || section.l1Mode === 'alphabetical'}
                      className="h-8 rounded-md border px-3 text-xs disabled:opacity-50"
                      data-testid={`home-category-layout-root-up-${root.id}`}
                    >
                      Yukarı
                    </button>
                    <button
                      type="button"
                      onClick={() => handleL1Move(section.moduleKey, rootIndex, 1)}
                      disabled={rootIndex === section.roots.length - 1 || section.l1Mode === 'alphabetical'}
                      className="h-8 rounded-md border px-3 text-xs disabled:opacity-50"
                      data-testid={`home-category-layout-root-down-${root.id}`}
                    >
                      Aşağı
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="rounded-xl border bg-white p-4" data-testid="home-category-crud-card">
        <div className="flex flex-wrap items-center justify-between gap-3" data-testid="home-category-crud-header">
          <div>
            <h2 className="text-lg font-semibold" data-testid="home-category-crud-title">Homepage Kategori Yönetimi</h2>
            <p className="text-xs text-slate-500" data-testid="home-category-crud-subtitle">Kategori / alt kategori CRUD, sıralama alanı ve icon SVG yönetimi.</p>
          </div>
          <div className="flex items-center gap-2" data-testid="home-category-crud-top-actions">
            <select
              className="h-10 rounded-md border px-3 text-sm"
              value={crudModule}
              onChange={(event) => setCrudModule(event.target.value)}
              data-testid="home-category-crud-module-filter"
            >
              {MODULES.map((item) => (
                <option key={item.key} value={item.key}>{item.label}</option>
              ))}
            </select>
            <button
              type="button"
              className="h-10 rounded-md bg-slate-900 px-4 text-sm text-white"
              onClick={() => openCreateModal({ moduleKey: crudModule })}
              data-testid="home-category-crud-add-root"
            >
              Ana Kategori Ekle
            </button>
          </div>
        </div>

        {crudStatus ? <div className="mt-3 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700" data-testid="home-category-crud-status">{crudStatus}</div> : null}
        {crudError ? <div className="mt-3 rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700" data-testid="home-category-crud-error">{crudError}</div> : null}

        <div className="mt-4 grid gap-3" data-testid="home-category-crud-list">
          {moduleCrudRows.length === 0 ? (
            <div className="rounded-md border border-dashed px-3 py-4 text-sm text-slate-500" data-testid="home-category-crud-empty">
              Bu modülde kategori bulunamadı.
            </div>
          ) : moduleCrudRows.map((root) => (
            <div key={root.id} className="rounded-lg border" data-testid={`home-category-crud-root-${root.id}`}>
              <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-50 px-3 py-2" data-testid={`home-category-crud-root-header-${root.id}`}>
                <div className="flex items-center gap-2 min-w-0">
                  <CategoryIconPreview iconSvg={root.icon_svg} testId={`home-category-crud-root-icon-${root.id}`} />
                  <div className="min-w-0">
                    <div className="truncate text-sm font-semibold" data-testid={`home-category-crud-root-name-${root.id}`}>{root.name}</div>
                    <div className="text-xs text-slate-500" data-testid={`home-category-crud-root-meta-${root.id}`}>slug: {root.slug} • sort: {root.sort_order}</div>
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-2" data-testid={`home-category-crud-root-actions-${root.id}`}>
                  <button type="button" className="h-8 rounded-md border px-3 text-xs" onClick={() => openCreateModal({ moduleKey: root.module, parentId: root.id })} data-testid={`home-category-crud-add-child-${root.id}`}>Alt Ekle</button>
                  <button type="button" className="h-8 rounded-md border px-3 text-xs" onClick={() => openEditModal(root)} data-testid={`home-category-crud-edit-root-${root.id}`}>Düzenle</button>
                  <button type="button" className="h-8 rounded-md border border-rose-200 px-3 text-xs text-rose-700" onClick={() => handleDeleteCategory(root)} data-testid={`home-category-crud-delete-root-${root.id}`}>Sil</button>
                </div>
              </div>

              <div className="space-y-2 px-3 py-3" data-testid={`home-category-crud-children-${root.id}`}>
                {root.children.length === 0 ? (
                  <div className="rounded-md border border-dashed px-3 py-2 text-xs text-slate-500" data-testid={`home-category-crud-children-empty-${root.id}`}>Alt kategori yok.</div>
                ) : root.children.map((child) => (
                  <div key={child.id} className="flex flex-wrap items-center justify-between gap-2 rounded-md border px-3 py-2" data-testid={`home-category-crud-child-${child.id}`}>
                    <div className="flex items-center gap-2 min-w-0">
                      <CategoryIconPreview iconSvg={child.icon_svg} testId={`home-category-crud-child-icon-${child.id}`} />
                      <div className="min-w-0">
                        <div className="truncate text-sm font-medium" data-testid={`home-category-crud-child-name-${child.id}`}>{child.name}</div>
                        <div className="text-xs text-slate-500" data-testid={`home-category-crud-child-meta-${child.id}`}>slug: {child.slug} • sort: {child.sort_order}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2" data-testid={`home-category-crud-child-actions-${child.id}`}>
                      <button type="button" className="h-8 rounded-md border px-3 text-xs" onClick={() => openEditModal(child)} data-testid={`home-category-crud-edit-child-${child.id}`}>Düzenle</button>
                      <button type="button" className="h-8 rounded-md border border-rose-200 px-3 text-xs text-rose-700" onClick={() => handleDeleteCategory(child)} data-testid={`home-category-crud-delete-child-${child.id}`}>Sil</button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {modalOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/45 p-4" data-testid="home-category-crud-modal-overlay">
          <div className="w-full max-w-xl rounded-xl bg-white p-5 shadow-xl" data-testid="home-category-crud-modal">
            <div className="mb-4 flex items-center justify-between gap-3" data-testid="home-category-crud-modal-header">
              <h3 className="text-lg font-semibold" data-testid="home-category-crud-modal-title">{categoryForm.id ? 'Kategori Düzenle' : 'Yeni Kategori'}</h3>
              <button type="button" className="rounded-md border px-3 py-1 text-xs" onClick={closeModal} data-testid="home-category-crud-modal-close">Kapat</button>
            </div>

            <div className="grid gap-3" data-testid="home-category-crud-modal-form">
              <label className="space-y-1" data-testid="home-category-crud-field-name-wrap">
                <span className="text-xs font-semibold text-slate-600">Kategori Adı</span>
                <input
                  type="text"
                  value={categoryForm.name}
                  onChange={(event) => setCategoryForm((prev) => ({
                    ...prev,
                    name: event.target.value,
                    slug: prev.id ? prev.slug : slugify(event.target.value),
                  }))}
                  className="h-10 w-full rounded-md border px-3 text-sm"
                  data-testid="home-category-crud-field-name"
                />
              </label>

              <label className="space-y-1" data-testid="home-category-crud-field-slug-wrap">
                <span className="text-xs font-semibold text-slate-600">Slug</span>
                <input
                  type="text"
                  value={categoryForm.slug}
                  onChange={(event) => setCategoryForm((prev) => ({ ...prev, slug: slugify(event.target.value) }))}
                  className="h-10 w-full rounded-md border px-3 text-sm"
                  data-testid="home-category-crud-field-slug"
                />
              </label>

              <div className="grid gap-3 md:grid-cols-2">
                <label className="space-y-1" data-testid="home-category-crud-field-module-wrap">
                  <span className="text-xs font-semibold text-slate-600">Modül</span>
                  <select
                    value={categoryForm.module}
                    onChange={(event) => setCategoryForm((prev) => ({ ...prev, module: event.target.value, parent_id: '' }))}
                    className="h-10 w-full rounded-md border px-3 text-sm"
                    data-testid="home-category-crud-field-module"
                  >
                    {MODULES.map((item) => (
                      <option key={item.key} value={item.key}>{item.label}</option>
                    ))}
                  </select>
                </label>

                <label className="space-y-1" data-testid="home-category-crud-field-parent-wrap">
                  <span className="text-xs font-semibold text-slate-600">Üst Kategori (opsiyonel)</span>
                  <select
                    value={categoryForm.parent_id}
                    onChange={(event) => {
                      const parentId = event.target.value;
                      setCategoryForm((prev) => ({
                        ...prev,
                        parent_id: parentId,
                        sort_order: getSiblingNextSortOrder(prev.module, parentId),
                      }));
                    }}
                    className="h-10 w-full rounded-md border px-3 text-sm"
                    data-testid="home-category-crud-field-parent"
                  >
                    <option value="">Ana Kategori</option>
                    {adminCategories
                      .filter((item) => item.module === categoryForm.module && !item.parent_id && item.id !== categoryForm.id)
                      .sort((a, b) => Number(a.sort_order || 0) - Number(b.sort_order || 0))
                      .map((item) => (
                        <option key={item.id} value={item.id}>{item.name}</option>
                      ))}
                  </select>
                </label>
              </div>

              <div className="grid gap-3 md:grid-cols-2">
                <label className="space-y-1" data-testid="home-category-crud-field-sort-wrap">
                  <span className="text-xs font-semibold text-slate-600">Sıralama</span>
                  <input
                    type="number"
                    min={1}
                    value={categoryForm.sort_order}
                    onChange={(event) => setCategoryForm((prev) => ({ ...prev, sort_order: Number(event.target.value) || 1 }))}
                    className="h-10 w-full rounded-md border px-3 text-sm"
                    data-testid="home-category-crud-field-sort"
                  />
                </label>

                <label className="flex items-center gap-2 self-end rounded-md border px-3 py-2" data-testid="home-category-crud-field-active-wrap">
                  <input
                    type="checkbox"
                    checked={categoryForm.active_flag}
                    onChange={(event) => setCategoryForm((prev) => ({ ...prev, active_flag: event.target.checked }))}
                    data-testid="home-category-crud-field-active"
                  />
                  <span className="text-sm">Aktif</span>
                </label>
              </div>

              <label className="space-y-1" data-testid="home-category-crud-field-icon-wrap">
                <span className="text-xs font-semibold text-slate-600">Icon SVG</span>
                <textarea
                  value={categoryForm.icon_svg}
                  onChange={(event) => setCategoryForm((prev) => ({ ...prev, icon_svg: event.target.value }))}
                  rows={4}
                  placeholder="<svg ...>...</svg>"
                  className="w-full rounded-md border px-3 py-2 text-xs"
                  data-testid="home-category-crud-field-icon"
                />
              </label>

              <div className="rounded-md border border-dashed p-3" data-testid="home-category-crud-field-icon-upload-wrap">
                <div className="mb-2 text-xs font-semibold text-slate-600">İkon Dosya Yükle (Ana kategoriler için önerilir)</div>
                <input
                  type="file"
                  accept=".svg,image/svg+xml,image/png,image/jpeg,image/webp"
                  onChange={handleIconFileUpload}
                  className="block w-full text-xs"
                  data-testid="home-category-crud-field-icon-upload"
                />
                <div className="mt-2 text-[11px] text-slate-500" data-testid="home-category-crud-field-icon-upload-help">
                  SVG dosyasını direkt yükleyebilir veya PNG/JPG/WEBP dosyasını otomatik SVG ikona çevirebilirsiniz.
                </div>
                {iconUploadStatus ? <div className="mt-2 text-xs text-emerald-600" data-testid="home-category-crud-field-icon-upload-status">{iconUploadStatus}</div> : null}
                {iconUploadError ? <div className="mt-2 text-xs text-rose-600" data-testid="home-category-crud-field-icon-upload-error">{iconUploadError}</div> : null}
              </div>

              <div className="flex items-center justify-end" data-testid="home-category-crud-icon-clear-wrap">
                <button
                  type="button"
                  className="h-8 rounded-md border px-3 text-xs"
                  onClick={() => setCategoryForm((prev) => ({ ...prev, icon_svg: '' }))}
                  data-testid="home-category-crud-icon-clear"
                >
                  İkonu Temizle
                </button>
              </div>

              <div className="rounded-md border bg-slate-50 p-3" data-testid="home-category-crud-icon-preview-wrap">
                <div className="mb-2 text-xs font-semibold text-slate-600">Icon Önizleme</div>
                <CategoryIconPreview iconSvg={categoryForm.icon_svg} testId="home-category-crud-icon-preview" />
              </div>
            </div>

            <div className="mt-5 flex items-center justify-end gap-2" data-testid="home-category-crud-modal-actions">
              <button type="button" className="h-10 rounded-md border px-4 text-sm" onClick={closeModal} data-testid="home-category-crud-modal-cancel">İptal</button>
              <button
                type="button"
                className="h-10 rounded-md bg-slate-900 px-4 text-sm text-white disabled:opacity-60"
                onClick={handleCategorySave}
                disabled={categorySaving}
                data-testid="home-category-crud-modal-save"
              >
                {categorySaving ? 'Kaydediliyor...' : 'Kaydet'}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
