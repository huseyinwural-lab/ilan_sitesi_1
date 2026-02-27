import React, { useEffect, useMemo, useRef, useState } from 'react';
import { DndContext, PointerSensor, KeyboardSensor, useSensor, useSensors, closestCenter } from '@dnd-kit/core';
import { SortableContext, useSortable, arrayMove, rectSortingStrategy, sortableKeyboardCoordinates } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { toast } from 'sonner';

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const MAX_WIDGETS = 12;

const WIDGET_PALETTE = [
  { type: 'kpi', title: 'KPI', width: 3 },
  { type: 'chart', title: 'Grafik', width: 6 },
  { type: 'list', title: 'Liste', width: 6 },
  { type: 'package_summary', title: 'Paket Özeti', width: 3 },
  { type: 'doping_summary', title: 'Doping Özeti', width: 3 },
];

const getPaletteByType = (type) => WIDGET_PALETTE.find((item) => item.type === type);

const normalizeWidgetType = (type) => {
  const safe = `${type || ''}`.trim().toLowerCase();
  if (safe === 'package-summary') return 'package_summary';
  if (safe === 'doping-summary') return 'doping_summary';
  return safe;
};

const buildLayoutFromWidgets = (widgets, previousLayout = []) => {
  const previousMap = new Map((Array.isArray(previousLayout) ? previousLayout : []).map((item) => [item.widget_id, item]));
  let cursorX = 0;
  let cursorY = 0;

  return widgets.map((widget) => {
    const previous = previousMap.get(widget.widget_id) || {};
    const palette = getPaletteByType(widget.widget_type);
    const width = Math.min(12, Math.max(1, Number(previous.w || palette?.width || 3)));
    const height = Math.max(1, Number(previous.h || 1));
    if (cursorX + width > 12) {
      cursorX = 0;
      cursorY += 1;
    }
    const next = {
      widget_id: widget.widget_id,
      x: cursorX,
      y: cursorY,
      w: width,
      h: height,
    };
    cursorX += width;
    return next;
  });
};

const normalizeDashboard = (item) => {
  const widgetsRaw = Array.isArray(item?.widgets)
    ? item.widgets
    : Array.isArray(item?.config_data?.widgets)
      ? item.config_data.widgets
      : [];

  const widgets = widgetsRaw
    .filter((widget) => widget && typeof widget === 'object')
    .map((widget, index) => {
      const widgetType = normalizeWidgetType(widget.widget_type || widget.type || 'list');
      const palette = getPaletteByType(widgetType);
      return {
        widget_id: `${widget.widget_id || widget.id || `${widgetType}-${index + 1}`}`,
        widget_type: widgetType,
        title: `${widget.title || palette?.title || widgetType}`,
        enabled: widget.enabled !== false,
      };
    });

  const layoutRaw = Array.isArray(item?.layout)
    ? item.layout
    : Array.isArray(item?.config_data?.layout)
      ? item.config_data.layout
      : [];
  const layout = buildLayoutFromWidgets(widgets, layoutRaw);

  return {
    widgets,
    layout,
    configData: item?.config_data && typeof item.config_data === 'object' ? item.config_data : { title: 'Dealer Dashboard V2' },
  };
};

const parseApiError = (payload, statusCode = 0) => {
  const detail = payload?.detail;
  if (detail && typeof detail === 'object') {
    return {
      code: detail.code || 'UNKNOWN',
      message: detail.message || 'İşlem başarısız',
      status: statusCode,
      raw: detail,
    };
  }
  return {
    code: statusCode === 409 ? 'CONFIG_VERSION_CONFLICT' : 'UNKNOWN',
    message: typeof detail === 'string' ? detail : 'İşlem başarısız',
    status: statusCode,
    raw: detail || {},
  };
};

const normalizeDiffWidgets = (item) => {
  if (!item || typeof item !== 'object') return [];
  const widgets = Array.isArray(item.widgets)
    ? item.widgets
    : Array.isArray(item.config_data?.widgets)
      ? item.config_data.widgets
      : [];
  return widgets
    .filter((widget) => widget && typeof widget === 'object')
    .map((widget, index) => ({
      widget_id: `${widget.widget_id || widget.id || `widget-${index + 1}`}`,
      widget_type: `${widget.widget_type || widget.type || 'widget'}`,
      title: `${widget.title || widget.widget_type || widget.type || 'Widget'}`,
    }));
};

const stableStringify = (value) => {
  if (Array.isArray(value)) {
    return `[${value.map((item) => stableStringify(item)).join(',')}]`;
  }
  if (value && typeof value === 'object') {
    const keys = Object.keys(value).sort();
    return `{${keys.map((key) => `${JSON.stringify(key)}:${stableStringify(value[key])}`).join(',')}}`;
  }
  return JSON.stringify(value);
};

