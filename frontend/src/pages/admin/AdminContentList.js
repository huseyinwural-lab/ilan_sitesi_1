import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const PAGE_TYPE_LABEL_MAP = {
  home: 'Ana Sayfa',
  category_l0_l1: 'L0/L1 Kategori Sayfası',
  search_ln: 'Kategori İlan Listesi',
  urgent_listings: 'Acil İlanlar',
  category_showcase: 'Kategori Vitrin',
  listing_detail: 'İlan Detay',
  listing_detail_parameters: 'İlan Detay Parametreleri',
  storefront_profile: 'Mağaza/Kurumsal Profil',
  wizard_step_l0: 'İlan Ver Adım 1 - L0',
  wizard_step_ln: 'İlan Ver Adım 2 - L1>Ln',
  wizard_step_form: 'İlan Ver Adım 3 - Form',
  wizard_preview: 'Ön İzleme',
  wizard_doping_payment: 'Doping ve Ödeme',
  wizard_result: 'Başarı/Sonuç',
  user_dashboard: 'Kullanıcı Paneli',
  search_l1: 'Legacy Search L1',
  search_l2: 'Legacy Search L2',
  listing_create_stepX: 'Legacy İlan Ver',
};

const PAGE_TYPE_OPTIONS = [
  'home',
  'category_l0_l1',
  'search_ln',
  'urgent_listings',
  'category_showcase',
  'listing_detail',
  'listing_detail_parameters',
  'storefront_profile',
  'wizard_step_l0',
  'wizard_step_ln',
  'wizard_step_form',
  'wizard_preview',
  'wizard_doping_payment',
  'wizard_result',
  'user_dashboard',
  'search_l1',
  'search_l2',
  'listing_create_stepX',
].map((value) => ({ value, label: `${PAGE_TYPE_LABEL_MAP[value] || value} (${value})` }));

const CONTENT_LIST_STATUS_FILTER = ['draft', 'published'];

const formatLayoutUpdatedAt = (value) => {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '-';
  return date.toLocaleString('tr-TR');
};

const resolveLayoutScopeLabel = (item) => {
  if (!item || typeof item !== 'object') return '-';
  if (item.category_id) return `Kategori: ${item.category_id}`;
  return item.scope || `${item.country || '-'} / ${item.module || '-'} / global`;
};

const parseCountriesInput = (value) => (
  String(value || '')
    .split(',')
    .map((token) => token.trim().toUpperCase())
    .filter(Boolean)
);

