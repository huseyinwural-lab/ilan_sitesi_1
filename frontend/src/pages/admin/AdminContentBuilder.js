import React, { useMemo, useState } from 'react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const PAGE_TYPE_OPTIONS = [
  { value: 'home', label: 'Ana Sayfa (home)' },
  { value: 'search_l1', label: 'Kategori L1 (search_l1)' },
  { value: 'search_l2', label: 'Kategori L2 (search_l2)' },
  { value: 'listing_create_stepX', label: 'İlan Ver (listing_create_stepX)' },
];

const DEFAULT_COMPONENT_LIBRARY = [
  { key: 'home.default-content', name: 'Home Varsayılan İçerik' },
  { key: 'search.l1.default-content', name: 'Search L1 Varsayılan İçerik' },
  { key: 'search.l2.default-content', name: 'Search L2 Varsayılan İçerik' },
  { key: 'shared.text-block', name: 'Metin Bloğu' },
  { key: 'shared.ad-slot', name: 'Reklam Slotu' },
];

const getDefaultComponentKey = (pageType) => {
  if (pageType === 'home') return 'home.default-content';
  if (pageType === 'search_l1') return 'search.l1.default-content';
  if (pageType === 'search_l2') return 'search.l2.default-content';
  return 'shared.text-block';
};

const createEmptyPayload = (pageType) => ({
  rows: [
    {
      id: `row-${Date.now()}`,
      columns: [
        {
          id: `col-${Date.now()}`,
          width: { desktop: 12, tablet: 12, mobile: 12 },
          components: [
            {
              id: `cmp-${Date.now()}`,
              key: getDefaultComponentKey(pageType),
              props: pageType === 'home' ? {} : { note: 'Varsayılan içerik bloğu' },
              visibility: { desktop: true, tablet: true, mobile: true },
            },
          ],
        },
      ],
    },
  ],
});

const deepClone = (value) => JSON.parse(JSON.stringify(value));

const normalizePayload = (rawPayload, pageType) => {
  if (!rawPayload || typeof rawPayload !== 'object' || !Array.isArray(rawPayload.rows)) {
    return createEmptyPayload(pageType);
  }
  return rawPayload;
};