const simpleHash = (value) => {
  const str = stableStringify(value);
  let hash = 5381;
  for (let i = 0; i < str.length; i += 1) {
    hash = ((hash << 5) + hash) + str.charCodeAt(i);
    hash &= 0xffffffff;
  }
  return `h${Math.abs(hash)}`;
};

const buildDraftHashPayload = ({ widgets, layout, configData, scope, scopeId }) => ({
  widgets,
  layout,
  configData,
  scope,
  scopeId: scope === 'tenant' ? (scopeId || '').trim() : null,
});

const SortableWidgetCard = ({ widget, width, largeScreen, onRemove, onToggleEnabled }) => {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: widget.widget_id });
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.75 : 1,
    gridColumn: `span ${largeScreen ? width : 12} / span ${largeScreen ? width : 12}`,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="rounded-xl border bg-white p-3 shadow-sm"
      data-testid={`ui-designer-dashboard-widget-${widget.widget_id}`}
    >
      <div className="flex flex-wrap items-center justify-between gap-2" data-testid={`ui-designer-dashboard-widget-header-${widget.widget_id}`}>
        <div>
          <p className="text-sm font-semibold text-slate-900" data-testid={`ui-designer-dashboard-widget-title-${widget.widget_id}`}>{widget.title}</p>
          <p className="text-xs text-slate-500" data-testid={`ui-designer-dashboard-widget-type-${widget.widget_id}`}>{widget.widget_type}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            className="rounded border px-2 py-1 text-xs text-slate-600"
            {...attributes}
            {...listeners}
            data-testid={`ui-designer-dashboard-widget-drag-${widget.widget_id}`}
          >
            Sürükle
          </button>
          <label className="inline-flex items-center gap-1 text-xs text-slate-600" data-testid={`ui-designer-dashboard-widget-enabled-wrap-${widget.widget_id}`}>
            <input
              type="checkbox"
              checked={widget.enabled !== false}
              onChange={(event) => onToggleEnabled(widget.widget_id, event.target.checked)}
              data-testid={`ui-designer-dashboard-widget-enabled-${widget.widget_id}`}
            />
            Görünür
          </label>
          <button
            type="button"
            onClick={() => onRemove(widget.widget_id)}
            className="rounded border border-rose-200 px-2 py-1 text-xs text-rose-600"
            data-testid={`ui-designer-dashboard-widget-remove-${widget.widget_id}`}
          >
            Kaldır
          </button>
        </div>
      </div>
    </div>
  );
};

