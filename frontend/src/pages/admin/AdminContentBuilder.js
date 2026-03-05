import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const PAGE_TYPE_OPTIONS = [
  { value: 'home', label: 'Ana Sayfa (home)' },
  { value: 'search_l1', label: 'Kategori L1 (search_l1)' },
  { value: 'search_l2', label: 'Kategori L2 (search_l2)' },
  { value: 'listing_create_stepX', label: 'İlan Ver (listing_create_stepX)' },
];

const DEFAULT_COMPONENT_LIBRARY = [
  {
    key: 'home.default-content',
    name: 'Home Varsayılan İçerik',
    schema_json: { type: 'object', properties: {}, additionalProperties: false },
  },
  {
    key: 'search.l1.default-content',
    name: 'Search L1 Varsayılan İçerik',
    schema_json: { type: 'object', properties: {}, additionalProperties: false },
  },
  {
    key: 'search.l2.default-content',
    name: 'Search L2 Varsayılan İçerik',
    schema_json: { type: 'object', properties: {}, additionalProperties: false },
  },
  {
    key: 'listing.create.default-content',
    name: 'İlan Ver Varsayılan İçerik',
    schema_json: { type: 'object', properties: {}, additionalProperties: false },
  },
  {
    key: 'shared.text-block',
    name: 'Metin Bloğu',
    schema_json: {
      type: 'object',
      properties: {
        title: { type: 'string', title: 'Başlık' },
        body: { type: 'string', title: 'Metin' },
      },
      additionalProperties: false,
    },
  },
  {
    key: 'shared.ad-slot',
    name: 'Reklam Slotu',
    schema_json: {
      type: 'object',
      properties: {
        placement: {
          type: 'string',
          title: 'Placement',
          enum: ['AD_HOME_TOP', 'AD_SEARCH_TOP', 'AD_LOGIN_1'],
        },
      },
      additionalProperties: false,
    },
  },
];

