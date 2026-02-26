import React, { useEffect, useMemo, useState } from 'react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const defaultTokenForm = {
  colors: {
    primary: '#111827',
    secondary: '#334155',
    accent: '#f97316',
    text: '#0f172a',
    inverse: '#ffffff',
  },
  typography: {
    font_family: 'Poppins',
    base_font_size: '16',
  },
  spacing: {
    xs: '4',
    sm: '8',
    md: '12',
    lg: '16',
    xl: '24',
  },
  radius: {
    sm: '4',
    md: '8',
    lg: '12',
  },
  shadow: {
    sm: '0 1px 2px rgba(0,0,0,0.08)',
    md: '0 4px 10px rgba(0,0,0,0.12)',
    lg: '0 8px 20px rgba(0,0,0,0.16)',
  },
};

const hexColorRegex = /^#[0-9a-fA-F]{6}$/;

const tokenFormFromTheme = (tokens = {}) => ({
  colors: {
    ...defaultTokenForm.colors,
    ...(tokens.colors || {}),
  },
  typography: {
    ...defaultTokenForm.typography,
    ...(tokens.typography || {}),
    base_font_size: `${tokens?.typography?.base_font_size ?? defaultTokenForm.typography.base_font_size}`,
  },
  spacing: {
    ...defaultTokenForm.spacing,
    ...(tokens.spacing || {}),
    xs: `${tokens?.spacing?.xs ?? defaultTokenForm.spacing.xs}`,
    sm: `${tokens?.spacing?.sm ?? defaultTokenForm.spacing.sm}`,
    md: `${tokens?.spacing?.md ?? defaultTokenForm.spacing.md}`,
    lg: `${tokens?.spacing?.lg ?? defaultTokenForm.spacing.lg}`,
    xl: `${tokens?.spacing?.xl ?? defaultTokenForm.spacing.xl}`,
  },
  radius: {
    ...defaultTokenForm.radius,
    ...(tokens.radius || {}),
    sm: `${tokens?.radius?.sm ?? defaultTokenForm.radius.sm}`,
    md: `${tokens?.radius?.md ?? defaultTokenForm.radius.md}`,
    lg: `${tokens?.radius?.lg ?? defaultTokenForm.radius.lg}`,
  },
  shadow: {
    ...defaultTokenForm.shadow,
    ...(tokens.shadow || {}),
  },
});

const toInt = (value) => Number.parseInt(`${value}`, 10);

const buildTokensPayload = (tokenForm) => ({
  colors: { ...tokenForm.colors },
  typography: {
    font_family: tokenForm.typography.font_family,
    base_font_size: toInt(tokenForm.typography.base_font_size),
  },
  spacing: {
    xs: toInt(tokenForm.spacing.xs),
    sm: toInt(tokenForm.spacing.sm),
    md: toInt(tokenForm.spacing.md),
    lg: toInt(tokenForm.spacing.lg),
    xl: toInt(tokenForm.spacing.xl),
  },
  radius: {
    sm: toInt(tokenForm.radius.sm),
    md: toInt(tokenForm.radius.md),
    lg: toInt(tokenForm.radius.lg),
  },
  shadow: { ...tokenForm.shadow },
});

const validateTokenForm = (tokenForm) => {
  const errors = [];
  Object.entries(tokenForm.colors).forEach(([key, value]) => {
    if (!hexColorRegex.test(`${value}`.trim())) {
      errors.push(`${key} hex formatında olmalı (#RRGGBB)`);
    }
  });

  const baseFont = toInt(tokenForm.typography.base_font_size);
  if (Number.isNaN(baseFont) || baseFont < 12 || baseFont > 24) {
    errors.push('base_font_size 12-24 aralığında olmalı');
  }

  ['xs', 'sm', 'md', 'lg', 'xl'].forEach((key) => {
    const value = toInt(tokenForm.spacing[key]);
    if (Number.isNaN(value) || value < 0 || value > 64) {
      errors.push(`spacing.${key} 0-64 aralığında olmalı`);
    }
  });

  ['sm', 'md', 'lg'].forEach((key) => {
    const value = toInt(tokenForm.radius[key]);
    if (Number.isNaN(value) || value < 0 || value > 32) {
      errors.push(`radius.${key} 0-32 aralığında olmalı`);
    }
  });

  return errors;
};

