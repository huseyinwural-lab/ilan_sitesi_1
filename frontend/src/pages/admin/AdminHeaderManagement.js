import React, { useEffect, useState } from 'react';
import axios from 'axios';
import SiteHeader from '@/components/public/SiteHeader';
import { useLanguage } from '@/contexts/LanguageContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const MAX_LOGO_MB = 2;
const MAX_LOGO_BYTES = MAX_LOGO_MB * 1024 * 1024;
const HEADER_MODES = [
  { key: 'guest', label: 'Misafir Header' },
  { key: 'auth', label: 'Giriş Yapmış Header' },
  { key: 'corporate', label: 'Kurumsal Header' },
];

const emptyMode = { logo_url: null, items: [] };

const normalizeHeaderConfig = (raw) => {
  const modes = { guest: { ...emptyMode }, auth: { ...emptyMode }, corporate: { ...emptyMode } };
  const sourceModes = raw?.modes || {};
  HEADER_MODES.forEach(({ key }) => {
    const source = sourceModes[key] || {};
    modes[key] = {
      logo_url: source?.logo_url || null,
      items: Array.isArray(source?.items) ? source.items : [],
    };
  });
  return {
    version: raw?.version || null,
    updated_at: raw?.updated_at || null,
    modes,
  };
};

export default function AdminHeaderManagement() {
  const { t } = useLanguage();
  const [headerConfig, setHeaderConfig] = useState(normalizeHeaderConfig({}));
  const [activeMode, setActiveMode] = useState('guest');
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const fetchHeader = async () => {
    const res = await axios.get(`${API}/admin/site/header`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
    });
    setHeaderConfig(normalizeHeaderConfig(res.data));
  };

  useEffect(() => {
    fetchHeader();
  }, []);

  const handleFileChange = (event) => {
    setStatus('');
    setError('');
    const selected = event.target.files?.[0] || null;
    if (!selected) {
      setFile(null);
      return;
    }
    if (selected.size > MAX_LOGO_BYTES) {
      setError(`Dosya boyutu ${MAX_LOGO_MB}MB sınırını aşıyor.`);
      setFile(null);
      return;
    }
    setFile(selected);
  };

  const updateModeItems = (mode, updater) => {
    setHeaderConfig((prev) => {
      const nextItems = updater([...(prev.modes[mode]?.items || [])]);
      return {
        ...prev,
        modes: {
          ...prev.modes,
          [mode]: {
            ...prev.modes[mode],
            items: nextItems,
          },
        },
      };
    });
  };

  const handleItemChange = (mode, index, field, value) => {
    updateModeItems(mode, (items) => items.map((item, idx) => (idx === index ? { ...item, [field]: value } : item)));
  };

  const addItem = () => {
    updateModeItems(activeMode, (items) => ([
      ...items,
      {
        id: `${activeMode}-item-${Date.now()}`,
        label: '',
        url: activeMode === 'corporate' ? '/dealer/overview' : '/',
        style: 'text',
        open_in_new_tab: false,
      },
    ]));
  };

  const removeItem = (index) => {
    updateModeItems(activeMode, (items) => items.filter((_, idx) => idx !== index));
  };

  const moveItem = (index, direction) => {
    updateModeItems(activeMode, (items) => {
      const next = [...items];
      const target = index + direction;
      if (target < 0 || target >= next.length) return next;
      const [picked] = next.splice(index, 1);
      next.splice(target, 0, picked);
      return next;
    });
  };

  const handleSave = async () => {
    setSaving(true);
    setStatus('');
    setError('');
    try {
      const payload = {
        modes: headerConfig.modes,
      };
      const res = await axios.put(`${API}/admin/site/header`, payload, {
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      });
      setHeaderConfig(normalizeHeaderConfig(res.data));
      setStatus(t('admin_header_saved'));
    } catch (err) {
      setError(err?.response?.data?.detail || t('admin_header_save_error'));
    } finally {
      setSaving(false);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError(t('admin_header_select_file'));
      return;
    }
    const formData = new FormData();
    formData.append('file', file);
    try {
      setError('');
      const res = await axios.post(`${API}/admin/site/header/logo?mode=${encodeURIComponent(activeMode)}`, formData, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      setStatus(t('admin_header_logo_updated'));
      setFile(null);
      setHeaderConfig((prev) => ({
        ...prev,
        version: res.data?.version || prev.version,
        updated_at: res.data?.updated_at || prev.updated_at,
        modes: {
          ...prev.modes,
          [activeMode]: {
            ...prev.modes[activeMode],
            logo_url: res.data?.logo_url || prev.modes[activeMode]?.logo_url || null,
          },
        },
      }));
    } catch (err) {
      setError(err?.response?.data?.detail || t('admin_header_upload_error'));
    }
  };

  const activeItems = headerConfig.modes[activeMode]?.items || [];
  const activeLogo = headerConfig.modes[activeMode]?.logo_url;

  return (
    <div className="space-y-6" data-testid="admin-header-management">
      <div>
        <h1 className="text-2xl font-semibold" data-testid="admin-header-title">{t('admin_header_title')}</h1>
        <p className="text-sm text-muted-foreground" data-testid="admin-header-subtitle">
          {t('admin_header_subtitle')}
        </p>
      </div>

      <div className="rounded-lg border bg-white p-4" data-testid="admin-header-mode-tabs">
        <div className="flex flex-wrap items-center gap-2">
          {HEADER_MODES.map((mode) => (
            <button
              key={mode.key}
              type="button"
              onClick={() => setActiveMode(mode.key)}
              className={`rounded-md border px-3 py-1.5 text-sm font-semibold ${activeMode === mode.key ? 'bg-slate-900 text-white border-slate-900' : 'bg-white text-slate-700 border-slate-300'}`}
              data-testid={`admin-header-mode-tab-${mode.key}`}
            >
              {mode.label}
            </button>
          ))}
        </div>
      </div>

      <div className="rounded-lg border bg-white p-4 space-y-4" data-testid="admin-header-upload-card">
        <div className="text-sm font-semibold" data-testid="admin-header-current-mode-title">
          {HEADER_MODES.find((mode) => mode.key === activeMode)?.label}
        </div>
        {activeLogo && (
          <img src={activeLogo} alt="Logo" className="h-12 object-contain" data-testid={`admin-header-current-logo-${activeMode}`} />
        )}
        <div className="text-xs text-muted-foreground" data-testid="admin-header-upload-hint">
          {t('admin_header_upload_hint')} {MAX_LOGO_MB}MB.
        </div>
        <input
          type="file"
          accept=".png,.svg"
          onChange={handleFileChange}
          data-testid="admin-header-file-input"
        />
        {error && (
          <div className="text-xs text-rose-600" data-testid="admin-header-error">{error}</div>
        )}
        {status && (
          <div className="text-xs text-emerald-600" data-testid="admin-header-status">{status}</div>
        )}
        {headerConfig.version && (
          <div className="text-xs text-muted-foreground" data-testid="admin-header-version">Versiyon: {headerConfig.version}</div>
        )}
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={handleUpload}
            className="h-9 px-4 rounded-md bg-primary text-primary-foreground text-sm"
            data-testid="admin-header-upload-button"
          >
            {t('admin_header_upload_button')}
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            className="h-9 px-4 rounded-md border border-slate-300 bg-white text-sm font-semibold text-slate-700 disabled:opacity-60"
            data-testid="admin-header-save-button"
          >
            {saving ? t('admin_header_saving') : t('admin_header_save_button')}
          </button>
        </div>
      </div>

      <div className="rounded-lg border bg-white p-4 space-y-4" data-testid="admin-header-links-editor">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-sm font-semibold" data-testid="admin-header-links-title">{t('admin_header_links_title')}</h2>
          <button
            type="button"
            onClick={addItem}
            className="h-8 rounded-md border border-slate-300 px-3 text-xs font-semibold"
            data-testid="admin-header-add-link-button"
          >
            {t('admin_header_add_link')}
          </button>
        </div>

        <div className="space-y-3" data-testid="admin-header-links-list">
          {activeItems.length === 0 ? (
            <div className="rounded border border-dashed px-3 py-4 text-xs text-slate-500" data-testid="admin-header-links-empty">
              {t('admin_header_links_empty')}
            </div>
          ) : activeItems.map((item, index) => (
            <div key={`${item.id || 'item'}-${index}`} className="rounded border p-3 space-y-2" data-testid={`admin-header-link-row-${activeMode}-${index}`}>
              <div className="grid gap-2 md:grid-cols-2">
                <input
                  value={item.label || ''}
                  onChange={(event) => handleItemChange(activeMode, index, 'label', event.target.value)}
                  placeholder={t('admin_header_link_label_placeholder')}
                  className="h-9 rounded border border-slate-300 px-3 text-sm"
                  data-testid={`admin-header-link-label-${activeMode}-${index}`}
                />
                <input
                  value={item.url || ''}
                  onChange={(event) => handleItemChange(activeMode, index, 'url', event.target.value)}
                  placeholder={t('admin_header_link_url_placeholder')}
                  className="h-9 rounded border border-slate-300 px-3 text-sm"
                  data-testid={`admin-header-link-url-${activeMode}-${index}`}
                />
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <select
                  value={item.style || 'text'}
                  onChange={(event) => handleItemChange(activeMode, index, 'style', event.target.value)}
                  className="h-9 rounded border border-slate-300 px-2 text-sm"
                  data-testid={`admin-header-link-style-${activeMode}-${index}`}
                >
                  <option value="text">Text</option>
                  <option value="solid">Solid</option>
                </select>

                <label className="inline-flex items-center gap-2 text-xs" data-testid={`admin-header-link-new-tab-wrap-${activeMode}-${index}`}>
                  <input
                    type="checkbox"
                    checked={Boolean(item.open_in_new_tab)}
                    onChange={(event) => handleItemChange(activeMode, index, 'open_in_new_tab', event.target.checked)}
                    data-testid={`admin-header-link-new-tab-${activeMode}-${index}`}
                  />
                  Yeni sekme
                </label>

                <button
                  type="button"
                  onClick={() => moveItem(index, -1)}
                  className="h-8 rounded border px-2 text-xs"
                  data-testid={`admin-header-link-up-${activeMode}-${index}`}
                >
                  ↑
                </button>
                <button
                  type="button"
                  onClick={() => moveItem(index, 1)}
                  className="h-8 rounded border px-2 text-xs"
                  data-testid={`admin-header-link-down-${activeMode}-${index}`}
                >
                  ↓
                </button>
                <button
                  type="button"
                  onClick={() => removeItem(index)}
                  className="h-8 rounded border border-rose-200 px-2 text-xs text-rose-600"
                  data-testid={`admin-header-link-remove-${activeMode}-${index}`}
                >
                  {t('delete')}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2" data-testid="admin-header-preview">
        <div className="rounded-lg border bg-white p-3" data-testid="admin-header-preview-guest">
          <div className="text-xs font-semibold text-muted-foreground mb-2">Guest Preview</div>
          <SiteHeader mode="guest" refreshToken={headerConfig.version} />
        </div>
        <div className="rounded-lg border bg-white p-3" data-testid="admin-header-preview-auth">
          <div className="text-xs font-semibold text-muted-foreground mb-2">Authenticated Preview</div>
          <SiteHeader mode="auth" refreshToken={headerConfig.version} />
        </div>
      </div>

      <div className="rounded-lg border bg-white p-3" data-testid="admin-header-preview-corporate">
        <div className="text-xs font-semibold text-muted-foreground mb-2">Corporate Preview</div>
        <div className="rounded border bg-slate-50 p-3 space-y-3" data-testid="admin-header-preview-corporate-card">
          {headerConfig.modes.corporate.logo_url ? (
            <img src={headerConfig.modes.corporate.logo_url} alt="Corporate logo" className="h-10 object-contain" data-testid="admin-header-preview-corporate-logo" />
          ) : (
            <div className="text-xs text-slate-500" data-testid="admin-header-preview-corporate-logo-empty">Logo yok</div>
          )}
          <div className="flex flex-wrap items-center gap-2" data-testid="admin-header-preview-corporate-links">
            {(headerConfig.modes.corporate.items || []).map((item, index) => (
              <span
                key={`${item.id || item.label}-${index}`}
                className={`rounded-full border px-3 py-1 text-xs ${item.style === 'solid' ? 'bg-slate-900 text-white border-slate-900' : 'bg-white text-slate-700 border-slate-300'}`}
                data-testid={`admin-header-preview-corporate-link-${index}`}
              >
                {item.label}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
