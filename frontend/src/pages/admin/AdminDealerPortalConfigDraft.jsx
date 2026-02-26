import React, { useEffect, useMemo, useRef, useState } from 'react';
import { DndContext, PointerSensor, KeyboardSensor, useSensor, useSensors, closestCenter } from '@dnd-kit/core';
import { arrayMove, SortableContext, sortableKeyboardCoordinates, useSortable, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { useToast } from '@/components/ui/toaster';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function SortableRow({ id, children, testId }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id });
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.7 : 1,
  };

  return (
    <div ref={setNodeRef} style={style} className="rounded-lg border bg-white p-3 shadow-sm" data-testid={testId}>
      <div className="flex items-center justify-between gap-3">
        <button
          type="button"
          className="rounded border px-2 py-1 text-xs text-slate-600"
          {...attributes}
          {...listeners}
          data-testid={`${testId}-drag`}
        >
          Sürükle
        </button>
        <div className="flex-1">{children}</div>
      </div>
    </div>
  );
}

const cloneSnapshot = (snapshot) => ({
  nav_items: JSON.parse(JSON.stringify(snapshot?.nav_items || [])),
  modules: JSON.parse(JSON.stringify(snapshot?.modules || [])),
});

const normalizeOrder = (rows) => rows.map((row, index) => ({ ...row, order_index: (index + 1) * 10 }));

