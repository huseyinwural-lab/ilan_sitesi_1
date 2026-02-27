import React, { useEffect, useMemo, useRef, useState } from 'react';
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

const MODULE_LIBRARY = [
  { type: 'search', label: 'Arama' },
  { type: 'quick_links', label: 'Hızlı Linkler' },
  { type: 'notifications', label: 'Bildirim' },
  { type: 'campaign_banner', label: 'Kampanya' },
  { type: 'favorites', label: 'Favoriler' },
  { type: 'user_menu', label: 'Kullanıcı Menüsü' },
];

const defaultIndividualHeaderConfig = {
  rows: [
    {
      id: 'row1',
      title: 'Row 1',
      visible: true,
      blocks: [
        { id: 'logo', type: 'logo', label: 'Logo', visible: true },
        { id: 'search', type: 'search', label: 'Arama', visible: true },
      ],
    },
    {
      id: 'row2',
      title: 'Row 2',
      visible: true,
      blocks: [
        { id: 'quick-links', type: 'quick_links', label: 'Hızlı Linkler', visible: true },
        { id: 'campaign', type: 'campaign_banner', label: 'Kampanya', visible: true },
      ],
    },
    {
      id: 'row3',
      title: 'Row 3',
      visible: true,
      blocks: [
        { id: 'notifications', type: 'notifications', label: 'Bildirim', visible: true },
        { id: 'user-menu', type: 'user_menu', label: 'Kullanıcı Menüsü', visible: true },
      ],
    },
  ],
  logo: {
    url: null,
    fallback_text: 'ANNONCIA',
    aspect_ratio: '3:1',
  },
};

const deepClone = (value) => JSON.parse(JSON.stringify(value));

const normalizeHeaderConfig = (rawConfig) => {
  const fallback = deepClone(defaultIndividualHeaderConfig);
  if (!rawConfig || typeof rawConfig !== 'object') return fallback;

  const rows = Array.isArray(rawConfig.rows) ? rawConfig.rows : fallback.rows;
  const normalizedRows = rows.map((row, rowIndex) => {
    const blocks = Array.isArray(row?.blocks) ? row.blocks : [];
    return {
      id: `${row?.id || `row${rowIndex + 1}`}`,
      title: `${row?.title || `Row ${rowIndex + 1}`}`,
      visible: row?.visible !== false,
      blocks: blocks
        .filter((block) => block && typeof block === 'object')
        .map((block, blockIndex) => ({
          id: `${block.id || `${block.type || 'module'}-${blockIndex + 1}`}`,
          type: `${block.type || 'module'}`,
          label: `${block.label || block.type || 'Modül'}`,
          visible: block.visible !== false,
        })),
    };
  });

  const row1 = normalizedRows[0];
  if (row1 && !row1.blocks.some((block) => block.type === 'logo')) {
    row1.blocks.unshift({ id: `logo-${Date.now()}`, type: 'logo', label: 'Logo', visible: true });
  }

  return {
    rows: normalizedRows,
    logo: {
      ...fallback.logo,
      ...(rawConfig.logo || {}),
      fallback_text: `${rawConfig?.logo?.fallback_text || fallback.logo.fallback_text}`,
    },
  };
};

const parseApiError = (payload, statusCode = 0) => {
  const detail = payload?.detail;
  if (detail && typeof detail === 'object') {
    return {
      code: detail.code || 'UNKNOWN',
      message: detail.message || 'İşlem başarısız',
      raw: detail,
      status: statusCode,
    };
  }
  return {
    code: statusCode === 409 ? 'CONFIG_VERSION_CONFLICT' : 'UNKNOWN',
    message: typeof detail === 'string' ? detail : 'İşlem başarısız',
    raw: detail || {},
    status: statusCode,
  };
};