export default function AdminContentBuilder() {
  const authHeaders = useMemo(
    () => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` }),
    [],
  );

  const [pageType, setPageType] = useState('home');
  const [country, setCountry] = useState('DE');
  const [moduleName, setModuleName] = useState('global');
  const [categoryId, setCategoryId] = useState('');

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');

  const [pageId, setPageId] = useState('');
  const [activeDraftId, setActiveDraftId] = useState('');
  const [revisionList, setRevisionList] = useState([]);
  const [payloadJson, setPayloadJson] = useState(createEmptyPayload('home'));

  const [selectedRowId, setSelectedRowId] = useState('');
  const [selectedColumnId, setSelectedColumnId] = useState('');
  const [draggingRowId, setDraggingRowId] = useState('');
  const [draggingComponentId, setDraggingComponentId] = useState('');

  const [componentLibrary, setComponentLibrary] = useState(DEFAULT_COMPONENT_LIBRARY);

  const getLibrary = async () => {
    try {
      const res = await axios.get(`${API}/admin/site/content-layout/components`, {
        headers: authHeaders,
        params: { page: 1, limit: 100, is_active: true },
      });
      const fetchedItems = Array.isArray(res.data?.items) ? res.data.items : [];
      if (!fetchedItems.length) {
        setComponentLibrary(DEFAULT_COMPONENT_LIBRARY);
        return;
      }
      const normalized = fetchedItems.map((item) => ({
        key: item.key,
        name: item.name || item.key,
      }));
      const merged = [...DEFAULT_COMPONENT_LIBRARY];
      normalized.forEach((item) => {
        if (!merged.some((existing) => existing.key === item.key)) merged.push(item);
      });
      setComponentLibrary(merged);
    } catch (_err) {
      setComponentLibrary(DEFAULT_COMPONENT_LIBRARY);
    }
  };

  const getRevisionsForPage = async (targetPageId, targetPageType) => {
    const res = await axios.get(`${API}/admin/site/content-layout/pages/${targetPageId}/revisions`, {
      headers: authHeaders,
    });
    const revisions = Array.isArray(res.data?.items) ? res.data.items : [];
    setRevisionList(revisions);

    const draft = revisions.find((item) => item.status === 'draft');
    if (draft) {
      setActiveDraftId(draft.id);
      setPayloadJson(normalizePayload(draft.payload_json, targetPageType));
      return;
    }

    const published = revisions.find((item) => item.status === 'published');
    const draftCreateRes = await axios.post(
      `${API}/admin/site/content-layout/pages/${targetPageId}/revisions/draft`,
      { payload_json: normalizePayload(published?.payload_json, targetPageType) },
      { headers: authHeaders },
    );
    const newDraft = draftCreateRes.data?.item;
    setActiveDraftId(newDraft?.id || '');
    setPayloadJson(normalizePayload(newDraft?.payload_json, targetPageType));
  };

  const loadOrCreatePage = async () => {
    setLoading(true);
    setError('');
    setStatus('');
    try {
      await getLibrary();
      const normalizedCategoryId = categoryId.trim();
      const listRes = await axios.get(`${API}/admin/site/content-layout/pages`, {
        headers: authHeaders,
        params: {
          page_type: pageType,
          country: country.toUpperCase(),
          module: moduleName.trim(),
          page: 1,
          limit: 50,
        },
      });

      const listItems = Array.isArray(listRes.data?.items) ? listRes.data.items : [];
      let page = listItems.find((item) => {
        if (normalizedCategoryId) return item.category_id === normalizedCategoryId;
        return item.category_id === null;
      });

      if (!page) {
        const createRes = await axios.post(
          `${API}/admin/site/content-layout/pages`,
          {
            page_type: pageType,
            country: country.toUpperCase(),
            module: moduleName.trim(),
            category_id: normalizedCategoryId || null,
          },
          { headers: authHeaders },
        );
        page = createRes.data?.item;
      }

      if (!page?.id) throw new Error('layout_page_not_created');
      setPageId(page.id);
      await getRevisionsForPage(page.id, pageType);
      setStatus('Sayfa yüklendi. Draft düzenleyebilirsiniz.');
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || 'Sayfa yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const saveDraft = async () => {
    if (!activeDraftId) {
      setError('Aktif draft bulunamadı. Önce “Sayfayı Yükle/Oluştur” yapın.');
      return;
    }
    setSaving(true);
    setError('');
    setStatus('');
    try {
      await axios.patch(
        `${API}/admin/site/content-layout/revisions/${activeDraftId}/draft`,
        { payload_json: payloadJson },
        { headers: authHeaders },
      );
      setStatus('Draft kaydedildi.');
    } catch (err) {
      setError(err?.response?.data?.detail || 'Draft kaydedilemedi');
    } finally {
      setSaving(false);
    }
  };

  const publishDraft = async () => {
    if (!activeDraftId) {
      setError('Yayınlanacak draft bulunamadı.');
      return;
    }
    setSaving(true);
    setError('');
    setStatus('');
    try {
      await saveDraft();
      await axios.post(`${API}/admin/site/content-layout/revisions/${activeDraftId}/publish`, {}, { headers: authHeaders });
      setStatus('Draft publish edildi. Yeni draft oluşturuluyor...');
      await getRevisionsForPage(pageId, pageType);
      setStatus('Publish tamamlandı. Yeni draft hazır.');
    } catch (err) {
      setError(err?.response?.data?.detail || 'Publish başarısız');
    } finally {
      setSaving(false);
    }
  };

  const updatePayload = (nextPayload) => {
    setPayloadJson(nextPayload);
  };

  const addRow = () => {
    const next = deepClone(payloadJson);
    if (!Array.isArray(next.rows)) next.rows = [];
    next.rows.push({
      id: `row-${Date.now()}`,
      columns: [{
        id: `col-${Date.now()}`,
        width: { desktop: 12, tablet: 12, mobile: 12 },
        components: [],
      }],
    });
    updatePayload(next);
  };

  const moveRow = (rowId, direction) => {
    const next = deepClone(payloadJson);
    const rows = Array.isArray(next.rows) ? next.rows : [];
    const index = rows.findIndex((row) => row.id === rowId);
    if (index < 0) return;
    const target = direction === 'up' ? index - 1 : index + 1;
    if (target < 0 || target >= rows.length) return;
    [rows[index], rows[target]] = [rows[target], rows[index]];
    updatePayload(next);
  };

  const removeRow = (rowId) => {
    const next = deepClone(payloadJson);
    next.rows = (next.rows || []).filter((row) => row.id !== rowId);
    updatePayload(next);
  };

  const addColumn = (rowId) => {
    const next = deepClone(payloadJson);
    const row = (next.rows || []).find((item) => item.id === rowId);
    if (!row) return;
    if (!Array.isArray(row.columns)) row.columns = [];
    row.columns.push({
      id: `col-${Date.now()}`,
      width: { desktop: 6, tablet: 12, mobile: 12 },
      components: [],
    });
    updatePayload(next);
  };

  const updateColumnWidth = (rowId, columnId, key, value) => {
    const next = deepClone(payloadJson);
    const row = (next.rows || []).find((item) => item.id === rowId);
    const column = (row?.columns || []).find((item) => item.id === columnId);
    if (!column) return;
    if (!column.width || typeof column.width !== 'object') column.width = {};
    column.width[key] = Math.max(1, Math.min(12, Number(value) || 12));
    updatePayload(next);
  };

  const removeColumn = (rowId, columnId) => {
    const next = deepClone(payloadJson);
    const row = (next.rows || []).find((item) => item.id === rowId);
    if (!row) return;
    row.columns = (row.columns || []).filter((column) => column.id !== columnId);
    updatePayload(next);
  };

  const addComponent = (rowId, columnId, key) => {
    if (!key) return;
    const next = deepClone(payloadJson);
    const row = (next.rows || []).find((item) => item.id === rowId);
    const column = (row?.columns || []).find((item) => item.id === columnId);
    if (!column) return;
    if (!Array.isArray(column.components)) column.components = [];
    column.components.push({
      id: `cmp-${Date.now()}-${Math.round(Math.random() * 100)}`,
      key,
      props: key === 'shared.text-block' ? { title: 'Başlık', body: 'Metin içeriği' } : {},
      visibility: { desktop: true, tablet: true, mobile: true },
    });
    updatePayload(next);
  };

  const updateComponentField = (rowId, columnId, componentId, field, value) => {
    const next = deepClone(payloadJson);
    const row = (next.rows || []).find((item) => item.id === rowId);
    const column = (row?.columns || []).find((item) => item.id === columnId);
    const component = (column?.components || []).find((item) => item.id === componentId);
    if (!component) return;
    component[field] = value;
    updatePayload(next);
  };

  const removeComponent = (rowId, columnId, componentId) => {
    const next = deepClone(payloadJson);
    const row = (next.rows || []).find((item) => item.id === rowId);
    const column = (row?.columns || []).find((item) => item.id === columnId);
    if (!column) return;
    column.components = (column.components || []).filter((component) => component.id !== componentId);
    updatePayload(next);
  };

  const moveComponent = (rowId, columnId, componentId, direction) => {
    const next = deepClone(payloadJson);
    const row = (next.rows || []).find((item) => item.id === rowId);
    const column = (row?.columns || []).find((item) => item.id === columnId);
    const list = column?.components || [];
    const index = list.findIndex((item) => item.id === componentId);
    if (index < 0) return;
    const target = direction === 'up' ? index - 1 : index + 1;
    if (target < 0 || target >= list.length) return;
    [list[index], list[target]] = [list[target], list[index]];
    updatePayload(next);
  };

  const handleRowDrop = (targetRowId) => {
    if (!draggingRowId || draggingRowId === targetRowId) return;
    const next = deepClone(payloadJson);
    const rows = next.rows || [];
    const fromIndex = rows.findIndex((row) => row.id === draggingRowId);
    const toIndex = rows.findIndex((row) => row.id === targetRowId);
    if (fromIndex < 0 || toIndex < 0) return;
    const [moved] = rows.splice(fromIndex, 1);
    rows.splice(toIndex, 0, moved);
    updatePayload(next);
    setDraggingRowId('');
  };

  const handleComponentDrop = (targetRowId, targetColumnId) => {
    if (!draggingComponentId) return;
    const next = deepClone(payloadJson);
    let movedComponent = null;

    (next.rows || []).forEach((row) => {
      (row.columns || []).forEach((column) => {
        const index = (column.components || []).findIndex((component) => component.id === draggingComponentId);
        if (index >= 0) {
          movedComponent = column.components[index];
          column.components.splice(index, 1);
        }
      });
    });

    if (!movedComponent) return;
    const targetRow = (next.rows || []).find((row) => row.id === targetRowId);
    const targetColumn = (targetRow?.columns || []).find((column) => column.id === targetColumnId);
    if (!targetColumn) return;
    if (!Array.isArray(targetColumn.components)) targetColumn.components = [];
    targetColumn.components.push(movedComponent);
    updatePayload(next);
    setDraggingComponentId('');
  };

  return (
    <div className="space-y-5" data-testid="admin-content-builder-page">
      <header className="rounded-xl border bg-white p-4" data-testid="admin-content-builder-header">
        <div className="flex flex-wrap items-end gap-3" data-testid="admin-content-builder-filters">
          <label className="text-xs min-w-[180px]" data-testid="admin-content-builder-page-type-wrap">
            Sayfa Tipi
            <select className="mt-1 h-10 w-full rounded border px-2" value={pageType} onChange={(e) => setPageType(e.target.value)} data-testid="admin-content-builder-page-type-select">
              {PAGE_TYPE_OPTIONS.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
            </select>
          </label>

          <label className="text-xs min-w-[120px]" data-testid="admin-content-builder-country-wrap">
            Ülke
            <input className="mt-1 h-10 w-full rounded border px-2" value={country} onChange={(e) => setCountry(e.target.value.toUpperCase())} data-testid="admin-content-builder-country-input" />
          </label>

          <label className="text-xs min-w-[160px]" data-testid="admin-content-builder-module-wrap">
            Module
            <input className="mt-1 h-10 w-full rounded border px-2" value={moduleName} onChange={(e) => setModuleName(e.target.value)} data-testid="admin-content-builder-module-input" />
          </label>

          <label className="text-xs min-w-[240px]" data-testid="admin-content-builder-category-wrap">
            Category ID (opsiyonel)
            <input className="mt-1 h-10 w-full rounded border px-2" value={categoryId} onChange={(e) => setCategoryId(e.target.value)} data-testid="admin-content-builder-category-input" />
          </label>

          <button type="button" className="h-10 rounded bg-slate-900 px-4 text-sm text-white" onClick={loadOrCreatePage} disabled={loading} data-testid="admin-content-builder-load-page-button">
            {loading ? 'Yükleniyor...' : 'Sayfayı Yükle/Oluştur'}
          </button>

          <button type="button" className="h-10 rounded border px-4 text-sm" onClick={saveDraft} disabled={saving || !activeDraftId} data-testid="admin-content-builder-save-draft-button">
            Draft Kaydet
          </button>

          <button type="button" className="h-10 rounded bg-emerald-600 px-4 text-sm text-white" onClick={publishDraft} disabled={saving || !activeDraftId} data-testid="admin-content-builder-publish-button">
            Publish
          </button>
        </div>

        <div className="mt-3 flex flex-wrap gap-3 text-xs text-slate-600" data-testid="admin-content-builder-meta-row">
          <span data-testid="admin-content-builder-page-id">page_id: {pageId || '-'}</span>
          <span data-testid="admin-content-builder-draft-id">draft_id: {activeDraftId || '-'}</span>
          <span data-testid="admin-content-builder-revision-count">revision_count: {revisionList.length}</span>
        </div>

        {status ? <p className="mt-2 text-xs text-emerald-700" data-testid="admin-content-builder-status-message">{status}</p> : null}
        {error ? <p className="mt-2 text-xs text-rose-700" data-testid="admin-content-builder-error-message">{error}</p> : null}
      </header>

      <div className="grid gap-5 xl:grid-cols-[280px_minmax(0,1fr)]" data-testid="admin-content-builder-main-grid">
        <aside className="rounded-xl border bg-white p-4" data-testid="admin-content-builder-library">
          <h2 className="text-sm font-semibold" data-testid="admin-content-builder-library-title">Component Library</h2>
          <p className="mt-1 text-xs text-slate-500" data-testid="admin-content-builder-library-note">
            Bir sütunu seçip aşağıdan bileşen ekleyin.
          </p>
          <div className="mt-3 space-y-2" data-testid="admin-content-builder-library-list">
            {componentLibrary.map((component) => (
              <div key={component.key} className="rounded border p-2" data-testid={`admin-content-builder-library-item-${component.key}`}>
                <div className="text-xs font-medium" data-testid={`admin-content-builder-library-item-name-${component.key}`}>{component.name}</div>
                <div className="text-[11px] text-slate-500" data-testid={`admin-content-builder-library-item-key-${component.key}`}>{component.key}</div>
                <button
                  type="button"
                  className="mt-2 h-8 rounded border px-2 text-xs"
                  onClick={() => {
                    if (!selectedRowId || !selectedColumnId) {
                      setError('Önce canvas üzerinde bir sütun seçin.');
                      return;
                    }
                    addComponent(selectedRowId, selectedColumnId, component.key);
                  }}
                  data-testid={`admin-content-builder-library-add-${component.key}`}
                >
                  Seçili Sütuna Ekle
                </button>
              </div>
            ))}
          </div>
        </aside>

        <section className="rounded-xl border bg-white p-4" data-testid="admin-content-builder-canvas">
          <div className="mb-3 flex items-center justify-between" data-testid="admin-content-builder-canvas-header">
            <h2 className="text-sm font-semibold" data-testid="admin-content-builder-canvas-title">Sortable Canvas</h2>
            <button type="button" className="h-9 rounded border px-3 text-xs" onClick={addRow} data-testid="admin-content-builder-add-row-button">Satır Ekle</button>
          </div>

          <div className="space-y-4" data-testid="admin-content-builder-rows">
            {(payloadJson.rows || []).map((row, rowIndex) => (
              <article
                key={row.id}
                className="rounded-lg border p-3"
                draggable
                onDragStart={() => setDraggingRowId(row.id)}
                onDragOver={(e) => e.preventDefault()}
                onDrop={() => handleRowDrop(row.id)}
                data-testid={`admin-content-builder-row-${row.id}`}
              >
                <div className="mb-3 flex flex-wrap items-center gap-2" data-testid={`admin-content-builder-row-actions-${row.id}`}>
                  <span className="text-xs font-semibold" data-testid={`admin-content-builder-row-label-${row.id}`}>Row {rowIndex + 1}</span>
                  <button type="button" className="h-8 rounded border px-2 text-xs" onClick={() => moveRow(row.id, 'up')} data-testid={`admin-content-builder-row-move-up-${row.id}`}>Yukarı</button>
                  <button type="button" className="h-8 rounded border px-2 text-xs" onClick={() => moveRow(row.id, 'down')} data-testid={`admin-content-builder-row-move-down-${row.id}`}>Aşağı</button>
                  <button type="button" className="h-8 rounded border px-2 text-xs" onClick={() => addColumn(row.id)} data-testid={`admin-content-builder-row-add-column-${row.id}`}>Sütun Ekle</button>
                  <button type="button" className="h-8 rounded border border-rose-300 px-2 text-xs text-rose-700" onClick={() => removeRow(row.id)} data-testid={`admin-content-builder-row-remove-${row.id}`}>Satırı Sil</button>
                </div>

                <div className="grid grid-cols-1 gap-3 lg:grid-cols-2" data-testid={`admin-content-builder-row-columns-${row.id}`}>
                  {(row.columns || []).map((column) => (
                    <div
                      key={column.id}
                      className={`rounded-md border p-3 ${selectedColumnId === column.id ? 'border-slate-900' : 'border-slate-200'}`}
                      onClick={() => {
                        setSelectedRowId(row.id);
                        setSelectedColumnId(column.id);
                      }}
                      onDragOver={(e) => e.preventDefault()}
                      onDrop={() => handleComponentDrop(row.id, column.id)}
                      data-testid={`admin-content-builder-column-${column.id}`}
                    >
                      <div className="mb-2 flex flex-wrap items-center gap-2" data-testid={`admin-content-builder-column-header-${column.id}`}>
                        <span className="text-xs font-medium" data-testid={`admin-content-builder-column-label-${column.id}`}>Column</span>
                        <label className="text-[11px]" data-testid={`admin-content-builder-width-desktop-wrap-${column.id}`}>D
                          <select className="ml-1 rounded border px-1" value={column.width?.desktop || 12} onChange={(e) => updateColumnWidth(row.id, column.id, 'desktop', e.target.value)} data-testid={`admin-content-builder-width-desktop-${column.id}`}>
                            {Array.from({ length: 12 }).map((_, index) => <option key={index + 1} value={index + 1}>{index + 1}/12</option>)}
                          </select>
                        </label>
                        <label className="text-[11px]" data-testid={`admin-content-builder-width-tablet-wrap-${column.id}`}>T
                          <select className="ml-1 rounded border px-1" value={column.width?.tablet || 12} onChange={(e) => updateColumnWidth(row.id, column.id, 'tablet', e.target.value)} data-testid={`admin-content-builder-width-tablet-${column.id}`}>
                            {Array.from({ length: 12 }).map((_, index) => <option key={index + 1} value={index + 1}>{index + 1}/12</option>)}
                          </select>
                        </label>
                        <label className="text-[11px]" data-testid={`admin-content-builder-width-mobile-wrap-${column.id}`}>M
                          <select className="ml-1 rounded border px-1" value={column.width?.mobile || 12} onChange={(e) => updateColumnWidth(row.id, column.id, 'mobile', e.target.value)} data-testid={`admin-content-builder-width-mobile-${column.id}`}>
                            {Array.from({ length: 12 }).map((_, index) => <option key={index + 1} value={index + 1}>{index + 1}/12</option>)}
                          </select>
                        </label>
                        <button type="button" className="ml-auto rounded border border-rose-300 px-2 py-1 text-[11px] text-rose-700" onClick={() => removeColumn(row.id, column.id)} data-testid={`admin-content-builder-remove-column-${column.id}`}>
                          Sil
                        </button>
                      </div>

                      <div className="space-y-2" data-testid={`admin-content-builder-components-${column.id}`}>
                        {(column.components || []).map((component, componentIndex) => (
                          <div
                            key={component.id}
                            className="rounded border bg-slate-50 p-2"
                            draggable
                            onDragStart={() => setDraggingComponentId(component.id)}
                            data-testid={`admin-content-builder-component-${component.id}`}
                          >
                            <div className="flex flex-wrap items-center gap-2" data-testid={`admin-content-builder-component-header-${component.id}`}>
                              <select
                                className="h-8 min-w-[220px] rounded border px-2 text-xs"
                                value={component.key}
                                onChange={(e) => updateComponentField(row.id, column.id, component.id, 'key', e.target.value)}
                                data-testid={`admin-content-builder-component-key-${component.id}`}
                              >
                                {componentLibrary.map((item) => <option key={item.key} value={item.key}>{item.name}</option>)}
                              </select>
                              <button type="button" className="h-8 rounded border px-2 text-xs" onClick={() => moveComponent(row.id, column.id, component.id, 'up')} data-testid={`admin-content-builder-component-up-${component.id}`}>↑</button>
                              <button type="button" className="h-8 rounded border px-2 text-xs" onClick={() => moveComponent(row.id, column.id, component.id, 'down')} data-testid={`admin-content-builder-component-down-${component.id}`}>↓</button>
                              <button type="button" className="h-8 rounded border border-rose-300 px-2 text-xs text-rose-700" onClick={() => removeComponent(row.id, column.id, component.id)} data-testid={`admin-content-builder-component-remove-${component.id}`}>Sil</button>
                            </div>
                            <label className="mt-2 block text-[11px]" data-testid={`admin-content-builder-component-props-${component.id}`}>
                              Props JSON
                              <textarea
                                className="mt-1 min-h-[76px] w-full rounded border p-2 font-mono text-[11px]"
                                value={JSON.stringify(component.props || {}, null, 2)}
                                onChange={(e) => {
                                  try {
                                    const parsed = JSON.parse(e.target.value || '{}');
                                    updateComponentField(row.id, column.id, component.id, 'props', parsed);
                                    setError('');
                                  } catch (_err) {
                                    setError('Props JSON geçersiz');
                                  }
                                }}
                                data-testid={`admin-content-builder-component-props-input-${component.id}`}
                              />
                            </label>
                            <div className="mt-1 text-[11px] text-slate-500" data-testid={`admin-content-builder-component-order-${component.id}`}>
                              Sıra: {componentIndex + 1}
                            </div>
                          </div>
                        ))}

                        <button
                          type="button"
                          className="h-8 rounded border px-2 text-xs"
                          onClick={() => addComponent(row.id, column.id, getDefaultComponentKey(pageType))}
                          data-testid={`admin-content-builder-column-add-default-component-${column.id}`}
                        >
                          Varsayılan Bileşen Ekle
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </article>
            ))}
          </div>

          <div className="mt-4" data-testid="admin-content-builder-payload-preview-wrap">
            <h3 className="text-xs font-semibold" data-testid="admin-content-builder-payload-preview-title">Payload Preview</h3>
            <textarea
              className="mt-2 min-h-[220px] w-full rounded border p-2 font-mono text-[11px]"
              value={JSON.stringify(payloadJson, null, 2)}
              onChange={(e) => {
                try {
                  const parsed = JSON.parse(e.target.value || '{}');
                  setPayloadJson(parsed);
                  setError('');
                } catch (_err) {
                  setError('Payload JSON geçersiz');
                }
              }}
              data-testid="admin-content-builder-payload-preview-input"
            />
          </div>
        </section>
      </div>
    </div>
  );
}
