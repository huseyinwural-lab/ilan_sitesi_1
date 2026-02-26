import React, { useEffect, useMemo, useState } from 'react';
import { DndContext, PointerSensor, KeyboardSensor, useSensor, useSensors, closestCenter } from '@dnd-kit/core';
import { arrayMove, SortableContext, sortableKeyboardCoordinates, useSortable, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { useToast } from '@/components/ui/toaster';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const SortableRow = ({ item, onToggle, testIdPrefix }) => {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id: item.id });
  const style = { transform: CSS.Transform.toString(transform), transition };
  return (
    <div ref={setNodeRef} style={style} className="flex items-center gap-3 rounded-md border bg-white px-3 py-2" data-testid={`${testIdPrefix}-row-${item.key}`}>
      <button type="button" {...attributes} {...listeners} className="cursor-grab text-slate-500" data-testid={`${testIdPrefix}-drag-${item.key}`}>☰</button>
      <div className="flex-1" data-testid={`${testIdPrefix}-label-${item.key}`}>
        <div className="text-sm font-medium">{item.label_i18n_key || item.title_i18n_key}</div>
        <div className="text-xs text-slate-500">{item.route || item.data_source_key}</div>
      </div>
      <div className="text-xs text-slate-500" data-testid={`${testIdPrefix}-flag-${item.key}`}>
        flag: {item.feature_flag || 'none'} ({String(item.feature_flag_enabled)})
      </div>
      <label className="inline-flex items-center gap-2 text-xs" data-testid={`${testIdPrefix}-visible-wrap-${item.key}`}>
        <input type="checkbox" checked={Boolean(item.visible)} onChange={(e) => onToggle(item, e.target.checked)} data-testid={`${testIdPrefix}-visible-${item.key}`} />
        visible
      </label>
    </div>
  );
};