export default function AdminContentList() {
  const navigate = useNavigate();

  const resolveRequestLocale = () => {
    const pathLocale = String(window.location.pathname || '').split('/').filter(Boolean)[0]?.toLowerCase();
    if (['tr', 'de', 'fr'].includes(pathLocale)) return pathLocale;
    const stored = String(localStorage.getItem('language') || '').toLowerCase();
    if (['tr', 'de', 'fr'].includes(stored)) return stored;
    return 'tr';
  };

  const authHeaders = useMemo(
    () => {
      const locale = resolveRequestLocale();
      const pathLocale = String(window.location.pathname || '').split('/').filter(Boolean)[0]?.toLowerCase();
      return {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        'Accept-Language': locale,
        'X-URL-Locale': ['tr', 'de', 'fr'].includes(pathLocale) ? pathLocale : locale,
      };
    },
    [],
  );

  const [contentListRows, setContentListRows] = useState([]);
  const [contentListLoading, setContentListLoading] = useState(false);
  const [contentListError, setContentListError] = useState('');
  const [statusMessage, setStatusMessage] = useState('');
  const [contentListIncludeDeleted, setContentListIncludeDeleted] = useState(true);

  const [copyTargetPageType, setCopyTargetPageType] = useState('home');
  const [copyTargetCountry, setCopyTargetCountry] = useState('DE');
  const [copyTargetModule, setCopyTargetModule] = useState('global');
  const [copyTargetCategoryId, setCopyTargetCategoryId] = useState('');
  const [copyPublishAfterCopy, setCopyPublishAfterCopy] = useState(false);

  const [presetCountriesInput, setPresetCountriesInput] = useState('TR,DE,FR');
  const [presetModule, setPresetModule] = useState('global');
  const [presetPersona, setPresetPersona] = useState('individual');
  const [presetVariant, setPresetVariant] = useState('A');
  const [presetOverwriteDraft, setPresetOverwriteDraft] = useState(true);
  const [presetPublishAfterSeed, setPresetPublishAfterSeed] = useState(true);
  const [presetIncludeExtendedTemplates, setPresetIncludeExtendedTemplates] = useState(false);
  const [presetLoading, setPresetLoading] = useState(false);
  const [presetError, setPresetError] = useState('');
  const [presetStatus, setPresetStatus] = useState('');
  const [presetInstallResult, setPresetInstallResult] = useState(null);
  const [presetVerifyResult, setPresetVerifyResult] = useState(null);

  const fetchContentList = useCallback(async ({ silent = false } = {}) => {
    setContentListLoading(true);
    if (!silent) setContentListError('');
    try {
      const response = await axios.get(`${API}/admin/layouts`, {
        headers: authHeaders,
        params: {
          include_deleted: contentListIncludeDeleted,
          statuses: CONTENT_LIST_STATUS_FILTER.join(','),
          page: 1,
          limit: 200,
        },
      });
      const items = Array.isArray(response.data?.items) ? response.data.items : [];
      setContentListRows(items);
      setContentListError('');
    } catch (err) {
      setContentListRows([]);
      setContentListError(err?.response?.data?.detail || 'Content list yüklenemedi');
      if (!silent) toast.error('Content list yüklenemedi.');
    } finally {
      setContentListLoading(false);
    }
  }, [authHeaders, contentListIncludeDeleted]);

  useEffect(() => {
    fetchContentList({ silent: true });
  }, [fetchContentList]);

  const handleContentListEdit = (item) => {
    if (!item?.layout_page_id || item.is_deleted) return;
    const params = new URLSearchParams();
    params.set('autoload_page_id', item.layout_page_id);
    params.set('page_type', item.page_type || 'home');
    params.set('country', String(item.country || 'DE').toUpperCase());
    params.set('module', String(item.module || 'global'));
    if (item.category_id) {
      params.set('category_id', item.category_id);
    }
    navigate(`/admin/site-design/content-builder?${params.toString()}`);
  };

  const handleContentListDelete = async (item) => {
    if (!item?.revision_id || item.is_deleted) return;
    const confirmed = window.confirm('Bu revision soft-delete edilsin mi?');
    if (!confirmed) return;

    setStatusMessage('');
    setContentListError('');
    try {
      await axios.delete(`${API}/admin/layouts/${item.revision_id}`, {
        headers: authHeaders,
      });
      setStatusMessage('Revision soft-delete edildi.');
      toast.success('Revision soft-delete edildi.');
      await fetchContentList({ silent: true });
    } catch (err) {
      setContentListError(err?.response?.data?.detail || 'Soft-delete başarısız');
      toast.error('Soft-delete başarısız.');
    }
  };

  const handleContentListCopy = async (item) => {
    if (!item?.revision_id) return;
    const normalizedModule = String(copyTargetModule || '').trim();
    const normalizedCountry = String(copyTargetCountry || '').trim().toUpperCase();

    if (!normalizedCountry || !normalizedModule) {
      toast.error('Kopya hedefi için ülke ve module zorunludur.');
      return;
    }

    setStatusMessage('');
    setContentListError('');
    try {
      await axios.post(
        `${API}/admin/layouts/${item.revision_id}/copy`,
        {
          target_page_type: copyTargetPageType,
          country: normalizedCountry,
          module: normalizedModule,
          category_id: String(copyTargetCategoryId || '').trim() || null,
          publish_after_copy: copyPublishAfterCopy,
        },
        { headers: authHeaders },
      );

      await fetchContentList({ silent: true });
      setStatusMessage('Sayfa bire bir kopyalandı. Düzenlemek için Edit ile Content Builder’a geçebilirsiniz.');
      toast.success('Bire bir kopyalama tamamlandı.');
    } catch (err) {
      setContentListError(err?.response?.data?.detail || 'Kopyalama başarısız');
      toast.error('Kopyalama başarısız.');
    }
  };

  const handleSetRevisionActive = async (item, nextActive) => {
    if (!item?.revision_id || item.is_deleted) return;

    setStatusMessage('');
    setContentListError('');
    try {
      await axios.patch(
        `${API}/admin/layouts/${item.revision_id}/active`,
        { is_active: nextActive },
        { headers: authHeaders },
      );
      setStatusMessage(`Revision ${nextActive ? 'aktif' : 'pasif'} olarak güncellendi.`);
      toast.success(`Revision ${nextActive ? 'aktif' : 'pasif'} olarak güncellendi.`);
      await fetchContentList({ silent: true });
    } catch (err) {
      setContentListError(err?.response?.data?.detail || 'Aktif/pasif güncellemesi başarısız');
      toast.error('Aktif/pasif güncellemesi başarısız.');
    }
  };

  const handleInstallStandardPack = async () => {
    const countries = parseCountriesInput(presetCountriesInput);
    if (!countries.length) {
      setPresetError('En az bir ülke giriniz. Örn: TR,DE,FR');
      return;
    }
    const normalizedModule = String(presetModule || '').trim();
    if (!normalizedModule) {
      setPresetError('Module zorunludur.');
      return;
    }

    setPresetLoading(true);
    setPresetError('');
    setPresetStatus('');
    try {
      const response = await axios.post(
        `${API}/admin/site/content-layout/preset/install-standard-pack`,
        {
          countries,
          module: normalizedModule,
          persona: presetPersona,
          variant: presetVariant,
          overwrite_existing_draft: presetOverwriteDraft,
          publish_after_seed: presetPublishAfterSeed,
          include_extended_templates: presetIncludeExtendedTemplates,
        },
        { headers: authHeaders },
      );
      setPresetInstallResult(response.data || null);
      setPresetStatus('Standart template pack kurulumu tamamlandı.');
      toast.success('Standart template pack kuruldu.');
      await fetchContentList({ silent: true });
    } catch (err) {
      setPresetError(err?.response?.data?.detail || 'Template pack kurulumu başarısız');
      toast.error('Template pack kurulumu başarısız.');
    } finally {
      setPresetLoading(false);
    }
  };

  const handleVerifyStandardPack = async () => {
    const countries = parseCountriesInput(presetCountriesInput);
    if (!countries.length) {
      setPresetError('En az bir ülke giriniz. Örn: TR,DE,FR');
      return;
    }
    const normalizedModule = String(presetModule || '').trim();
    if (!normalizedModule) {
      setPresetError('Module zorunludur.');
      return;
    }

    setPresetLoading(true);
    setPresetError('');
    try {
      const response = await axios.get(`${API}/admin/site/content-layout/preset/verify-standard-pack`, {
        headers: authHeaders,
        params: {
          countries: countries.join(','),
          module: normalizedModule,
          include_extended_templates: presetIncludeExtendedTemplates,
        },
      });
      setPresetVerifyResult(response.data || null);
      const ratio = response.data?.summary?.ready_ratio;
      setPresetStatus(`TR/DE/FR publish doğrulaması güncellendi. Hazır oran: ${ratio ?? 0}%`);
      toast.success('Standart pack doğrulaması tamamlandı.');
    } catch (err) {
      setPresetError(err?.response?.data?.detail || 'Template pack doğrulaması başarısız');
      toast.error('Template pack doğrulaması başarısız.');
    } finally {
      setPresetLoading(false);
    }
  };

  return (
    <div className="space-y-5" data-testid="admin-content-list-page">
      <section className="rounded-xl border bg-white p-4" data-testid="admin-content-list-panel">
        <div className="flex flex-wrap items-center justify-between gap-2" data-testid="admin-content-list-header">
          <div>
            <h1 className="text-sm font-semibold" data-testid="admin-content-list-title">Content List</h1>
            <p className="text-xs text-slate-500" data-testid="admin-content-list-subtitle">
              Filtre: draft + published • Silinen kayıtlar kırmızı gösterilir • Aktif/Pasif durumları yönetilebilir.
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs" data-testid="admin-content-list-header-actions">
            <button
              type="button"
              className="h-9 rounded border px-3"
              onClick={() => fetchContentList()}
              disabled={contentListLoading}
              data-testid="admin-content-list-refresh-button"
            >
              Yenile
            </button>
            <label className="inline-flex items-center gap-2" data-testid="admin-content-list-include-deleted-wrap">
              <input
                type="checkbox"
                checked={contentListIncludeDeleted}
                onChange={(event) => setContentListIncludeDeleted(event.target.checked)}
                data-testid="admin-content-list-include-deleted-input"
              />
              Silinenleri göster
            </label>
          </div>
        </div>

        <div className="mt-3 rounded-lg border bg-slate-50 p-3" data-testid="admin-content-list-copy-target-panel">
          <div className="text-xs font-semibold" data-testid="admin-content-list-copy-target-title">Bire bir kopya hedefi</div>
          <div className="mt-2 grid grid-cols-1 gap-2 md:grid-cols-2 xl:grid-cols-5" data-testid="admin-content-list-copy-target-grid">
            <label className="text-xs" data-testid="admin-content-list-copy-target-page-type-wrap">
              Page Type
              <select
                className="mt-1 h-9 w-full rounded border px-2"
                value={copyTargetPageType}
                onChange={(event) => setCopyTargetPageType(event.target.value)}
                data-testid="admin-content-list-copy-target-page-type-select"
              >
                {PAGE_TYPE_OPTIONS.map((item) => <option key={`content-list-copy-target-${item.value}`} value={item.value}>{item.label}</option>)}
              </select>
            </label>

            <label className="text-xs" data-testid="admin-content-list-copy-target-country-wrap">
              Country
              <input
                className="mt-1 h-9 w-full rounded border px-2"
                value={copyTargetCountry}
                onChange={(event) => setCopyTargetCountry(event.target.value.toUpperCase())}
                data-testid="admin-content-list-copy-target-country-input"
              />
            </label>

            <label className="text-xs" data-testid="admin-content-list-copy-target-module-wrap">
              Module
              <input
                className="mt-1 h-9 w-full rounded border px-2"
                value={copyTargetModule}
                onChange={(event) => setCopyTargetModule(event.target.value)}
                data-testid="admin-content-list-copy-target-module-input"
              />
            </label>

            <label className="text-xs" data-testid="admin-content-list-copy-target-category-wrap">
              Category ID (opsiyonel)
              <input
                className="mt-1 h-9 w-full rounded border px-2"
                value={copyTargetCategoryId}
                onChange={(event) => setCopyTargetCategoryId(event.target.value)}
                data-testid="admin-content-list-copy-target-category-input"
              />
            </label>

            <label className="mt-6 inline-flex items-center gap-2 text-xs" data-testid="admin-content-list-copy-target-publish-wrap">
              <input
                type="checkbox"
                checked={copyPublishAfterCopy}
                onChange={(event) => setCopyPublishAfterCopy(event.target.checked)}
                data-testid="admin-content-list-copy-target-publish-input"
              />
              Kopya sonrası publish et
            </label>
          </div>
        </div>

        <div className="mt-3 rounded-lg border bg-white p-3" data-testid="admin-content-list-template-pack-panel">
          <div className="flex flex-wrap items-center justify-between gap-2" data-testid="admin-content-list-template-pack-header">
            <div>
              <h2 className="text-xs font-semibold" data-testid="admin-content-list-template-pack-title">#612 + P1 Başlangıç: Standart Template Pack</h2>
              <p className="text-xs text-slate-500" data-testid="admin-content-list-template-pack-subtitle">TR/DE/FR için (varsayılan: core 4 şablon) publish doğrulama ve tek tık preset kurulum akışı</p>
            </div>
            <div className="flex gap-2" data-testid="admin-content-list-template-pack-header-actions">
              <button
                type="button"
                className="h-8 rounded border px-3 text-xs"
                onClick={handleVerifyStandardPack}
                disabled={presetLoading}
                data-testid="admin-content-list-template-pack-verify-button"
              >
                Publish Doğrula
              </button>
              <button
                type="button"
                className="h-8 rounded border border-blue-300 px-3 text-xs text-blue-700"
                onClick={handleInstallStandardPack}
                disabled={presetLoading}
                data-testid="admin-content-list-template-pack-install-button"
              >
                Tek Tık Kurulum Başlat
              </button>
            </div>
          </div>

          <div className="mt-2 grid grid-cols-1 gap-2 md:grid-cols-2 xl:grid-cols-6" data-testid="admin-content-list-template-pack-form-grid">
            <label className="text-xs" data-testid="admin-content-list-template-pack-countries-wrap">
              Countries (CSV)
              <input
                className="mt-1 h-8 w-full rounded border px-2"
                value={presetCountriesInput}
                onChange={(event) => setPresetCountriesInput(event.target.value.toUpperCase())}
                placeholder="TR,DE,FR"
                data-testid="admin-content-list-template-pack-countries-input"
              />
            </label>

            <label className="text-xs" data-testid="admin-content-list-template-pack-module-wrap">
              Module
              <input
                className="mt-1 h-8 w-full rounded border px-2"
                value={presetModule}
                onChange={(event) => setPresetModule(event.target.value)}
                data-testid="admin-content-list-template-pack-module-input"
              />
            </label>

            <label className="text-xs" data-testid="admin-content-list-template-pack-persona-wrap">
              Persona
              <select
                className="mt-1 h-8 w-full rounded border px-2"
                value={presetPersona}
                onChange={(event) => setPresetPersona(event.target.value)}
                data-testid="admin-content-list-template-pack-persona-select"
              >
                <option value="individual">individual</option>
                <option value="corporate">corporate</option>
              </select>
            </label>

            <label className="text-xs" data-testid="admin-content-list-template-pack-variant-wrap">
              Variant
              <select
                className="mt-1 h-8 w-full rounded border px-2"
                value={presetVariant}
                onChange={(event) => setPresetVariant(event.target.value)}
                data-testid="admin-content-list-template-pack-variant-select"
              >
                <option value="A">A</option>
                <option value="B">B</option>
              </select>
            </label>

            <label className="mt-6 inline-flex items-center gap-2 text-xs" data-testid="admin-content-list-template-pack-overwrite-wrap">
              <input
                type="checkbox"
                checked={presetOverwriteDraft}
                onChange={(event) => setPresetOverwriteDraft(event.target.checked)}
                data-testid="admin-content-list-template-pack-overwrite-input"
              />
              Draft üzerine yaz
            </label>

            <label className="mt-6 inline-flex items-center gap-2 text-xs" data-testid="admin-content-list-template-pack-publish-wrap">
              <input
                type="checkbox"
                checked={presetPublishAfterSeed}
                onChange={(event) => setPresetPublishAfterSeed(event.target.checked)}
                data-testid="admin-content-list-template-pack-publish-input"
              />
              Seed sonrası publish
            </label>

            <label className="mt-6 inline-flex items-center gap-2 text-xs" data-testid="admin-content-list-template-pack-extended-wrap">
              <input
                type="checkbox"
                checked={presetIncludeExtendedTemplates}
                onChange={(event) => setPresetIncludeExtendedTemplates(event.target.checked)}
                data-testid="admin-content-list-template-pack-extended-input"
              />
              Genişletilmiş şablonlar (core dışı)
            </label>
          </div>

          {presetStatus ? (
            <p className="mt-2 text-xs text-emerald-700" data-testid="admin-content-list-template-pack-status-message">{presetStatus}</p>
          ) : null}
          {presetError ? (
            <p className="mt-2 text-xs text-rose-700" data-testid="admin-content-list-template-pack-error-message">{presetError}</p>
          ) : null}

          {presetInstallResult?.summary ? (
            <div className="mt-2 rounded border bg-slate-50 p-2 text-xs" data-testid="admin-content-list-template-pack-install-summary">
              <span data-testid="admin-content-list-template-pack-install-scope">scope: {presetInstallResult.template_scope || 'core'}</span>
              {' · '}
              <span data-testid="admin-content-list-template-pack-install-created-pages">created_pages: {presetInstallResult.summary.created_pages ?? 0}</span>
              {' · '}
              <span data-testid="admin-content-list-template-pack-install-updated-drafts">updated_drafts: {presetInstallResult.summary.updated_drafts ?? 0}</span>
              {' · '}
              <span data-testid="admin-content-list-template-pack-install-published">published_revisions: {presetInstallResult.summary.published_revisions ?? 0}</span>
            </div>
          ) : null}

          {presetVerifyResult?.summary ? (
            <div className="mt-2 rounded border bg-slate-50 p-2 text-xs" data-testid="admin-content-list-template-pack-verify-summary">
              <span data-testid="admin-content-list-template-pack-verify-scope">scope: {presetVerifyResult.template_scope || 'core'}</span>
              {' · '}
              <span data-testid="admin-content-list-template-pack-verify-ready-rows">ready_rows: {presetVerifyResult.summary.ready_rows ?? 0}</span>
              {' / '}
              <span data-testid="admin-content-list-template-pack-verify-total-rows">total_rows: {presetVerifyResult.summary.total_rows ?? 0}</span>
              {' · '}
              <span data-testid="admin-content-list-template-pack-verify-ratio">ready_ratio: {presetVerifyResult.summary.ready_ratio ?? 0}%</span>
            </div>
          ) : null}
        </div>

        <div className="mt-3 overflow-x-auto" data-testid="admin-content-list-table-wrap">
          <table className="min-w-full text-left text-xs" data-testid="admin-content-list-table">
            <thead>
              <tr className="border-b bg-slate-50" data-testid="admin-content-list-head-row">
                <th className="px-2 py-2">page_type</th>
                <th className="px-2 py-2">country</th>
                <th className="px-2 py-2">module</th>
                <th className="px-2 py-2">category / scope</th>
                <th className="px-2 py-2">status</th>
                <th className="px-2 py-2">active_state</th>
                <th className="px-2 py-2">version</th>
                <th className="px-2 py-2">updated_at</th>
                <th className="px-2 py-2">actions</th>
              </tr>
            </thead>
            <tbody data-testid="admin-content-list-table-body">
              {contentListLoading ? (
                <tr data-testid="admin-content-list-loading-row">
                  <td className="px-2 py-3 text-slate-500" colSpan={9} data-testid="admin-content-list-loading-cell">İçerik listesi yükleniyor...</td>
                </tr>
              ) : contentListRows.length === 0 ? (
                <tr data-testid="admin-content-list-empty-row">
                  <td className="px-2 py-3 text-slate-500" colSpan={9} data-testid="admin-content-list-empty-cell">Kayıt bulunamadı.</td>
                </tr>
              ) : (
                contentListRows.map((item) => {
                  const rowKey = item.revision_id || item.id;
                  const deleted = Boolean(item.is_deleted);
                  const active = !deleted && Boolean(item.is_active);
                  return (
                    <tr
                      key={rowKey}
                      className={`border-b ${deleted ? 'bg-rose-50 text-rose-700' : 'text-slate-700'}`}
                      data-testid={`admin-content-list-row-${rowKey}`}
                    >
                      <td className="px-2 py-2 font-medium" data-testid={`admin-content-list-page-type-${rowKey}`}>
                        {PAGE_TYPE_LABEL_MAP[item.page_type] || item.page_type}
                      </td>
                      <td className="px-2 py-2" data-testid={`admin-content-list-country-${rowKey}`}>{item.country || '-'}</td>
                      <td className="px-2 py-2" data-testid={`admin-content-list-module-${rowKey}`}>{item.module || '-'}</td>
                      <td className="px-2 py-2" data-testid={`admin-content-list-scope-${rowKey}`}>{resolveLayoutScopeLabel(item)}</td>
                      <td className="px-2 py-2" data-testid={`admin-content-list-status-${rowKey}`}>
                        <span className={`inline-flex rounded border px-2 py-1 text-[11px] ${deleted ? 'border-rose-300 bg-rose-100 text-rose-700' : 'border-slate-200 bg-slate-100 text-slate-700'}`}>
                          {deleted ? 'deleted' : item.status}
                        </span>
                      </td>
                      <td className="px-2 py-2" data-testid={`admin-content-list-active-state-${rowKey}`}>
                        <span className="inline-flex items-center gap-1">
                          <span
                            className={`h-2.5 w-2.5 rounded-full ${active ? 'bg-emerald-500' : 'bg-rose-500'}`}
                            data-testid={`admin-content-list-active-dot-${rowKey}`}
                          />
                          <span data-testid={`admin-content-list-active-label-${rowKey}`}>{active ? 'aktif' : 'pasif'}</span>
                        </span>
                      </td>
                      <td className="px-2 py-2" data-testid={`admin-content-list-version-${rowKey}`}>{item.version ?? '-'}</td>
                      <td className="px-2 py-2" data-testid={`admin-content-list-updated-at-${rowKey}`}>{formatLayoutUpdatedAt(item.updated_at)}</td>
                      <td className="px-2 py-2" data-testid={`admin-content-list-actions-${rowKey}`}>
                        <div className="flex flex-wrap gap-1">
                          <button
                            type="button"
                            className="h-8 rounded border px-2 text-[11px]"
                            onClick={() => handleContentListEdit(item)}
                            disabled={deleted}
                            data-testid={`admin-content-list-edit-button-${rowKey}`}
                          >
                            Edit
                          </button>
                          <button
                            type="button"
                            className="h-8 rounded border border-rose-300 px-2 text-[11px] text-rose-700"
                            onClick={() => handleContentListDelete(item)}
                            disabled={deleted}
                            data-testid={`admin-content-list-delete-button-${rowKey}`}
                          >
                            Delete
                          </button>
                          <button
                            type="button"
                            className="h-8 rounded border border-blue-300 px-2 text-[11px] text-blue-700"
                            onClick={() => handleContentListCopy(item)}
                            disabled={deleted}
                            data-testid={`admin-content-list-copy-button-${rowKey}`}
                          >
                            Kopyala
                          </button>
                          <button
                            type="button"
                            className="h-8 rounded border border-emerald-300 px-2 text-[11px] text-emerald-700"
                            onClick={() => handleSetRevisionActive(item, true)}
                            disabled={deleted || active}
                            data-testid={`admin-content-list-activate-button-${rowKey}`}
                          >
                            Aktif Et
                          </button>
                          <button
                            type="button"
                            className="h-8 rounded border border-rose-300 px-2 text-[11px] text-rose-700"
                            onClick={() => handleSetRevisionActive(item, false)}
                            disabled={deleted || !active}
                            data-testid={`admin-content-list-deactivate-button-${rowKey}`}
                          >
                            Pasif Et
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {statusMessage ? (
          <p className="mt-2 text-xs text-emerald-700" data-testid="admin-content-list-status-message">{statusMessage}</p>
        ) : null}
        {contentListError ? (
          <p className="mt-2 text-xs text-rose-700" data-testid="admin-content-list-error-message">{contentListError}</p>
        ) : null}
      </section>
    </div>
  );
}