export const CorporateDashboardDesigner = () => {
  const authHeader = useMemo(() => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` }), []);
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 4 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  const [scope, setScope] = useState('system');
  const [scopeId, setScopeId] = useState('');
  const [widgets, setWidgets] = useState([]);
  const [layout, setLayout] = useState([]);
  const [configData, setConfigData] = useState({ title: 'Dealer Dashboard V2' });
  const [latestConfigId, setLatestConfigId] = useState(null);
  const [latestConfigVersion, setLatestConfigVersion] = useState(null);
  const [latestResolvedHash, setLatestResolvedHash] = useState('');
  const [versions, setVersions] = useState([]);
  const [effectivePayload, setEffectivePayload] = useState(null);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [isPublishOpen, setIsPublishOpen] = useState(false);
  const [isRollbackOpen, setIsRollbackOpen] = useState(false);
  const [confirmChecked, setConfirmChecked] = useState(false);
  const [selectedRollbackId, setSelectedRollbackId] = useState('');
  const [diffPayload, setDiffPayload] = useState({});
  const [publishDiffContext, setPublishDiffContext] = useState({ fromItem: null, toItem: null });
  const [conflictInfo, setConflictInfo] = useState(null);
  const [conflictOpen, setConflictOpen] = useState(false);
  const [rollbackReason, setRollbackReason] = useState('');
  const [serverDraftHash, setServerDraftHash] = useState('');
  const [publishRetryCount, setPublishRetryCount] = useState(0);
  const [publishAuditItems, setPublishAuditItems] = useState([]);
  const [publishTelemetry, setPublishTelemetry] = useState(null);
  const [largeScreen, setLargeScreen] = useState(typeof window !== 'undefined' ? window.innerWidth >= 1024 : true);

  const initializedRef = useRef(false);
  const autoSaveRef = useRef(null);
  const lastSavedHashRef = useRef('');

  const scopeQuery = scope === 'tenant' && scopeId.trim() ? `&scope_id=${encodeURIComponent(scopeId.trim())}` : '';
  const tenantQuery = scope === 'tenant' && scopeId.trim() ? `&tenant_id=${encodeURIComponent(scopeId.trim())}` : '';

  const snapshotHash = useMemo(
    () => JSON.stringify({ widgets, layout, configData, scope, scopeId: scope === 'tenant' ? scopeId.trim() : null }),
    [widgets, layout, configData, scope, scopeId],
  );

  const localDraftHash = useMemo(
    () => simpleHash(buildDraftHashPayload({ widgets, layout, configData, scope, scopeId })),
    [widgets, layout, configData, scope, scopeId],
  );

  const driftMismatch = useMemo(
    () => Boolean(serverDraftHash) && localDraftHash !== serverDraftHash,
    [localDraftHash, serverDraftHash],
  );

  const enabledKpiCount = useMemo(
    () => widgets.filter((widget) => widget.widget_type === 'kpi' && widget.enabled !== false).length,
    [widgets],
  );

  const publishDisabledReason = useMemo(() => {
    if (widgets.length > MAX_WIDGETS) return 'En fazla 12 widget ekleyebilirsiniz';
    if (enabledKpiCount < 1) return 'En az 1 görünür KPI widget zorunludur';
    return '';
  }, [enabledKpiCount, widgets.length]);

  const payloadForSave = useMemo(
    () => ({
      segment: 'corporate',
      scope,
      scope_id: scope === 'tenant' ? scopeId.trim() : null,
      status: 'draft',
      config_data: { ...configData, title: configData?.title || 'Dealer Dashboard V2' },
      layout,
      widgets,
    }),
    [configData, layout, scope, scopeId, widgets],
  );

  const loadDraft = async ({ silent = false } = {}) => {
    if (!silent) {
      setStatus('');
      setError('');
    }
    try {
      const response = await fetch(
        `${API}/admin/ui/configs/dashboard?segment=corporate&scope=${scope}${scopeQuery}&status=draft`,
        { headers: authHeader },
      );
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data?.detail || 'Dashboard taslağı yüklenemedi');
      }

      const normalized = normalizeDashboard(data?.item || {});
      setWidgets(normalized.widgets);
      setLayout(normalized.layout);
      setConfigData(normalized.configData);
      setLatestConfigId(data?.item?.id || null);
      setLatestConfigVersion(data?.item?.version ?? null);
      setLatestResolvedHash(data?.item?.resolved_config_hash || '');
      setVersions(Array.isArray(data?.items) ? data.items : []);
      setSelectedRollbackId('');
      if (!silent) {
        setStatus('Dashboard taslağı yüklendi');
      }

      const nextHash = JSON.stringify({
        widgets: normalized.widgets,
        layout: normalized.layout,
        configData: normalized.configData,
        scope,
        scopeId: scope === 'tenant' ? scopeId.trim() : null,
      });
      lastSavedHashRef.current = nextHash;
      setServerDraftHash(simpleHash(buildDraftHashPayload({
        widgets: normalized.widgets,
        layout: normalized.layout,
        configData: normalized.configData,
        scope,
        scopeId,
      })));
      initializedRef.current = true;
      return data;
    } catch (requestError) {
      setError(requestError.message || 'Dashboard taslağı yüklenemedi');
      setWidgets([]);
      setLayout([]);
      setConfigData({ title: 'Dealer Dashboard V2' });
      setLatestConfigId(null);
      setLatestConfigVersion(null);
      setLatestResolvedHash('');
      setVersions([]);
      setSelectedRollbackId('');
      setServerDraftHash('');
      return null;
    }
  };

  const loadEffective = async () => {
    try {
      const response = await fetch(`${API}/ui/dashboard?segment=corporate${tenantQuery}`, { headers: authHeader });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data?.detail || 'Canlı dashboard okunamadı');
      }
      setEffectivePayload(data);
    } catch (requestError) {
      setError(requestError.message || 'Canlı dashboard okunamadı');
    }
  };

  const loadPublishAudits = async () => {
    try {
      const response = await fetch(
        `${API}/admin/ui/configs/dashboard/publish-audits?segment=corporate&scope=${scope}${scopeQuery}&limit=25`,
        { headers: authHeader },
      );
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(parseApiError(data, response.status).message || 'Publish audit verisi alınamadı');
      }
      setPublishAuditItems(Array.isArray(data?.items) ? data.items : []);
      setPublishTelemetry(data?.telemetry || null);
    } catch (_) {
      setPublishAuditItems([]);
      setPublishTelemetry(null);
    }
  };

  const saveDraft = async (silent = false) => {
    setSaving(true);
    if (!silent) {
      setStatus('');
      setError('');
    }
    try {
      const response = await fetch(`${API}/admin/ui/configs/dashboard`, {
        method: 'POST',
        headers: {
          ...authHeader,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payloadForSave),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(parseApiError(data, response.status).message || 'Taslak kaydedilemedi');
      }

      setLatestConfigId(data?.item?.id || null);
      setLatestConfigVersion(data?.item?.version ?? null);
      lastSavedHashRef.current = snapshotHash;
      setStatus(`Taslak kaydedildi (v${data?.item?.version || '-'})`);
      if (silent) {
        toast.success('Dashboard taslağı otomatik kaydedildi');
      }
      await loadDraft({ silent: true });
      await loadPublishAudits();
    } catch (requestError) {
      setError(requestError.message || 'Taslak kaydedilemedi');
      if (silent) {
        toast.error(requestError.message || 'Otomatik kaydetme başarısız');
      }
    } finally {
      setSaving(false);
    }
  };

  const loadDiff = async () => {
    const response = await fetch(
      `${API}/admin/ui/configs/dashboard/diff?segment=corporate&scope=${scope}${scopeQuery}&from_status=published&to_status=draft`,
      { headers: authHeader },
    );
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const apiError = parseApiError(data, response.status);
      throw new Error(apiError.message || 'Diff bilgisi alınamadı');
    }
    setDiffPayload(data?.diff || {});
    setPublishDiffContext({
      fromItem: data?.from_item || null,
      toItem: data?.to_item || null,
    });
    return data?.diff || {};
  };

  const openPublishDialog = async () => {
    setStatus('');
    setError('');
    if (driftMismatch) {
      setError('Draft hash mismatch tespit edildi. Lütfen taslağı yeniden senkronize edin.');
      return;
    }
    try {
      const nextDiff = await loadDiff();
      if ((nextDiff?.change_count || 0) < 1) {
        setError('Publish öncesi görsel diff üzerinde en az bir değişiklik bulunmalı');
      }
      setConfirmChecked(false);
      setIsPublishOpen(true);
    } catch (requestError) {
      setError(requestError.message || 'Diff bilgisi alınamadı');
    }
  };

  const publishDraft = async () => {
    setPublishing(true);
    setStatus('');
    setError('');
    try {
      const response = await fetch(`${API}/admin/ui/configs/dashboard/publish`, {
        method: 'POST',
        headers: {
          ...authHeader,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          segment: 'corporate',
          scope,
          scope_id: scope === 'tenant' ? scopeId.trim() : null,
          config_id: latestConfigId,
          config_version: latestConfigVersion,
          require_confirm: true,
        }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        const apiError = parseApiError(data, response.status);
        if (response.status === 409 && apiError.code === 'CONFIG_VERSION_CONFLICT') {
          setConflictInfo(apiError.raw || {});
          setConflictOpen(true);
          throw new Error(apiError.message || 'Başka bir admin daha yeni bir versiyon yayınladı');
        }
        if (response.status === 409 && apiError.code === 'PUBLISH_LOCKED') {
          setConflictInfo(apiError.raw || {});
          setConflictOpen(true);
          throw new Error(apiError.message || 'Publish lock aktif. Kısa süre sonra tekrar deneyin.');
        }
        if (response.status === 400 && apiError.code === 'MISSING_CONFIG_VERSION') {
          throw new Error('Version bilgisi eksik. Lütfen sayfayı yenileyin ve tekrar deneyin.');
        }
        throw new Error(apiError.message || 'Yayınlama başarısız');
      }

      setStatus(`Yayınlandı (v${data?.item?.version || '-'})`);
      toast.success('Dashboard konfigürasyonu yayınlandı');
      setIsPublishOpen(false);
      await Promise.all([loadDraft(), loadEffective()]);
    } catch (requestError) {
      setError(requestError.message || 'Yayınlama başarısız');
      toast.error(requestError.message || 'Yayınlama başarısız');
    } finally {
      setPublishing(false);
    }
  };

  const rollbackLatest = async () => {
    setStatus('');
    setError('');
    try {
      const response = await fetch(`${API}/admin/ui/configs/dashboard/rollback`, {
        method: 'POST',
        headers: {
          ...authHeader,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          segment: 'corporate',
          scope,
          scope_id: scope === 'tenant' ? scopeId.trim() : null,
          target_config_id: selectedRollbackId || null,
          rollback_reason: rollbackReason,
          require_confirm: true,
        }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        const apiError = parseApiError(data, response.status);
        if (response.status === 400 && apiError.code === 'MISSING_ROLLBACK_REASON') {
          throw new Error('Rollback sebebi zorunludur');
        }
        throw new Error(apiError.message || 'Rollback başarısız');
      }
      setStatus(`Rollback tamamlandı (v${data?.item?.version || '-'})`);
      toast.success('Dashboard rollback tamamlandı');
      setIsRollbackOpen(false);
      setRollbackReason('');
      await Promise.all([loadDraft(), loadEffective()]);
    } catch (requestError) {
      setError(requestError.message || 'Rollback başarısız');
      toast.error(requestError.message || 'Rollback başarısız');
    }
  };

  const addWidget = (widgetType) => {
    if (widgets.length >= MAX_WIDGETS) {
      setError(`En fazla ${MAX_WIDGETS} widget ekleyebilirsiniz`);
      return;
    }
    const palette = getPaletteByType(widgetType);
    const nextWidget = {
      widget_id: `${widgetType}-${Date.now()}`,
      widget_type: widgetType,
      title: palette?.title || widgetType,
      enabled: true,
    };
    const nextWidgets = [...widgets, nextWidget];
    setWidgets(nextWidgets);
    setLayout(buildLayoutFromWidgets(nextWidgets, layout));
    setError('');
  };

  const removeWidget = (widgetId) => {
    const nextWidgets = widgets.filter((item) => item.widget_id !== widgetId);
    setWidgets(nextWidgets);
    setLayout(buildLayoutFromWidgets(nextWidgets, layout));
  };

  const toggleWidgetEnabled = (widgetId, enabled) => {
    setWidgets((prev) => prev.map((item) => (item.widget_id === widgetId ? { ...item, enabled } : item)));
  };

  const onDragEnd = (event) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    const oldIndex = widgets.findIndex((item) => item.widget_id === active.id);
    const newIndex = widgets.findIndex((item) => item.widget_id === over.id);
    if (oldIndex < 0 || newIndex < 0) return;

    const nextWidgets = arrayMove(widgets, oldIndex, newIndex);
    setWidgets(nextWidgets);
    setLayout(buildLayoutFromWidgets(nextWidgets, layout));
  };

  useEffect(() => {
    loadDraft();
    loadEffective();
  }, [scope, scopeId]);

  useEffect(() => {
    const onResize = () => setLargeScreen(window.innerWidth >= 1024);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  useEffect(() => {
    if (!initializedRef.current) return undefined;
    if (snapshotHash === lastSavedHashRef.current) return undefined;

    if (autoSaveRef.current) {
      window.clearTimeout(autoSaveRef.current);
    }
    autoSaveRef.current = window.setTimeout(() => {
      saveDraft(true);
    }, 1200);

    return () => {
      if (autoSaveRef.current) {
        window.clearTimeout(autoSaveRef.current);
      }
    };
  }, [snapshotHash]);

  const layoutMap = useMemo(() => new Map(layout.map((item) => [item.widget_id, item])), [layout]);
  const diffFromWidgets = useMemo(() => normalizeDiffWidgets(publishDiffContext.fromItem), [publishDiffContext.fromItem]);
  const diffToWidgets = useMemo(() => normalizeDiffWidgets(publishDiffContext.toItem), [publishDiffContext.toItem]);
  const addedWidgetIds = useMemo(() => new Set(diffPayload?.added_widgets || []), [diffPayload]);
  const removedWidgetIds = useMemo(() => new Set(diffPayload?.removed_widgets || []), [diffPayload]);
  const movedWidgetIds = useMemo(
    () => new Set((diffPayload?.moved_widgets || []).map((item) => item?.widget_id).filter(Boolean)),
    [diffPayload],
  );

  return (
    <div className="space-y-4" data-testid="ui-designer-dashboard-container">
      <div className="grid gap-3 md:grid-cols-3" data-testid="ui-designer-dashboard-scope-grid">
        <label className="text-sm" data-testid="ui-designer-dashboard-scope-label">
          Scope
          <select
            value={scope}
            onChange={(event) => setScope(event.target.value)}
            className="mt-1 h-10 w-full rounded-md border px-3"
            data-testid="ui-designer-dashboard-scope-select"
          >
            <option value="system">system</option>
            <option value="tenant">tenant</option>
          </select>
        </label>
        <label className="text-sm md:col-span-2" data-testid="ui-designer-dashboard-scope-id-label">
          Scope ID (tenant)
          <input
            value={scopeId}
            onChange={(event) => setScopeId(event.target.value)}
            className="mt-1 h-10 w-full rounded-md border px-3"
            placeholder="tenant-001"
            data-testid="ui-designer-dashboard-scope-id-input"
          />
        </label>
      </div>

      <div className="rounded-xl border bg-slate-50 p-3" data-testid="ui-designer-dashboard-widget-palette">
        <div className="text-sm font-semibold" data-testid="ui-designer-dashboard-widget-palette-title">Widget Palette</div>
        <div className="mt-2 flex flex-wrap gap-2" data-testid="ui-designer-dashboard-widget-palette-actions">
          {WIDGET_PALETTE.map((widget) => (
            <button
              key={widget.type}
              type="button"
              onClick={() => addWidget(widget.type)}
              className="h-9 rounded-md border px-3 text-sm"
              data-testid={`ui-designer-dashboard-add-${widget.type}`}
            >
              + {widget.title}
            </button>
          ))}
        </div>
        <div className="mt-2 text-xs text-slate-600" data-testid="ui-designer-dashboard-guardrail-summary">
          Widget: {widgets.length}/{MAX_WIDGETS} • Görünür KPI: {enabledKpiCount}
        </div>
      </div>

      <div className="rounded-xl border bg-white p-3" data-testid="ui-designer-dashboard-grid-wrapper">
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={onDragEnd}>
          <SortableContext items={widgets.map((item) => item.widget_id)} strategy={rectSortingStrategy}>
            <div className="grid grid-cols-12 gap-3" data-testid="ui-designer-dashboard-grid">
              {widgets.map((widget) => (
                <SortableWidgetCard
                  key={widget.widget_id}
                  widget={widget}
                  width={layoutMap.get(widget.widget_id)?.w || 3}
                  largeScreen={largeScreen}
                  onRemove={removeWidget}
                  onToggleEnabled={toggleWidgetEnabled}
                />
              ))}
              {widgets.length === 0 ? (
                <div className="col-span-12 rounded-lg border border-dashed px-4 py-8 text-center text-sm text-slate-500" data-testid="ui-designer-dashboard-grid-empty">
                  Palette’den widget ekleyerek başlayın.
                </div>
              ) : null}
            </div>
          </SortableContext>
        </DndContext>
      </div>

      <div className="flex flex-wrap gap-2" data-testid="ui-designer-dashboard-actions">
        <button type="button" onClick={loadDraft} className="h-9 rounded-md border px-3 text-sm" data-testid="ui-designer-dashboard-load-draft">
          Taslağı Yükle
        </button>
        <button type="button" onClick={() => saveDraft(false)} className="h-9 rounded-md border px-3 text-sm" disabled={saving} data-testid="ui-designer-dashboard-save-draft">
          {saving ? 'Kaydediliyor...' : 'Taslağı Kaydet'}
        </button>
        <button
          type="button"
          onClick={openPublishDialog}
          className="h-9 rounded-md bg-slate-900 px-3 text-sm text-white disabled:cursor-not-allowed disabled:opacity-50"
          disabled={Boolean(publishDisabledReason) || !latestConfigId || publishing}
          data-testid="ui-designer-dashboard-open-publish"
          title={publishDisabledReason || 'Draft diff ve onay ile yayınla'}
        >
          Yayınla
        </button>
        <button
          type="button"
          onClick={() => {
            setRollbackReason('');
            setIsRollbackOpen(true);
          }}
          className="h-9 rounded-md border px-3 text-sm"
          data-testid="ui-designer-dashboard-open-rollback"
        >
          Rollback
        </button>
        <button
          type="button"
          onClick={() => {
            setSelectedRollbackId('');
            setRollbackReason('');
            setIsRollbackOpen(true);
          }}
          className="h-9 rounded-md border px-3 text-sm"
          data-testid="ui-designer-dashboard-rollback-last-snapshot"
        >
          Son Snapshot’a Dön
        </button>
        <button type="button" onClick={loadEffective} className="h-9 rounded-md border px-3 text-sm" data-testid="ui-designer-dashboard-load-effective">
          Canlı Render Oku
        </button>
      </div>

      {publishDisabledReason ? (
        <div className="text-xs text-amber-600" data-testid="ui-designer-dashboard-publish-disabled-reason">{publishDisabledReason}</div>
      ) : null}
      {status ? <div className="text-xs text-emerald-600" data-testid="ui-designer-dashboard-status">{status}</div> : null}
      {error ? <div className="text-xs text-rose-600" data-testid="ui-designer-dashboard-error">{error}</div> : null}

      <div className="grid gap-4 lg:grid-cols-2" data-testid="ui-designer-dashboard-bottom-grid">
        <div className="rounded-xl border bg-white p-3" data-testid="ui-designer-dashboard-versions-card">
          <div className="text-sm font-semibold" data-testid="ui-designer-dashboard-versions-title">Snapshot / Versiyonlar</div>
          <div className="mt-2 max-h-56 space-y-2 overflow-auto" data-testid="ui-designer-dashboard-versions-list">
            {versions.length === 0 ? (
              <div className="text-xs text-slate-500" data-testid="ui-designer-dashboard-versions-empty">Versiyon bulunamadı.</div>
            ) : versions.map((item) => (
              <label key={item.id} className="flex cursor-pointer items-center justify-between gap-2 rounded border px-2 py-2 text-xs" data-testid={`ui-designer-dashboard-version-${item.id}`}>
                <span data-testid={`ui-designer-dashboard-version-meta-${item.id}`}>
                  v{item.version} • {item.status} • {item.scope}/{item.scope_id || 'system'}
                </span>
                <input
                  type="radio"
                  name="dashboard-rollback-target"
                  checked={selectedRollbackId === item.id}
                  onChange={() => setSelectedRollbackId(item.id)}
                  data-testid={`ui-designer-dashboard-version-radio-${item.id}`}
                />
              </label>
            ))}
          </div>
        </div>

        <div className="rounded-xl border bg-white p-3" data-testid="ui-designer-dashboard-effective-card">
          <div className="text-sm font-semibold" data-testid="ui-designer-dashboard-effective-title">Canlı Render Doğrulama</div>
          <div className="mt-2 text-xs text-slate-600" data-testid="ui-designer-dashboard-effective-source">
            Source: {effectivePayload?.source_scope || '-'} / {effectivePayload?.source_scope_id || 'system'}
          </div>
          <div className="mt-2 text-xs text-slate-600" data-testid="ui-designer-dashboard-effective-widget-count">
            Widget Sayısı: {(effectivePayload?.widgets || []).length}
          </div>
          <pre className="mt-2 max-h-44 overflow-auto rounded bg-slate-50 p-2 text-[11px]" data-testid="ui-designer-dashboard-effective-json">
            {JSON.stringify(effectivePayload?.config_data || {}, null, 2)}
          </pre>
        </div>
      </div>

      <Dialog open={isPublishOpen} onOpenChange={setIsPublishOpen}>
        <DialogContent data-testid="ui-designer-dashboard-publish-dialog">
          <DialogHeader>
            <DialogTitle data-testid="ui-designer-dashboard-publish-dialog-title">Draft → Publish Onayı</DialogTitle>
            <DialogDescription data-testid="ui-designer-dashboard-publish-dialog-description">
              Yayın öncesi fark özeti aşağıdadır. Onay olmadan yayın yapılamaz.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2 text-xs" data-testid="ui-designer-dashboard-diff-content">
            <div data-testid="ui-designer-dashboard-diff-added">Eklenen: {(diffPayload?.added_widgets || []).join(', ') || '-'}</div>
            <div data-testid="ui-designer-dashboard-diff-removed">Kaldırılan: {(diffPayload?.removed_widgets || []).join(', ') || '-'}</div>
            <div data-testid="ui-designer-dashboard-diff-moved">Taşınan: {(diffPayload?.moved_widgets || []).length}</div>
          </div>
          <div className="grid gap-3 md:grid-cols-2" data-testid="ui-designer-dashboard-diff-visual-grid">
            <div className="rounded-md border p-2" data-testid="ui-designer-dashboard-diff-before-panel">
              <div className="mb-2 text-xs font-semibold text-slate-700" data-testid="ui-designer-dashboard-diff-before-title">Önceki Grid</div>
              <div className="space-y-2" data-testid="ui-designer-dashboard-diff-before-list">
                {diffFromWidgets.length === 0 ? (
                  <div className="text-[11px] text-slate-400" data-testid="ui-designer-dashboard-diff-before-empty">Önceki widget yok</div>
                ) : diffFromWidgets.map((widget) => {
                  const isRemoved = removedWidgetIds.has(widget.widget_id);
                  const isMoved = movedWidgetIds.has(widget.widget_id);
                  return (
                    <div
                      key={`before-${widget.widget_id}`}
                      className={`rounded border px-2 py-1 text-[11px] ${isRemoved ? 'border-rose-300 bg-rose-50' : isMoved ? 'border-amber-300 bg-amber-50' : 'border-slate-200 bg-white'}`}
                      data-testid={`ui-designer-dashboard-diff-before-widget-${widget.widget_id}`}
                    >
                      {widget.title} ({widget.widget_type})
                    </div>
                  );
                })}
              </div>
            </div>
            <div className="rounded-md border p-2" data-testid="ui-designer-dashboard-diff-after-panel">
              <div className="mb-2 text-xs font-semibold text-slate-700" data-testid="ui-designer-dashboard-diff-after-title">Yeni Grid</div>
              <div className="space-y-2" data-testid="ui-designer-dashboard-diff-after-list">
                {diffToWidgets.length === 0 ? (
                  <div className="text-[11px] text-slate-400" data-testid="ui-designer-dashboard-diff-after-empty">Yeni widget yok</div>
                ) : diffToWidgets.map((widget) => {
                  const isAdded = addedWidgetIds.has(widget.widget_id);
                  const isMoved = movedWidgetIds.has(widget.widget_id);
                  return (
                    <div
                      key={`after-${widget.widget_id}`}
                      className={`rounded border px-2 py-1 text-[11px] ${isAdded ? 'border-emerald-300 bg-emerald-50' : isMoved ? 'border-amber-300 bg-amber-50' : 'border-slate-200 bg-white'}`}
                      data-testid={`ui-designer-dashboard-diff-after-widget-${widget.widget_id}`}
                    >
                      {widget.title} ({widget.widget_type})
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
          <label className="inline-flex items-center gap-2 text-xs" data-testid="ui-designer-dashboard-publish-confirm-wrap">
            <input
              type="checkbox"
              checked={confirmChecked}
              onChange={(event) => setConfirmChecked(event.target.checked)}
              data-testid="ui-designer-dashboard-publish-confirm-checkbox"
            />
            Diff özetini inceledim, yayınlamayı onaylıyorum.
          </label>
          <DialogFooter>
            <button type="button" onClick={() => setIsPublishOpen(false)} className="h-9 rounded-md border px-3 text-sm" data-testid="ui-designer-dashboard-publish-cancel">
              Vazgeç
            </button>
            <button
              type="button"
              onClick={publishDraft}
              disabled={!confirmChecked || Boolean(publishDisabledReason) || publishing || (diffPayload?.change_count || 0) < 1}
              className="h-9 rounded-md bg-slate-900 px-3 text-sm text-white disabled:opacity-50"
              data-testid="ui-designer-dashboard-publish-confirm-button"
            >
              {publishing ? 'Yayınlanıyor...' : 'Yayınla'}
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={isRollbackOpen} onOpenChange={setIsRollbackOpen}>
        <DialogContent data-testid="ui-designer-dashboard-rollback-dialog">
          <DialogHeader>
            <DialogTitle data-testid="ui-designer-dashboard-rollback-dialog-title">Rollback Onayı</DialogTitle>
            <DialogDescription data-testid="ui-designer-dashboard-rollback-dialog-description">
              Seçili snapshot versiyonuna geri dönülecek.
            </DialogDescription>
          </DialogHeader>
          <div className="text-xs text-slate-600" data-testid="ui-designer-dashboard-rollback-selected">
            Seçili target: {selectedRollbackId || 'Otomatik son snapshot'}
          </div>
          <label className="text-xs" data-testid="ui-designer-dashboard-rollback-reason-label">
            Rollback Sebebi (zorunlu)
            <textarea
              value={rollbackReason}
              onChange={(event) => setRollbackReason(event.target.value)}
              className="mt-1 min-h-[84px] w-full rounded-md border px-3 py-2 text-xs"
              placeholder="Örn: Yanlış widget sıralaması canlıya çıktı"
              data-testid="ui-designer-dashboard-rollback-reason-input"
            />
          </label>
          <DialogFooter>
            <button type="button" onClick={() => setIsRollbackOpen(false)} className="h-9 rounded-md border px-3 text-sm" data-testid="ui-designer-dashboard-rollback-cancel">
              Vazgeç
            </button>
            <button
              type="button"
              onClick={rollbackLatest}
              disabled={!rollbackReason.trim()}
              className="h-9 rounded-md bg-slate-900 px-3 text-sm text-white disabled:opacity-50"
              data-testid="ui-designer-dashboard-rollback-confirm"
            >
              Rollback Uygula
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={conflictOpen} onOpenChange={setConflictOpen}>
        <DialogContent data-testid="ui-designer-dashboard-conflict-dialog">
          <DialogHeader>
            <DialogTitle data-testid="ui-designer-dashboard-conflict-title">Publish Çakışması</DialogTitle>
            <DialogDescription data-testid="ui-designer-dashboard-conflict-description">
              Başka bir admin daha yeni bir versiyon yayınladı veya publish lock aktif.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-1 text-xs" data-testid="ui-designer-dashboard-conflict-meta">
            <div data-testid="ui-designer-dashboard-conflict-current-version">Current Version: {conflictInfo?.current_version ?? '-'}</div>
            <div data-testid="ui-designer-dashboard-conflict-your-version">Your Version: {conflictInfo?.your_version ?? latestConfigVersion ?? '-'}</div>
            <div data-testid="ui-designer-dashboard-conflict-last-published-by">Last Published By: {conflictInfo?.last_published_by || '-'}</div>
            <div data-testid="ui-designer-dashboard-conflict-last-published-at">Last Published At: {conflictInfo?.last_published_at || '-'}</div>
          </div>
          <DialogFooter>
            <button
              type="button"
              onClick={async () => {
                setConflictOpen(false);
                await loadDraft();
              }}
              className="h-9 rounded-md border px-3 text-sm"
              data-testid="ui-designer-dashboard-conflict-reload-button"
            >
              Sayfayı Yenile
            </button>
            <button
              type="button"
              onClick={async () => {
                setConflictOpen(false);
                await openPublishDialog();
              }}
              className="h-9 rounded-md bg-slate-900 px-3 text-sm text-white"
              data-testid="ui-designer-dashboard-conflict-view-diff-button"
            >
              Diff Gör
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};