export const ThemeTokenManagementTab = () => {
  const authHeader = useMemo(
    () => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` }),
    [],
  );

  const [themeName, setThemeName] = useState('Yeni Tema');
  const [tokenForm, setTokenForm] = useState(defaultTokenForm);
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

  const tokensPreview = useMemo(() => JSON.stringify(buildTokensPayload(tokenForm), null, 2), [tokenForm]);

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

  const setTokenField = (section, key, value) => {
    setTokenForm((prev) => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value,
      },
    }));
  };

  const runTokenValidation = () => {
    const validationErrors = validateTokenForm(tokenForm);
    if (validationErrors.length > 0) {
      throw new Error(validationErrors.join(' • '));
    }
    return buildTokensPayload(tokenForm);
  };

  const createTheme = async () => {
    setStatus('');
    setError('');
    try {
      const tokens = runTokenValidation();
      const payload = {
        name: themeName.trim(),
        tokens,
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

  const updateSelectedTheme = async () => {
    if (!selectedThemeId) {
      setError('Önce bir theme seçin');
      return;
    }
    setStatus('');
    setError('');
    try {
      const tokens = runTokenValidation();
      const response = await fetch(`${API}/admin/ui/themes/${selectedThemeId}`, {
        method: 'PATCH',
        headers: {
          ...authHeader,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: themeName.trim(),
          tokens,
        }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data?.detail || 'Theme güncellenemedi');

      setStatus(`Theme güncellendi: ${data?.item?.name || '-'}`);
      await refreshThemeData();
    } catch (requestError) {
      setError(requestError.message || 'Theme güncellenemedi');
    }
  };

  const loadSelectedThemeToForm = () => {
    if (!selectedThemeId) {
      setError('Önce bir theme seçin');
      return;
    }
    const match = themes.find((theme) => theme.id === selectedThemeId);
    if (!match) {
      setError('Seçili theme bulunamadı');
      return;
    }

    setTokenForm(tokenFormFromTheme(match.tokens || {}));
    setThemeName(match.name || 'Tema');
    setStatus('Theme tokenları forma yüklendi');
    setError('');
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
      setError('Önce bir theme seçin');
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
      <div className="grid gap-3 md:grid-cols-3" data-testid="ui-designer-theme-head-grid">
        <label className="text-sm md:col-span-2" data-testid="ui-designer-theme-name-label">
          Theme Adı
          <input
            value={themeName}
            onChange={(event) => setThemeName(event.target.value)}
            className="mt-1 h-10 w-full rounded-md border px-3"
            data-testid="ui-designer-theme-name-input"
          />
        </label>
        <div className="flex items-end gap-2" data-testid="ui-designer-theme-head-actions">
          <button type="button" onClick={createTheme} className="h-10 rounded-md bg-slate-900 px-4 text-sm text-white" data-testid="ui-designer-theme-create-button">
            Theme Oluştur
          </button>
          <button type="button" onClick={updateSelectedTheme} className="h-10 rounded-md border px-4 text-sm" data-testid="ui-designer-theme-update-button">
            Seçiliyi Güncelle
          </button>
        </div>
      </div>

      <div className="rounded-md border bg-white p-3" data-testid="ui-designer-theme-token-form-card">
        <div className="text-sm font-semibold" data-testid="ui-designer-theme-token-form-title">Token Form Editörü</div>
        <div className="mt-3 grid gap-3 md:grid-cols-5" data-testid="ui-designer-theme-color-grid">
          {Object.keys(tokenForm.colors).map((key) => (
            <label key={key} className="text-xs" data-testid={`ui-designer-theme-color-${key}-label`}>
              {key}
              <input
                value={tokenForm.colors[key]}
                onChange={(event) => setTokenField('colors', key, event.target.value)}
                className="mt-1 h-9 w-full rounded-md border px-2"
                data-testid={`ui-designer-theme-color-${key}-input`}
              />
            </label>
          ))}
        </div>

        <div className="mt-3 grid gap-3 md:grid-cols-3" data-testid="ui-designer-theme-typography-grid">
          <label className="text-xs" data-testid="ui-designer-theme-font-family-label">
            font_family
            <input
              value={tokenForm.typography.font_family}
              onChange={(event) => setTokenField('typography', 'font_family', event.target.value)}
              className="mt-1 h-9 w-full rounded-md border px-2"
              data-testid="ui-designer-theme-font-family-input"
            />
          </label>
          <label className="text-xs" data-testid="ui-designer-theme-base-font-size-label">
            base_font_size (12-24)
            <input
              value={tokenForm.typography.base_font_size}
              onChange={(event) => setTokenField('typography', 'base_font_size', event.target.value)}
              className="mt-1 h-9 w-full rounded-md border px-2"
              data-testid="ui-designer-theme-base-font-size-input"
            />
          </label>
          <div className="text-xs text-slate-500" data-testid="ui-designer-theme-validation-hint">
            Hex / spacing / radius validasyonu create-update sırasında zorunludur.
          </div>
        </div>

        <div className="mt-3 grid gap-3 md:grid-cols-5" data-testid="ui-designer-theme-spacing-grid">
          {Object.keys(tokenForm.spacing).map((key) => (
            <label key={key} className="text-xs" data-testid={`ui-designer-theme-spacing-${key}-label`}>
              spacing.{key}
              <input
                value={tokenForm.spacing[key]}
                onChange={(event) => setTokenField('spacing', key, event.target.value)}
                className="mt-1 h-9 w-full rounded-md border px-2"
                data-testid={`ui-designer-theme-spacing-${key}-input`}
              />
            </label>
          ))}
        </div>

        <div className="mt-3 grid gap-3 md:grid-cols-3" data-testid="ui-designer-theme-radius-grid">
          {Object.keys(tokenForm.radius).map((key) => (
            <label key={key} className="text-xs" data-testid={`ui-designer-theme-radius-${key}-label`}>
              radius.{key}
              <input
                value={tokenForm.radius[key]}
                onChange={(event) => setTokenField('radius', key, event.target.value)}
                className="mt-1 h-9 w-full rounded-md border px-2"
                data-testid={`ui-designer-theme-radius-${key}-input`}
              />
            </label>
          ))}
        </div>

        <div className="mt-3 grid gap-3 md:grid-cols-3" data-testid="ui-designer-theme-shadow-grid">
          {Object.keys(tokenForm.shadow).map((key) => (
            <label key={key} className="text-xs" data-testid={`ui-designer-theme-shadow-${key}-label`}>
              shadow.{key}
              <input
                value={tokenForm.shadow[key]}
                onChange={(event) => setTokenField('shadow', key, event.target.value)}
                className="mt-1 h-9 w-full rounded-md border px-2"
                data-testid={`ui-designer-theme-shadow-${key}-input`}
              />
            </label>
          ))}
        </div>

        <pre className="mt-3 max-h-60 overflow-auto rounded bg-slate-50 p-2 text-[11px]" data-testid="ui-designer-theme-token-preview-json">
          {tokensPreview}
        </pre>
      </div>

      <div className="rounded-md border bg-white p-3" data-testid="ui-designer-theme-select-card">
        <div className="text-sm font-semibold" data-testid="ui-designer-theme-select-title">Seçili Theme</div>
        <div className="mt-2 grid gap-3 md:grid-cols-[1fr_auto]" data-testid="ui-designer-theme-select-grid">
          <label className="text-xs" data-testid="ui-designer-theme-select-label">
            Theme ID
            <input
              value={selectedThemeId}
              onChange={(event) => setSelectedThemeId(event.target.value)}
              className="mt-1 h-10 w-full rounded-md border px-2"
              placeholder="Theme ID"
              data-testid="ui-designer-theme-select-input"
            />
          </label>
          <button
            type="button"
            onClick={loadSelectedThemeToForm}
            className="h-10 rounded-md border px-3 text-sm"
            data-testid="ui-designer-theme-load-to-form-button"
          >
            Forma Yükle
          </button>
        </div>
        <div className="mt-2 flex flex-wrap gap-2" data-testid="ui-designer-theme-quick-select-list">
          {themes.slice(0, 8).map((theme) => (
            <button
              key={theme.id}
              type="button"
              onClick={() => setSelectedThemeId(theme.id)}
              className="rounded border px-2 py-1 text-[11px]"
              data-testid={`ui-designer-theme-quick-select-${theme.id}`}
            >
              {theme.name}
            </button>
          ))}
        </div>
      </div>

      <div className="rounded-md border bg-white p-3" data-testid="ui-designer-theme-assign-card">
        <div className="text-sm font-semibold" data-testid="ui-designer-theme-assign-title">Theme Assign (system / tenant / user)</div>
        <div className="mt-2 grid gap-3 md:grid-cols-4" data-testid="ui-designer-theme-assign-grid">
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
          <label className="text-xs md:col-span-2" data-testid="ui-designer-theme-assign-scope-id-label">
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
          {JSON.stringify(effectiveResult?.tokens || {}, null, 2)}
        </pre>
      </div>

      {status ? <div className="text-xs text-emerald-600" data-testid="ui-designer-theme-status">{status}</div> : null}
      {error ? <div className="text-xs text-rose-600" data-testid="ui-designer-theme-error">{error}</div> : null}
    </div>
  );
};
