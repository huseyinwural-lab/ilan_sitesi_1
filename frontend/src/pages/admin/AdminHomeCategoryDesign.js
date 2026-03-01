import React, { useEffect, useMemo, useState } from 'react';
import { useLanguage } from '@/contexts/LanguageContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const MODULES = [
  { key: 'real_estate', label: 'Emlak' },
  { key: 'vehicle', label: 'Vasıta' },
  { key: 'other', label: 'Diğer' },
];

const DEFAULT_CONFIG = {
  column_width: 286,
  l1_initial_limit: 5,
  module_order_mode: 'manual',
  module_order: MODULES.map((item) => item.key),
  module_l1_order_mode: {},
  module_l1_order: {},
};

const LANGUAGE_LOCALE_MAP = {
  tr: 'tr-TR',
  de: 'de-DE',
  fr: 'fr-FR',
};

const clamp = (value, min, max, fallback) => {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return fallback;
  return Math.min(max, Math.max(min, Math.floor(parsed)));
};

const normalizeConfig = (raw) => {
  const source = raw || {};
  const rawModuleOrder = Array.isArray(source.module_order) ? source.module_order : [];
  const moduleOrder = [];
  const seen = new Set();
  rawModuleOrder.forEach((item) => {
    const value = String(item || '').trim();
    if (!value || seen.has(value)) return;
    moduleOrder.push(value);
    seen.add(value);
  });
  MODULES.forEach((item) => {
    if (!moduleOrder.includes(item.key)) moduleOrder.push(item.key);
  });
  const moduleOrderMode = source.module_order_mode === 'alphabetical' ? 'alphabetical' : 'manual';
  const l1Modes = typeof source.module_l1_order_mode === 'object' && source.module_l1_order_mode ? source.module_l1_order_mode : {};
  const moduleL1OrderMode = {};
  Object.entries(l1Modes).forEach(([key, value]) => {
    if (value === 'alphabetical' || value === 'manual') {
      moduleL1OrderMode[key] = value;
    }
  });
  return {
    column_width: clamp(source.column_width, 220, 520, DEFAULT_CONFIG.column_width),
    l1_initial_limit: DEFAULT_CONFIG.l1_initial_limit,
    module_order_mode: moduleOrderMode,
    module_order: moduleOrder,
    module_l1_order_mode: moduleL1OrderMode,
    module_l1_order: typeof source.module_l1_order === 'object' && source.module_l1_order ? source.module_l1_order : {},
  };
};

const moveItem = (list, fromIndex, toIndex) => {
  const next = [...list];
  const [moved] = next.splice(fromIndex, 1);
  next.splice(toIndex, 0, moved);
  return next;
};

const resolveOrderIndex = (orderIndex, node) => {
  if (!node) return null;
  if (orderIndex.has(node.id)) return orderIndex.get(node.id);
  if (node.slug && orderIndex.has(node.slug)) return orderIndex.get(node.slug);
  return null;
};

