import React, { useEffect, useMemo, useState } from 'react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const prettyJson = (value) => JSON.stringify(value ?? {}, null, 2);

const parseJsonOrThrow = (raw, label) => {
  try {
    return JSON.parse(raw || '{}');
  } catch (error) {
    throw new Error(`${label} JSON formatı geçersiz`);
  }
};

export const IndividualHeaderConfigTab = () => {
  const authHeader = useMemo(
    () => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` }),
    [],
  );

  const [scope, setScope] = useState('system');
  const [scopeId, setScopeId] = useState('');
  const [headerJson, setHeaderJson] = useState(prettyJson({}));
  const [latestConfigId, setLatestConfigId] = useState(null);
  const [versions, setVersions] = useState([]);
  const [effectivePayload, setEffectivePayload] = useState(null);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');

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
        throw new Error(data?.detail || 'Taslak yüklenemedi');
      }

      const item = data?.item;
      setLatestConfigId(item?.id || null);
      setHeaderJson(prettyJson(item?.config_data || {}));
      setVersions(Array.isArray(data?.items) ? data.items : []);
      setStatus('Taslak yüklendi');
    } catch (requestError) {
      setError(requestError.message || 'Taslak yüklenemedi');
      setVersions([]);
      setLatestConfigId(null);
    }
  };

  const saveDraft = async () => {
    setStatus('');
    setError('');
    try {
      const payload = {
        segment: 'individual',
        scope,
        scope_id: scope === 'tenant' ? scopeId.trim() : null,
        status: 'draft',
        config_data: parseJsonOrThrow(headerJson, 'Bireysel header config'),
      };

      const response = await fetch(`${API}/admin/ui/configs/header`, {
        method: 'POST',
        headers: {
          ...authHeader,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
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
    }
  };

  const publishConfig = async (configId = latestConfigId) => {
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

      setLatestConfigId(data?.item?.id || configId);
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
      const response = await fetch(`${API}/ui/header?segment=individual${tenantPart}`, {
        headers: authHeader,
      });
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

  useEffect(() => {
    loadDraft();
  }, [scope, scopeId]);

  return (
    <div className="space-y-4" data-testid="ui-designer-individual-header-container">
      <div className="grid gap-3 md:grid-cols-3" data-testid="ui-designer-individual-header-scope-row">
        <label className="text-sm" data-testid="ui-designer-individual-header-scope-label">
          Scope
          <select
            value={scope}
            onChange={(event) => setScope(event.target.value)}
            className="mt-1 h-10 w-full rounded-md border px-3"
            data-testid="ui-designer-individual-header-scope-select"
          >
            <option value="system">system</option>
            <option value="tenant">tenant</option>
          </select>
        </label>
        <label className="text-sm md:col-span-2" data-testid="ui-designer-individual-header-scope-id-label">
          Scope ID (tenant için)
          <input
            value={scopeId}
            onChange={(event) => setScopeId(event.target.value)}
            className="mt-1 h-10 w-full rounded-md border px-3"
            placeholder="tenant-001"
            data-testid="ui-designer-individual-header-scope-id-input"
          />
        </label>
      </div>

      <label className="block text-sm" data-testid="ui-designer-individual-header-json-label">
        Header Config JSON
        <textarea
          value={headerJson}
          onChange={(event) => setHeaderJson(event.target.value)}
          rows={12}
          className="mt-1 w-full rounded-md border p-3 font-mono text-xs"
          data-testid="ui-designer-individual-header-json-textarea"
        />
      </label>

      <div className="flex flex-wrap gap-2" data-testid="ui-designer-individual-header-actions">
        <button type="button" onClick={loadDraft} className="h-9 rounded-md border px-3 text-sm" data-testid="ui-designer-individual-header-load-draft">
          Taslağı Yükle
        </button>
        <button type="button" onClick={saveDraft} className="h-9 rounded-md border px-3 text-sm" data-testid="ui-designer-individual-header-save-draft">
          Taslak Kaydet
        </button>
        <button type="button" onClick={() => publishConfig()} className="h-9 rounded-md bg-slate-900 px-3 text-sm text-white" data-testid="ui-designer-individual-header-publish-latest">
          Son Taslağı Yayınla
        </button>
        <button type="button" onClick={loadEffective} className="h-9 rounded-md border px-3 text-sm" data-testid="ui-designer-individual-header-load-effective">
          Effective Oku
        </button>
      </div>

      {status ? (
        <div className="text-xs text-emerald-600" data-testid="ui-designer-individual-header-status">{status}</div>
      ) : null}
      {error ? (
        <div className="text-xs text-rose-600" data-testid="ui-designer-individual-header-error">{error}</div>
      ) : null}

      <div className="rounded-md border bg-white p-3" data-testid="ui-designer-individual-header-versions">
        <div className="text-sm font-semibold" data-testid="ui-designer-individual-header-versions-title">Versiyonlar</div>
        <div className="mt-2 space-y-2" data-testid="ui-designer-individual-header-versions-list">
          {versions.length === 0 ? (
            <div className="text-xs text-slate-500" data-testid="ui-designer-individual-header-versions-empty">Versiyon bulunamadı.</div>
          ) : versions.map((item) => (
            <div key={item.id} className="flex items-center justify-between gap-2 rounded border px-2 py-2 text-xs" data-testid={`ui-designer-individual-header-version-${item.id}`}>
              <div data-testid={`ui-designer-individual-header-version-meta-${item.id}`}>
                v{item.version} • {item.status} • {item.scope}/{item.scope_id || 'system'}
              </div>
              <button
                type="button"
                onClick={() => publishConfig(item.id)}
                className="rounded border px-2 py-1"
                data-testid={`ui-designer-individual-header-publish-version-${item.id}`}
              >
                Yayınla
              </button>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-md border bg-white p-3" data-testid="ui-designer-individual-header-effective">
        <div className="text-sm font-semibold" data-testid="ui-designer-individual-header-effective-title">Effective Sonuç</div>
        <div className="mt-2 text-xs text-slate-600" data-testid="ui-designer-individual-header-effective-source">
          Source: {effectivePayload?.source_scope || '-'} / {effectivePayload?.source_scope_id || 'system'}
        </div>
        <pre className="mt-2 max-h-52 overflow-auto rounded bg-slate-50 p-2 text-[11px]" data-testid="ui-designer-individual-header-effective-json">
          {prettyJson(effectivePayload?.config_data || {})}
        </pre>
      </div>
    </div>
  );
};
