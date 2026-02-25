import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { DEFAULT_THEME_CONFIG, THEME_GROUPS, THEME_REQUIRED_KEYS } from '@/data/themeDefaults';
import { buildThemeCssVars, normalizeThemeConfig } from '@/lib/themeUtils';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const formatHex = (value) => {
  if (!value) return '#';
  const raw = value.trim();
  if (raw.startsWith('#')) return raw.toUpperCase();
  return `#${raw.toUpperCase()}`;
};

const safePalette = (config, mode) => {
  const fallback = DEFAULT_THEME_CONFIG[mode];
  return { ...fallback, ...(config?.[mode] || {}) };
};

export default function AdminThemeManagement() {
  const [themeConfig, setThemeConfig] = useState(DEFAULT_THEME_CONFIG);
  const [activeMode, setActiveMode] = useState('light');
  const [status, setStatus] = useState('idle');
  const [saveStatus, setSaveStatus] = useState('idle');
  const [error, setError] = useState('');
  const [validationReport, setValidationReport] = useState([]);
  const [versions, setVersions] = useState([]);
  const [activeVersion, setActiveVersion] = useState(null);

  const authHeader = useMemo(() => ({ Authorization: `Bearer ${localStorage.getItem('token')}` }), []);

  const previewVars = useMemo(() => buildThemeCssVars(themeConfig), [themeConfig]);

  const fetchTheme = async () => {
    try {
      setStatus('loading');
      const res = await axios.get(`${API}/admin/site/theme`, { headers: authHeader });
      const normalized = normalizeThemeConfig(res.data?.config || DEFAULT_THEME_CONFIG);
      setThemeConfig(normalized);
      setActiveVersion(res.data?.id || null);
      setStatus('ok');
    } catch (err) {
      setStatus('error');
    }
  };

  const fetchVersions = async () => {
    try {
      const res = await axios.get(`${API}/admin/site/theme/configs`, { headers: authHeader });
      setVersions(res.data?.items || []);
    } catch (err) {
      setVersions([]);
    }
  };

  const loadVersion = async (versionId) => {
    try {
      const res = await axios.get(`${API}/admin/site/theme/config/${versionId}`, { headers: authHeader });
      setThemeConfig(normalizeThemeConfig(res.data?.config || DEFAULT_THEME_CONFIG));
      setActiveVersion(versionId);
      setError('');
    } catch (err) {
      setError('Versiyon yüklenemedi.');
    }
  };

  useEffect(() => {
    fetchTheme();
    fetchVersions();
  }, []);

  const updateColor = (mode, key, value) => {
    const formatted = formatHex(value);
    setThemeConfig((prev) => ({
      ...prev,
      [mode]: {
        ...prev[mode],
        [key]: formatted,
      },
    }));
  };

  const resetDefaults = () => {
    setThemeConfig(DEFAULT_THEME_CONFIG);
    setValidationReport([]);
    setError('');
  };

  const saveDraft = async () => {
    setSaveStatus('saving');
    setError('');
    setValidationReport([]);
    try {
      const res = await axios.put(
        `${API}/admin/site/theme/config`,
        { config: themeConfig, status: 'draft' },
        { headers: authHeader },
      );
      setSaveStatus('draft');
      await fetchVersions();
      setActiveVersion(res.data?.id || null);
      return res.data;
    } catch (err) {
      setSaveStatus('error');
      setError(err?.response?.data?.detail?.message || 'Kaydetme başarısız.');
      return null;
    }
  };

  const publishVersion = async (versionId) => {
    setSaveStatus('publishing');
    setError('');
    setValidationReport([]);
    try {
      const res = await axios.post(
        `${API}/admin/site/theme/config/${versionId}/publish`,
        {},
        { headers: authHeader },
      );
      setSaveStatus('published');
      setValidationReport(res.data?.validation_report || []);
      await fetchVersions();
      await fetchTheme();
    } catch (err) {
      const detail = err?.response?.data?.detail || {};
      setSaveStatus('error');
      setError(detail?.message || 'Yayınlama başarısız.');
      setValidationReport(detail?.validation_report || []);
    }
  };

  const handlePublish = async () => {
    const saved = await saveDraft();
    if (saved?.id) {
      await publishVersion(saved.id);
    }
  };

  const modePalette = safePalette(themeConfig, activeMode);

  return (
    <div className="space-y-6" data-testid="admin-theme-management">
      <div className="flex flex-wrap items-center justify-between gap-4" data-testid="admin-theme-header">
        <div>
          <h1 className="text-2xl font-semibold">Tema Yönetimi</h1>
          <p className="text-sm text-muted-foreground">Tüm semantik renkleri tek JSON üzerinden yönetin.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2" data-testid="admin-theme-actions">
          <button
            type="button"
            className="h-9 rounded-md border px-4 text-sm"
            onClick={resetDefaults}
            data-testid="admin-theme-reset"
          >
            Varsayılanlara Dön
          </button>
          <button
            type="button"
            className="h-9 rounded-md border px-4 text-sm"
            onClick={saveDraft}
            data-testid="admin-theme-save-draft"
          >
            Kaydet (Draft)
          </button>
          <button
            type="button"
            className="h-9 rounded-md bg-primary px-4 text-sm text-primary-foreground"
            onClick={handlePublish}
            data-testid="admin-theme-publish"
          >
            Publish
          </button>
        </div>
      </div>

      {status === 'loading' && (
        <div className="text-sm text-muted-foreground" data-testid="admin-theme-loading">Yükleniyor...</div>
      )}
      {status === 'error' && (
        <div className="text-sm text-rose-600" data-testid="admin-theme-error">Tema verisi alınamadı.</div>
      )}
      {error && (
        <div className="text-sm text-rose-600" data-testid="admin-theme-save-error">{error}</div>
      )}
      {saveStatus === 'draft' && (
        <div className="text-sm text-emerald-600" data-testid="admin-theme-save-success">Draft kaydedildi.</div>
      )}
      {saveStatus === 'published' && (
        <div className="text-sm text-emerald-600" data-testid="admin-theme-publish-success">Tema yayına alındı.</div>
      )}

      <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]" data-testid="admin-theme-layout">
        <div className="space-y-6" data-testid="admin-theme-editor">
          <div className="flex items-center gap-2" data-testid="admin-theme-mode-tabs">
            {['light', 'dark'].map((mode) => (
              <button
                key={mode}
                type="button"
                onClick={() => setActiveMode(mode)}
                className={`h-9 rounded-md border px-4 text-sm ${activeMode === mode ? 'bg-primary text-primary-foreground' : 'bg-white'}`}
                data-testid={`admin-theme-mode-${mode}`}
              >
                {mode === 'light' ? 'Light' : 'Dark'}
              </button>
            ))}
          </div>

          {THEME_GROUPS.map((group) => (
            <div key={group.title} className="rounded-lg border bg-white" data-testid={`admin-theme-group-${group.title}`}>
              <div className="border-b px-4 py-3 text-sm font-semibold" data-testid={`admin-theme-group-title-${group.title}`}>
                {group.title}
              </div>
              <div className="divide-y">
                {group.items.map((item) => (
                  <div key={item.key} className="flex flex-wrap items-center justify-between gap-4 px-4 py-3">
                    <div>
                      <div className="text-sm font-medium" data-testid={`admin-theme-label-${activeMode}-${item.key}`}>
                        {item.label}
                      </div>
                      <div className="text-xs text-muted-foreground" data-testid={`admin-theme-key-${activeMode}-${item.key}`}>
                        {item.key}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <input
                        type="color"
                        value={modePalette[item.key]}
                        onChange={(e) => updateColor(activeMode, item.key, e.target.value)}
                        className="h-9 w-12 rounded border"
                        data-testid={`admin-theme-color-${activeMode}-${item.key}`}
                      />
                      <input
                        type="text"
                        value={modePalette[item.key]}
                        onChange={(e) => updateColor(activeMode, item.key, e.target.value)}
                        className="h-9 w-32 rounded-md border px-2 text-xs"
                        data-testid={`admin-theme-hex-${activeMode}-${item.key}`}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="space-y-6" data-testid="admin-theme-sidebar">
          <div className="rounded-lg border bg-white p-4" data-testid="admin-theme-preview">
            <div className="text-sm font-semibold" data-testid="admin-theme-preview-title">Live Preview</div>
            <div className="mt-4 grid gap-4">
              <div
                className="rounded-xl border p-4"
                style={previewVars}
                data-testid="admin-theme-preview-light"
              >
                <div className="rounded-lg border bg-[var(--bg-page)] text-[var(--text-primary)]">
                  <div className="flex items-center justify-between border-b bg-[var(--header-bg)] px-4 py-2 text-[var(--header-text)]">
                    <span className="text-sm font-semibold" data-testid="admin-theme-preview-header-light">Header</span>
                    <button className="rounded-full bg-[var(--button-primary-bg)] px-3 py-1 text-xs text-[var(--button-primary-text)]">
                      İlan Ver
                    </button>
                  </div>
                  <div className="p-4 space-y-3">
                    <div className="text-sm text-[var(--text-secondary)]">Kısa açıklama örneği</div>
                    <div className="flex flex-wrap gap-2">
                      <button className="rounded-md bg-[var(--button-primary-bg)] px-3 py-2 text-xs text-[var(--button-primary-text)]" data-testid="admin-theme-preview-primary">
                        Primary CTA
                      </button>
                      <button className="rounded-md border border-[var(--border)] bg-[var(--button-secondary-bg)] px-3 py-2 text-xs text-[var(--button-secondary-text)]" data-testid="admin-theme-preview-secondary">
                        Secondary
                      </button>
                    </div>
                    <a href="#preview" className="text-xs text-[var(--link)] hover:text-[var(--link-hover)]" data-testid="admin-theme-preview-link">
                      Örnek Link
                    </a>
                  </div>
                  <div className="border-t bg-[var(--footer-bg)] px-4 py-2 text-xs text-[var(--footer-text)]" data-testid="admin-theme-preview-footer-light">
                    Footer alanı
                  </div>
                </div>
              </div>
              <div
                className="rounded-xl border p-4 dark"
                style={previewVars}
                data-testid="admin-theme-preview-dark"
              >
                <div className="rounded-lg border bg-[var(--bg-page)] text-[var(--text-primary)]">
                  <div className="flex items-center justify-between border-b bg-[var(--header-bg)] px-4 py-2 text-[var(--header-text)]">
                    <span className="text-sm font-semibold" data-testid="admin-theme-preview-header-dark">Header</span>
                    <button className="rounded-full bg-[var(--button-primary-bg)] px-3 py-1 text-xs text-[var(--button-primary-text)]">
                      İlan Ver
                    </button>
                  </div>
                  <div className="p-4 space-y-3">
                    <div className="text-sm text-[var(--text-secondary)]">Kısa açıklama örneği</div>
                    <div className="flex flex-wrap gap-2">
                      <button className="rounded-md bg-[var(--button-primary-bg)] px-3 py-2 text-xs text-[var(--button-primary-text)]" data-testid="admin-theme-preview-primary-dark">
                        Primary CTA
                      </button>
                      <button className="rounded-md border border-[var(--border)] bg-[var(--button-secondary-bg)] px-3 py-2 text-xs text-[var(--button-secondary-text)]" data-testid="admin-theme-preview-secondary-dark">
                        Secondary
                      </button>
                    </div>
                    <a href="#preview" className="text-xs text-[var(--link)] hover:text-[var(--link-hover)]" data-testid="admin-theme-preview-link-dark">
                      Örnek Link
                    </a>
                  </div>
                  <div className="border-t bg-[var(--footer-bg)] px-4 py-2 text-xs text-[var(--footer-text)]" data-testid="admin-theme-preview-footer-dark">
                    Footer alanı
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-lg border bg-white p-4" data-testid="admin-theme-versioning">
            <div className="text-sm font-semibold">Versiyonlar</div>
            <div className="mt-3 space-y-2">
              {versions.length === 0 && (
                <div className="text-xs text-muted-foreground" data-testid="admin-theme-version-empty">Kayıtlı versiyon yok.</div>
              )}
              {versions.map((item) => (
                <div key={item.id} className="flex items-center justify-between gap-2 rounded-md border px-3 py-2 text-xs" data-testid={`admin-theme-version-${item.id}`}>
                  <div>
                    <div className="font-semibold">v{item.version}</div>
                    <div className="text-muted-foreground">{item.status}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      className="rounded-md border px-2 py-1"
                      onClick={() => loadVersion(item.id)}
                      data-testid={`admin-theme-version-load-${item.id}`}
                    >
                      Yükle
                    </button>
                    {item.status !== 'published' && (
                      <button
                        type="button"
                        className="rounded-md bg-primary px-2 py-1 text-primary-foreground"
                        onClick={() => publishVersion(item.id)}
                        data-testid={`admin-theme-version-publish-${item.id}`}
                      >
                        Yayınla
                      </button>
                    )}
                    {item.status === 'published' && (
                      <span className="rounded-full bg-emerald-100 px-2 py-1 text-emerald-700" data-testid={`admin-theme-version-live-${item.id}`}>Aktif</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-lg border bg-white p-4" data-testid="admin-theme-validation">
            <div className="text-sm font-semibold">WCAG AA Kontrast Raporu</div>
            <div className="mt-3 space-y-2">
              {validationReport.length === 0 && (
                <div className="text-xs text-muted-foreground" data-testid="admin-theme-validation-empty">Rapor yok.</div>
              )}
              {validationReport.map((item, index) => (
                <div key={`${item.mode}-${index}`} className="flex items-center justify-between text-xs" data-testid={`admin-theme-validation-${index}`}>
                  <div>{item.label} ({item.mode})</div>
                  <div className={item.pass ? 'text-emerald-600' : 'text-rose-600'}>
                    {item.ratio} / {item.threshold}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-lg border bg-white p-4" data-testid="admin-theme-meta">
            <div className="text-sm font-semibold">Aktif Versiyon</div>
            <div className="mt-2 text-xs text-muted-foreground" data-testid="admin-theme-active-version">
              {activeVersion ? `ID: ${activeVersion}` : 'Henüz yayınlanmadı.'}
            </div>
            <div className="mt-2 text-xs text-muted-foreground" data-testid="admin-theme-required-keys">
              {THEME_REQUIRED_KEYS.length} renk anahtarı aktif.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