export const IndividualHeaderDesigner = () => {
  const authHeader = useMemo(() => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` }), []);

  const [scope, setScope] = useState('system');
  const [scopeId, setScopeId] = useState('');
  const [configData, setConfigData] = useState(deepClone(defaultIndividualHeaderConfig));
  const [latestConfigId, setLatestConfigId] = useState(null);
  const [latestConfigVersion, setLatestConfigVersion] = useState(null);
  const [versions, setVersions] = useState([]);
  const [effectivePayload, setEffectivePayload] = useState(null);
  const [selectedRollbackId, setSelectedRollbackId] = useState('');
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const [publishing, setPublishing] = useState(false);
  const [diffPayload, setDiffPayload] = useState({});
  const [confirmChecked, setConfirmChecked] = useState(false);
  const [publishOpen, setPublishOpen] = useState(false);
  const [rollbackOpen, setRollbackOpen] = useState(false);
  const [rollbackReason, setRollbackReason] = useState('');

  const dragRef = useRef(null);
  const scopeQuery = scope === 'tenant' && scopeId.trim() ? `&scope_id=${encodeURIComponent(scopeId.trim())}` : '';

  const loadDraft = async () => {
    setStatus('');
    setError('');
    try {
      const response = await fetch(
        `${API}/admin/ui/configs/header?segment=individual&scope=${scope}${scopeQuery}&status=draft`,
        { headers: authHeader },
      );
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data?.detail || 'Bireysel header taslağı yüklenemedi');
      }

      const normalized = normalizeHeaderConfig(data?.item?.config_data || defaultIndividualHeaderConfig);
      setConfigData(normalized);
      setLatestConfigId(data?.item?.id || null);
      setLatestConfigVersion(data?.item?.version ?? null);
      setVersions(Array.isArray(data?.items) ? data.items : []);
      setStatus('Bireysel header taslağı yüklendi');
    } catch (requestError) {
      setError(requestError.message || 'Bireysel header taslağı yüklenemedi');
      setConfigData(deepClone(defaultIndividualHeaderConfig));
      setLatestConfigId(null);
      setLatestConfigVersion(null);
      setVersions([]);
    }
  };

  const saveDraft = async () => {
    setStatus('');
    setError('');
    try {
      const safePayload = normalizeHeaderConfig(configData);
      safePayload.logo.fallback_text = `${safePayload.logo.fallback_text || 'ANNONCIA'}`.trim() || 'ANNONCIA';

      const response = await fetch(`${API}/admin/ui/configs/header`, {
        method: 'POST',
        headers: {
          ...authHeader,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          segment: 'individual',
          scope,
          scope_id: scope === 'tenant' ? scopeId.trim() : null,
          status: 'draft',
          config_data: safePayload,
        }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data?.detail || 'Taslak kaydedilemedi');
      }
      setLatestConfigId(data?.item?.id || null);
      setLatestConfigVersion(data?.item?.version ?? null);
      setStatus(`Taslak kaydedildi (v${data?.item?.version || '-'})`);
      toast.success('Bireysel header taslağı kaydedildi');
      await loadDraft();
    } catch (requestError) {
      setError(requestError.message || 'Taslak kaydedilemedi');
      toast.error(requestError.message || 'Taslak kaydedilemedi');
    }
  };

  const loadEffective = async () => {
    setStatus('');
    setError('');
    try {
      const tenantPart = scope === 'tenant' && scopeId.trim() ? `&tenant_id=${encodeURIComponent(scopeId.trim())}` : '';
      const response = await fetch(`${API}/ui/header?segment=individual${tenantPart}`, { headers: authHeader });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data?.detail || 'Effective config okunamadı');
      }
      setEffectivePayload(data);
      setStatus('Effective config yüklendi');
    } catch (requestError) {
      setError(requestError.message || 'Effective config okunamadı');
    }
  };

  const loadDiff = async () => {
    const response = await fetch(
      `${API}/admin/ui/configs/header/diff?segment=individual&scope=${scope}${scopeQuery}&from_status=published&to_status=draft`,
      { headers: authHeader },
    );
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data?.detail || 'Diff alınamadı');
    }
    setDiffPayload(data?.diff || {});
  };

  const openPublishDialog = async () => {
    setStatus('');
    setError('');
    try {
      await loadDiff();
      setConfirmChecked(false);
      setPublishOpen(true);
    } catch (requestError) {
      setError(requestError.message || 'Diff alınamadı');
    }
  };

  const publishDraft = async () => {
    setPublishing(true);
    setStatus('');
    setError('');
    try {
      const response = await fetch(`${API}/admin/ui/configs/header/publish`, {
        method: 'POST',
        headers: {
          ...authHeader,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          segment: 'individual',
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
        if (response.status === 400 && apiError.code === 'MISSING_CONFIG_VERSION') {
          throw new Error('Version bilgisi eksik. Lütfen sayfayı yenileyin ve tekrar deneyin.');
        }
        if (response.status === 409 && apiError.code === 'CONFIG_VERSION_CONFLICT') {
          throw new Error('Başka bir admin daha yeni bir versiyon yayınladı. Lütfen sayfayı yenileyin.');
        }
        throw new Error(apiError.message || 'Yayınlama başarısız');
      }
      setStatus(`Yayınlandı (v${data?.item?.version || '-'})`);
      setPublishOpen(false);
      toast.success('Bireysel header yayınlandı');
      await Promise.all([loadDraft(), loadEffective()]);
    } catch (requestError) {
      setError(requestError.message || 'Yayınlama başarısız');
      toast.error(requestError.message || 'Yayınlama başarısız');
    } finally {
      setPublishing(false);
    }
  };

  const rollbackConfig = async () => {
    setStatus('');
    setError('');
    try {
      const response = await fetch(`${API}/admin/ui/configs/header/rollback`, {
        method: 'POST',
        headers: {
          ...authHeader,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          segment: 'individual',
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
      setRollbackOpen(false);
      setRollbackReason('');
      toast.success('Bireysel header rollback tamamlandı');
      await Promise.all([loadDraft(), loadEffective()]);
    } catch (requestError) {
      setError(requestError.message || 'Rollback başarısız');
      toast.error(requestError.message || 'Rollback başarısız');
    }
  };

  const updateRowVisibility = (rowId, visible) => {
    setConfigData((prev) => ({
      ...prev,
      rows: prev.rows.map((row) => (row.id === rowId ? { ...row, visible } : row)),
    }));
  };

  const updateBlockVisibility = (rowId, blockId, visible) => {
    setConfigData((prev) => ({
      ...prev,
      rows: prev.rows.map((row) => {
        if (row.id !== rowId) return row;
        return {
          ...row,
          blocks: row.blocks.map((block) => (block.id === blockId ? { ...block, visible } : block)),
        };
      }),
    }));
  };

  const addModuleToRow = (rowId, moduleType) => {
    const moduleInfo = MODULE_LIBRARY.find((item) => item.type === moduleType);
    if (!moduleInfo) return;
    setConfigData((prev) => ({
      ...prev,
      rows: prev.rows.map((row) => {
        if (row.id !== rowId) return row;
        return {
          ...row,
          blocks: [
            ...row.blocks,
            {
              id: `${moduleType}-${Date.now()}`,
              type: moduleType,
              label: moduleInfo.label,
              visible: true,
            },
          ],
        };
      }),
    }));
  };

  const removeModule = (rowId, blockId) => {
    setConfigData((prev) => ({
      ...prev,
      rows: prev.rows.map((row) => {
        if (row.id !== rowId) return row;
        return {
          ...row,
          blocks: row.blocks.filter((block) => block.id !== blockId || block.type === 'logo'),
        };
      }),
    }));
  };

  const onDragStart = (event, rowId, blockIndex) => {
    dragRef.current = { rowId, blockIndex };
    event.dataTransfer.effectAllowed = 'move';
  };

  const onDropToRow = (targetRowId, targetIndex = null) => {
    const dragInfo = dragRef.current;
    dragRef.current = null;
    if (!dragInfo) return;

    const { rowId: sourceRowId, blockIndex } = dragInfo;
    setConfigData((prev) => {
      const next = deepClone(prev);
      const sourceRow = next.rows.find((row) => row.id === sourceRowId);
      const targetRow = next.rows.find((row) => row.id === targetRowId);
      if (!sourceRow || !targetRow) return prev;

      const sourceBlocks = [...sourceRow.blocks];
      const [dragged] = sourceBlocks.splice(blockIndex, 1);
      if (!dragged) return prev;
      if (dragged.type === 'logo' && targetRowId !== 'row1') {
        setError('Logo modülü sadece Row1 içinde kalabilir');
        return prev;
      }
      sourceRow.blocks = sourceBlocks;

      const targetBlocks = [...targetRow.blocks];
      const insertAt = Number.isInteger(targetIndex) ? targetIndex : targetBlocks.length;
      targetBlocks.splice(Math.max(0, insertAt), 0, dragged);
      targetRow.blocks = targetBlocks;
      return next;
    });
  };

  useEffect(() => {
    loadDraft();
  }, [scope, scopeId]);

  return (
    <div className="space-y-4" data-testid="ui-designer-individual-header-v2-container">
      <div className="grid gap-3 md:grid-cols-3" data-testid="ui-designer-individual-header-v2-scope-grid">
        <label className="text-sm" data-testid="ui-designer-individual-header-v2-scope-label">
          Scope
          <select
            value={scope}
            onChange={(event) => setScope(event.target.value)}
            className="mt-1 h-10 w-full rounded-md border px-3"
            data-testid="ui-designer-individual-header-v2-scope-select"
          >
            <option value="system">system</option>
            <option value="tenant">tenant</option>
          </select>
        </label>
        <label className="text-sm md:col-span-2" data-testid="ui-designer-individual-header-v2-scope-id-label">
          Scope ID (tenant)
          <input
            value={scopeId}
            onChange={(event) => setScopeId(event.target.value)}
            className="mt-1 h-10 w-full rounded-md border px-3"
            placeholder="tenant-001"
            data-testid="ui-designer-individual-header-v2-scope-id-input"
          />
        </label>
      </div>

      <div className="rounded-xl border bg-slate-50 p-3" data-testid="ui-designer-individual-header-v2-fallback-card">
        <label className="text-sm" data-testid="ui-designer-individual-header-v2-fallback-label">
          Logo Fallback Text
          <input
            value={configData.logo?.fallback_text || 'ANNONCIA'}
            onChange={(event) => setConfigData((prev) => ({
              ...prev,
              logo: {
                ...(prev.logo || {}),
                fallback_text: event.target.value,
              },
            }))}
            className="mt-1 h-10 w-full rounded-md border px-3"
            data-testid="ui-designer-individual-header-v2-fallback-input"
          />
        </label>
      </div>

      <div className="space-y-3" data-testid="ui-designer-individual-header-v2-rows">
        {configData.rows.map((row) => (
          <div key={row.id} className="rounded-xl border bg-white p-3" data-testid={`ui-designer-individual-header-v2-row-${row.id}`}>
            <div className="flex flex-wrap items-center justify-between gap-2" data-testid={`ui-designer-individual-header-v2-row-header-${row.id}`}>
              <div className="text-sm font-semibold" data-testid={`ui-designer-individual-header-v2-row-title-${row.id}`}>{row.title}</div>
              <label className="inline-flex items-center gap-2 text-xs" data-testid={`ui-designer-individual-header-v2-row-visible-wrap-${row.id}`}>
                <input
                  type="checkbox"
                  checked={row.visible !== false}
                  onChange={(event) => updateRowVisibility(row.id, event.target.checked)}
                  data-testid={`ui-designer-individual-header-v2-row-visible-${row.id}`}
                />
                Row Görünür
              </label>
            </div>

            <div className="mt-2 flex flex-wrap gap-2" data-testid={`ui-designer-individual-header-v2-row-module-library-${row.id}`}>
              {MODULE_LIBRARY.map((moduleItem) => (
                <button
                  key={`${row.id}-${moduleItem.type}`}
                  type="button"
                  onClick={() => addModuleToRow(row.id, moduleItem.type)}
                  className="h-8 rounded border px-2 text-xs"
                  data-testid={`ui-designer-individual-header-v2-row-add-${row.id}-${moduleItem.type}`}
                >
                  + {moduleItem.label}
                </button>
              ))}
            </div>

            <div className="mt-3 space-y-2" data-testid={`ui-designer-individual-header-v2-row-blocks-${row.id}`}>
              {row.blocks.map((block, blockIndex) => (
                <div
                  key={block.id}
                  draggable
                  onDragStart={(event) => onDragStart(event, row.id, blockIndex)}
                  onDragOver={(event) => event.preventDefault()}
                  onDrop={() => onDropToRow(row.id, blockIndex)}
                  className="flex flex-wrap items-center justify-between gap-2 rounded border px-2 py-2 text-xs"
                  data-testid={`ui-designer-individual-header-v2-block-${row.id}-${block.id}`}
                >
                  <div className="flex items-center gap-2" data-testid={`ui-designer-individual-header-v2-block-meta-${row.id}-${block.id}`}>
                    <span className="rounded border px-1 py-0.5" data-testid={`ui-designer-individual-header-v2-block-drag-${row.id}-${block.id}`}>Sürükle</span>
                    <span data-testid={`ui-designer-individual-header-v2-block-label-${row.id}-${block.id}`}>{block.label}</span>
                    <span className="text-slate-500" data-testid={`ui-designer-individual-header-v2-block-type-${row.id}-${block.id}`}>{block.type}</span>
                  </div>
                  <div className="flex items-center gap-2" data-testid={`ui-designer-individual-header-v2-block-actions-${row.id}-${block.id}`}>
                    <label className="inline-flex items-center gap-1" data-testid={`ui-designer-individual-header-v2-block-visible-wrap-${row.id}-${block.id}`}>
                      <input
                        type="checkbox"
                        checked={block.visible !== false}
                        onChange={(event) => updateBlockVisibility(row.id, block.id, event.target.checked)}
                        data-testid={`ui-designer-individual-header-v2-block-visible-${row.id}-${block.id}`}
                      />
                      Görünür
                    </label>
                    <button
                      type="button"
                      onClick={() => removeModule(row.id, block.id)}
                      className="rounded border border-rose-200 px-2 py-1 text-rose-600"
                      data-testid={`ui-designer-individual-header-v2-block-remove-${row.id}-${block.id}`}
                    >
                      Kaldır
                    </button>
                  </div>
                </div>
              ))}
              <div
                className="rounded border border-dashed px-2 py-2 text-[11px] text-slate-400"
                onDragOver={(event) => event.preventDefault()}
                onDrop={() => onDropToRow(row.id, null)}
                data-testid={`ui-designer-individual-header-v2-row-dropzone-${row.id}`}
              >
                Modülü bu alana bırakarak satır sonuna ekleyin.
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="flex flex-wrap gap-2" data-testid="ui-designer-individual-header-v2-actions">
        <button type="button" onClick={loadDraft} className="h-9 rounded-md border px-3 text-sm" data-testid="ui-designer-individual-header-v2-load-draft">Taslağı Yükle</button>
        <button type="button" onClick={saveDraft} className="h-9 rounded-md border px-3 text-sm" data-testid="ui-designer-individual-header-v2-save-draft">Taslağı Kaydet</button>
        <button type="button" onClick={openPublishDialog} className="h-9 rounded-md bg-slate-900 px-3 text-sm text-white" data-testid="ui-designer-individual-header-v2-open-publish" disabled={!latestConfigId}>Yayınla</button>
        <button type="button" onClick={() => setRollbackOpen(true)} className="h-9 rounded-md border px-3 text-sm" data-testid="ui-designer-individual-header-v2-open-rollback">Rollback</button>
        <button type="button" onClick={loadEffective} className="h-9 rounded-md border px-3 text-sm" data-testid="ui-designer-individual-header-v2-load-effective">Effective Oku</button>
      </div>

      {status ? <div className="text-xs text-emerald-600" data-testid="ui-designer-individual-header-v2-status">{status}</div> : null}
      {error ? <div className="text-xs text-rose-600" data-testid="ui-designer-individual-header-v2-error">{error}</div> : null}

      <div className="grid gap-4 lg:grid-cols-2" data-testid="ui-designer-individual-header-v2-bottom-grid">
        <div className="rounded-xl border bg-white p-3" data-testid="ui-designer-individual-header-v2-versions-card">
          <div className="text-sm font-semibold" data-testid="ui-designer-individual-header-v2-versions-title">Snapshot / Versiyonlar</div>
          <div className="mt-2 max-h-52 space-y-2 overflow-auto" data-testid="ui-designer-individual-header-v2-versions-list">
            {versions.length === 0 ? (
              <div className="text-xs text-slate-500" data-testid="ui-designer-individual-header-v2-versions-empty">Versiyon bulunamadı.</div>
            ) : versions.map((item) => (
              <label key={item.id} className="flex cursor-pointer items-center justify-between gap-2 rounded border px-2 py-2 text-xs" data-testid={`ui-designer-individual-header-v2-version-${item.id}`}>
                <span data-testid={`ui-designer-individual-header-v2-version-meta-${item.id}`}>
                  v{item.version} • {item.status} • {item.scope}/{item.scope_id || 'system'}
                </span>
                <input
                  type="radio"
                  name="individual-header-rollback-target"
                  checked={selectedRollbackId === item.id}
                  onChange={() => setSelectedRollbackId(item.id)}
                  data-testid={`ui-designer-individual-header-v2-version-radio-${item.id}`}
                />
              </label>
            ))}
          </div>
        </div>

        <div className="rounded-xl border bg-white p-3" data-testid="ui-designer-individual-header-v2-effective-card">
          <div className="text-sm font-semibold" data-testid="ui-designer-individual-header-v2-effective-title">Effective Sonuç</div>
          <div className="mt-2 text-xs text-slate-600" data-testid="ui-designer-individual-header-v2-effective-source">
            Source: {effectivePayload?.source_scope || '-'} / {effectivePayload?.source_scope_id || 'system'}
          </div>
          <pre className="mt-2 max-h-44 overflow-auto rounded bg-slate-50 p-2 text-[11px]" data-testid="ui-designer-individual-header-v2-effective-json">
            {JSON.stringify(effectivePayload?.config_data || {}, null, 2)}
          </pre>
        </div>
      </div>

      <Dialog open={publishOpen} onOpenChange={setPublishOpen}>
        <DialogContent data-testid="ui-designer-individual-header-v2-publish-dialog">
          <DialogHeader>
            <DialogTitle data-testid="ui-designer-individual-header-v2-publish-title">Draft → Publish Onayı</DialogTitle>
            <DialogDescription data-testid="ui-designer-individual-header-v2-publish-description">
              Yayın öncesi modül farklarını kontrol edin.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-1 text-xs" data-testid="ui-designer-individual-header-v2-diff-content">
            <div data-testid="ui-designer-individual-header-v2-diff-added">Eklenen: {(diffPayload?.added_modules || []).join(', ') || '-'}</div>
            <div data-testid="ui-designer-individual-header-v2-diff-removed">Kaldırılan: {(diffPayload?.removed_modules || []).join(', ') || '-'}</div>
            <div data-testid="ui-designer-individual-header-v2-diff-moved">Taşınan: {(diffPayload?.moved_modules || []).length}</div>
            <div data-testid="ui-designer-individual-header-v2-diff-visible">Visible Değişimi: {(diffPayload?.visibility_changes || []).length}</div>
          </div>
          <label className="inline-flex items-center gap-2 text-xs" data-testid="ui-designer-individual-header-v2-publish-confirm-wrap">
            <input
              type="checkbox"
              checked={confirmChecked}
              onChange={(event) => setConfirmChecked(event.target.checked)}
              data-testid="ui-designer-individual-header-v2-publish-confirm-checkbox"
            />
            Değişiklikleri inceledim, yayınlamayı onaylıyorum.
          </label>
          <DialogFooter>
            <button type="button" onClick={() => setPublishOpen(false)} className="h-9 rounded-md border px-3 text-sm" data-testid="ui-designer-individual-header-v2-publish-cancel">Vazgeç</button>
            <button
              type="button"
              onClick={publishDraft}
              disabled={!confirmChecked || publishing}
              className="h-9 rounded-md bg-slate-900 px-3 text-sm text-white disabled:opacity-50"
              data-testid="ui-designer-individual-header-v2-publish-confirm"
            >
              {publishing ? 'Yayınlanıyor...' : 'Yayınla'}
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={rollbackOpen} onOpenChange={setRollbackOpen}>
        <DialogContent data-testid="ui-designer-individual-header-v2-rollback-dialog">
          <DialogHeader>
            <DialogTitle data-testid="ui-designer-individual-header-v2-rollback-title">Rollback Onayı</DialogTitle>
            <DialogDescription data-testid="ui-designer-individual-header-v2-rollback-description">
              Seçili snapshot versiyonuna dönülecek.
            </DialogDescription>
          </DialogHeader>
          <div className="text-xs text-slate-600" data-testid="ui-designer-individual-header-v2-rollback-selected">
            Seçili target: {selectedRollbackId || 'Otomatik son snapshot'}
          </div>
          <DialogFooter>
            <button type="button" onClick={() => setRollbackOpen(false)} className="h-9 rounded-md border px-3 text-sm" data-testid="ui-designer-individual-header-v2-rollback-cancel">Vazgeç</button>
            <button type="button" onClick={rollbackConfig} className="h-9 rounded-md bg-slate-900 px-3 text-sm text-white" data-testid="ui-designer-individual-header-v2-rollback-confirm">Rollback Uygula</button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};