export default function AdminDealerPortalConfigDraft() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [error, setError] = useState('');
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
  const [revisions, setRevisions] = useState([]);
  const [draftMeta, setDraftMeta] = useState(null);
  const [lastSavedAt, setLastSavedAt] = useState('');
  const [revisionStack, setRevisionStack] = useState([]);

  const baselineSnapshotRef = useRef({ nav_items: [], modules: [] });

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 4 } }),
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

  const currentSnapshot = useMemo(
    () => ({ nav_items: navItems, modules }),
    [navItems, modules],
  );

  const hasUnsavedChanges = useMemo(() => {
    return JSON.stringify(currentSnapshot) !== JSON.stringify(baselineSnapshotRef.current);
  }, [currentSnapshot]);

  const headerItems = useMemo(
    () => navItems.filter((item) => item.location === 'header').sort((a, b) => a.order_index - b.order_index),
    [navItems],
  );

  const sidebarItems = useMemo(
    () => navItems.filter((item) => item.location === 'sidebar').sort((a, b) => a.order_index - b.order_index),
    [navItems],
  );

  const changeSummary = useMemo(() => {
    const baseline = baselineSnapshotRef.current;
    const baseNavByKey = new Map((baseline.nav_items || []).map((item) => [item.key, item]));
    const baseModuleByKey = new Map((baseline.modules || []).map((item) => [item.key, item]));

    const navOrderChanges = [];
    const moduleOrderChanges = [];

    navItems.forEach((item) => {
      const old = baseNavByKey.get(item.key);
      if (!old) return;
      if (Number(old.order_index) !== Number(item.order_index)) {
        navOrderChanges.push(`${item.key}: ${old.order_index} → ${item.order_index}`);
      }
    });

    modules.forEach((item) => {
      const old = baseModuleByKey.get(item.key);
      if (!old) return;
      if (Number(old.order_index) !== Number(item.order_index)) {
        moduleOrderChanges.push(`${item.key}: ${old.order_index} → ${item.order_index}`);
      }
    });

    return {
      navOrderChanges,
      moduleOrderChanges,
      total: navOrderChanges.length + moduleOrderChanges.length,
    };
  }, [navItems, modules]);

  const fetchDraftConfig = async () => {
    const res = await fetch(`${API}/admin/dealer-portal/config?mode=draft`, { headers: authHeader });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(resolveErrorMessage(data, 'Dealer draft config yüklenemedi'));
    return data;
  };

  const fetchPreview = async () => {
    const res = await fetch(`${API}/admin/dealer-portal/config/preview?mode=draft`, { headers: authHeader });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(resolveErrorMessage(data, 'Dealer preview yüklenemedi'));
    return data;
  };

  const fetchRevisions = async () => {
    const res = await fetch(`${API}/admin/dealer-portal/config/revisions`, { headers: authHeader });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(resolveErrorMessage(data, 'Revision listesi yüklenemedi'));
    return data;
  };

  const fetchAll = async () => {
    setLoading(true);
    setError('');
    try {
      const [configPayload, previewPayload, revisionsPayload] = await Promise.all([
        fetchDraftConfig(),
        fetchPreview(),
        fetchRevisions(),
      ]);

      const nextNav = Array.isArray(configPayload?.nav_items) ? configPayload.nav_items : [];
      const nextModules = Array.isArray(configPayload?.modules) ? configPayload.modules : [];

      setNavItems(nextNav);
      setModules(nextModules);
      setDraftMeta(configPayload?.draft || null);
      setPreview(previewPayload || {
        header_items: [],
        header_row1_items: [],
        header_row1_fixed_blocks: [],
        header_row2_modules: [],
        header_row3_controls: {},
        sidebar_items: [],
        modules: [],
      });
      setRevisions(Array.isArray(revisionsPayload?.items) ? revisionsPayload.items : []);

      baselineSnapshotRef.current = cloneSnapshot({ nav_items: nextNav, modules: nextModules });
      setRevisionStack([]);
    } catch (err) {
      setError(err?.message || 'Dealer draft config yüklenemedi');
      setNavItems([]);
      setModules([]);
      setPreview({ header_items: [], sidebar_items: [], modules: [] });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAll();
  }, []);

  useEffect(() => {
    const onBeforeUnload = (event) => {
      if (!hasUnsavedChanges) return;
      event.preventDefault();
      event.returnValue = 'Kaydedilmemiş değişiklikler var. Sayfadan ayrılmak istediğinize emin misiniz?';
    };
    window.addEventListener('beforeunload', onBeforeUnload);
    return () => window.removeEventListener('beforeunload', onBeforeUnload);
  }, [hasUnsavedChanges]);

  const pushRevisionSnapshot = () => {
    setRevisionStack((prev) => [...prev.slice(-19), cloneSnapshot(currentSnapshot)]);
  };

  const updateNavItemsLocal = (updater) => {
    pushRevisionSnapshot();
    setNavItems((prev) => updater(prev));
  };

  const updateModulesLocal = (updater) => {
    pushRevisionSnapshot();
    setModules((prev) => updater(prev));
  };

  const handleDragEnd = (event, rows, updateFn) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    const oldIndex = rows.findIndex((row) => row.id === active.id);
    const newIndex = rows.findIndex((row) => row.id === over.id);
    if (oldIndex < 0 || newIndex < 0) return;
    const reordered = normalizeOrder(arrayMove(rows, oldIndex, newIndex));
    updateFn((prev) => {
      const map = new Map(reordered.map((row) => [row.id, row]));
      return prev
        .map((row) => (map.has(row.id) ? map.get(row.id) : row))
        .sort((a, b) => {
          if (a.location !== b.location) return a.location.localeCompare(b.location);
          return Number(a.order_index || 0) - Number(b.order_index || 0);
        });
    });
  };

  const toggleNavVisibilityLocal = (item, visible) => {
    updateNavItemsLocal((prev) => prev.map((row) => (row.id === item.id ? { ...row, visible } : row)));
  };

  const toggleModuleVisibilityLocal = (item, visible) => {
    updateModulesLocal((prev) => prev.map((row) => (row.id === item.id ? { ...row, visible } : row)));
  };

  const undoLastChange = () => {
    setRevisionStack((prev) => {
      if (!prev.length) return prev;
      const next = [...prev];
      const snapshot = next.pop();
      setNavItems(snapshot.nav_items || []);
      setModules(snapshot.modules || []);
      return next;
    });
  };

  const saveDraft = async () => {
    setSaving(true);
    setError('');
    try {
      const res = await fetch(`${API}/admin/dealer-portal/config/draft/save`, {
        method: 'POST',
        headers: { ...authHeader, 'Content-Type': 'application/json' },
        body: JSON.stringify({ nav_items: navItems, modules }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(resolveErrorMessage(data, 'Taslak kaydedilemedi'));

      setDraftMeta(data?.draft || draftMeta);
      baselineSnapshotRef.current = cloneSnapshot(currentSnapshot);
      setRevisionStack([]);
      setLastSavedAt(new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit', second: '2-digit' }));

      const previewPayload = await fetchPreview();
      setPreview(previewPayload);
      toast({ title: 'Taslak kaydedildi', description: 'Değişiklikler draft olarak saklandı.' });
    } catch (err) {
      setError(err?.message || 'Taslak kaydedilemedi');
      toast({ title: 'Kaydetme başarısız', description: err?.message || 'Taslak kaydedilemedi', variant: 'destructive' });
    } finally {
      setSaving(false);
    }
  };

  const publishDraft = async () => {
    if (hasUnsavedChanges) {
      toast({ title: 'Önce kaydet', description: 'Yayınlamadan önce taslağı kaydetmelisiniz.', variant: 'destructive' });
      return;
    }

    setPublishing(true);
    try {
      const res = await fetch(`${API}/admin/dealer-portal/config/draft/publish`, {
        method: 'POST',
        headers: { ...authHeader, 'Content-Type': 'application/json' },
        body: JSON.stringify({ note: 'Admin panel publish' }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(resolveErrorMessage(data, 'Taslak yayınlanamadı'));

      toast({ title: 'Yayınlandı', description: `Revision #${data?.published?.revision_no || '-'}` });
      await fetchAll();
    } catch (err) {
      setError(err?.message || 'Taslak yayınlanamadı');
      toast({ title: 'Publish başarısız', description: err?.message || 'Taslak yayınlanamadı', variant: 'destructive' });
    } finally {
      setPublishing(false);
    }
  };

  const rollbackToRevision = async (revisionId) => {
    if (!window.confirm('Seçilen revizyona dönmek istediğinize emin misiniz?')) {
      return;
    }

    try {
      const res = await fetch(`${API}/admin/dealer-portal/config/rollback`, {
        method: 'POST',
        headers: { ...authHeader, 'Content-Type': 'application/json' },
        body: JSON.stringify({ revision_id: revisionId }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(resolveErrorMessage(data, 'Rollback başarısız'));
      toast({ title: 'Rollback tamamlandı', description: `Yeni revision: #${data?.published?.revision_no || '-'}` });
      await fetchAll();
    } catch (err) {
      setError(err?.message || 'Rollback başarısız');
      toast({ title: 'Rollback başarısız', description: err?.message || 'Rollback başarısız', variant: 'destructive' });
    }
  };

  return (
    <div className="space-y-6" data-testid="admin-dealer-config-page">
      <div className="flex flex-wrap items-center justify-between gap-3" data-testid="admin-dealer-config-header">
        <div>
          <h1 className="text-2xl font-semibold" data-testid="admin-dealer-config-title">Kurumsal Menü Yönetimi (Draft Mode)</h1>
          <p className="text-sm text-slate-600" data-testid="admin-dealer-config-subtitle">Undo + Draft Save + Publish + Rollback</p>
          <p className="text-xs text-slate-500" data-testid="admin-dealer-config-save-meta">
            {lastSavedAt ? `Son draft kaydı: ${lastSavedAt}` : 'Henüz draft kaydı yok'}
          </p>
          <div className="mt-1 text-xs text-slate-500" data-testid="admin-dealer-config-draft-meta">
            Draft ID: {draftMeta?.id || '-'} • Revision: #{draftMeta?.revision_no || '-'}
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2" data-testid="admin-dealer-config-actions">
          <button onClick={undoLastChange} disabled={!revisionStack.length || saving || publishing} className="h-9 rounded-md border px-3 text-sm" data-testid="admin-dealer-config-undo">Son işlemi geri al</button>
          <button onClick={saveDraft} disabled={saving || publishing || !hasUnsavedChanges} className="h-9 rounded-md border px-3 text-sm" data-testid="admin-dealer-config-save-draft">{saving ? 'Kaydediliyor...' : 'Taslağı Kaydet'}</button>
          <button onClick={publishDraft} disabled={publishing || saving} className="h-9 rounded-md bg-slate-900 px-3 text-sm text-white" data-testid="admin-dealer-config-publish">{publishing ? 'Yayınlanıyor...' : 'Yayınla'}</button>
          <button onClick={fetchAll} className="h-9 rounded-md border px-3 text-sm" data-testid="admin-dealer-config-refresh">Yenile</button>
        </div>
      </div>

      {hasUnsavedChanges && (
        <div className="rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-800" data-testid="admin-dealer-config-unsaved-warning">
          Persist edilmemiş değişiklikler var. Sayfadan ayrılırsanız kaybolabilir.
        </div>
      )}

      {error ? (
        <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700" data-testid="admin-dealer-config-error">{error}</div>
      ) : null}

      <div className="rounded-xl border bg-white p-4" data-testid="admin-dealer-config-diff-panel">
        <h2 className="text-lg font-semibold" data-testid="admin-dealer-config-diff-title">Değişiklik Özeti</h2>
        <div className="mt-2 text-sm text-slate-600" data-testid="admin-dealer-config-diff-total">Toplam fark: {changeSummary.total}</div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2" data-testid="admin-dealer-config-nav-sections">
        <div className="space-y-3 rounded-xl border bg-white p-4" data-testid="admin-dealer-config-header-card">
          <h2 className="text-lg font-semibold" data-testid="admin-dealer-config-header-title-quick">Header 1. Satır</h2>
          <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={(event) => handleDragEnd(event, headerItems, updateNavItemsLocal)}>
            <SortableContext items={headerItems.map((row) => row.id)} strategy={verticalListSortingStrategy}>
              <div className="space-y-2" data-testid="admin-dealer-config-header-list">
                {headerItems.map((item) => (
                  <SortableRow key={item.id} id={item.id} testId={`admin-dealer-config-header-item-${item.key}`}>
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-sm" data-testid={`admin-dealer-config-header-item-label-${item.key}`}>{item.label_i18n_key}</div>
                      <label className="inline-flex items-center gap-2 text-xs" data-testid={`admin-dealer-config-header-item-visibility-${item.key}`}>
                        <input type="checkbox" checked={Boolean(item.visible)} onChange={(e) => toggleNavVisibilityLocal(item, e.target.checked)} />
                        Görünür
                      </label>
                    </div>
                  </SortableRow>
                ))}
              </div>
            </SortableContext>
          </DndContext>
        </div>

        <div className="space-y-3 rounded-xl border bg-white p-4" data-testid="admin-dealer-config-sidebar-card">
          <h2 className="text-lg font-semibold" data-testid="admin-dealer-config-sidebar-title">Sidebar</h2>
          <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={(event) => handleDragEnd(event, sidebarItems, updateNavItemsLocal)}>
            <SortableContext items={sidebarItems.map((row) => row.id)} strategy={verticalListSortingStrategy}>
              <div className="space-y-2" data-testid="admin-dealer-config-sidebar-list">
                {sidebarItems.map((item) => (
                  <SortableRow key={item.id} id={item.id} testId={`admin-dealer-config-sidebar-item-${item.key}`}>
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-sm" data-testid={`admin-dealer-config-sidebar-item-label-${item.key}`}>{item.label_i18n_key}</div>
                      <label className="inline-flex items-center gap-2 text-xs" data-testid={`admin-dealer-config-sidebar-item-visibility-${item.key}`}>
                        <input type="checkbox" checked={Boolean(item.visible)} onChange={(e) => toggleNavVisibilityLocal(item, e.target.checked)} />
                        Görünür
                      </label>
                    </div>
                  </SortableRow>
                ))}
              </div>
            </SortableContext>
          </DndContext>
        </div>
      </div>

      <div className="rounded-xl border bg-white p-4" data-testid="admin-dealer-config-modules-card">
        <h2 className="text-lg font-semibold mb-3" data-testid="admin-dealer-config-modules-title">Header 2. Satır</h2>
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={(event) => handleDragEnd(event, modules, updateModulesLocal)}>
          <SortableContext items={modules.map((row) => row.id)} strategy={verticalListSortingStrategy}>
            <div className="space-y-2" data-testid="admin-dealer-config-modules-list">
              {modules.map((item) => (
                <SortableRow key={item.id} id={item.id} testId={`admin-dealer-config-module-item-${item.key}`}>
                  <div className="flex items-center justify-between gap-3">
                    <div className="text-sm" data-testid={`admin-dealer-config-module-item-label-${item.key}`}>{item.title_i18n_key}</div>
                    <label className="inline-flex items-center gap-2 text-xs" data-testid={`admin-dealer-config-module-item-visibility-${item.key}`}>
                      <input type="checkbox" checked={Boolean(item.visible)} onChange={(e) => toggleModuleVisibilityLocal(item, e.target.checked)} />
                      Görünür
                    </label>
                  </div>
                </SortableRow>
              ))}
            </div>
          </SortableContext>
        </DndContext>
      </div>

      <div className="rounded-xl border bg-white p-4" data-testid="admin-dealer-config-preview-card">
        <h2 className="text-lg font-semibold" data-testid="admin-dealer-config-preview-title">Preview Mode (Draft)</h2>
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

      <div className="rounded-xl border bg-white p-4" data-testid="admin-dealer-config-revisions-card">
        <h2 className="text-lg font-semibold" data-testid="admin-dealer-config-revisions-title">Revision Listesi / Rollback</h2>
        <div className="mt-3 space-y-2" data-testid="admin-dealer-config-revisions-list">
          {revisions.length === 0 ? (
            <div className="text-sm text-slate-500" data-testid="admin-dealer-config-revisions-empty">Revision bulunamadı.</div>
          ) : revisions.map((rev) => (
            <div key={rev.id} className="flex flex-wrap items-center justify-between gap-2 rounded border p-2" data-testid={`admin-dealer-config-revision-${rev.id}`}>
              <div className="text-xs text-slate-700" data-testid={`admin-dealer-config-revision-meta-${rev.id}`}>
                #{rev.revision_no} • {rev.state} • {rev.published_at || rev.created_at}
              </div>
              <button type="button" className="rounded border px-2 py-1 text-xs" onClick={() => rollbackToRevision(rev.id)} data-testid={`admin-dealer-config-revision-rollback-${rev.id}`}>
                Bu revizyona dön
              </button>
            </div>
          ))}
        </div>
      </div>

      {loading ? <div className="text-xs text-slate-500" data-testid="admin-dealer-config-loading">Yükleniyor...</div> : null}
    </div>
  );
}
