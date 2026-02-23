import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { CheckCircle2, Search } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const MODULE_OPTIONS = [
  { key: 'vehicle', label: 'Vasıta' },
  { key: 'real_estate', label: 'Emlak' },
  { key: 'machinery', label: 'Makine' },
  { key: 'services', label: 'Hizmet' },
  { key: 'jobs', label: 'İş' },
];

const ListingCategorySelect = () => {
  const navigate = useNavigate();
  const [columns, setColumns] = useState([]);
  const [selectedPath, setSelectedPath] = useState([]);
  const [loadingColumn, setLoadingColumn] = useState(null);
  const [pageLoading, setPageLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectionComplete, setSelectionComplete] = useState(false);
  const [activeCategory, setActiveCategory] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [selectedModule, setSelectedModule] = useState('');
  const [recentCategory, setRecentCategory] = useState(null);
  const [recentLoading, setRecentLoading] = useState(true);
  const [recentError, setRecentError] = useState('');

  const country = useMemo(() => (localStorage.getItem('selected_country') || 'DE').toUpperCase(), []);

  const selectedModuleLabel = useMemo(() => {
    const match = MODULE_OPTIONS.find((item) => item.key === selectedModule);
    return match ? match.label : '';
  }, [selectedModule]);

  const recentStorageKey = 'ilan_ver_recent_category';
  const recentPathKey = 'ilan_ver_recent_path';

  const moduleLabelByKey = useCallback((moduleKey) => {
    const match = MODULE_OPTIONS.find((item) => item.key === moduleKey);
    return match ? match.label : moduleKey;
  }, []);

  const persistRecentToStorage = useCallback((recent) => {
    if (!recent?.category?.id) return;
    localStorage.setItem(recentStorageKey, JSON.stringify({
      category: recent.category,
      module: recent.module,
      country: recent.country,
      updated_at: recent.updated_at || null,
    }));
    localStorage.setItem(recentPathKey, JSON.stringify(recent.path || []));
  }, []);

  const readRecentFromStorage = useCallback(() => {
    const stored = localStorage.getItem(recentStorageKey);
    if (!stored) return null;
    try {
      const parsed = JSON.parse(stored);
      const storedPath = localStorage.getItem(recentPathKey);
      let parsedPath = [];
      if (storedPath) {
        try {
          parsedPath = JSON.parse(storedPath) || [];
        } catch (err) {
          parsedPath = [];
        }
      }
      return {
        category: parsed.category,
        module: parsed.module,
        country: parsed.country,
        updated_at: parsed.updated_at,
        path: parsedPath,
      };
    } catch (err) {
      return null;
    }
  }, []);

  const trackEvent = useCallback(async (eventName, metadata = {}) => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;
      await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/analytics/events`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          event_name: eventName,
          metadata: {
            country,
            ...metadata,
          },
        }),
      });
    } catch (err) {
      console.error('Analytics event error', err);
    }
  }, [country]);

  const fetchChildren = useCallback(async (parentId, moduleKey) => {
    if (!moduleKey) return [];
    const params = new URLSearchParams({ country, module: moduleKey });
    if (parentId) params.append('parent_id', parentId);
    const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/categories/children?${params.toString()}`);
    if (!res.ok) return [];
    const data = await res.json();
    return data || [];
  }, [country]);

  const loadRootCategories = useCallback(async () => {
    if (!selectedModule) {
      setColumns([]);
      setPageLoading(false);
      return;
    }
    setPageLoading(true);
    setError('');
    try {
      const roots = await fetchChildren(null, selectedModule);
      setColumns([{ parentId: null, items: roots, selectedId: null }]);
    } catch (err) {
      setError('Kategoriler yüklenemedi.');
    } finally {
      setPageLoading(false);
    }
  }, [fetchChildren, selectedModule]);

  useEffect(() => {
    loadRootCategories();
  }, [loadRootCategories]);

  const fetchRecentCategory = useCallback(async () => {
    setRecentLoading(true);
    setRecentError('');
    const token = localStorage.getItem('access_token');
    if (!token) {
      setRecentCategory(readRecentFromStorage());
      setRecentLoading(false);
      return;
    }
    try {
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/account/recent-category`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (!res.ok) {
        const fallback = readRecentFromStorage();
        setRecentCategory(fallback);
        return;
      }
      const data = await res.json();
      if (data?.recent) {
        setRecentCategory(data.recent);
        persistRecentToStorage(data.recent);
      } else {
        setRecentCategory(null);
      }
    } catch (err) {
      const fallback = readRecentFromStorage();
      setRecentCategory(fallback);
      setRecentError('Son seçiminiz yüklenemedi.');
    } finally {
      setRecentLoading(false);
    }
  }, [persistRecentToStorage, readRecentFromStorage]);

  useEffect(() => {
    fetchRecentCategory();
  }, [fetchRecentCategory]);

  const breadcrumbLabel = selectedPath.length
    ? selectedPath.map((item) => item.name).join(' > ')
    : selectedModuleLabel
      ? `${selectedModuleLabel} seçildi, kategori bekleniyor`
      : 'Modül seçimi bekleniyor';

  const handleSelectModule = (moduleKey) => {
    setSelectedModule(moduleKey);
    setColumns([]);
    setSelectedPath([]);
    setSelectionComplete(false);
    setActiveCategory(null);
    setSearchTerm('');
    setSearchResults([]);
    trackEvent('step_select_module', { module: moduleKey });
  };

  const handleSelectCategory = async (columnIndex, category) => {
    setError('');
    const nextPath = [...selectedPath.slice(0, columnIndex), category];
    const trimmedColumns = columns.slice(0, columnIndex + 1).map((col, idx) => ({
      ...col,
      selectedId: idx === columnIndex ? category.id : col.selectedId,
    }));
    setSelectedPath(nextPath);
    setSelectionComplete(false);
    setActiveCategory(null);
    setColumns(trimmedColumns);

    trackEvent(`step_select_category_L${columnIndex + 1}`, {
      module: selectedModule,
      category_id: category.id,
      category_name: category.name,
      level: columnIndex + 1,
      path: nextPath.map((item) => item.name),
    });

    setLoadingColumn(columnIndex + 1);
    const children = await fetchChildren(category.id, selectedModule);
    setLoadingColumn(null);

    if (children.length > 0) {
      setColumns([...trimmedColumns, { parentId: category.id, items: children, selectedId: null }]);
    } else {
      setSelectionComplete(true);
      setActiveCategory(category);
    }
  };

  const hydratePathFromSearch = async (path) => {
    if (!path || path.length === 0) return;
    const nextColumns = [];
    let parentId = null;
    for (let index = 0; index < path.length; index += 1) {
      const items = await fetchChildren(parentId, selectedModule);
      nextColumns.push({ parentId, items, selectedId: path[index].id });
      parentId = path[index].id;
    }
    const children = await fetchChildren(parentId, selectedModule);
    if (children.length > 0) {
      nextColumns.push({ parentId, items: children, selectedId: null });
    }
    setColumns(nextColumns);
    setSelectedPath(path);
    setSelectionComplete(children.length === 0);
    setActiveCategory(children.length === 0 ? path[path.length - 1] : null);
  };

  useEffect(() => {
    if (!selectedModule) {
      setSearchResults([]);
      setSearchLoading(false);
      return undefined;
    }
    if (!searchTerm.trim()) {
      setSearchResults([]);
      setSearchLoading(false);
      return undefined;
    }
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      try {
        setSearchLoading(true);
        const params = new URLSearchParams({ country, query: searchTerm.trim(), module: selectedModule });
        const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/categories/search?${params.toString()}`, {
          signal: controller.signal,
        });
        if (!res.ok) {
          setSearchResults([]);
          return;
        }
        const data = await res.json();
        setSearchResults(data?.items || []);
      } catch (err) {
        if (!controller.signal.aborted) {
          setSearchResults([]);
        }
      } finally {
        if (!controller.signal.aborted) {
          setSearchLoading(false);
        }
      }
    }, 350);

    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [searchTerm, country, selectedModule]);

  const handleSearchSelect = async (item) => {
    const path = (item?.path || []).map((entry) => ({
      id: entry.id,
      name: entry.name,
      slug: entry.slug,
    }));
    setSearchTerm('');
    setSearchResults([]);
    if (path.length) {
      trackEvent(`step_select_category_L${path.length}`, {
        module: selectedModule,
        category_id: path[path.length - 1].id,
        category_name: path[path.length - 1].name,
        level: path.length,
        path: path.map((p) => p.name),
        source: 'search',
      });
    }
    await hydratePathFromSearch(path);
  };

  const persistWizardSelection = useCallback((category, path, moduleKey, moduleLabel) => {
    if (!category?.id || !moduleKey) return;
    localStorage.setItem('ilan_ver_category', JSON.stringify({ ...category, module: moduleKey }));
    localStorage.setItem('ilan_ver_category_path', JSON.stringify(path || []));
    localStorage.setItem('ilan_ver_module', moduleKey);
    localStorage.setItem('ilan_ver_module_label', moduleLabel || moduleKey);
  }, []);

  const saveRecentCategory = useCallback(async (category, path, moduleKey) => {
    if (!category?.id || !moduleKey) return;
    const token = localStorage.getItem('access_token');
    if (!token) return;
    try {
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/account/recent-category`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          category_id: category.id,
          module: moduleKey,
          country,
          path: path || [],
          category_name: category.name,
        }),
      });
      if (!res.ok) return;
      const data = await res.json();
      if (data?.recent) {
        setRecentCategory(data.recent);
        persistRecentToStorage(data.recent);
      }
    } catch (err) {
      // ignore
    }
  }, [country, persistRecentToStorage]);

  const handleContinue = async () => {
    if (!activeCategory || !selectedModule) return;
    const nextPath = selectedPath.length ? selectedPath : [activeCategory];
    const localRecent = {
      category: activeCategory,
      module: selectedModule,
      country,
      path: nextPath,
    };
    persistRecentToStorage(localRecent);
    persistWizardSelection(activeCategory, nextPath, selectedModule, selectedModuleLabel || selectedModule);
    await saveRecentCategory(activeCategory, nextPath, selectedModule);
    const targetRoute = selectedModule === 'vehicle' ? '/account/create/vehicle-wizard' : '/account/create/listing-wizard';
    navigate(targetRoute);
  };

  const handleRecentContinue = () => {
    if (!recentCategory?.category?.id) return;
    const moduleKey = recentCategory.module;
    const path = recentCategory.path || [];
    persistWizardSelection(recentCategory.category, path, moduleKey, moduleLabelByKey(moduleKey));
    if (recentCategory.country) {
      localStorage.setItem('selected_country', recentCategory.country);
    }
    const targetRoute = moduleKey === 'vehicle' ? '/account/create/vehicle-wizard' : '/account/create/listing-wizard';
    navigate(targetRoute);
  };

  return (
    <div className="mx-auto max-w-6xl space-y-6" data-testid="ilan-ver-category-page">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900" data-testid="ilan-ver-title">Adım Adım Kategori Seç</h1>
          <p className="text-sm text-slate-600" data-testid="ilan-ver-subtitle">
            Önce modül seçin, ardından kategoriyi adım adım seçin.
          </p>
        </div>
        <div className="rounded-full bg-emerald-50 px-4 py-2 text-xs font-semibold text-emerald-700" data-testid="ilan-ver-step-label">
          Modül + Kategori
        </div>
      </div>

      <div className="rounded-xl border bg-white p-4" data-testid="ilan-ver-module-panel">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-semibold text-slate-900" data-testid="ilan-ver-module-title">Modül Seçimi</div>
            <div className="text-xs text-slate-500" data-testid="ilan-ver-module-subtitle">İlan vermek istediğiniz modülü seçin.</div>
          </div>
          {selectedModuleLabel && (
            <span className="text-xs font-semibold text-blue-600" data-testid="ilan-ver-module-selected">{selectedModuleLabel}</span>
          )}
        </div>
        <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-5" data-testid="ilan-ver-module-grid">
          {MODULE_OPTIONS.map((item) => (
            <button
              key={item.key}
              type="button"
              onClick={() => handleSelectModule(item.key)}
              className={`rounded-lg border px-3 py-2 text-sm text-left transition ${
                selectedModule === item.key ? 'border-blue-600 bg-blue-50 text-blue-700' : 'border-slate-200 bg-white hover:border-blue-400'
              }`}
              data-testid={`ilan-ver-module-card-${item.key}`}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      <div className="rounded-xl border bg-white p-4" data-testid="ilan-ver-breadcrumb-panel">
        <div className="text-xs uppercase tracking-[0.2em] text-slate-400" data-testid="ilan-ver-breadcrumb-label">Seçim yolu</div>
        <div className="mt-2 text-sm font-semibold text-slate-900" data-testid="ilan-ver-breadcrumb">{breadcrumbLabel}</div>
      </div>

      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700" data-testid="ilan-ver-error">
          {error}
        </div>
      )}

      <div className="rounded-xl border bg-white p-4" data-testid="ilan-ver-columns-wrapper">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-semibold text-slate-900">Kategori Sütunları</div>
            <div className="text-xs text-slate-500">Seçtikçe yeni sütunlar sağa açılır.</div>
          </div>
          {pageLoading && (
            <div className="text-xs text-slate-500" data-testid="ilan-ver-columns-loading">Yükleniyor...</div>
          )}
        </div>

        {!selectedModule && !pageLoading ? (
          <div className="mt-4 text-sm text-slate-500" data-testid="ilan-ver-columns-empty">Önce modül seçiniz.</div>
        ) : (
          <div className="mt-4 flex gap-4 overflow-x-auto pb-2" data-testid="ilan-ver-columns">
            {columns.length === 0 && !pageLoading ? (
              <div className="text-sm text-slate-500" data-testid="ilan-ver-columns-empty">Kategori bulunamadı.</div>
            ) : (
              columns.map((column, columnIndex) => (
                <div
                  key={`column-${column.parentId || 'root'}-${columnIndex}`}
                  className="min-w-[220px] rounded-lg border bg-slate-50 p-3"
                  data-testid={`ilan-ver-column-${columnIndex}`}
                >
                  <div className="flex items-center justify-between">
                    <div className="text-sm font-semibold text-slate-800" data-testid={`ilan-ver-column-title-${columnIndex}`}>
                      Kategori {columnIndex + 1}
                    </div>
                    {loadingColumn === columnIndex && (
                      <span className="text-xs text-slate-500" data-testid={`ilan-ver-column-loading-${columnIndex}`}>Yükleniyor...</span>
                    )}
                  </div>
                  <div className="mt-3 space-y-2 max-h-[360px] overflow-y-auto" data-testid={`ilan-ver-column-items-${columnIndex}`}>
                    {column.items.length === 0 ? (
                      <div className="text-xs text-slate-500" data-testid={`ilan-ver-column-empty-${columnIndex}`}>
                        Bu seviyede kategori yok.
                      </div>
                    ) : (
                      column.items.map((item) => (
                        <button
                          key={item.id}
                          type="button"
                          onClick={() => handleSelectCategory(columnIndex, item)}
                          className={`w-full rounded-md border px-3 py-2 text-left text-sm transition hover:border-blue-500 hover:bg-blue-50 ${
                            column.selectedId === item.id ? 'border-blue-600 bg-blue-50 text-blue-700' : 'border-slate-200 bg-white'
                          }`}
                          data-testid={`ilan-ver-column-item-${columnIndex}-${item.id}`}
                        >
                          {item.name}
                        </button>
                      ))
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {selectionComplete && activeCategory && (
          <div
            className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3"
            data-testid="ilan-ver-complete"
          >
            <div className="flex items-center gap-2 text-sm font-semibold text-emerald-700" data-testid="ilan-ver-complete-message">
              <CheckCircle2 size={18} />
              Kategori seçimi tamamlanmıştır: {activeCategory.name}
            </div>
            <button
              type="button"
              onClick={handleContinue}
              className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-semibold text-white"
              data-testid="ilan-ver-continue"
            >
              Devam
            </button>
          </div>
        )}
      </div>

      <div className="rounded-xl border bg-white p-4" data-testid="ilan-ver-search-panel">
        <div className="text-sm font-semibold text-slate-900">Kelime ile Arayarak Kategori Seç</div>
        <p className="text-xs text-slate-500">Örn: Daire</p>
        {!selectedModule && (
          <p className="mt-2 text-xs text-slate-500" data-testid="ilan-ver-search-disabled">Arama için önce modül seçiniz.</p>
        )}
        <div className="relative mt-3">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
          <input
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
            placeholder="Lütfen ilanınızı tanımlayan kelimelerle arama yapınız"
            disabled={!selectedModule}
            className="w-full rounded-lg border border-slate-200 bg-white py-2 pl-9 pr-3 text-sm focus:border-blue-500 focus:outline-none disabled:bg-slate-100"
            data-testid="ilan-ver-search-input"
          />
        </div>
        {searchLoading && (
          <div className="mt-2 text-xs text-slate-500" data-testid="ilan-ver-search-loading">Aranıyor...</div>
        )}
        {searchResults.length > 0 && (
          <div className="mt-3 space-y-2" data-testid="ilan-ver-search-results">
            {searchResults.map((item) => (
              <button
                key={item.category.id}
                type="button"
                onClick={() => handleSearchSelect(item)}
                className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-left text-sm hover:border-blue-500 hover:bg-blue-50"
                data-testid={`ilan-ver-search-result-${item.category.id}`}
              >
                <div className="font-semibold text-slate-800">{item.category.name}</div>
                <div className="text-xs text-slate-500">{(item.path || []).map((p) => p.name).join(' > ')}</div>
              </button>
            ))}
          </div>
        )}
        {!searchLoading && searchTerm.trim().length > 1 && searchResults.length === 0 && (
          <div className="mt-2 text-xs text-slate-500" data-testid="ilan-ver-search-empty">Sonuç bulunamadı.</div>
        )}
      </div>
    </div>
  );
};

export default ListingCategorySelect;
