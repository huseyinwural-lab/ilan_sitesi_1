import React, { useEffect, useMemo, useRef, useState } from 'react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const MAX_LOGO_BYTES = 2 * 1024 * 1024;
const TARGET_RATIO = 3;
const RATIO_TOLERANCE = 0.1;

const defaultCorporateHeaderConfig = {
  rows: [
    {
      id: 'row1',
      title: 'Row 1',
      blocks: [
        { id: 'logo', type: 'logo', label: 'Logo', required: true },
        { id: 'quick_actions', type: 'quick_actions', label: 'Hızlı Aksiyonlar' },
        { id: 'language_switcher', type: 'language_switcher', label: 'Dil Seçici' },
      ],
    },
    {
      id: 'row2',
      title: 'Row 2',
      blocks: [
        { id: 'fixed_blocks', type: 'fixed_blocks', label: 'Sabit Bloklar' },
        { id: 'modules', type: 'modules', label: 'Modül Butonları' },
      ],
    },
    {
      id: 'row3',
      title: 'Row 3',
      blocks: [
        { id: 'store_filter', type: 'store_filter', label: 'Mağaza Filtresi' },
        { id: 'user_menu', type: 'user_menu', label: 'Kullanıcı Menüsü' },
      ],
    },
  ],
  logo: {
    url: null,
    fallback_text: 'ANNONCIA',
    aspect_ratio: '3:1',
  },
};

const cloneDefaultConfig = () => JSON.parse(JSON.stringify(defaultCorporateHeaderConfig));

const safeConfigData = (value) => {
  const base = cloneDefaultConfig();
  if (!value || typeof value !== 'object') return base;

  if (Array.isArray(value.rows)) {
    base.rows = base.rows.map((row) => {
      const match = value.rows.find((item) => `${item?.id || ''}`.trim().toLowerCase() === row.id);
      if (!match || !Array.isArray(match.blocks)) return row;
      return {
        ...row,
        blocks: match.blocks
          .filter((block) => block && typeof block === 'object' && `${block.type || ''}`.trim())
          .map((block, index) => ({
            id: `${block.id || `${block.type}-${index}`}`,
            type: `${block.type}`,
            label: `${block.label || block.type}`,
            required: Boolean(block.required),
            logo_url: block.logo_url || null,
          })),
      };
    });
  }

  if (value.logo && typeof value.logo === 'object') {
    base.logo = {
      ...base.logo,
      ...value.logo,
    };
  }

  return base;
};

const prettyJson = (value) => JSON.stringify(value ?? {}, null, 2);

const fileExtension = (fileName = '') => {
  if (!fileName.includes('.')) return '';
  return fileName.split('.').pop().toLowerCase();
};