const getDefaultComponentKey = (pageType) => {
  if (pageType === 'home') return 'home.default-content';
  if (pageType === 'search_l1') return 'search.l1.default-content';
  if (pageType === 'search_l2') return 'search.l2.default-content';
  if (pageType === 'listing_create_stepX') return 'listing.create.default-content';
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

const buildCategoryTreeOptions = (items) => {
  const byParent = new Map();
  items.forEach((item) => {
    const parentKey = item.parent_id || '__root__';
    if (!byParent.has(parentKey)) byParent.set(parentKey, []);
    byParent.get(parentKey).push(item);
  });

  const sortNodes = (nodes) => {
    return [...nodes].sort((a, b) => {
      const aOrder = Number(a.sort_order || 0);
      const bOrder = Number(b.sort_order || 0);
      if (aOrder !== bOrder) return aOrder - bOrder;
      return String(a.name || '').localeCompare(String(b.name || ''), 'tr');
    });
  };

  const flattened = [];
  const walk = (parentId, depth) => {
    const children = sortNodes(byParent.get(parentId) || []);
    children.forEach((child) => {
      flattened.push({ ...child, depth });
      walk(child.id, depth + 1);
    });
  };

  walk('__root__', 0);
  return flattened;
};

const computeLayoutDiff = (publishedPayload, draftPayload) => {
  const publishedRows = Array.isArray(publishedPayload?.rows) ? publishedPayload.rows : [];
  const draftRows = Array.isArray(draftPayload?.rows) ? draftPayload.rows : [];

  const publishedRowMap = new Map(publishedRows.map((row) => [row.id, row]));
  const draftRowMap = new Map(draftRows.map((row) => [row.id, row]));

  const changedRowIds = new Set();
  const changedColumnIds = new Set();
  const changedComponentIds = new Set();

  const allRowIds = new Set([...publishedRowMap.keys(), ...draftRowMap.keys()]);
  allRowIds.forEach((rowId) => {
    const beforeRow = publishedRowMap.get(rowId);
    const afterRow = draftRowMap.get(rowId);
    if (!beforeRow || !afterRow) {
      changedRowIds.add(rowId);
      return;
    }

    const beforeColumns = Array.isArray(beforeRow.columns) ? beforeRow.columns : [];
    const afterColumns = Array.isArray(afterRow.columns) ? afterRow.columns : [];
    const beforeColumnMap = new Map(beforeColumns.map((column) => [column.id, column]));
    const afterColumnMap = new Map(afterColumns.map((column) => [column.id, column]));
    const allColumnIds = new Set([...beforeColumnMap.keys(), ...afterColumnMap.keys()]);

    allColumnIds.forEach((columnId) => {
      const beforeColumn = beforeColumnMap.get(columnId);
      const afterColumn = afterColumnMap.get(columnId);
      if (!beforeColumn || !afterColumn) {
        changedRowIds.add(rowId);
        changedColumnIds.add(columnId);
        return;
      }

      const beforeWidth = JSON.stringify(beforeColumn.width || {});
      const afterWidth = JSON.stringify(afterColumn.width || {});
      if (beforeWidth !== afterWidth) {
        changedRowIds.add(rowId);
        changedColumnIds.add(columnId);
      }

      const beforeComponents = Array.isArray(beforeColumn.components) ? beforeColumn.components : [];
      const afterComponents = Array.isArray(afterColumn.components) ? afterColumn.components : [];
      const beforeComponentMap = new Map(beforeComponents.map((component) => [component.id, component]));
      const afterComponentMap = new Map(afterComponents.map((component) => [component.id, component]));
      const allComponentIds = new Set([...beforeComponentMap.keys(), ...afterComponentMap.keys()]);

      allComponentIds.forEach((componentId) => {
        const beforeComponent = beforeComponentMap.get(componentId);
        const afterComponent = afterComponentMap.get(componentId);
        if (!beforeComponent || !afterComponent) {
          changedRowIds.add(rowId);
          changedColumnIds.add(columnId);
          changedComponentIds.add(componentId);
          return;
        }
        const beforeSnapshot = JSON.stringify({ key: beforeComponent.key, props: beforeComponent.props || {} });
        const afterSnapshot = JSON.stringify({ key: afterComponent.key, props: afterComponent.props || {} });
        if (beforeSnapshot !== afterSnapshot) {
          changedRowIds.add(rowId);
          changedColumnIds.add(columnId);
          changedComponentIds.add(componentId);
        }
      });
    });
  });

  return {
    changedRowIds,
    changedColumnIds,
    changedComponentIds,
    summary: {
      rows: changedRowIds.size,
      columns: changedColumnIds.size,
      components: changedComponentIds.size,
    },
  };
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

  const [bindingCategoryId, setBindingCategoryId] = useState('');
  const [bindingActiveItem, setBindingActiveItem] = useState(null);
  const [bindingLoading, setBindingLoading] = useState(false);
  const [showPreviewComparison, setShowPreviewComparison] = useState(false);

  const [selectedRowId, setSelectedRowId] = useState('');
  const [selectedColumnId, setSelectedColumnId] = useState('');
  const [draggingRowId, setDraggingRowId] = useState('');
  const [draggingComponentId, setDraggingComponentId] = useState('');
  const [dragOverRowId, setDragOverRowId] = useState('');
  const [dragOverColumnId, setDragOverColumnId] = useState('');

  const [componentLibrary, setComponentLibrary] = useState(DEFAULT_COMPONENT_LIBRARY);
  const [categoryOptions, setCategoryOptions] = useState([]);
  const [categorySearch, setCategorySearch] = useState('');
  const [categoriesLoading, setCategoriesLoading] = useState(false);

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
        schema_json: item.schema_json && typeof item.schema_json === 'object'
          ? item.schema_json
          : { type: 'object', properties: {}, additionalProperties: true },
      }));
      const merged = [...DEFAULT_COMPONENT_LIBRARY];
      normalized.forEach((item) => {
        const index = merged.findIndex((existing) => existing.key === item.key);
        if (index >= 0) {
          merged[index] = { ...merged[index], ...item };
        } else {
          merged.push(item);
        }
      });
      setComponentLibrary(merged);
    } catch (_err) {
      setComponentLibrary(DEFAULT_COMPONENT_LIBRARY);
    }
  };

  useEffect(() => {
    let active = true;
    const fetchCategories = async () => {
      setCategoriesLoading(true);
      try {
        const res = await axios.get(`${API}/categories`, {
          params: {
            module: moduleName.trim(),
            country: country.toUpperCase(),
          },
        });
        if (!active) return;
        const list = Array.isArray(res.data) ? res.data : [];
        setCategoryOptions(buildCategoryTreeOptions(list));
      } catch (_err) {
        if (active) setCategoryOptions([]);
      } finally {
        if (active) setCategoriesLoading(false);
      }
    };

    if (moduleName.trim()) {
      fetchCategories();
    } else {
      setCategoryOptions([]);
    }

    return () => {
      active = false;
    };
  }, [moduleName, country]);

  const filteredCategoryOptions = useMemo(() => {
    const query = categorySearch.trim().toLowerCase();
    if (!query) return categoryOptions;
    return categoryOptions.filter((item) => {
      const name = String(item.name || '').toLowerCase();
      const slug = String(item.slug || '').toLowerCase();
      return name.includes(query) || slug.includes(query);
    });
  }, [categoryOptions, categorySearch]);

  const previewBasePath = useMemo(() => {
    const selectedCategory = (bindingCategoryId || categoryId).trim();
    if (pageType === 'home') return '/';
    if (pageType === 'search_l1' || pageType === 'search_l2') {
      return `/search${selectedCategory ? `?category=${encodeURIComponent(selectedCategory)}` : ''}`;
    }
    return '/ilan-ver/detaylar';
  }, [pageType, bindingCategoryId, categoryId]);

  const publishedPreviewUrl = useMemo(() => {
    if (typeof window === 'undefined') return previewBasePath;
    return `${window.location.origin}${previewBasePath}`;
  }, [previewBasePath]);

  const draftPreviewUrl = useMemo(() => {
    if (typeof window === 'undefined') return previewBasePath;
    const separator = previewBasePath.includes('?') ? '&' : '?';
    return `${window.location.origin}${previewBasePath}${separator}layout_preview=draft`;
  }, [previewBasePath]);

  const publishedRevisionPayload = useMemo(() => {
    const published = revisionList.find((revision) => revision.status === 'published');
    return published?.payload_json || { rows: [] };
  }, [revisionList]);

  const layoutDiff = useMemo(
    () => computeLayoutDiff(publishedRevisionPayload, payloadJson),
    [publishedRevisionPayload, payloadJson],
  );

  const getComponentSchema = (componentKey) => {
    const componentDef = componentLibrary.find((item) => item.key === componentKey);
    return componentDef?.schema_json && typeof componentDef.schema_json === 'object'
      ? componentDef.schema_json
      : { type: 'object', properties: {}, additionalProperties: true };
  };

  const updateComponentPropValue = (rowId, columnId, componentId, propKey, propValue) => {
    const next = deepClone(payloadJson);
    const row = (next.rows || []).find((item) => item.id === rowId);
    const column = (row?.columns || []).find((item) => item.id === columnId);
    const component = (column?.components || []).find((item) => item.id === componentId);
    if (!component) return;
    if (!component.props || typeof component.props !== 'object') component.props = {};
    component.props[propKey] = propValue;
    updatePayload(next);
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
      setBindingCategoryId(normalizedCategoryId);
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

  const moveColumn = (rowId, columnId, direction) => {
    const next = deepClone(payloadJson);
    const row = (next.rows || []).find((item) => item.id === rowId);
    const columns = row?.columns || [];
    const index = columns.findIndex((item) => item.id === columnId);
    if (index < 0) return;
    const target = direction === 'left' ? index - 1 : index + 1;
    if (target < 0 || target >= columns.length) return;
    [columns[index], columns[target]] = [columns[target], columns[index]];
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
    if (!draggingRowId || draggingRowId === targetRowId) {
      setDragOverRowId('');
      return;
    }
    const next = deepClone(payloadJson);
    const rows = next.rows || [];
    const fromIndex = rows.findIndex((row) => row.id === draggingRowId);
    const toIndex = rows.findIndex((row) => row.id === targetRowId);
    if (fromIndex < 0 || toIndex < 0) return;
    const [moved] = rows.splice(fromIndex, 1);
    rows.splice(toIndex, 0, moved);
    updatePayload(next);
    setDraggingRowId('');
    setDragOverRowId('');
  };

  const handleComponentDrop = (targetRowId, targetColumnId) => {
    if (!draggingComponentId) {
      setDragOverColumnId('');
      return;
    }
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
    setDragOverColumnId('');
  };

  const fetchActiveBinding = async () => {
    const categoryToCheck = (bindingCategoryId || categoryId).trim();
    if (!categoryToCheck) {
      setError('Binding için kategori ID zorunlu.');
      return;
    }
    setBindingLoading(true);
    try {
      const res = await axios.get(`${API}/admin/site/content-layout/bindings/active`, {
        headers: authHeaders,
        params: {
          country: country.toUpperCase(),
          module: moduleName.trim(),
          category_id: categoryToCheck,
        },
      });
      setBindingActiveItem(res.data?.item || null);
      setStatus('Aktif binding sorgulandı.');
    } catch (err) {
      setError(err?.response?.data?.detail || 'Aktif binding getirilemedi');
    } finally {
      setBindingLoading(false);
    }
  };

  const bindCurrentPage = async () => {
    const categoryToBind = (bindingCategoryId || categoryId).trim();
    if (!pageId) {
      setError('Önce bir page oluşturun/yükleyin.');
      return;
    }
    if (!categoryToBind) {
      setError('Binding için kategori ID zorunlu.');
      return;
    }
    setBindingLoading(true);
    try {
      await axios.post(
        `${API}/admin/site/content-layout/bindings`,
        {
          country: country.toUpperCase(),
          module: moduleName.trim(),
          category_id: categoryToBind,
          layout_page_id: pageId,
        },
        { headers: authHeaders },
      );
      setStatus('Kategori binding kaydedildi.');
      await fetchActiveBinding();
    } catch (err) {
      setError(err?.response?.data?.detail || 'Binding kaydedilemedi');
    } finally {
      setBindingLoading(false);
    }
  };

  const unbindCurrentCategory = async () => {
    const categoryToUnbind = (bindingCategoryId || categoryId).trim();
    if (!categoryToUnbind) {
      setError('Unbind için kategori ID zorunlu.');
      return;
    }
    setBindingLoading(true);
    try {
      await axios.post(
        `${API}/admin/site/content-layout/bindings/unbind`,
        {
          country: country.toUpperCase(),
          module: moduleName.trim(),
          category_id: categoryToUnbind,
        },
        { headers: authHeaders },
      );
      setBindingActiveItem(null);
      setStatus('Kategori binding kaldırıldı.');
    } catch (err) {
      setError(err?.response?.data?.detail || 'Unbind başarısız');
    } finally {
      setBindingLoading(false);
    }
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

        <div className="mt-3 rounded-lg border border-slate-200 bg-slate-50 p-3" data-testid="admin-content-builder-binding-panel">
          <div className="flex flex-wrap items-end gap-2" data-testid="admin-content-builder-binding-controls">
            <label className="text-xs min-w-[220px]" data-testid="admin-content-builder-binding-category-search-wrap">
              Kategori Ara
              <input
                className="mt-1 h-9 w-full rounded border px-2"
                value={categorySearch}
                onChange={(e) => setCategorySearch(e.target.value)}
                placeholder="Kategori adı / slug"
                data-testid="admin-content-builder-binding-category-search-input"
              />
            </label>

            <label className="text-xs min-w-[340px]" data-testid="admin-content-builder-binding-category-wrap">
              Kategori Ağacı Seçimi
              <select
                className="mt-1 h-9 w-full rounded border px-2"
                value={bindingCategoryId}
                onChange={(e) => setBindingCategoryId(e.target.value)}
                data-testid="admin-content-builder-binding-category-input"
              >
                <option value="">{categoriesLoading ? 'Kategoriler yükleniyor...' : 'Kategori seçin'}</option>
                {filteredCategoryOptions.map((item) => (
                  <option key={item.id} value={item.id}>
                    {`${'— '.repeat(item.depth)}${item.name}`}
                  </option>
                ))}
              </select>
            </label>
            <button type="button" className="h-9 rounded border px-3 text-xs" onClick={fetchActiveBinding} disabled={bindingLoading} data-testid="admin-content-builder-binding-fetch-button">Aktifi Getir</button>
            <button type="button" className="h-9 rounded bg-blue-600 px-3 text-xs text-white" onClick={bindCurrentPage} disabled={bindingLoading} data-testid="admin-content-builder-binding-bind-button">Bu Page'i Bağla</button>
            <button type="button" className="h-9 rounded border border-rose-300 px-3 text-xs text-rose-700" onClick={unbindCurrentCategory} disabled={bindingLoading} data-testid="admin-content-builder-binding-unbind-button">Binding Kaldır</button>
          </div>

          <div className="mt-2 text-xs text-slate-700" data-testid="admin-content-builder-binding-active-summary">
            {bindingActiveItem ? (
              <>
                Aktif Binding → page_id: <strong data-testid="admin-content-builder-binding-active-page-id">{bindingActiveItem.layout_page_id}</strong>
              </>
            ) : (
              <span data-testid="admin-content-builder-binding-active-empty">Aktif binding bulunamadı.</span>
            )}
          </div>
        </div>

        <div className="mt-3 rounded-lg border border-sky-200 bg-sky-50 p-3" data-testid="admin-content-builder-preview-panel">
          <div className="flex flex-wrap items-center gap-2" data-testid="admin-content-builder-preview-controls">
            <button
              type="button"
              className="h-9 rounded border px-3 text-xs"
              onClick={() => setShowPreviewComparison((prev) => !prev)}
              data-testid="admin-content-builder-preview-toggle-button"
            >
              {showPreviewComparison ? 'Preview Karşılaştırmayı Gizle' : 'Preview Karşılaştırmayı Aç'}
            </button>
            <a href={publishedPreviewUrl} target="_blank" rel="noreferrer" className="text-xs font-medium underline" data-testid="admin-content-builder-preview-published-link">
              Published Aç
            </a>
            <a href={draftPreviewUrl} target="_blank" rel="noreferrer" className="text-xs font-medium underline" data-testid="admin-content-builder-preview-draft-link">
              Draft Preview Aç (layout_preview=draft)
            </a>
          </div>

          {showPreviewComparison ? (
            <div className="mt-3 grid grid-cols-1 gap-3 xl:grid-cols-2" data-testid="admin-content-builder-preview-iframes">
              <div className="rounded border bg-white p-2" data-testid="admin-content-builder-preview-published-wrap">
                <div className="mb-1 text-[11px] text-slate-600" data-testid="admin-content-builder-preview-published-label">Published</div>
                <iframe title="published-preview" src={publishedPreviewUrl} className="h-[380px] w-full rounded border" data-testid="admin-content-builder-preview-published-iframe" />
              </div>
              <div className="rounded border bg-white p-2" data-testid="admin-content-builder-preview-draft-wrap">
                <div className="mb-1 text-[11px] text-slate-600" data-testid="admin-content-builder-preview-draft-label">Draft Preview</div>
                <iframe title="draft-preview" src={draftPreviewUrl} className="h-[380px] w-full rounded border" data-testid="admin-content-builder-preview-draft-iframe" />
              </div>
            </div>
          ) : null}
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

          <div className="mb-3 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs" data-testid="admin-content-builder-diff-summary">
            <span data-testid="admin-content-builder-diff-rows">Row değişimi: <strong>{layoutDiff.summary.rows}</strong></span>
            <span className="mx-2">•</span>
            <span data-testid="admin-content-builder-diff-columns">Column değişimi: <strong>{layoutDiff.summary.columns}</strong></span>
            <span className="mx-2">•</span>
            <span data-testid="admin-content-builder-diff-components">Component değişimi: <strong>{layoutDiff.summary.components}</strong></span>
          </div>

          <div className="space-y-4" data-testid="admin-content-builder-rows">
            {(payloadJson.rows || []).map((row, rowIndex) => (
              <article
                key={row.id}
                className={`rounded-lg border p-3 transition ${dragOverRowId === row.id ? 'border-slate-900 bg-slate-50' : 'border-slate-200'} ${layoutDiff.changedRowIds.has(row.id) ? 'ring-1 ring-amber-500' : ''}`}
                draggable
                onDragStart={() => setDraggingRowId(row.id)}
                onDragEnd={() => {
                  setDraggingRowId('');
                  setDragOverRowId('');
                }}
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragOverRowId(row.id);
                }}
                onDragLeave={() => {
                  if (dragOverRowId === row.id) setDragOverRowId('');
                }}
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

                {dragOverRowId === row.id ? (
                  <div className="mb-3 rounded border border-dashed border-slate-500 bg-white px-2 py-1 text-[11px] text-slate-600" data-testid={`admin-content-builder-row-drop-indicator-${row.id}`}>
                    Satırı buraya bırak
                  </div>
                ) : null}

                <div className="grid grid-cols-1 gap-3 lg:grid-cols-2" data-testid={`admin-content-builder-row-columns-${row.id}`}>
                  {(row.columns || []).map((column) => (
                    <div
                      key={column.id}
                      className={`rounded-md border p-3 transition ${selectedColumnId === column.id ? 'border-slate-900' : 'border-slate-200'} ${dragOverColumnId === column.id ? 'bg-amber-50 border-amber-400' : ''} ${layoutDiff.changedColumnIds.has(column.id) ? 'ring-1 ring-amber-500' : ''}`}
                      onClick={() => {
                        setSelectedRowId(row.id);
                        setSelectedColumnId(column.id);
                      }}
                      onDragOver={(e) => {
                        e.preventDefault();
                        setDragOverColumnId(column.id);
                      }}
                      onDragLeave={() => {
                        if (dragOverColumnId === column.id) setDragOverColumnId('');
                      }}
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
                        <button type="button" className="rounded border px-2 py-1 text-[11px]" onClick={() => moveColumn(row.id, column.id, 'left')} data-testid={`admin-content-builder-move-column-left-${column.id}`}>
                          ←
                        </button>
                        <button type="button" className="rounded border px-2 py-1 text-[11px]" onClick={() => moveColumn(row.id, column.id, 'right')} data-testid={`admin-content-builder-move-column-right-${column.id}`}>
                          →
                        </button>
                      </div>

                      {dragOverColumnId === column.id ? (
                        <div className="mb-2 rounded border border-dashed border-amber-500 bg-amber-100 px-2 py-1 text-[11px] text-amber-700" data-testid={`admin-content-builder-column-drop-indicator-${column.id}`}>
                          Bileşeni bu sütuna bırak
                        </div>
                      ) : null}

                      <div className="space-y-2" data-testid={`admin-content-builder-components-${column.id}`}>
                        {(column.components || []).map((component, componentIndex) => (
                          <div
                            key={component.id}
                            className={`rounded border bg-slate-50 p-2 ${layoutDiff.changedComponentIds.has(component.id) ? 'border-amber-500 bg-amber-50' : ''}`}
                            draggable
                            onDragStart={() => setDraggingComponentId(component.id)}
                            onDragEnd={() => {
                              setDraggingComponentId('');
                              setDragOverColumnId('');
                            }}
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
                            <div className="mt-2 rounded border bg-white p-2" data-testid={`admin-content-builder-component-props-${component.id}`}>
                              <div className="mb-1 text-[11px] font-semibold text-slate-700" data-testid={`admin-content-builder-component-props-title-${component.id}`}>
                                Schema Form Editor
                              </div>
                              {Object.entries(getComponentSchema(component.key)?.properties || {}).length === 0 ? (
                                <div className="text-[11px] text-slate-500" data-testid={`admin-content-builder-component-props-empty-${component.id}`}>
                                  Bu bileşenin düzenlenebilir prop alanı yok.
                                </div>
                              ) : (
                                <div className="space-y-2" data-testid={`admin-content-builder-component-props-fields-${component.id}`}>
                                  {Object.entries(getComponentSchema(component.key)?.properties || {}).map(([propKey, propSchema]) => {
                                    const fieldType = propSchema?.type || 'string';
                                    const fieldTitle = propSchema?.title || propKey;
                                    const value = component.props?.[propKey];

                                    if (Array.isArray(propSchema?.enum)) {
                                      return (
                                        <label key={propKey} className="block text-[11px]" data-testid={`admin-content-builder-prop-wrap-${component.id}-${propKey}`}>
                                          {fieldTitle}
                                          <select
                                            className="mt-1 h-8 w-full rounded border px-2 text-[11px]"
                                            value={value ?? propSchema.enum[0]}
                                            onChange={(e) => updateComponentPropValue(row.id, column.id, component.id, propKey, e.target.value)}
                                            data-testid={`admin-content-builder-prop-input-${component.id}-${propKey}`}
                                          >
                                            {propSchema.enum.map((option) => (
                                              <option key={`${propKey}-${option}`} value={option}>{option}</option>
                                            ))}
                                          </select>
                                        </label>
                                      );
                                    }

                                    if (fieldType === 'boolean') {
                                      return (
                                        <label key={propKey} className="inline-flex items-center gap-2 text-[11px]" data-testid={`admin-content-builder-prop-wrap-${component.id}-${propKey}`}>
                                          <input
                                            type="checkbox"
                                            checked={Boolean(value)}
                                            onChange={(e) => updateComponentPropValue(row.id, column.id, component.id, propKey, e.target.checked)}
                                            data-testid={`admin-content-builder-prop-input-${component.id}-${propKey}`}
                                          />
                                          {fieldTitle}
                                        </label>
                                      );
                                    }

                                    if (fieldType === 'number' || fieldType === 'integer') {
                                      return (
                                        <label key={propKey} className="block text-[11px]" data-testid={`admin-content-builder-prop-wrap-${component.id}-${propKey}`}>
                                          {fieldTitle}
                                          <input
                                            type="number"
                                            className="mt-1 h-8 w-full rounded border px-2 text-[11px]"
                                            value={Number.isFinite(Number(value)) ? Number(value) : ''}
                                            onChange={(e) => updateComponentPropValue(row.id, column.id, component.id, propKey, Number(e.target.value || 0))}
                                            data-testid={`admin-content-builder-prop-input-${component.id}-${propKey}`}
                                          />
                                        </label>
                                      );
                                    }

                                    return (
                                      <label key={propKey} className="block text-[11px]" data-testid={`admin-content-builder-prop-wrap-${component.id}-${propKey}`}>
                                        {fieldTitle}
                                        <input
                                          type="text"
                                          className="mt-1 h-8 w-full rounded border px-2 text-[11px]"
                                          value={value ?? ''}
                                          onChange={(e) => updateComponentPropValue(row.id, column.id, component.id, propKey, e.target.value)}
                                          data-testid={`admin-content-builder-prop-input-${component.id}-${propKey}`}
                                        />
                                      </label>
                                    );
                                  })}
                                </div>
                              )}

                              <details className="mt-2" data-testid={`admin-content-builder-component-raw-json-${component.id}`}>
                                <summary className="cursor-pointer text-[11px] text-slate-500">Gelişmiş JSON</summary>
                                <textarea
                                  className="mt-1 min-h-[70px] w-full rounded border p-2 font-mono text-[11px]"
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
                              </details>
                            </div>
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