export default function AdminHomeCategoryDesign() {
  const { language } = useLanguage();
  const [config, setConfig] = useState(DEFAULT_CONFIG);
  const [categoriesByModule, setCategoriesByModule] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');

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
    const l1Mode = config.module_l1_order_mode?.[moduleKey] || 'manual';
    const orderedRoots = [...roots].sort((a, b) => {
      if (l1Mode === 'alphabetical') {
        const nameA = (a.name || a.slug || '').toString();
        const nameB = (b.name || b.slug || '').toString();
        return nameA.localeCompare(nameB, LANGUAGE_LOCALE_MAP[language] || 'tr-TR');
      }
      const ai = resolveOrderIndex(orderIndex, a);
      const bi = resolveOrderIndex(orderIndex, b);
      if (ai !== null || bi !== null) {
        return (ai ?? 9999) - (bi ?? 9999);
      }
      return Number(a.sort_order || 0) - Number(b.sort_order || 0);
    });
    return {
      moduleKey,
      moduleLabel,
      roots: orderedRoots,
      l1Mode,
    };
  }), [categoriesByModule, config.module_l1_order, config.module_l1_order_mode, language, moduleLabelMap, moduleOrder]);

  const fetchConfig = async () => {
    try {
      const res = await fetch(`${API}/admin/site/home-category-layout?country=${countryCode}`, { headers: authHeader });
      const payload = await res.json().catch(() => ({}));
      setConfig(normalizeConfig(payload?.config));
    } catch (_err) {
      setConfig(DEFAULT_CONFIG);
    }
  };

  const fetchCategories = async () => {
    try {
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
    } catch (_err) {
      setCategoriesByModule({});
    }
  };

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      await Promise.all([fetchConfig(), fetchCategories()]);
      setLoading(false);
    };
    init();
  }, []);

  const handleWidthChange = (value) => {
    setConfig((prev) => ({
      ...prev,
      column_width: clamp(value, 220, 520, prev.column_width),
    }));
  };

  const handleModuleMove = (index, direction) => {
    if (config.module_order_mode === 'alphabetical') return;
    setConfig((prev) => {
      const order = moduleOrder;
      const nextIndex = index + direction;
      if (nextIndex < 0 || nextIndex >= order.length) return prev;
      return {
        ...prev,
        module_order: moveItem(order, index, nextIndex),
      };
    });
  };

  const handleModuleOrderMode = (value) => {
    setConfig((prev) => ({
      ...prev,
      module_order_mode: value === 'alphabetical' ? 'alphabetical' : 'manual',
    }));
  };

  const handleL1ModeChange = (moduleKey, value) => {
    setConfig((prev) => ({
      ...prev,
      module_l1_order_mode: {
        ...prev.module_l1_order_mode,
        [moduleKey]: value === 'alphabetical' ? 'alphabetical' : 'manual',
      },
    }));
  };

  const handleL1Move = (moduleKey, index, direction) => {
    if (config.module_l1_order_mode?.[moduleKey] === 'alphabetical') return;
    setConfig((prev) => {
      const roots = (categoriesByModule[moduleKey] || []).filter((item) => !item.parent_id);
      const orderList = Array.isArray(prev.module_l1_order?.[moduleKey]) ? prev.module_l1_order[moduleKey] : [];
      const orderIndex = new Map(orderList.map((item, idx) => [item, idx]));
      const orderedRoots = [...roots].sort((a, b) => {
        const ai = resolveOrderIndex(orderIndex, a);
        const bi = resolveOrderIndex(orderIndex, b);
        if (ai !== null || bi !== null) {
          return (ai ?? 9999) - (bi ?? 9999);
        }
        return Number(a.sort_order || 0) - Number(b.sort_order || 0);
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

  const handleSave = async () => {
    setSaving(true);
    setStatus('');
    setError('');
    try {
      const res = await fetch(`${API}/admin/site/home-category-layout`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...authHeader,
        },
        body: JSON.stringify({
          config,
          country_code: countryCode,
        }),
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(payload?.detail?.message || payload?.detail || payload?.message || 'Kaydetme başarısız');
      }
      setConfig(normalizeConfig(payload?.config || config));
      setStatus('Kaydedildi.');
    } catch (err) {
      setError(err?.message || 'Kaydetme başarısız');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="home-category-design-page">
      <div className="flex flex-wrap items-center justify-between gap-4" data-testid="home-category-design-header">
        <div>
          <h1 className="text-2xl font-semibold" data-testid="home-category-design-title">Ana Site Kategorisi</h1>
          <p className="text-sm text-slate-600" data-testid="home-category-design-subtitle">
            Ana sayfadaki kategori kolonunun sıralaması ve genişliği buradan yönetilir. Modül altında ilk 5 L1 gösterilir.
          </p>
        </div>
        <div className="flex items-center gap-2" data-testid="home-category-design-actions">
          <button
            type="button"
            onClick={() => {
              fetchConfig();
              fetchCategories();
            }}
            className="h-10 rounded-md border px-4 text-sm"
            data-testid="home-category-design-refresh"
          >
            Yenile
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            className="h-10 rounded-md bg-slate-900 px-5 text-sm text-white disabled:opacity-60"
            data-testid="home-category-design-save"
          >
            {saving ? 'Kaydediliyor...' : 'Kaydet'}
          </button>
        </div>
      </div>

      {status ? (
        <div className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700" data-testid="home-category-design-status">
          {status}
        </div>
      ) : null}
      {error ? (
        <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-600" data-testid="home-category-design-error">
          {error}
        </div>
      ) : null}

      <div className="rounded-xl border bg-white p-4" data-testid="home-category-width-card">
        <div className="flex flex-wrap items-center justify-between gap-4" data-testid="home-category-width-header">
          <div>
            <div className="text-sm font-semibold" data-testid="home-category-width-title">Kolon Genişliği</div>
            <div className="text-xs text-slate-500" data-testid="home-category-width-hint">220 - 520 px aralığında ayarlanabilir.</div>
          </div>
          <div className="text-sm font-semibold" data-testid="home-category-width-value">{config.column_width}px</div>
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-3" data-testid="home-category-width-controls">
          <input
            type="range"
            min={220}
            max={520}
            value={config.column_width}
            onChange={(event) => handleWidthChange(event.target.value)}
            className="w-full max-w-md"
            data-testid="home-category-width-range"
          />
          <input
            type="number"
            min={220}
            max={520}
            value={config.column_width}
            onChange={(event) => handleWidthChange(event.target.value)}
            className="h-10 w-24 rounded-md border px-2 text-sm"
            data-testid="home-category-width-input"
          />
        </div>
      </div>

      <div className="rounded-xl border bg-white p-4" data-testid="home-category-module-order-card">
        <div className="flex flex-wrap items-center justify-between gap-4" data-testid="home-category-module-order-header">
          <div>
            <div className="text-sm font-semibold" data-testid="home-category-module-order-title">Modül Sıralama Modu (L0)</div>
            <div className="text-xs text-slate-500" data-testid="home-category-module-order-hint">L0 modüllerini manuel ya da alfabetik sıralayın.</div>
          </div>
          <select
            className="h-10 rounded-md border px-3 text-sm"
            value={config.module_order_mode}
            onChange={(event) => handleModuleOrderMode(event.target.value)}
            data-testid="home-category-module-order-select"
          >
            <option value="manual">Manuel</option>
            <option value="alphabetical">Alfabetik</option>
          </select>
        </div>
      </div>

      <div className="grid gap-4" data-testid="home-category-module-list">
        {loading ? (
          <div className="rounded-md border bg-white p-4 text-sm text-slate-600" data-testid="home-category-loading">Yükleniyor...</div>
        ) : moduleSections.map((section, index) => (
          <div key={section.moduleKey} className="rounded-xl border bg-white p-4" data-testid={`home-category-module-${section.moduleKey}`}>
            <div className="flex flex-wrap items-center justify-between gap-3" data-testid={`home-category-module-header-${section.moduleKey}`}>
              <div>
                <div className="text-xs text-slate-500" data-testid={`home-category-module-label-${section.moduleKey}`}>Modül</div>
                <div className="text-lg font-semibold" data-testid={`home-category-module-title-${section.moduleKey}`}>{section.moduleLabel}</div>
              </div>
              <div className="flex flex-wrap items-center gap-2" data-testid={`home-category-module-actions-${section.moduleKey}`}>
                <select
                  className="h-9 rounded-md border px-3 text-sm"
                  value={section.l1Mode}
                  onChange={(event) => handleL1ModeChange(section.moduleKey, event.target.value)}
                  data-testid={`home-category-l1-mode-${section.moduleKey}`}
                >
                  <option value="manual">L1 Manuel</option>
                  <option value="alphabetical">L1 Alfabetik</option>
                </select>
                <button
                  type="button"
                  onClick={() => handleModuleMove(index, -1)}
                  disabled={index === 0 || config.module_order_mode === 'alphabetical'}
                  className="h-9 rounded-md border px-3 text-sm disabled:opacity-50"
                  data-testid={`home-category-module-up-${section.moduleKey}`}
                >
                  Yukarı
                </button>
                <button
                  type="button"
                  onClick={() => handleModuleMove(index, 1)}
                  disabled={index === moduleSections.length - 1 || config.module_order_mode === 'alphabetical'}
                  className="h-9 rounded-md border px-3 text-sm disabled:opacity-50"
                  data-testid={`home-category-module-down-${section.moduleKey}`}
                >
                  Aşağı
                </button>
              </div>
            </div>

            {section.l1Mode === 'alphabetical' ? (
              <div className="mt-2 text-xs text-slate-500" data-testid={`home-category-module-alpha-hint-${section.moduleKey}`}>
                L1 listesi alfabetik sıralanıyor. Manuel butonlar devre dışı.
              </div>
            ) : null}

            <div className="mt-4 space-y-2" data-testid={`home-category-module-rows-${section.moduleKey}`}>
              {section.roots.length === 0 ? (
                <div className="rounded-md border border-dashed px-3 py-2 text-sm text-slate-500" data-testid={`home-category-module-empty-${section.moduleKey}`}>
                  Bu modül altında L1 kategori bulunamadı.
                </div>
              ) : section.roots.map((root, rootIndex) => (
                <div
                  key={root.id}
                  className="flex flex-wrap items-center justify-between gap-3 rounded-md border px-3 py-2"
                  data-testid={`home-category-l1-${section.moduleKey}-${root.id}`}
                >
                  <div>
                    <div className="text-xs text-slate-500">L1</div>
                    <div className="text-sm font-semibold" data-testid={`home-category-l1-title-${section.moduleKey}-${root.id}`}>{root.name || root.slug || root.id}</div>
                  </div>
                  <div className="flex items-center gap-2" data-testid={`home-category-l1-actions-${section.moduleKey}-${root.id}`}>
                    <button
                      type="button"
                      onClick={() => handleL1Move(section.moduleKey, rootIndex, -1)}
                      disabled={rootIndex === 0}
                      className="h-8 rounded-md border px-3 text-xs disabled:opacity-50"
                      data-testid={`home-category-l1-up-${section.moduleKey}-${root.id}`}
                    >
                      Yukarı
                    </button>
                    <button
                      type="button"
                      onClick={() => handleL1Move(section.moduleKey, rootIndex, 1)}
                      disabled={rootIndex === section.roots.length - 1}
                      className="h-8 rounded-md border px-3 text-xs disabled:opacity-50"
                      data-testid={`home-category-l1-down-${section.moduleKey}-${root.id}`}
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
    </div>
  );
}