const parseSvgDimensions = async (file) => {
  const text = await file.text();
  const viewBoxMatch = text.match(/viewBox\s*=\s*"([^"]+)"/i);
  if (viewBoxMatch) {
    const parts = viewBoxMatch[1].split(/[\s,]+/).filter(Boolean).map(Number);
    if (parts.length === 4 && parts[2] > 0 && parts[3] > 0) {
      return { width: parts[2], height: parts[3], ratio: parts[2] / parts[3] };
    }
  }

  const widthMatch = text.match(/width\s*=\s*"([0-9.]+)/i);
  const heightMatch = text.match(/height\s*=\s*"([0-9.]+)/i);
  const width = Number(widthMatch?.[1] || 0);
  const height = Number(heightMatch?.[1] || 0);
  if (width > 0 && height > 0) {
    return { width, height, ratio: width / height };
  }
  throw new Error('SVG width/height metadata okunamadı');
};

const parseRasterDimensions = (file) => new Promise((resolve, reject) => {
  const objectUrl = URL.createObjectURL(file);
  const image = new Image();
  image.onload = () => {
    const width = image.width;
    const height = image.height;
    URL.revokeObjectURL(objectUrl);
    if (!width || !height) {
      reject(new Error('Görsel ölçüsü geçersiz'));
      return;
    }
    resolve({ width, height, ratio: width / height });
  };
  image.onerror = () => {
    URL.revokeObjectURL(objectUrl);
    reject(new Error('Görsel okunamadı'));
  };
  image.src = objectUrl;
});

const validateRatio = (ratio) => {
  const min = TARGET_RATIO * (1 - RATIO_TOLERANCE);
  const max = TARGET_RATIO * (1 + RATIO_TOLERANCE);
  return ratio >= min && ratio <= max;
};

export const CorporateHeaderDesigner = () => {
  const authHeader = useMemo(
    () => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` }),
    [],
  );

  const [scope, setScope] = useState('system');
  const [scopeId, setScopeId] = useState('');
  const [configData, setConfigData] = useState(cloneDefaultConfig());
  const [latestConfigId, setLatestConfigId] = useState(null);
  const [versions, setVersions] = useState([]);
  const [effectivePayload, setEffectivePayload] = useState(null);

  const [uploadFile, setUploadFile] = useState(null);
  const [uploadPreviewUrl, setUploadPreviewUrl] = useState('');
  const [uploadMeta, setUploadMeta] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);

  const [status, setStatus] = useState('');
  const [error, setError] = useState('');

  const dragRef = useRef(null);

  useEffect(() => {
    return () => {
      if (uploadPreviewUrl && uploadPreviewUrl.startsWith('blob:')) {
        URL.revokeObjectURL(uploadPreviewUrl);
      }
    };
  }, [uploadPreviewUrl]);

  const scopeQuery = scope === 'tenant' && scopeId.trim() ? `&scope_id=${encodeURIComponent(scopeId.trim())}` : '';

  const ensureLogoInRow1 = (draftConfig) => {
    const safeDraft = safeConfigData(draftConfig);
    const row1 = safeDraft.rows[0];
    const hasLogo = row1.blocks.some((block) => block.type === 'logo');
    if (!hasLogo) {
      row1.blocks.unshift({ id: `logo-${Date.now()}`, type: 'logo', label: 'Logo', required: true });
    }
    return safeDraft;
  };

  const loadDraft = async () => {
    setStatus('');
    setError('');
    try {
      const response = await fetch(
        `${API}/admin/ui/configs/header?segment=corporate&scope=${scope}${scopeQuery}&status=draft`,
        { headers: authHeader },
      );
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data?.detail || 'Kurumsal header taslağı yüklenemedi');
      }

      const item = data?.item;
      const safeDraft = ensureLogoInRow1(item?.config_data || cloneDefaultConfig());
      setConfigData(safeDraft);
      setLatestConfigId(item?.id || null);
      setVersions(Array.isArray(data?.items) ? data.items : []);
      setUploadPreviewUrl(safeDraft?.logo?.url || '');
      setStatus('Kurumsal header taslağı yüklendi');
    } catch (requestError) {
      setError(requestError.message || 'Kurumsal header taslağı yüklenemedi');
      setConfigData(cloneDefaultConfig());
      setLatestConfigId(null);
      setVersions([]);
      setUploadPreviewUrl('');
    }
  };

  useEffect(() => {
    loadDraft();
  }, [scope, scopeId]);

  const validateGuardrails = (candidate) => {
    const rows = Array.isArray(candidate?.rows) ? candidate.rows : [];
    if (rows.length !== 3) {
      throw new Error('Header 3 satır içermelidir');
    }
    if (!rows[0]?.blocks?.some((block) => block.type === 'logo')) {
      throw new Error('Row1 içinde logo bileşeni zorunludur');
    }
    rows.forEach((row) => {
      if (!Array.isArray(row?.blocks) || row.blocks.length === 0) {
        throw new Error(`${row?.id || 'row'} en az bir bileşen içermelidir`);
      }
    });
  };

  const saveDraft = async () => {
    setStatus('');
    setError('');
    try {
      const safeDraft = ensureLogoInRow1(configData);
      validateGuardrails(safeDraft);
      setSaving(true);
      const response = await fetch(`${API}/admin/ui/configs/header`, {
        method: 'POST',
        headers: {
          ...authHeader,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          segment: 'corporate',
          scope,
          scope_id: scope === 'tenant' ? scopeId.trim() : null,
          status: 'draft',
          config_data: safeDraft,
        }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data?.detail || 'Taslak kaydedilemedi');
      }
      setLatestConfigId(data?.item?.id || null);
      setStatus(`Taslak kaydedildi (v${data?.item?.version || '-'})`);
      await loadDraft();
    } catch (requestError) {
      setError(requestError.message || 'Taslak kaydedilemedi');
    } finally {
      setSaving(false);
    }
  };

  const publishLatest = async (configId = latestConfigId) => {
    if (!configId) {
      setError('Yayınlanacak versiyon bulunamadı');
      return;
    }
    setStatus('');
    setError('');
    try {
      const response = await fetch(`${API}/admin/ui/configs/header/publish/${configId}`, {
        method: 'POST',
        headers: authHeader,
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data?.detail || 'Yayınlama başarısız');
      }
      setStatus(`Yayınlandı (v${data?.item?.version || '-'})`);
      await loadDraft();
    } catch (requestError) {
      setError(requestError.message || 'Yayınlama başarısız');
    }
  };

  const loadEffective = async () => {
    setStatus('');
    setError('');
    try {
      const tenantPart = scope === 'tenant' && scopeId.trim()
        ? `&tenant_id=${encodeURIComponent(scopeId.trim())}`
        : '';
      const response = await fetch(`${API}/ui/header?segment=corporate${tenantPart}`, {
        headers: authHeader,
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data?.detail || 'Effective config alınamadı');
      }
      setEffectivePayload(data);
      setStatus('Effective config yüklendi');
    } catch (requestError) {
      setError(requestError.message || 'Effective config alınamadı');
    }
  };

  const onDragStart = (event, rowId, blockIndex) => {
    dragRef.current = { rowId, blockIndex };
    event.dataTransfer.effectAllowed = 'move';
  };

  const onDropToRow = (targetRowId, targetIndex = null) => {
    const dragData = dragRef.current;
    dragRef.current = null;
    if (!dragData) return;

    const { rowId: sourceRowId, blockIndex } = dragData;
    const nextConfig = safeConfigData(configData);
    const sourceRow = nextConfig.rows.find((row) => row.id === sourceRowId);
    const targetRow = nextConfig.rows.find((row) => row.id === targetRowId);
    if (!sourceRow || !targetRow) return;

    const sourceBlocks = [...(sourceRow.blocks || [])];
    if (!sourceBlocks[blockIndex]) return;
    const [draggedBlock] = sourceBlocks.splice(blockIndex, 1);

    if (draggedBlock.type === 'logo' && targetRowId !== 'row1') {
      setError('Logo bileşeni sadece Row1 içinde kalabilir');
      return;
    }

    sourceRow.blocks = sourceBlocks;

    const targetBlocks = [...(targetRow.blocks || [])];
    const insertAt = Number.isInteger(targetIndex) ? targetIndex : targetBlocks.length;
    targetBlocks.splice(Math.max(0, insertAt), 0, draggedBlock);
    targetRow.blocks = targetBlocks;

    try {
      validateGuardrails(nextConfig);
      setConfigData(nextConfig);
    } catch (guardrailError) {
      setError(guardrailError.message || 'Geçersiz yerleşim');
    }
  };

  const removeBlock = (rowId, blockIndex) => {
    const nextConfig = safeConfigData(configData);
    const row = nextConfig.rows.find((item) => item.id === rowId);
    if (!row) return;
    const block = row.blocks?.[blockIndex];
    if (!block) return;
    if (block.required || block.type === 'logo') {
      setError('Logo/zorunlu bileşen kaldırılamaz');
      return;
    }
    row.blocks = row.blocks.filter((_, index) => index !== blockIndex);
    setConfigData(nextConfig);
  };

  const resetDefaults = () => {
    setConfigData(cloneDefaultConfig());
    setUploadPreviewUrl('');
    setUploadMeta(null);
    setStatus('Header düzeni varsayılana sıfırlandı');
    setError('');
  };

  const handleLogoFileChange = async (event) => {
    setStatus('');
    setError('');
    const selected = event.target.files?.[0];
    if (!selected) {
      setUploadFile(null);
      setUploadMeta(null);
      return;
    }

    const ext = fileExtension(selected.name);
    if (!['png', 'svg', 'webp'].includes(ext)) {
      setError('Sadece png/svg/webp formatı desteklenir');
      setUploadFile(null);
      setUploadMeta(null);
      return;
    }
    if (selected.size > MAX_LOGO_BYTES) {
      setError('Logo dosyası 2MB sınırını aşamaz');
      setUploadFile(null);
      setUploadMeta(null);
      return;
    }

    try {
      const dimensions = ext === 'svg' ? await parseSvgDimensions(selected) : await parseRasterDimensions(selected);
      if (!validateRatio(dimensions.ratio)) {
        setError(`Aspect ratio 3:1 (±%10) olmalı. Mevcut: ${dimensions.ratio.toFixed(2)}`);
        setUploadFile(null);
        setUploadMeta(null);
        return;
      }

      if (uploadPreviewUrl && uploadPreviewUrl.startsWith('blob:')) {
        URL.revokeObjectURL(uploadPreviewUrl);
      }
      const localPreview = URL.createObjectURL(selected);
      setUploadPreviewUrl(localPreview);
      setUploadFile(selected);
      setUploadMeta({
        width: Math.round(dimensions.width),
        height: Math.round(dimensions.height),
        ratio: Number(dimensions.ratio.toFixed(4)),
      });
      setStatus('Logo dosyası doğrulandı, yüklemeye hazır');
    } catch (parseError) {
      setUploadFile(null);
      setUploadMeta(null);
      setError(parseError.message || 'Logo doğrulaması başarısız');
    }
  };

  const uploadLogo = async () => {
    if (!uploadFile) {
      setError('Önce logo dosyası seçin');
      return;
    }

    setStatus('');
    setError('');
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      formData.append('segment', 'corporate');
      formData.append('scope', scope);
      if (scope === 'tenant') {
        formData.append('scope_id', scopeId.trim());
      }

      const response = await fetch(`${API}/admin/ui/configs/header/logo`, {
        method: 'POST',
        headers: authHeader,
        body: formData,
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data?.detail || 'Logo yükleme başarısız');
      }

      const item = data?.item;
      const safeDraft = ensureLogoInRow1(item?.config_data || configData);
      setConfigData(safeDraft);
      setLatestConfigId(item?.id || null);
      setUploadPreviewUrl(data?.logo_url || safeDraft?.logo?.url || '');
      setUploadMeta(data?.logo_meta || uploadMeta);
      setUploadFile(null);
      setStatus(`Logo yüklendi ve taslağa işlendi (v${item?.version || '-'})`);
      await loadDraft();
    } catch (requestError) {
      setError(requestError.message || 'Logo yükleme başarısız');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-4" data-testid="ui-designer-corporate-header-designer">
      <div className="grid gap-3 md:grid-cols-3" data-testid="ui-designer-corporate-scope-grid">
        <label className="text-sm" data-testid="ui-designer-corporate-scope-label">
          Scope
          <select
            value={scope}
            onChange={(event) => setScope(event.target.value)}
            className="mt-1 h-10 w-full rounded-md border px-3"
            data-testid="ui-designer-corporate-scope-select"
          >
            <option value="system">system</option>
            <option value="tenant">tenant</option>
          </select>
        </label>
        <label className="text-sm md:col-span-2" data-testid="ui-designer-corporate-scope-id-label">
          Scope ID (tenant için)
          <input
            value={scopeId}
            onChange={(event) => setScopeId(event.target.value)}
            className="mt-1 h-10 w-full rounded-md border px-3"
            placeholder="tenant-001"
            data-testid="ui-designer-corporate-scope-id-input"
          />
        </label>
      </div>

      <div className="rounded-xl border bg-slate-50 p-3" data-testid="ui-designer-corporate-logo-uploader">
        <div className="text-sm font-semibold" data-testid="ui-designer-corporate-logo-title">Row1 · Logo Yükle (3:1 ±%10)</div>
        <div className="mt-2 grid gap-3 md:grid-cols-[1fr_auto]" data-testid="ui-designer-corporate-logo-grid">
          <div className="space-y-2" data-testid="ui-designer-corporate-logo-input-wrap">
            <input
              type="file"
              accept=".png,.svg,.webp,image/png,image/webp,image/svg+xml"
              onChange={handleLogoFileChange}
              data-testid="ui-designer-corporate-logo-file-input"
            />
            <div className="text-xs text-slate-500" data-testid="ui-designer-corporate-logo-hint">
              Format: png/svg/webp · Max: 2MB · Aspect ratio: 3:1 (±%10)
            </div>
          </div>
          <button
            type="button"
            onClick={uploadLogo}
            disabled={uploading || !uploadFile}
            className="h-10 rounded-md bg-slate-900 px-4 text-sm text-white disabled:opacity-60"
            data-testid="ui-designer-corporate-logo-upload-button"
          >
            {uploading ? 'Yükleniyor...' : 'Logo Yükle'}
          </button>
        </div>
        <div className="mt-3 rounded-lg border bg-white p-3" data-testid="ui-designer-corporate-logo-preview-card">
          <div className="text-xs text-slate-500" data-testid="ui-designer-corporate-logo-preview-title">Önizleme</div>
          <div className="mt-2 flex min-h-14 items-center rounded border bg-slate-50 px-3" data-testid="ui-designer-corporate-logo-preview-wrap">
            {uploadPreviewUrl ? (
              <img
                src={uploadPreviewUrl}
                alt="Kurumsal Logo Preview"
                className="h-10 w-32 object-contain"
                data-testid="ui-designer-corporate-logo-preview-image"
              />
            ) : (
              <span className="text-xs font-semibold text-slate-600" data-testid="ui-designer-corporate-logo-preview-fallback">ANNONCIA</span>
            )}
          </div>
          <div className="mt-2 text-xs text-slate-500" data-testid="ui-designer-corporate-logo-meta">
            {uploadMeta ? `w:${uploadMeta.width} · h:${uploadMeta.height} · ratio:${uploadMeta.ratio}` : 'Boyut bilgisi yok'}
          </div>
        </div>
      </div>

      <div className="rounded-xl border bg-white p-3" data-testid="ui-designer-corporate-dnd-editor">
        <div className="flex flex-wrap items-center justify-between gap-2" data-testid="ui-designer-corporate-dnd-header">
          <div className="text-sm font-semibold" data-testid="ui-designer-corporate-dnd-title">Kurumsal Header · 3 Satır Drag&Drop</div>
          <button
            type="button"
            onClick={resetDefaults}
            className="h-8 rounded-md border px-3 text-xs"
            data-testid="ui-designer-corporate-reset-defaults"
          >
            Varsayılanı Yükle
          </button>
        </div>

        <div className="mt-3 grid gap-3 lg:grid-cols-3" data-testid="ui-designer-corporate-dnd-rows">
          {configData.rows.map((row) => (
            <div
              key={row.id}
              className="rounded-lg border bg-slate-50 p-3"
              onDragOver={(event) => event.preventDefault()}
              onDrop={() => onDropToRow(row.id)}
              data-testid={`ui-designer-corporate-row-${row.id}`}
            >
              <div className="mb-2 text-xs font-semibold text-slate-600" data-testid={`ui-designer-corporate-row-title-${row.id}`}>
                {row.title}
              </div>
              <div className="space-y-2" data-testid={`ui-designer-corporate-row-blocks-${row.id}`}>
                {row.blocks.map((block, index) => (
                  <div
                    key={`${block.id}-${index}`}
                    draggable
                    onDragStart={(event) => onDragStart(event, row.id, index)}
                    onDragOver={(event) => event.preventDefault()}
                    onDrop={() => onDropToRow(row.id, index)}
                    className="flex items-center justify-between rounded border bg-white px-2 py-2 text-xs"
                    data-testid={`ui-designer-corporate-block-${row.id}-${block.type}-${index}`}
                  >
                    <div className="flex items-center gap-2" data-testid={`ui-designer-corporate-block-meta-${row.id}-${index}`}>
                      <span className="rounded bg-slate-100 px-1.5 py-0.5">{block.type}</span>
                      <span>{block.label}</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeBlock(row.id, index)}
                      className="rounded border px-2 py-1 text-[11px]"
                      data-testid={`ui-designer-corporate-block-remove-${row.id}-${index}`}
                      disabled={block.required || block.type === 'logo'}
                    >
                      Kaldır
                    </button>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-xl border bg-white p-3" data-testid="ui-designer-corporate-live-preview">
        <div className="text-sm font-semibold" data-testid="ui-designer-corporate-live-preview-title">Canlı Önizleme (Layout JSON)</div>
        <pre className="mt-2 max-h-64 overflow-auto rounded bg-slate-50 p-2 text-[11px]" data-testid="ui-designer-corporate-live-preview-json">
          {prettyJson(configData)}
        </pre>
      </div>

      <div className="flex flex-wrap gap-2" data-testid="ui-designer-corporate-actions">
        <button type="button" onClick={loadDraft} className="h-9 rounded-md border px-3 text-sm" data-testid="ui-designer-corporate-load-draft">
          Taslağı Yükle
        </button>
        <button
          type="button"
          onClick={saveDraft}
          disabled={saving}
          className="h-9 rounded-md border px-3 text-sm"
          data-testid="ui-designer-corporate-save-draft"
        >
          {saving ? 'Kaydediliyor...' : 'Taslak Kaydet'}
        </button>
        <button type="button" onClick={() => publishLatest()} className="h-9 rounded-md bg-slate-900 px-3 text-sm text-white" data-testid="ui-designer-corporate-publish-latest">
          Son Taslağı Yayınla
        </button>
        <button type="button" onClick={loadEffective} className="h-9 rounded-md border px-3 text-sm" data-testid="ui-designer-corporate-load-effective">
          Effective Oku
        </button>
      </div>

      {status ? <div className="text-xs text-emerald-600" data-testid="ui-designer-corporate-status">{status}</div> : null}
      {error ? <div className="text-xs text-rose-600" data-testid="ui-designer-corporate-error">{error}</div> : null}

      <div className="rounded-md border bg-white p-3" data-testid="ui-designer-corporate-versions-card">
        <div className="text-sm font-semibold" data-testid="ui-designer-corporate-versions-title">Versiyonlar</div>
        <div className="mt-2 space-y-2" data-testid="ui-designer-corporate-versions-list">
          {versions.length === 0 ? (
            <div className="text-xs text-slate-500" data-testid="ui-designer-corporate-versions-empty">Versiyon bulunamadı.</div>
          ) : versions.map((item) => (
            <div key={item.id} className="flex items-center justify-between gap-2 rounded border px-2 py-2 text-xs" data-testid={`ui-designer-corporate-version-${item.id}`}>
              <div data-testid={`ui-designer-corporate-version-meta-${item.id}`}>
                v{item.version} • {item.status} • {item.scope}/{item.scope_id || 'system'}
              </div>
              <button
                type="button"
                onClick={() => publishLatest(item.id)}
                className="rounded border px-2 py-1"
                data-testid={`ui-designer-corporate-publish-version-${item.id}`}
              >
                Yayınla
              </button>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-md border bg-white p-3" data-testid="ui-designer-corporate-effective-card">
        <div className="text-sm font-semibold" data-testid="ui-designer-corporate-effective-title">Effective Sonuç</div>
        <div className="mt-2 text-xs text-slate-600" data-testid="ui-designer-corporate-effective-source">
          Source: {effectivePayload?.source_scope || '-'} / {effectivePayload?.source_scope_id || 'system'}
        </div>
        <pre className="mt-2 max-h-52 overflow-auto rounded bg-slate-50 p-2 text-[11px]" data-testid="ui-designer-corporate-effective-json">
          {prettyJson(effectivePayload?.config_data || {})}
        </pre>
      </div>

      <div className="hidden" data-testid="ui-designer-corporate-latest-config-id">{latestConfigId || ''}</div>
    </div>
  );
};
