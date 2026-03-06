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

  return (
    <div className="space-y-5" data-testid="admin-content-list-page">
      <section className="rounded-xl border bg-white p-4" data-testid="admin-content-list-panel">
        <div className="flex flex-wrap items-center justify-between gap-2" data-testid="admin-content-list-header">
          <div>
            <h1 className="text-sm font-semibold" data-testid="admin-content-list-title">Content List</h1>
            <p className="text-xs text-slate-500" data-testid="admin-content-list-subtitle">
              Filtre: draft + published • Silinen kayıtlar kırmızı gösterilir.
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

        <div className="mt-3 overflow-x-auto" data-testid="admin-content-list-table-wrap">
          <table className="min-w-full text-left text-xs" data-testid="admin-content-list-table">
            <thead>
              <tr className="border-b bg-slate-50" data-testid="admin-content-list-head-row">
                <th className="px-2 py-2">page_type</th>
                <th className="px-2 py-2">country</th>
                <th className="px-2 py-2">module</th>
                <th className="px-2 py-2">category / scope</th>
                <th className="px-2 py-2">status</th>
                <th className="px-2 py-2">version</th>
                <th className="px-2 py-2">updated_at</th>
                <th className="px-2 py-2">actions</th>
              </tr>
            </thead>
            <tbody data-testid="admin-content-list-table-body">
              {contentListLoading ? (
                <tr data-testid="admin-content-list-loading-row">
                  <td className="px-2 py-3 text-slate-500" colSpan={8} data-testid="admin-content-list-loading-cell">İçerik listesi yükleniyor...</td>
                </tr>
              ) : contentListRows.length === 0 ? (
                <tr data-testid="admin-content-list-empty-row">
                  <td className="px-2 py-3 text-slate-500" colSpan={8} data-testid="admin-content-list-empty-cell">Kayıt bulunamadı.</td>
                </tr>
              ) : (
                contentListRows.map((item) => {
                  const rowKey = item.revision_id || item.id;
                  const deleted = Boolean(item.is_deleted);
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
