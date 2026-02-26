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

function HeaderConfigTab({ segment, testIdPrefix }) {
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
        `${API}/admin/ui/header?segment=${segment}&scope=${scope}${scopeQuery}&status=draft`,
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
        segment,
        scope,
        scope_id: scope === 'tenant' ? scopeId.trim() : null,
        status: 'draft',
        config_data: parseJsonOrThrow(headerJson, 'Header config'),
      };

      const response = await fetch(`${API}/admin/ui/header`, {
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
      const response = await fetch(`${API}/admin/ui/header/publish/${configId}`, {
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
      const response = await fetch(`${API}/ui/header?segment=${segment}${tenantPart}`, {
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
  }, [segment]);

  return (
    <div className="space-y-4" data-testid={`${testIdPrefix}-container`}>
      <div className="grid gap-3 md:grid-cols-3" data-testid={`${testIdPrefix}-scope-row`}>
        <label className="text-sm" data-testid={`${testIdPrefix}-scope-label`}>
          Scope
          <select
            value={scope}
            onChange={(event) => setScope(event.target.value)}
            className="mt-1 h-10 w-full rounded-md border px-3"
            data-testid={`${testIdPrefix}-scope-select`}
          >
            <option value="system">system</option>
            <option value="tenant">tenant</option>
          </select>
        </label>
        <label className="text-sm md:col-span-2" data-testid={`${testIdPrefix}-scope-id-label`}>
          Scope ID (tenant için)
          <input
            value={scopeId}
            onChange={(event) => setScopeId(event.target.value)}
            className="mt-1 h-10 w-full rounded-md border px-3"
            placeholder="tenant-001"
            data-testid={`${testIdPrefix}-scope-id-input`}
          />
        </label>
      </div>

      <label className="block text-sm" data-testid={`${testIdPrefix}-json-label`}>
        Header Config JSON
        <textarea
          value={headerJson}
          onChange={(event) => setHeaderJson(event.target.value)}
          rows={12}
          className="mt-1 w-full rounded-md border p-3 font-mono text-xs"
          data-testid={`${testIdPrefix}-json-textarea`}
        />
      </label>

      <div className="flex flex-wrap gap-2" data-testid={`${testIdPrefix}-actions`}>
        <button type="button" onClick={loadDraft} className="h-9 rounded-md border px-3 text-sm" data-testid={`${testIdPrefix}-load-draft`}>
          Taslağı Yükle
        </button>
        <button type="button" onClick={saveDraft} className="h-9 rounded-md border px-3 text-sm" data-testid={`${testIdPrefix}-save-draft`}>
          Taslak Kaydet
        </button>
        <button type="button" onClick={() => publishConfig()} className="h-9 rounded-md bg-slate-900 px-3 text-sm text-white" data-testid={`${testIdPrefix}-publish-latest`}>
          Son Taslağı Yayınla
        </button>
        <button type="button" onClick={loadEffective} className="h-9 rounded-md border px-3 text-sm" data-testid={`${testIdPrefix}-load-effective`}>
          Effective Oku
        </button>
      </div>

      {status ? (
        <div className="text-xs text-emerald-600" data-testid={`${testIdPrefix}-status`}>
          {status}
        </div>
      ) : null}
      {error ? (
        <div className="text-xs text-rose-600" data-testid={`${testIdPrefix}-error`}>
          {error}
        </div>
      ) : null}

      <div className="rounded-md border bg-white p-3" data-testid={`${testIdPrefix}-versions`}>
        <div className="text-sm font-semibold" data-testid={`${testIdPrefix}-versions-title`}>Versiyonlar</div>
        <div className="mt-2 space-y-2" data-testid={`${testIdPrefix}-versions-list`}>
          {versions.length === 0 ? (
            <div className="text-xs text-slate-500" data-testid={`${testIdPrefix}-versions-empty`}>Versiyon bulunamadı.</div>
          ) : versions.map((item) => (
            <div key={item.id} className="flex items-center justify-between gap-2 rounded border px-2 py-2 text-xs" data-testid={`${testIdPrefix}-version-${item.id}`}>
              <div data-testid={`${testIdPrefix}-version-meta-${item.id}`}>
                v{item.version} • {item.status} • {item.scope}/{item.scope_id || 'system'}
              </div>
              <button
                type="button"
                onClick={() => publishConfig(item.id)}
                className="rounded border px-2 py-1"
                data-testid={`${testIdPrefix}-publish-version-${item.id}`}
              >
                Yayınla
              </button>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-md border bg-white p-3" data-testid={`${testIdPrefix}-effective` }>
        <div className="text-sm font-semibold" data-testid={`${testIdPrefix}-effective-title`}>Effective Sonuç</div>
        <div className="mt-2 text-xs text-slate-600" data-testid={`${testIdPrefix}-effective-source`}>
          Source: {effectivePayload?.source_scope || '-'} / {effectivePayload?.source_scope_id || 'system'}
        </div>
        <pre className="mt-2 max-h-52 overflow-auto rounded bg-slate-50 p-2 text-[11px]" data-testid={`${testIdPrefix}-effective-json`}>
          {prettyJson(effectivePayload?.config_data || {})}
        </pre>
      </div>
    </div>
  );
}

function ThemeManagementTab() {
  const authHeader = useMemo(
    () => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` }),
    [],
  );

  const [themeName, setThemeName] = useState('Yeni Tema');
  const [tokensJson, setTokensJson] = useState(prettyJson({ primary: '#111827', accent: '#f97316' }));
  const [themes, setThemes] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [selectedThemeId, setSelectedThemeId] = useState('');
  const [assignScope, setAssignScope] = useState('system');
  const [assignScopeId, setAssignScopeId] = useState('');
  const [effectiveTenantId, setEffectiveTenantId] = useState('');
  const [effectiveUserId, setEffectiveUserId] = useState('');
  const [effectiveResult, setEffectiveResult] = useState(null);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');

  const fetchThemes = async () => {
    const response = await fetch(`${API}/admin/ui/themes`, { headers: authHeader });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data?.detail || 'Theme listesi alınamadı');
    const items = Array.isArray(data?.items) ? data.items : [];
    setThemes(items);
    if (!selectedThemeId && items[0]?.id) {
      setSelectedThemeId(items[0].id);
    }
  };

  const fetchAssignments = async () => {
    const response = await fetch(`${API}/admin/ui/theme-assignments`, { headers: authHeader });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data?.detail || 'Theme assignment listesi alınamadı');
    setAssignments(Array.isArray(data?.items) ? data.items : []);
  };

  const refreshThemeData = async () => {
    await Promise.all([fetchThemes(), fetchAssignments()]);
  };

  useEffect(() => {
    refreshThemeData().catch((requestError) => setError(requestError.message || 'Tema verisi alınamadı'));
  }, []);

  const createTheme = async () => {
    setStatus('');
    setError('');
    try {
      const payload = {
        name: themeName.trim(),
        tokens: parseJsonOrThrow(tokensJson, 'Theme tokens'),
        is_active: false,
      };
      const response = await fetch(`${API}/admin/ui/themes`, {
        method: 'POST',
        headers: {
          ...authHeader,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data?.detail || 'Theme oluşturulamadı');

      setSelectedThemeId(data?.item?.id || '');
      setStatus(`Theme oluşturuldu: ${data?.item?.name || '-'}`);
      await refreshThemeData();
    } catch (requestError) {
      setError(requestError.message || 'Theme oluşturulamadı');
    }
  };

  const activateTheme = async (themeId) => {
    setStatus('');
    setError('');
    try {
      const response = await fetch(`${API}/admin/ui/themes/${themeId}`, {
        method: 'PATCH',
        headers: {
          ...authHeader,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ is_active: true }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data?.detail || 'Theme aktive edilemedi');

      setStatus(`Aktif tema: ${data?.item?.name || '-'}`);
      await refreshThemeData();
    } catch (requestError) {
      setError(requestError.message || 'Theme aktive edilemedi');
    }
  };

  const assignTheme = async () => {
    if (!selectedThemeId) {
      setError('Önce bir tema seçin');
      return;
    }

    setStatus('');
    setError('');
    try {
      const response = await fetch(`${API}/admin/ui/theme-assignments`, {
        method: 'POST',
        headers: {
          ...authHeader,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          theme_id: selectedThemeId,
          scope: assignScope,
          scope_id: assignScope === 'system' ? null : assignScopeId.trim(),
        }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data?.detail || 'Theme ataması başarısız');

      setStatus('Theme ataması kaydedildi');
      await fetchAssignments();
    } catch (requestError) {
      setError(requestError.message || 'Theme ataması başarısız');
    }
  };

  const resolveEffectiveTheme = async () => {
    setStatus('');
    setError('');
    try {
      const params = new URLSearchParams();
      if (effectiveTenantId.trim()) params.set('tenant_id', effectiveTenantId.trim());
      if (effectiveUserId.trim()) params.set('user_id', effectiveUserId.trim());

      const response = await fetch(`${API}/ui/themes/effective?${params.toString()}`, {
        headers: authHeader,
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data?.detail || 'Effective theme alınamadı');

      setEffectiveResult(data);
      setStatus('Effective theme alındı');
    } catch (requestError) {
      setError(requestError.message || 'Effective theme alınamadı');
    }
  };

  return (
    <div className="space-y-4" data-testid="ui-designer-theme-container">
      <div className="grid gap-3 md:grid-cols-2" data-testid="ui-designer-theme-create-grid">
        <label className="text-sm" data-testid="ui-designer-theme-name-label">
          Theme Adı
          <input
            value={themeName}
            onChange={(event) => setThemeName(event.target.value)}
            className="mt-1 h-10 w-full rounded-md border px-3"
            data-testid="ui-designer-theme-name-input"
          />
        </label>
        <div className="flex items-end" data-testid="ui-designer-theme-create-action">
          <button type="button" onClick={createTheme} className="h-10 rounded-md bg-slate-900 px-4 text-sm text-white" data-testid="ui-designer-theme-create-button">
            Theme Oluştur
          </button>
        </div>
      </div>

      <label className="block text-sm" data-testid="ui-designer-theme-tokens-label">
        Tokens JSON
        <textarea
          value={tokensJson}
          onChange={(event) => setTokensJson(event.target.value)}
          rows={8}
          className="mt-1 w-full rounded-md border p-3 font-mono text-xs"
          data-testid="ui-designer-theme-tokens-textarea"
        />
      </label>

      <div className="rounded-md border bg-white p-3" data-testid="ui-designer-theme-assign-card">
        <div className="text-sm font-semibold" data-testid="ui-designer-theme-assign-title">Theme Assign (system / tenant / user)</div>
        <div className="mt-2 grid gap-3 md:grid-cols-4" data-testid="ui-designer-theme-assign-grid">
          <label className="text-xs" data-testid="ui-designer-theme-select-label">
            Theme
            <select
              value={selectedThemeId}
              onChange={(event) => setSelectedThemeId(event.target.value)}
              className="mt-1 h-10 w-full rounded-md border px-2"
              data-testid="ui-designer-theme-select"
            >
              <option value="">Seçiniz</option>
              {themes.map((theme) => (
                <option key={theme.id} value={theme.id}>{theme.name}</option>
              ))}
            </select>
          </label>
          <label className="text-xs" data-testid="ui-designer-theme-assign-scope-label">
            Scope
            <select
              value={assignScope}
              onChange={(event) => setAssignScope(event.target.value)}
              className="mt-1 h-10 w-full rounded-md border px-2"
              data-testid="ui-designer-theme-assign-scope-select"
            >
              <option value="system">system</option>
              <option value="tenant">tenant</option>
              <option value="user">user</option>
            </select>
          </label>
          <label className="text-xs" data-testid="ui-designer-theme-assign-scope-id-label">
            Scope ID
            <input
              value={assignScopeId}
              onChange={(event) => setAssignScopeId(event.target.value)}
              className="mt-1 h-10 w-full rounded-md border px-2"
              placeholder="tenant-001 veya user-001"
              data-testid="ui-designer-theme-assign-scope-id-input"
            />
          </label>
          <div className="flex items-end" data-testid="ui-designer-theme-assign-action">
            <button type="button" onClick={assignTheme} className="h-10 rounded-md border px-3 text-sm" data-testid="ui-designer-theme-assign-button">
              Atamayı Kaydet
            </button>
          </div>
        </div>
      </div>

      <div className="rounded-md border bg-white p-3" data-testid="ui-designer-theme-list-card">
        <div className="text-sm font-semibold" data-testid="ui-designer-theme-list-title">Theme Listesi</div>
        <div className="mt-2 space-y-2" data-testid="ui-designer-theme-list">
          {themes.length === 0 ? (
            <div className="text-xs text-slate-500" data-testid="ui-designer-theme-list-empty">Theme bulunamadı.</div>
          ) : themes.map((theme) => (
            <div key={theme.id} className="flex items-center justify-between gap-2 rounded border px-2 py-2 text-xs" data-testid={`ui-designer-theme-item-${theme.id}`}>
              <div data-testid={`ui-designer-theme-item-meta-${theme.id}`}>
                {theme.name} • active={String(theme.is_active)}
              </div>
              <button type="button" onClick={() => activateTheme(theme.id)} className="rounded border px-2 py-1" data-testid={`ui-designer-theme-activate-${theme.id}`}>
                Aktif Yap
              </button>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-md border bg-white p-3" data-testid="ui-designer-theme-assignment-list-card">
        <div className="text-sm font-semibold" data-testid="ui-designer-theme-assignment-list-title">Theme Assignment Listesi</div>
        <div className="mt-2 space-y-2" data-testid="ui-designer-theme-assignment-list">
          {assignments.length === 0 ? (
            <div className="text-xs text-slate-500" data-testid="ui-designer-theme-assignment-list-empty">Atama bulunamadı.</div>
          ) : assignments.map((assignment) => (
            <div key={assignment.id} className="rounded border px-2 py-2 text-xs" data-testid={`ui-designer-theme-assignment-item-${assignment.id}`}>
              scope={assignment.scope} / scope_id={assignment.scope_id || 'system'} / theme_id={assignment.theme_id}
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-md border bg-white p-3" data-testid="ui-designer-theme-effective-card">
        <div className="text-sm font-semibold" data-testid="ui-designer-theme-effective-title">Effective Theme Resolve</div>
        <div className="mt-2 grid gap-3 md:grid-cols-3" data-testid="ui-designer-theme-effective-grid">
          <label className="text-xs" data-testid="ui-designer-theme-effective-tenant-label">
            tenant_id
            <input
              value={effectiveTenantId}
              onChange={(event) => setEffectiveTenantId(event.target.value)}
              className="mt-1 h-10 w-full rounded-md border px-2"
              data-testid="ui-designer-theme-effective-tenant-input"
            />
          </label>
          <label className="text-xs" data-testid="ui-designer-theme-effective-user-label">
            user_id
            <input
              value={effectiveUserId}
              onChange={(event) => setEffectiveUserId(event.target.value)}
              className="mt-1 h-10 w-full rounded-md border px-2"
              data-testid="ui-designer-theme-effective-user-input"
            />
          </label>
          <div className="flex items-end" data-testid="ui-designer-theme-effective-action">
            <button type="button" onClick={resolveEffectiveTheme} className="h-10 rounded-md border px-3 text-sm" data-testid="ui-designer-theme-effective-button">
              Effective Getir
            </button>
          </div>
        </div>
        <div className="mt-2 text-xs text-slate-600" data-testid="ui-designer-theme-effective-source">
          Source: {effectiveResult?.source_scope || '-'} / {effectiveResult?.source_scope_id || 'system'}
        </div>
        <pre className="mt-2 max-h-52 overflow-auto rounded bg-slate-50 p-2 text-[11px]" data-testid="ui-designer-theme-effective-json">
          {prettyJson(effectiveResult?.tokens || {})}
        </pre>
      </div>

      {status ? <div className="text-xs text-emerald-600" data-testid="ui-designer-theme-status">{status}</div> : null}
      {error ? <div className="text-xs text-rose-600" data-testid="ui-designer-theme-error">{error}</div> : null}
    </div>
  );
}

export default function AdminUserInterfaceDesign() {
  const [activeTab, setActiveTab] = useState('corporate');

  return (
    <div className="space-y-6" data-testid="admin-user-interface-design-page">
      <div data-testid="admin-user-interface-design-header">
        <h1 className="text-2xl font-semibold" data-testid="admin-user-interface-design-title">Kullanıcı Tasarım</h1>
        <p className="text-sm text-slate-600" data-testid="admin-user-interface-design-subtitle">
          Sprint 1: API roundtrip doğrulaması (Header config + Theme yönetimi)
        </p>
      </div>

      <div className="flex flex-wrap gap-2" data-testid="admin-user-interface-design-tabs">
        <button
          type="button"
          onClick={() => setActiveTab('corporate')}
          className={`h-10 rounded-md border px-4 text-sm ${activeTab === 'corporate' ? 'bg-slate-900 text-white' : ''}`}
          data-testid="admin-user-interface-design-tab-corporate"
        >
          Kurumsal UI Tasarım
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('individual')}
          className={`h-10 rounded-md border px-4 text-sm ${activeTab === 'individual' ? 'bg-slate-900 text-white' : ''}`}
          data-testid="admin-user-interface-design-tab-individual"
        >
          Bireysel Header Tasarım
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('theme')}
          className={`h-10 rounded-md border px-4 text-sm ${activeTab === 'theme' ? 'bg-slate-900 text-white' : ''}`}
          data-testid="admin-user-interface-design-tab-theme"
        >
          Tema Yönetimi
        </button>
      </div>

      <div className="rounded-xl border bg-white p-4" data-testid="admin-user-interface-design-tab-content">
        {activeTab === 'corporate' ? (
          <HeaderConfigTab segment="corporate" testIdPrefix="ui-designer-corporate-header" />
        ) : null}
        {activeTab === 'individual' ? (
          <HeaderConfigTab segment="individual" testIdPrefix="ui-designer-individual-header" />
        ) : null}
        {activeTab === 'theme' ? <ThemeManagementTab /> : null}
      </div>
    </div>
  );
}
