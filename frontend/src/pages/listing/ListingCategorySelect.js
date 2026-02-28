import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { CheckCircle2, Search } from 'lucide-react';
import { useNavigate, useSearchParams } from 'react-router-dom';

const MODULE_OPTIONS = [
  { key: 'vehicle', label: 'Vasıta' },
  { key: 'real_estate', label: 'Emlak' },
  { key: 'other', label: 'Diğer' },
];

const ListingCategorySelect = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
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
  const [columnErrors, setColumnErrors] = useState({});
  const [isMobileView, setIsMobileView] = useState(() => window.innerWidth < 768);
  const [mobileColumnIndex, setMobileColumnIndex] = useState(0);
  const childrenCacheRef = useRef(new Map());

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

  const updateUrlState = useCallback((moduleKey, pathIds = []) => {
    const params = new URLSearchParams();
    if (moduleKey) params.set('module', moduleKey);
    if (pathIds.length) params.set('path', pathIds.join(','));
    setSearchParams(params);
  }, [setSearchParams]);

  const getCacheKey = useCallback((parentId, moduleKey) => `${moduleKey}::${parentId || 'root'}`, []);

  const fetchChildren = useCallback(async (parentId, moduleKey, options = {}) => {
    const { force = false } = options;
    if (!moduleKey) return [];
    const cacheKey = getCacheKey(parentId, moduleKey);
    if (!force && childrenCacheRef.current.has(cacheKey)) {
      return childrenCacheRef.current.get(cacheKey) || [];
    }

    const params = new URLSearchParams({ country, module: moduleKey });
    if (parentId) params.append('parent_id', parentId);
    const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/categories/children?${params.toString()}`);
    if (!res.ok) {
      throw new Error('CATEGORY_CHILD_FETCH_FAILED');
    }
    const data = await res.json();
    const normalized = Array.isArray(data) ? data : [];
    childrenCacheRef.current.set(cacheKey, normalized);
    return normalized;
  }, [country, getCacheKey]);

  const loadRootCategories = useCallback(async (moduleKey) => {
    if (!moduleKey) {
      setColumns([]);
      setPageLoading(false);
      setColumnErrors({});
      return;
    }
    setPageLoading(true);
    setError('');
    setColumnErrors({});
    try {
      const roots = await fetchChildren(null, moduleKey);
      if (!roots.length) {
        setColumns([]);
        setSelectionComplete(false);
        setActiveCategory(null);
        return;
      }
      setColumns([{ parentId: null, items: roots, selectedId: null }]);
      setMobileColumnIndex(0);
    } catch (err) {
      setError('Kategoriler yüklenemedi.');
    } finally {
      setPageLoading(false);
    }
  }, [fetchChildren]);

  const hydratePathFromIds = useCallback(async (pathIds, moduleKey) => {
    if (!moduleKey || pathIds.length === 0) return;
    setPageLoading(true);
    setError('');
    setColumnErrors({});
    try {
      const nextColumns = [];
      const nextPath = [];
      let parentId = null;
      for (let index = 0; index < pathIds.length; index += 1) {
        const items = await fetchChildren(parentId, moduleKey);
        if (!items.length) break;
        const match = items.find((item) => item.id === pathIds[index]);
        if (!match) break;
        nextColumns.push({ parentId, items, selectedId: match.id });
        nextPath.push(match);
        parentId = match.id;
      }
      if (nextPath.length === 0) {
        await loadRootCategories(moduleKey);
        setSelectedPath([]);
        setSelectionComplete(false);
        setActiveCategory(null);
        return;
      }
      const children = await fetchChildren(parentId, moduleKey);
      if (children.length > 0) {
        nextColumns.push({ parentId, items: children, selectedId: null });
      }
      setColumns(nextColumns);
      setSelectedPath(nextPath);
      setSelectionComplete(children.length === 0);
      setActiveCategory(children.length === 0 ? nextPath[nextPath.length - 1] : null);
      setMobileColumnIndex(Math.min(nextPath.length, Math.max(nextColumns.length - 1, 0)));
    } catch (err) {
      setError('Kategori yolu yüklenemedi.');
    } finally {
      setPageLoading(false);
    }
  }, [fetchChildren, loadRootCategories]);

  useEffect(() => {
    const moduleParam = searchParams.get('module') || '';
    const pathParam = searchParams.get('path') || '';
    const pathIds = pathParam ? pathParam.split(',').filter(Boolean) : [];
    const selectedPathKey = selectedPath.map((item) => item.id).join(',');
    if (!moduleParam) {
      setSelectedModule('');
      setSelectedPath([]);
      setColumns([]);
      setSelectionComplete(false);
      setActiveCategory(null);
      setLoadingColumn(null);
      setColumnErrors({});
      return;
    }
    if (moduleParam === selectedModule && selectedPathKey === pathParam && columns.length > 0) {
      return;
    }
    setLoadingColumn(null);
    setColumnErrors({});
    setSelectedModule(moduleParam);
    setSelectionComplete(false);
    setActiveCategory(null);
    setSearchTerm('');
    setSearchResults([]);
    if (pathIds.length > 0) {
      hydratePathFromIds(pathIds, moduleParam);
    } else {
      setSelectedPath([]);
      setMobileColumnIndex(0);
      loadRootCategories(moduleParam);
    }
  }, [hydratePathFromIds, loadRootCategories, searchParams]);

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

  useEffect(() => {
    const onResize = () => setIsMobileView(window.innerWidth < 768);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  useEffect(() => {
    childrenCacheRef.current.clear();
  }, [country]);

  useEffect(() => {
    if (!columns.length) {
      setMobileColumnIndex(0);
      return;
    }
    setMobileColumnIndex((prev) => Math.min(prev, columns.length - 1));
  }, [columns]);

  const breadcrumbLabel = selectedPath.length
    ? selectedPath.map((item) => item.name).join(' > ')
    : selectedModuleLabel
      ? `${selectedModuleLabel} seçildi, kategori bekleniyor`
      : 'Modül seçimi bekleniyor';

  const recentBreadcrumb = useMemo(() => {
    if (!recentCategory?.path?.length) return '';
    return recentCategory.path.map((item) => item.name).join(' > ');
  }, [recentCategory]);

  const recentModuleLabel = useMemo(() => {
    if (!recentCategory?.module) return '';
    return moduleLabelByKey(recentCategory.module);
  }, [moduleLabelByKey, recentCategory]);

  const handleSelectModule = (moduleKey) => {
    autoAdvanceRef.current = false;
    setAutoAdvanceActive(false);
    setSelectedModule(moduleKey);
    setColumns([]);
    setSelectedPath([]);
    setSelectionComplete(false);
    setActiveCategory(null);
    setSearchTerm('');
    setSearchResults([]);
    updateUrlState(moduleKey, []);
    trackEvent('step_select_module', { module: moduleKey });
  };

  const handleSelectCategory = async (columnIndex, category) => {
    setError('');
    autoAdvanceRef.current = false;
    setAutoAdvanceActive(false);
    const nextPath = [...selectedPath.slice(0, columnIndex), category];
    const trimmedColumns = columns.slice(0, columnIndex + 1).map((col, idx) => ({
      ...col,
      selectedId: idx === columnIndex ? category.id : col.selectedId,
    }));
    setSelectedPath(nextPath);
    setSelectionComplete(false);
    setActiveCategory(null);
    setColumns(trimmedColumns);

    const nextPathIds = nextPath.map((item) => item.id);
    updateUrlState(selectedModule, nextPathIds);

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
      autoAdvanceRef.current = false;
      handleContinue(category, nextPath, { auto: true });
    }
  };

  const hydratePathFromSearch = async (path) => {
    if (!path || path.length === 0) return;
    const pathIds = path.map((entry) => entry.id).filter(Boolean);
    updateUrlState(selectedModule, pathIds);
    await hydratePathFromIds(pathIds, selectedModule);
    autoAdvanceRef.current = true;
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

  const handleContinue = useCallback(async (categoryOverride, pathOverride, options = {}) => {
    const { auto = false } = options;
    const category = categoryOverride || activeCategory;
    const path = pathOverride && pathOverride.length ? pathOverride : selectedPath.length ? selectedPath : [category].filter(Boolean);
    if (!category || !selectedModule) return;
    if (auto) {
      setAutoAdvanceActive(true);
    }
    const localRecent = {
      category,
      module: selectedModule,
      country,
      path,
    };
    persistRecentToStorage(localRecent);
    persistWizardSelection(category, path, selectedModule, selectedModuleLabel || selectedModule);
    localStorage.setItem('ilan_ver_force_core_step', 'true');
    if (selectedModule === 'vehicle') {
      localStorage.removeItem('ilan_ver_vehicle_selection');
      localStorage.removeItem('ilan_ver_vehicle_trim_id');
      localStorage.removeItem('ilan_ver_manual_trim_flag');
      localStorage.removeItem('ilan_ver_manual_trim');
    }
    await saveRecentCategory(category, path, selectedModule);
    const targetRoute = selectedModule === 'vehicle' ? '/ilan-ver/arac-sec' : '/ilan-ver/detaylar';
    navigate(targetRoute);
  }, [activeCategory, country, navigate, persistRecentToStorage, persistWizardSelection, saveRecentCategory, selectedModule, selectedModuleLabel, selectedPath]);

  useEffect(() => {
    if (selectionComplete && activeCategory && autoAdvanceRef.current) {
      autoAdvanceRef.current = false;
      handleContinue(activeCategory, selectedPath, { auto: true });
    }
    if (!selectionComplete) {
      setAutoAdvanceActive(false);
    }
  }, [activeCategory, handleContinue, selectedPath, selectionComplete]);

  const handleRecentContinue = () => {
    if (!recentCategory?.category?.id) return;
    const moduleKey = recentCategory.module;
    const path = recentCategory.path || [];
    persistWizardSelection(recentCategory.category, path, moduleKey, moduleLabelByKey(moduleKey));
    localStorage.setItem('ilan_ver_force_core_step', 'true');
    if (moduleKey === 'vehicle') {
      localStorage.removeItem('ilan_ver_vehicle_selection');
      localStorage.removeItem('ilan_ver_vehicle_trim_id');
      localStorage.removeItem('ilan_ver_manual_trim_flag');
      localStorage.removeItem('ilan_ver_manual_trim');
    }
    if (recentCategory.country) {
      localStorage.setItem('selected_country', recentCategory.country);
    }
    const targetRoute = moduleKey === 'vehicle' ? '/ilan-ver/arac-sec' : '/ilan-ver/detaylar';
    navigate(targetRoute);
  };

  const columnTitle = (columnIndex) => {
    if (columnIndex === 0) return 'Kategori 1 (L1)';
    if (columnIndex === 1) return 'Kategori 2 (L2)';
    if (columnIndex === 2) return 'Kategori 3 (L3)';
    return 'Alt Tip Seçimi';
  };

  return (
    <div className="mx-auto max-w-6xl space-y-6" data-testid="ilan-ver-category-page">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900" data-testid="ilan-ver-title">Adım Adım Kategori Seç</h1>
          <p className="text-sm text-slate-600" data-testid="ilan-ver-subtitle">
            Modül → L1 → L2/L3 → Alt tip sırasıyla ilerleyin.
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

      {(recentLoading || recentCategory) && (
        <div className="rounded-xl border bg-white p-4" data-testid="ilan-ver-recent-card">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-semibold text-slate-900" data-testid="ilan-ver-recent-title">Son Seçiminiz</div>
              <div className="text-xs text-slate-500" data-testid="ilan-ver-recent-subtitle">Tek tıkla devam edebilirsiniz.</div>
            </div>
            {recentModuleLabel && (
              <span className="text-xs font-semibold text-blue-600" data-testid="ilan-ver-recent-module">{recentModuleLabel}</span>
            )}
          </div>

          {recentLoading ? (
            <div className="mt-3 text-xs text-slate-500" data-testid="ilan-ver-recent-loading">Yükleniyor...</div>
          ) : (
            <div className="mt-3 space-y-2">
              <div className="text-sm font-semibold text-slate-900" data-testid="ilan-ver-recent-category">
                {recentCategory?.category?.name}
              </div>
              <div className="text-xs text-slate-500" data-testid="ilan-ver-recent-path">
                {recentBreadcrumb}
              </div>
              <div className="flex flex-wrap gap-2 text-xs text-slate-500" data-testid="ilan-ver-recent-meta">
                <span data-testid="ilan-ver-recent-country">Ülke: {recentCategory?.country}</span>
                <span data-testid="ilan-ver-recent-module-pill">Modül: {recentModuleLabel}</span>
              </div>
              <button
                type="button"
                onClick={handleRecentContinue}
                className="mt-2 inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white"
                data-testid="ilan-ver-recent-continue"
              >
                Devam Et
              </button>
              {recentError && (
                <div className="text-xs text-amber-600" data-testid="ilan-ver-recent-error">{recentError}</div>
              )}
            </div>
          )}
        </div>
      )}

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
            <div className="text-sm font-semibold text-slate-900" data-testid="ilan-ver-columns-title">Kategori Sütunları</div>
            <div className="text-xs text-slate-500" data-testid="ilan-ver-columns-subtitle">Her adım URL’de saklanır, geri tuşu state kaybetmez.</div>
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
              <div
                className="flex flex-col gap-3 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800"
                data-testid="ilan-ver-fallback"
              >
                <div className="font-semibold" data-testid="ilan-ver-fallback-message">
                  Kategori bulunamadı – yöneticiye başvurun.
                </div>
                <div className="text-xs text-amber-700" data-testid="ilan-ver-fallback-hint">
                  Farklı bir modül seçebilir veya daha sonra tekrar deneyebilirsiniz.
                </div>
                <button
                  type="button"
                  onClick={() => updateUrlState('', [])}
                  className="self-start rounded-md border border-amber-300 bg-white px-3 py-1 text-xs font-semibold text-amber-700"
                  data-testid="ilan-ver-fallback-cta"
                >
                  Modül seçimine dön
                </button>
              </div>
            ) : (
              columns.map((column, columnIndex) => (
                <div
                  key={`column-${column.parentId || 'root'}-${columnIndex}`}
                  className="min-w-[220px] rounded-lg border bg-slate-50 p-3"
                  data-testid={`ilan-ver-column-${columnIndex}`}
                >
                  <div className="flex items-center justify-between">
                    <div className="text-sm font-semibold text-slate-800" data-testid={`ilan-ver-column-title-${columnIndex}`}>
                      {columnTitle(columnIndex)}
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
              Kategori seçimi tamamlandı: {activeCategory.name}
            </div>
            {autoAdvanceActive && (
              <div className="text-xs text-emerald-700" data-testid="ilan-ver-complete-auto">Çekirdek alanlara yönlendiriliyor...</div>
            )}
          </div>
        )}
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border bg-white p-4" data-testid="ilan-ver-action-bar">
        <div className="text-xs text-slate-500" data-testid="ilan-ver-action-hint">
          Alt tip seçimi tamamlanmadan ileri butonu aktifleşmez.
        </div>
        <button
          type="button"
          onClick={() => handleContinue(activeCategory, selectedPath, { auto: false })}
          disabled={!selectionComplete}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
          data-testid="ilan-ver-continue-button"
        >
          Devam
        </button>
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