export default function AdminDealerPortalConfig() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [navItems, setNavItems] = useState([]);
  const [modules, setModules] = useState([]);
  const [preview, setPreview] = useState({
    header_items: [],
    header_row1_items: [],
    header_row1_fixed_blocks: [],
    header_row2_modules: [],
    header_row3_controls: {},
    sidebar_items: [],
    modules: [],
  });
  const [lastSavedAt, setLastSavedAt] = useState('');

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );
  const { toast } = useToast();
  const authHeader = useMemo(() => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` }), []);

  const resolveErrorMessage = (payload, fallback) => {
    if (typeof payload?.detail === 'string') return payload.detail;
    if (payload?.detail?.message) return payload.detail.message;
    if (payload?.message) return payload.message;
    return fallback;
  };

  const fetchAll = async () => {
    setLoading(true);
    setError('');
    try {
      const [configRes, previewRes] = await Promise.all([
        fetch(`${API}/admin/dealer-portal/config`, { headers: authHeader }),
        fetch(`${API}/admin/dealer-portal/config/preview`, { headers: authHeader }),
      ]);
      const configPayload = await configRes.json().catch(() => ({}));
      const previewPayload = await previewRes.json().catch(() => ({}));
      if (!configRes.ok) throw new Error(resolveErrorMessage(configPayload, 'Dealer config yüklenemedi'));
      if (!previewRes.ok) throw new Error(resolveErrorMessage(previewPayload, 'Dealer preview yüklenemedi'));
      setNavItems(Array.isArray(configPayload?.nav_items) ? configPayload.nav_items : []);
      setModules(Array.isArray(configPayload?.modules) ? configPayload.modules : []);
      setPreview(previewPayload || {
        header_items: [],
        header_row1_items: [],
        header_row1_fixed_blocks: [],
        header_row2_modules: [],
        header_row3_controls: {},
        sidebar_items: [],
        modules: [],
      });
    } catch (err) {
      setError(err?.message || 'Dealer config yüklenemedi');
      setNavItems([]);
      setModules([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAll();
  }, []);

  const saveRequest = async (url, payload, fallbackMessage) => {
    const res = await fetch(url, {
      method: 'POST',
      headers: { ...authHeader, 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(resolveErrorMessage(data, fallbackMessage));
    }
    setLastSavedAt(new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    return data;
  };

  const persistNavOrder = async (location, orderedItems) => {
    setSaving(true);
    try {
      await saveRequest(
        `${API}/admin/dealer-portal/nav/reorder`,
        { location, ordered_ids: orderedItems.map((row) => row.id) },
        'Header/Sidebar sıralaması kaydedilemedi',
      );
      toast({ title: 'Sıralama kaydedildi', description: `${location} sırası güncellendi.` });
      await fetchAll();
    } catch (err) {
      setError(err?.message || 'Sıralama kaydedilemedi');
      toast({ title: 'Kaydetme başarısız', description: err?.message || 'Sıralama kaydedilemedi', variant: 'destructive' });
      await fetchAll();
    } finally {
      setSaving(false);
    }
  };

  const persistModuleOrder = async (orderedItems) => {
    setSaving(true);
    try {
      await saveRequest(
        `${API}/admin/dealer-portal/modules/reorder`,
        { ordered_ids: orderedItems.map((row) => row.id) },
        'Modül sıralaması kaydedilemedi',
      );
      toast({ title: 'Sıralama kaydedildi', description: 'Modül sırası güncellendi.' });
      await fetchAll();
    } catch (err) {
      setError(err?.message || 'Modül sıralaması kaydedilemedi');
      toast({ title: 'Kaydetme başarısız', description: err?.message || 'Modül sıralaması kaydedilemedi', variant: 'destructive' });
      await fetchAll();
    } finally {
      setSaving(false);
    }
  };

  const updateNavVisibility = async (item, visible) => {
    try {
      const res = await fetch(`${API}/admin/dealer-portal/nav/${item.id}`, {
        method: 'PATCH',
        headers: { ...authHeader, 'Content-Type': 'application/json' },
        body: JSON.stringify({ visible }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(resolveErrorMessage(data, 'Görünürlük güncellenemedi'));
      setLastSavedAt(new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
      await fetchAll();
    } catch (err) {
      setError(err?.message || 'Görünürlük güncellenemedi');
      toast({ title: 'Güncelleme başarısız', description: err?.message || 'Görünürlük güncellenemedi', variant: 'destructive' });
    }
  };

  const updateModuleVisibility = async (item, visible) => {
    try {
      const res = await fetch(`${API}/admin/dealer-portal/modules/${item.id}`, {
        method: 'PATCH',
        headers: { ...authHeader, 'Content-Type': 'application/json' },
        body: JSON.stringify({ visible }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(resolveErrorMessage(data, 'Modül görünürlüğü güncellenemedi'));
      setLastSavedAt(new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
      await fetchAll();
    } catch (err) {
      setError(err?.message || 'Modül görünürlüğü güncellenemedi');
      toast({ title: 'Güncelleme başarısız', description: err?.message || 'Modül görünürlüğü güncellenemedi', variant: 'destructive' });
    }
  };

  const sidebarItems = navItems.filter((row) => row.location === 'sidebar').sort((a, b) => a.order_index - b.order_index);
  const headerItems = navItems.filter((row) => row.location === 'header').sort((a, b) => a.order_index - b.order_index);
  const sortedModules = [...modules].sort((a, b) => a.order_index - b.order_index);

  const handleDragEnd = async (event, rows, setRows, persistFn) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    const oldIndex = rows.findIndex((row) => row.id === active.id);
    const newIndex = rows.findIndex((row) => row.id === over.id);
    if (oldIndex < 0 || newIndex < 0) return;
    const next = arrayMove(rows, oldIndex, newIndex);
    setRows((prev) => {
      const others = prev.filter((row) => !rows.some((it) => it.id === row.id));
      return [...others, ...next];
    });
    await persistFn(next);
  };

  return (
    <div className="space-y-4" data-testid="admin-dealer-config-page">
      <div className="flex items-center justify-between" data-testid="admin-dealer-config-header">
        <div>
          <h1 className="text-2xl font-semibold" data-testid="admin-dealer-config-title">Kurumsal Menü Yönetimi</h1>
          <p className="text-sm text-slate-600" data-testid="admin-dealer-config-subtitle">Sadece manuel kontrol: sıralama + görünürlük.</p>
          <p className="text-xs text-slate-500" data-testid="admin-dealer-config-save-meta">
            {lastSavedAt ? `Son kaydetme: ${lastSavedAt}` : 'Henüz sıralama kaydı yok'}
          </p>
        </div>
        <button onClick={fetchAll} className="h-9 rounded-md border px-3 text-sm" data-testid="admin-dealer-config-refresh">Yenile</button>
      </div>

      {(loading || saving) && <div className="text-sm text-slate-500" data-testid="admin-dealer-config-loading">İşleniyor...</div>}
      {error && <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700" data-testid="admin-dealer-config-error">{error}</div>}

      <div className="grid gap-4 lg:grid-cols-2" data-testid="admin-dealer-config-grid">
        <div className="space-y-3 rounded-xl border bg-white p-4" data-testid="admin-dealer-config-sidebar-card">
          <h2 className="text-lg font-semibold" data-testid="admin-dealer-config-sidebar-title">Sidebar</h2>
          <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={(event) => handleDragEnd(event, sidebarItems, setNavItems, (rows) => persistNavOrder('sidebar', rows))}>
            <SortableContext items={sidebarItems.map((row) => row.id)} strategy={verticalListSortingStrategy}>
              <div className="space-y-2" data-testid="admin-dealer-config-sidebar-list">
                {sidebarItems.map((item) => (
                  <SortableRow key={item.id} item={item} onToggle={updateNavVisibility} testIdPrefix="admin-dealer-sidebar" />
                ))}
              </div>
            </SortableContext>
          </DndContext>
        </div>

        <div className="space-y-3 rounded-xl border bg-white p-4" data-testid="admin-dealer-config-header-card">
          <h2 className="text-lg font-semibold" data-testid="admin-dealer-config-header-title-quick">Header 1. Satır (Sabit + Manuel Sıralama)</h2>
          <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={(event) => handleDragEnd(event, headerItems, setNavItems, (rows) => persistNavOrder('header', rows))}>
            <SortableContext items={headerItems.map((row) => row.id)} strategy={verticalListSortingStrategy}>
              <div className="space-y-2" data-testid="admin-dealer-config-header-list">
                {headerItems.map((item) => (
                  <SortableRow key={item.id} item={item} onToggle={updateNavVisibility} testIdPrefix="admin-dealer-header" />
                ))}
              </div>
            </SortableContext>
          </DndContext>
        </div>
      </div>

      <div className="rounded-xl border bg-white p-4" data-testid="admin-dealer-config-modules-card">
        <h2 className="text-lg font-semibold mb-3" data-testid="admin-dealer-config-modules-title">Header 2. Satır (Modül Bazlı Manuel Sıralama)</h2>
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={(event) => handleDragEnd(event, sortedModules, setModules, persistModuleOrder)}>
          <SortableContext items={sortedModules.map((row) => row.id)} strategy={verticalListSortingStrategy}>
            <div className="space-y-2" data-testid="admin-dealer-config-modules-list">
              {sortedModules.map((item) => (
                <SortableRow key={item.id} item={item} onToggle={updateModuleVisibility} testIdPrefix="admin-dealer-module" />
              ))}
            </div>
          </SortableContext>
        </DndContext>
      </div>

      <div className="rounded-xl border bg-white p-4" data-testid="admin-dealer-config-preview-card">
        <h2 className="text-lg font-semibold" data-testid="admin-dealer-config-preview-title">Önizleme (Dealer görünümü)</h2>
        <div className="mt-3 grid gap-3 md:grid-cols-4 text-sm" data-testid="admin-dealer-config-preview-grid">
          <div data-testid="admin-dealer-config-preview-header-items">
            <div className="font-medium">Header 1. Satır</div>
            <ul className="list-disc pl-5">
              {(preview.header_row1_items || preview.header_items || []).map((row) => <li key={row.id} data-testid={`admin-dealer-config-preview-header-${row.key}`}>{row.label_i18n_key}</li>)}
            </ul>
          </div>
          <div data-testid="admin-dealer-config-preview-header-modules-items">
            <div className="font-medium">Header 2. Satır</div>
            <ul className="list-disc pl-5">
              {(preview.header_row2_modules || preview.modules || []).map((row) => <li key={row.id} data-testid={`admin-dealer-config-preview-header-module-${row.key}`}>{row.title_i18n_key}</li>)}
            </ul>
          </div>
          <div data-testid="admin-dealer-config-preview-header-controls-items">
            <div className="font-medium">Header 3. Satır</div>
            <ul className="list-disc pl-5">
              <li data-testid="admin-dealer-config-preview-header-row3-store">Mağaza filtresi: {String(preview?.header_row3_controls?.store_filter_enabled !== false)}</li>
              <li data-testid="admin-dealer-config-preview-header-row3-user">Kullanıcı dropdown: {String(preview?.header_row3_controls?.user_dropdown_enabled !== false)}</li>
            </ul>
          </div>
          <div data-testid="admin-dealer-config-preview-sidebar-items">
            <div className="font-medium">Sidebar</div>
            <ul className="list-disc pl-5">
              {(preview.sidebar_items || []).map((row) => <li key={row.id} data-testid={`admin-dealer-config-preview-sidebar-${row.key}`}>{row.label_i18n_key}</li>)}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
