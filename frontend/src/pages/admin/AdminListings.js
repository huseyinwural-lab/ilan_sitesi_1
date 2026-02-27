import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import axios from 'axios';
import { EyeOff, Trash2 } from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const statusColors = {
  draft: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
  pending_moderation: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
  published: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400',
  rejected: 'bg-rose-100 text-rose-800 dark:bg-rose-900/30 dark:text-rose-400',
  needs_revision: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
  unpublished: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300',
  archived: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300',
};

const statusOptions = [
  { value: '', label: 'Tümü' },
  { value: 'draft', label: 'draft' },
  { value: 'pending_moderation', label: 'pending_moderation' },
  { value: 'published', label: 'published' },
  { value: 'rejected', label: 'rejected' },
  { value: 'needs_revision', label: 'needs_revision' },
  { value: 'unpublished', label: 'unpublished' },
  { value: 'archived', label: 'archived' },
];

const dopingTabs = [
  { value: 'all', label: 'Tümü' },
  { value: 'free', label: 'Ücretsiz İlan' },
  { value: 'showcase', label: 'Vitrin İlan' },
  { value: 'urgent', label: 'Acil İlan' },
];

export default function AdminListingsPage({
  title = 'İlanlar',
  dataTestId = 'admin-listings-page',
  applicantType = 'all',
  applicationsMode = false,
}) {
  const [searchParams] = useSearchParams();
  const urlCountry = (searchParams.get('country') || '').toUpperCase();

  const [items, setItems] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);

  const [status, setStatus] = useState(applicationsMode ? 'pending_moderation' : '');
  const [search, setSearch] = useState('');
  const [dealerOnly, setDealerOnly] = useState(false);
  const [categoryId, setCategoryId] = useState('');
  const [dopingType, setDopingType] = useState('all');
  const [dopingCounts, setDopingCounts] = useState({ free: 0, showcase: 0, urgent: 0 });
  const [dopingConfig, setDopingConfig] = useState({});
  const [dopingBusyId, setDopingBusyId] = useState('');
  const [page, setPage] = useState(0);
  const limit = 20;

  const [actionDialog, setActionDialog] = useState(null); // { listing, action }
  const [actionReason, setActionReason] = useState('');
  const [actionNote, setActionNote] = useState('');

  const statusValue = status || 'all';
  const categoryValue = categoryId || 'all';

  const authHeader = useMemo(() => ({
    Authorization: `Bearer ${localStorage.getItem('access_token')}`,
  }), []);

  const categoryMap = useMemo(() => {
    const map = new Map();
    categories.forEach((cat) => {
      const label = cat?.name || cat?.slug || cat?.id;
      if (cat?.id) map.set(cat.id, label);
      if (cat?.slug) map.set(cat.slug, label);
    });
    return map;
  }, [categories]);

  const fetchCategories = async () => {
    try {
      const params = urlCountry ? `?country=${urlCountry}` : '';
      const res = await axios.get(`${API}/admin/categories${params}`, { headers: authHeader });
      setCategories(res.data.items || []);
    } catch (e) {
      console.error('Failed to load categories', e);
    }
  };

  const fetchListings = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set('skip', String(page * limit));
      params.set('limit', String(limit));
      if (applicationsMode) params.set('status', 'pending_moderation');
      else if (status) params.set('status', status);
      if (search) params.set('q', search);
      if (!applicationsMode && dealerOnly) params.set('dealer_only', 'true');
      if (categoryId) params.set('category_id', categoryId);
      if (urlCountry) params.set('country', urlCountry);
      if (applicantType && applicantType !== 'all') params.set('applicant_type', applicantType);
      if (dopingType && dopingType !== 'all') params.set('doping_type', dopingType);

      const res = await axios.get(`${API}/admin/listings?${params.toString()}`, {
        headers: authHeader,
      });
      setItems(res.data.items || []);
      setTotal(res.data.pagination?.total ?? 0);
      setDopingCounts(res.data.doping_counts || { free: 0, showcase: 0, urgent: 0 });
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCategories();
  }, []);

  useEffect(() => {
    fetchListings();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, search, dealerOnly, categoryId, page, urlCountry, applicantType, dopingType, applicationsMode]);

  const openActionDialog = (listing, action) => {
    setActionDialog({ listing, action });
    setActionReason('');
    setActionNote('');
  };

  const submitAction = async () => {
    if (!actionDialog) return;
    const payload = {
      reason: actionReason.trim() || undefined,
      reason_note: actionNote.trim() || undefined,
    };

    try {
      if (actionDialog.action === 'soft_delete') {
        await axios.post(
          `${API}/admin/listings/${actionDialog.listing.id}/soft-delete`,
          payload,
          { headers: authHeader }
        );
      }
      if (actionDialog.action === 'force_unpublish') {
        await axios.post(
          `${API}/admin/listings/${actionDialog.listing.id}/force-unpublish`,
          payload,
          { headers: authHeader }
        );
      }
      await fetchListings();
      setActionDialog(null);
    } catch (e) {
      alert(e.response?.data?.detail || 'Aksiyon başarısız');
    }
  };

  const applyDoping = async (listing) => {
    const config = dopingConfig[listing.id] || { type: listing.doping_type || 'free', preset: '7', customDays: '' };
    const payload = {
      doping_type: config.type || 'free',
      reason: 'moderation_manual_doping',
    };

    if (payload.doping_type !== 'free') {
      const preset = config.preset || '7';
      const customDays = Number(config.customDays || 0);
      if (preset === 'custom') {
        if (!Number.isFinite(customDays) || customDays <= 0) {
          alert('Manuel gün sayısı 1 veya daha büyük olmalı');
          return;
        }
        payload.duration_days = Math.min(365, Math.floor(customDays));
      } else {
        payload.duration_days = Number(preset);
      }
    }

    setDopingBusyId(listing.id);
    try {
      await axios.post(`${API}/admin/listings/${listing.id}/doping`, payload, { headers: authHeader });
      await fetchListings();
    } catch (error) {
      alert(error.response?.data?.detail || 'Doping güncellenemedi');
    } finally {
      setDopingBusyId('');
    }
  };

  const clearFilters = () => {
    setStatus(applicationsMode ? 'pending_moderation' : '');
    setSearch('');
    setDealerOnly(false);
    setCategoryId('');
    setDopingType('all');
    setPage(0);
  };

  const resolveCategoryLabel = (key) => {
    if (!key) return '-';
    return categoryMap.get(key) || key;
  };

  const toTestId = (value) => String(value || 'all')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-');

  return (
    <div className="space-y-6" data-testid={dataTestId}>
      <div className="flex flex-col gap-2">
        <div>
          <h1 className="text-2xl font-bold tracking-tight" data-testid="admin-listings-title">{title}</h1>
          <p className="text-sm text-muted-foreground">Global Listing Yönetimi (Sprint 2.1)</p>
        </div>
        <div className="text-xs text-muted-foreground" data-testid="admin-listings-context">
          Mod: <span className="font-semibold">{urlCountry ? `Country (${urlCountry})` : 'Global'}</span>
        </div>
      </div>

      <div className="flex flex-wrap gap-3 items-center" data-testid="listings-filters">
        <input
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(0); }}
          placeholder="ID / Başlık / Marka / Model"
          className="h-9 px-3 rounded-md border bg-background text-sm"
          data-testid="listings-search-input"
        />
        {!applicationsMode ? (
          <Select
            value={statusValue}
            onValueChange={(value) => { setStatus(value === 'all' ? '' : value); setPage(0); }}
          >
            <SelectTrigger className="h-9 w-[180px]" data-testid="listings-status-select">
              <SelectValue placeholder="Tümü" />
            </SelectTrigger>
            <SelectContent>
              {statusOptions.map((opt) => (
                <SelectItem
                  key={opt.value || 'all'}
                  value={opt.value || 'all'}
                  data-testid={`listings-status-option-${toTestId(opt.value || 'all')}`}
                >
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        ) : null}
        <Select
          value={categoryValue}
          onValueChange={(value) => { setCategoryId(value === 'all' ? '' : value); setPage(0); }}
        >
          <SelectTrigger className="h-9 min-w-[200px]" data-testid="listings-category-select">
            <SelectValue placeholder="Tüm Kategoriler" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all" data-testid="listings-category-option-all">Tüm Kategoriler</SelectItem>
            {categories.map((cat) => {
              const label = cat?.name || cat?.slug || cat?.id;
              const value = cat?.id || cat?.slug || label;
              return (
                <SelectItem
                  key={value}
                  value={value}
                  data-testid={`listings-category-option-${toTestId(value)}`}
                >
                  {label}
                </SelectItem>
              );
            })}
          </SelectContent>
        </Select>
        {!applicationsMode ? (
          <label className="flex items-center gap-2 text-sm" data-testid="listings-dealer-only-toggle">
            <input
              type="checkbox"
              checked={dealerOnly}
              onChange={(e) => { setDealerOnly(e.target.checked); setPage(0); }}
              className="h-4 w-4"
              data-testid="listings-dealer-only-checkbox"
            />
            Dealer Only
          </label>
        ) : null}
        <button
          onClick={clearFilters}
          className="h-9 px-3 rounded-md border text-sm hover:bg-muted"
          data-testid="listings-clear-filters-button"
        >
          Filtreleri Temizle
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-2" data-testid="listings-doping-tabs">
        {dopingTabs.map((tab) => {
          const count = tab.value === 'all'
            ? (Number(dopingCounts.free || 0) + Number(dopingCounts.showcase || 0) + Number(dopingCounts.urgent || 0))
            : Number(dopingCounts[tab.value] || 0);
          const active = dopingType === tab.value;
          return (
            <button
              key={tab.value}
              type="button"
              onClick={() => { setDopingType(tab.value); setPage(0); }}
              className={`h-9 rounded-full border px-3 text-sm font-semibold ${active ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-300 text-slate-800'}`}
              data-testid={`listings-doping-tab-${tab.value}`}
            >
              {tab.label} ({count})
            </button>
          );
        })}
      </div>

      <div className="flex items-center justify-between text-sm text-muted-foreground" data-testid="listings-summary">
        <span data-testid="listings-total-count">Toplam: {total}</span>
        <span data-testid="listings-page-indicator">Sayfa: {page + 1}</span>
      </div>

      <div className="rounded-md border bg-card overflow-hidden" data-testid="listings-table">
        <div className="hidden lg:grid grid-cols-[2fr_1.1fr_1.1fr_0.9fr_1.2fr_1.4fr] gap-4 bg-muted px-4 py-3 text-sm font-medium">
          <div>İlan</div>
          <div>Sahip</div>
          <div>Ülke / Kategori</div>
          <div>Durum</div>
          <div>Doping</div>
          <div className="text-right">Aksiyon</div>
        </div>

        <div className="divide-y">
          {loading ? (
            <div className="p-6 text-center" data-testid="listings-loading-state">Yükleniyor…</div>
          ) : items.length === 0 ? (
            <div className="p-6 text-center text-muted-foreground" data-testid="listings-empty-state">
              Kayıt bulunamadı
            </div>
          ) : (
            items.map((listing) => (
              <div
                key={listing.id}
                className="grid grid-cols-1 gap-4 px-4 py-4 lg:grid-cols-[2fr_1.1fr_1.1fr_0.9fr_1.2fr_1.4fr]"
                data-testid={`listing-row-${listing.id}`}
              >
                <div>
                  <div className="text-xs uppercase text-muted-foreground lg:hidden">İlan</div>
                  <div className="font-medium" data-testid={`listing-title-${listing.id}`}>{listing.title}</div>
                  <div className="text-xs text-muted-foreground" data-testid={`listing-id-${listing.id}`}>{listing.id}</div>
                  <div className="text-xs text-muted-foreground" data-testid={`listing-price-${listing.id}`}>
                    {listing.price ? `${listing.price.toLocaleString()} ${listing.currency || 'EUR'}` : '—'}
                  </div>
                </div>
                <div data-testid={`listing-owner-${listing.id}`}>
                  <div className="text-xs uppercase text-muted-foreground lg:hidden">Sahip</div>
                  <div className="font-medium">{listing.owner_email || '—'}</div>
                  <div className="text-xs text-muted-foreground">{listing.owner_role || 'unknown'}</div>
                </div>
                <div data-testid={`listing-country-${listing.id}`}>
                  <div className="text-xs uppercase text-muted-foreground lg:hidden">Ülke / Kategori</div>
                  <div className="font-medium">{listing.country || '—'}</div>
                  <div className="text-xs text-muted-foreground" data-testid={`listing-category-${listing.id}`}>
                    {resolveCategoryLabel(listing.category_key)}
                  </div>
                </div>
                <div data-testid={`listing-status-${listing.id}`}>
                  <div className="text-xs uppercase text-muted-foreground lg:hidden">Durum</div>
                  <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${statusColors[listing.status] || 'bg-muted text-foreground'}`}>
                    {listing.status}
                  </span>
                </div>
                <div data-testid={`listing-doping-${listing.id}`}>
                  <div className="text-xs uppercase text-muted-foreground lg:hidden">Doping</div>
                  <div className="flex flex-wrap gap-1">
                    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold ${listing.is_featured ? 'bg-indigo-100 text-indigo-700' : 'bg-slate-100 text-slate-700'}`} data-testid={`listing-doping-featured-${listing.id}`}>
                      {listing.is_featured ? 'Vitrin' : 'Vitrin Yok'}
                    </span>
                    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold ${listing.is_urgent ? 'bg-rose-100 text-rose-700' : 'bg-slate-100 text-slate-700'}`} data-testid={`listing-doping-urgent-${listing.id}`}>
                      {listing.is_urgent ? 'Acil' : 'Acil Yok'}
                    </span>
                  </div>
                  <div className="mt-1 text-[11px] text-muted-foreground" data-testid={`listing-doping-bucket-${listing.id}`}>
                    {listing.doping_type || 'free'}
                  </div>
                </div>
                <div className="flex flex-col gap-2 lg:items-end">
                  <div className="text-xs uppercase text-muted-foreground lg:hidden">Aksiyon</div>
                  <div className="flex flex-wrap items-center gap-1" data-testid={`listing-doping-editor-${listing.id}`}>
                    <select
                      value={(dopingConfig[listing.id]?.type) || listing.doping_type || 'free'}
                      onChange={(event) => setDopingConfig((prev) => ({
                        ...prev,
                        [listing.id]: {
                          ...(prev[listing.id] || {}),
                          type: event.target.value,
                        },
                      }))}
                      className="h-8 rounded-md border px-2 text-xs"
                      data-testid={`listing-doping-type-select-${listing.id}`}
                    >
                      <option value="free">Ücretsiz</option>
                      <option value="showcase">Vitrin</option>
                      <option value="urgent">Acil</option>
                    </select>
                    <select
                      value={(dopingConfig[listing.id]?.preset) || '7'}
                      onChange={(event) => setDopingConfig((prev) => ({
                        ...prev,
                        [listing.id]: {
                          ...(prev[listing.id] || {}),
                          preset: event.target.value,
                        },
                      }))}
                      className="h-8 rounded-md border px-2 text-xs"
                      data-testid={`listing-doping-preset-select-${listing.id}`}
                    >
                      <option value="7">7g</option>
                      <option value="30">30g</option>
                      <option value="90">90g</option>
                      <option value="custom">Manuel</option>
                    </select>
                    {(dopingConfig[listing.id]?.preset || '7') === 'custom' ? (
                      <input
                        type="number"
                        min={1}
                        max={365}
                        value={dopingConfig[listing.id]?.customDays || ''}
                        onChange={(event) => setDopingConfig((prev) => ({
                          ...prev,
                          [listing.id]: {
                            ...(prev[listing.id] || {}),
                            customDays: event.target.value,
                          },
                        }))}
                        className="h-8 w-20 rounded-md border px-2 text-xs"
                        placeholder="gün"
                        data-testid={`listing-doping-custom-days-${listing.id}`}
                      />
                    ) : null}
                    <button
                      type="button"
                      onClick={() => applyDoping(listing)}
                      className="h-8 rounded-md border border-slate-300 px-2 text-xs font-semibold"
                      disabled={dopingBusyId === listing.id}
                      data-testid={`listing-doping-apply-${listing.id}`}
                    >
                      {dopingBusyId === listing.id ? 'Uygulanıyor...' : 'Uygula'}
                    </button>
                  </div>
                  <div className="inline-flex flex-wrap gap-2 lg:justify-end">
                    <button
                      onClick={() => openActionDialog(listing, 'force_unpublish')}
                      className="h-8 px-2.5 rounded-md border text-xs text-orange-700 hover:bg-orange-50 disabled:opacity-50"
                      disabled={listing.status !== 'published'}
                      data-testid={`listing-force-unpublish-${listing.id}`}
                    >
                      <span className="inline-flex items-center gap-1">
                        <EyeOff size={14} />
                        Yayından Kaldır
                      </span>
                    </button>
                    <button
                      onClick={() => openActionDialog(listing, 'soft_delete')}
                      className="h-8 px-2.5 rounded-md border text-xs text-rose-600 hover:bg-rose-50 disabled:opacity-50"
                      disabled={listing.status === 'archived'}
                      data-testid={`listing-soft-delete-${listing.id}`}
                    >
                      <span className="inline-flex items-center gap-1">
                        <Trash2 size={14} />
                        Soft Delete
                      </span>
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="flex items-center justify-end gap-2">
        <button
          onClick={() => setPage(Math.max(0, page - 1))}
          disabled={page === 0}
          className="h-9 px-3 rounded-md border text-sm disabled:opacity-50"
          data-testid="listings-prev-page-button"
        >
          Prev
        </button>
        <button
          onClick={() => setPage(page + 1)}
          className="h-9 px-3 rounded-md border text-sm"
          data-testid="listings-next-page-button"
        >
          Next
        </button>
      </div>

      {actionDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" data-testid="listing-action-modal">
          <div className="bg-card rounded-lg border shadow-xl w-full max-w-md">
            <div className="p-4 border-b">
              <h3 className="text-lg font-semibold" data-testid="listing-action-title">
                {actionDialog.action === 'soft_delete' ? 'Soft Delete' : 'Force Unpublish'}
              </h3>
              <p className="text-sm text-muted-foreground mt-1" data-testid="listing-action-subtitle">
                {actionDialog.listing?.title}
              </p>
            </div>

            <div className="p-4 space-y-4">
              <div>
                <label className="text-sm font-medium">Reason (optional)</label>
                <input
                  value={actionReason}
                  onChange={(e) => setActionReason(e.target.value)}
                  className="mt-1 w-full h-9 px-3 rounded-md border bg-background text-sm"
                  placeholder="Kısa sebep"
                  data-testid="listing-action-reason-input"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Note (optional)</label>
                <textarea
                  value={actionNote}
                  onChange={(e) => setActionNote(e.target.value)}
                  className="mt-1 w-full min-h-[90px] p-3 rounded-md border bg-background text-sm"
                  placeholder="Detaylı açıklama"
                  data-testid="listing-action-note-input"
                />
              </div>
            </div>

            <div className="p-4 border-t flex items-center justify-end gap-2">
              <button
                onClick={() => setActionDialog(null)}
                className="h-9 px-3 rounded-md border hover:bg-muted text-sm"
                data-testid="listing-action-cancel-button"
              >
                Cancel
              </button>
              <button
                onClick={submitAction}
                className="h-9 px-3 rounded-md bg-primary text-primary-foreground hover:opacity-90 text-sm"
                data-testid="listing-action-confirm-button"
              >
                Confirm
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
