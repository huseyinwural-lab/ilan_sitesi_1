import { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { Search, X, ChevronLeft, ChevronRight, Plus } from 'lucide-react';
import { toast } from '@/components/ui/use-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const STATUS_OPTIONS = [
  { value: 'draft', label: 'Taslak' },
  { value: 'active', label: 'Aktif' },
  { value: 'paused', label: 'Durduruldu' },
  { value: 'ended', label: 'Bitti' },
];

const TARGET_OPTIONS = [
  { value: 'showcase', label: 'İlan Öne Çıkarma' },
  { value: 'discount', label: 'İndirim' },
  { value: 'package', label: 'Paket' },
];

const PRIORITY_OPTIONS = [
  { value: 'low', label: 'Düşük' },
  { value: 'medium', label: 'Orta' },
  { value: 'high', label: 'Yüksek' },
];

const SEGMENT_OPTIONS = [
  { value: 'all', label: 'Tümü' },
  { value: 'new_users', label: 'Yeni Kullanıcılar' },
  { value: 'returning', label: 'Dönen Kullanıcılar' },
  { value: 'selected', label: 'Seçili' },
];

const DEALER_PLAN_OPTIONS = [
  { value: 'any', label: 'Tümü' },
  { value: 'basic', label: 'Basic' },
  { value: 'pro', label: 'Pro' },
  { value: 'enterprise', label: 'Enterprise' },
];

const statusBadge = (status) => {
  switch (status) {
    case 'active':
      return { label: 'Aktif', className: 'bg-emerald-100 text-emerald-700' };
    case 'paused':
      return { label: 'Durduruldu', className: 'bg-amber-100 text-amber-700' };
    case 'draft':
      return { label: 'Taslak', className: 'bg-slate-100 text-slate-600' };
    case 'ended':
      return { label: 'Bitti', className: 'bg-zinc-200 text-zinc-700' };
    default:
      return { label: status || '-', className: 'bg-slate-100 text-slate-600' };
  }
};

const formatDate = (value) => {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '-';
  return date.toLocaleString();
};

const formatDiscount = (campaign) => {
  const rules = campaign.rules_json || {};
  if (rules.discount_percent) {
    return `%${rules.discount_percent}`;
  }
  if (rules.discount_amount) {
    return `${rules.discount_amount} ${rules.discount_currency || ''}`.trim();
  }
  return '-';
};

const parseCsv = (value) =>
  value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);

const buildErrorToast = (error, fallback) => {
  const detail = error?.response?.data?.detail || error?.response?.data;
  const message = detail?.message || detail?.detail || fallback;
  const requestId = detail?.request_id;
  toast({
    title: message,
    description: requestId ? `Request ID: ${requestId}` : undefined,
    variant: 'destructive',
  });
};

const initialFormState = {
  name: '',
  description: '',
  status: 'draft',
  target: 'discount',
  countryScope: 'global',
  countryCode: '',
  startAt: '',
  endAt: '',
  priority: 'medium',
  discountMode: 'percent',
  discountPercent: '',
  discountAmount: '',
  minListingCount: '',
  maxListingCount: '',
  eligibleCategories: '',
  eligibleUserSegment: 'all',
  eligibleDealerPlan: 'any',
  eligibleDealers: '',
  eligibleUsers: '',
  freeListingQuotaBonus: '',
};

export default function CampaignsManager({ campaignType, title, subtitle, testIdPrefix }) {
  const [items, setItems] = useState([]);
  const [countries, setCountries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [countryFilter, setCountryFilter] = useState('');
  const [page, setPage] = useState(1);
  const [limit] = useState(10);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [dbReady, setDbReady] = useState(false);
  const [formOpen, setFormOpen] = useState(false);
  const [formState, setFormState] = useState(initialFormState);
  const [editing, setEditing] = useState(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailData, setDetailData] = useState(null);
  const [saving, setSaving] = useState(false);

  const authHeader = useMemo(() => ({
    Authorization: `Bearer ${localStorage.getItem('access_token')}`,
  }), []);

  const disabled = !dbReady;

  const checkDbReady = async () => {
    try {
      const res = await axios.get(`${API}/health/db`, { headers: authHeader });
      setDbReady(res.status === 200 && res.data?.status === 'healthy');
    } catch (err) {
      setDbReady(false);
    }
  };

  const fetchCountries = async () => {
    try {
      const res = await axios.get(`${API}/admin/countries`, { headers: authHeader });
      setCountries(res.data.items || []);
    } catch (e) {
      setCountries([]);
    }
  };

  const fetchCampaigns = async () => {
    if (!dbReady) {
      setItems([]);
      setTotalCount(0);
      setTotalPages(1);
      setLoading(false);
      setError('DB hazır değil. Kampanya verisi okunamıyor.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams();
      params.set('type', campaignType);
      params.set('page', String(page));
      params.set('limit', String(limit));
      if (searchQuery) params.set('q', searchQuery);
      if (statusFilter) params.set('status', statusFilter);
      if (countryFilter) params.set('country', countryFilter);
      if (startDate && endDate) params.set('date_range', `${startDate},${endDate}`);

      const res = await axios.get(`${API}/admin/campaigns?${params.toString()}`, { headers: authHeader });
      setItems(res.data.items || []);
      setTotalCount(res.data.total_count ?? 0);
      setTotalPages(res.data.total_pages ?? 1);
    } catch (err) {
      setError('Kampanya listesi yüklenemedi.');
      buildErrorToast(err, 'Kampanya listesi yüklenemedi.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCountries();
    checkDbReady();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    fetchCampaigns();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [campaignType, page, searchQuery, statusFilter, countryFilter, startDate, endDate, dbReady]);

  const handleSearchSubmit = (event) => {
    event.preventDefault();
    setPage(1);
    setSearchQuery(searchInput.trim());
  };

  const handleClearSearch = () => {
    setSearchInput('');
    setSearchQuery('');
    setPage(1);
  };

  const openCreate = () => {
    setEditing(null);
    setFormState(initialFormState);
    setFormOpen(true);
  };

  const openEdit = (campaign) => {
    setEditing(campaign);
    const rules = campaign.rules_json || {};
    setFormState({
      name: campaign.name || '',
      description: campaign.notes || '',
      status: campaign.status || 'draft',
      target: rules.target || 'discount',
      countryScope: rules.country_scope || 'country',
      countryCode: campaign.country_code || '',
      startAt: campaign.start_at ? campaign.start_at.slice(0, 16) : '',
      endAt: campaign.end_at ? campaign.end_at.slice(0, 16) : '',
      priority: rules.priority || 'medium',
      discountMode: rules.discount_percent ? 'percent' : rules.discount_amount ? 'amount' : 'percent',
      discountPercent: rules.discount_percent || '',
      discountAmount: rules.discount_amount || '',
      minListingCount: rules.min_listing_count || '',
      maxListingCount: rules.max_listing_count || '',
      eligibleCategories: (rules.eligible_categories || []).join(', '),
      eligibleUserSegment: rules.eligible_user_segment || 'all',
      eligibleDealerPlan: rules.eligible_dealer_plan || 'any',
      eligibleDealers: (rules.eligible_dealers || []).join(', '),
      eligibleUsers: (rules.eligible_users || []).join(', '),
      freeListingQuotaBonus: rules.free_listing_quota_bonus || '',
    });
    setFormOpen(true);
  };

  const openDetail = async (campaign) => {
    setDetailOpen(true);
    setDetailData(null);
    if (!dbReady) return;
    try {
      const res = await axios.get(`${API}/admin/campaigns/${campaign.id}`, { headers: authHeader });
      setDetailData(res.data);
    } catch (err) {
      buildErrorToast(err, 'Detay yüklenemedi.');
    }
  };

  const handleFormSubmit = async (event) => {
    event.preventDefault();
    if (disabled) return;

    const resolvedCountryCode = formState.countryCode || countryFilter || countries[0]?.code || 'DE';
    const rulesJson = {
      target: formState.target,
      priority: formState.priority,
      discount_percent: formState.discountMode === 'percent' && formState.discountPercent !== '' ? Number(formState.discountPercent) : null,
      discount_amount: formState.discountMode === 'amount' && formState.discountAmount !== '' ? Number(formState.discountAmount) : null,
      discount_currency: resolveCurrency('country', resolvedCountryCode),
      min_listing_count: formState.minListingCount !== '' ? Number(formState.minListingCount) : null,
      max_listing_count: formState.maxListingCount !== '' ? Number(formState.maxListingCount) : null,
      eligible_categories: formState.eligibleCategories ? parseCsv(formState.eligibleCategories) : [],
      eligible_user_segment: formState.eligibleUserSegment,
      eligible_dealer_plan: campaignType === 'corporate' ? formState.eligibleDealerPlan : null,
      eligible_dealers: campaignType === 'corporate' ? parseCsv(formState.eligibleDealers) : [],
      eligible_users: campaignType === 'individual' ? parseCsv(formState.eligibleUsers) : [],
      free_listing_quota_bonus: campaignType === 'individual' && formState.freeListingQuotaBonus !== '' ? Number(formState.freeListingQuotaBonus) : null,
      campaign_type: campaignType,
      country_scope: formState.countryScope,
    };

    const payload = {
      name: formState.name.trim(),
      status: formState.status,
      start_at: formState.startAt,
      end_at: formState.endAt || null,
      country_code: resolvedCountryCode,
      notes: formState.description.trim() || null,
      rules_json: rulesJson,
    };

    setSaving(true);
    try {
      if (editing) {
        await axios.put(`${API}/admin/campaigns/${editing.id}`, payload, { headers: authHeader });
        toast({ title: 'Kampanya güncellendi.' });
      } else {
        await axios.post(`${API}/admin/campaigns`, payload, { headers: authHeader });
        toast({ title: 'Kampanya oluşturuldu.' });
      }
      setFormOpen(false);
      fetchCampaigns();
    } catch (err) {
      buildErrorToast(err, 'Kampanya kaydedilemedi.');
    } finally {
      setSaving(false);
    }
  };

  const handleStatusAction = async (campaign, action) => {
    if (disabled) return;
    try {
      await axios.post(`${API}/admin/campaigns/${campaign.id}/${action}`, {}, { headers: authHeader });
      toast({ title: 'Durum güncellendi.' });
      fetchCampaigns();
    } catch (err) {
      buildErrorToast(err, 'Durum güncellenemedi.');
    }
  };

  const handleArchive = async (campaign) => {
    if (disabled) return;
    try {
      await axios.post(`${API}/admin/campaigns/${campaign.id}/archive`, {}, { headers: authHeader });
      toast({ title: 'Kampanya arşivlendi.' });
      fetchCampaigns();
    } catch (err) {
      buildErrorToast(err, 'Kampanya arşivlenemedi.');
    }
  };

  const resultLabel = searchQuery ? `${totalCount} sonuç bulundu` : `Toplam ${totalCount} kayıt`;

  return (
    <div className="space-y-6" data-testid={`${testIdPrefix}-page`}>
      <div>
        <h1 className="text-2xl font-bold" data-testid={`${testIdPrefix}-title`}>{title}</h1>
        <p className="text-sm text-muted-foreground" data-testid={`${testIdPrefix}-subtitle`}>{subtitle}</p>
      </div>

      {!dbReady && (
        <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800" data-testid={`${testIdPrefix}-db-banner`}>
          DB hazır değil. Kampanya aksiyonları devre dışı. Ops ekibine DATABASE_URL + migration kontrolü gerekiyor.
        </div>
      )}

      <div className="flex flex-wrap items-center justify-between gap-3" data-testid={`${testIdPrefix}-toolbar`}>
        <button
          type="button"
          className="h-10 px-4 rounded-md bg-primary text-primary-foreground text-sm flex items-center gap-2 disabled:opacity-50"
          onClick={openCreate}
          disabled={disabled}
          data-testid={`${testIdPrefix}-create-button`}
        >
          <Plus size={16} /> Yeni Kampanya
        </button>
        <div className="text-xs text-muted-foreground" data-testid={`${testIdPrefix}-result-count`}>{resultLabel}</div>
      </div>

      <div className="bg-card border rounded-md p-4 space-y-4" data-testid={`${testIdPrefix}-filters`}>
        <form onSubmit={handleSearchSubmit} className="flex flex-wrap items-center gap-3">
          <div className="relative flex items-center gap-2 border rounded-md px-3 h-10 bg-background w-full sm:w-96">
            <Search size={16} className="text-muted-foreground" />
            <input
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
              placeholder="Kampanya ara"
              className="bg-transparent outline-none text-sm flex-1"
              data-testid={`${testIdPrefix}-search-input`}
            />
            {searchInput && (
              <button
                type="button"
                onClick={handleClearSearch}
                className="text-muted-foreground hover:text-foreground"
                data-testid={`${testIdPrefix}-search-clear`}
              >
                <X size={14} />
              </button>
            )}
          </div>
          <button type="submit" className="h-10 px-4 rounded-md border text-sm" data-testid={`${testIdPrefix}-search-button`}>
            Ara
          </button>
        </form>

        <div className="grid gap-3 md:grid-cols-4" data-testid={`${testIdPrefix}-filter-grid`}>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">Durum</div>
            <select
              value={statusFilter}
              onChange={(event) => { setStatusFilter(event.target.value); setPage(1); }}
              className="h-10 rounded-md border bg-background px-3 text-sm w-full"
              data-testid={`${testIdPrefix}-status-filter`}
            >
              <option value="">Tümü</option>
              {STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">Scope</div>
            <select
              value={countryFilter}
              onChange={(event) => { setCountryFilter(event.target.value); setPage(1); }}
              className="h-10 rounded-md border bg-background px-3 text-sm w-full"
              data-testid={`${testIdPrefix}-country-filter`}
            >
              <option value="">Tümü</option>
              <option value="global">Global</option>
              {countries.map((country) => (
                <option key={country.country_code} value={country.country_code}>
                  {country.name} ({country.country_code})
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">Başlangıç</div>
            <input
              type="date"
              value={startDate}
              onChange={(event) => { setStartDate(event.target.value); setPage(1); }}
              className="h-10 rounded-md border bg-background px-3 text-sm w-full"
              data-testid={`${testIdPrefix}-start-date`}
            />
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">Bitiş</div>
            <input
              type="date"
              value={endDate}
              onChange={(event) => { setEndDate(event.target.value); setPage(1); }}
              className="h-10 rounded-md border bg-background px-3 text-sm w-full"
              data-testid={`${testIdPrefix}-end-date`}
            />
          </div>
        </div>
      </div>

      {error && (
        <div className="text-sm text-rose-600" data-testid={`${testIdPrefix}-error`}>{error}</div>
      )}

      <div className="rounded-md border bg-card overflow-hidden" data-testid={`${testIdPrefix}-table`}>
        <div className="overflow-x-auto">
          <table className="min-w-[1200px] w-full text-sm">
            <thead className="bg-muted">
              <tr>
                <th className="p-3 text-left" data-testid={`${testIdPrefix}-header-name`}>Name</th>
                <th className="p-3 text-left" data-testid={`${testIdPrefix}-header-status`}>Status</th>
                <th className="p-3 text-left" data-testid={`${testIdPrefix}-header-type`}>Type</th>
                <th className="p-3 text-left" data-testid={`${testIdPrefix}-header-scope`}>Scope</th>
                <th className="p-3 text-left" data-testid={`${testIdPrefix}-header-date`}>Start-End</th>
                <th className="p-3 text-left" data-testid={`${testIdPrefix}-header-discount`}>Discount</th>
                <th className="p-3 text-left" data-testid={`${testIdPrefix}-header-priority`}>Priority</th>
                <th className="p-3 text-left" data-testid={`${testIdPrefix}-header-updated`}>Updated</th>
                {campaignType === 'corporate' ? (
                  <th className="p-3 text-left" data-testid={`${testIdPrefix}-header-plan`}>Plan/Dealers</th>
                ) : (
                  <th className="p-3 text-left" data-testid={`${testIdPrefix}-header-users`}>Users</th>
                )}
                <th className="p-3 text-right" data-testid={`${testIdPrefix}-header-actions`}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={10} className="p-6 text-center text-muted-foreground" data-testid={`${testIdPrefix}-loading`}>
                    Yükleniyor...
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={10} className="p-6 text-center text-muted-foreground" data-testid={`${testIdPrefix}-empty`}>
                    Kampanya bulunamadı.
                  </td>
                </tr>
              ) : (
                items.map((campaign) => {
                  const badge = statusBadge(campaign.status);
                  const rules = campaign.rules_json || {};
                  const scopeLabel = campaign.country_code || '-';
                  const typeLabel = campaignType === 'corporate' ? 'Kurumsal' : 'Bireysel';
                  const priorityLabel = rules.priority || '-';
                  const dealerCount = Array.isArray(rules.eligible_dealers) ? rules.eligible_dealers.length : 0;
                  const userCount = Array.isArray(rules.eligible_users) ? rules.eligible_users.length : 0;
                  const dealerPlan = rules.eligible_dealer_plan || '-';
                  const actionDisabled = disabled;
                  return (
                    <tr key={campaign.id} className="border-b last:border-none" data-testid={`${testIdPrefix}-row-${campaign.id}`}>
                      <td className="p-3" data-testid={`${testIdPrefix}-name-${campaign.id}`}>{campaign.name}</td>
                      <td className="p-3" data-testid={`${testIdPrefix}-status-${campaign.id}`}>
                        <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs ${badge.className}`}>{badge.label}</span>
                      </td>
                      <td className="p-3" data-testid={`${testIdPrefix}-type-${campaign.id}`}>{typeLabel}</td>
                      <td className="p-3" data-testid={`${testIdPrefix}-scope-${campaign.id}`}>{scopeLabel}</td>
                      <td className="p-3" data-testid={`${testIdPrefix}-date-${campaign.id}`}>
                        {formatDate(campaign.start_at)} - {formatDate(campaign.end_at)}
                      </td>
                      <td className="p-3" data-testid={`${testIdPrefix}-discount-${campaign.id}`}>{formatDiscount(campaign)}</td>
                      <td className="p-3" data-testid={`${testIdPrefix}-priority-${campaign.id}`}>{campaign.priority}</td>
                      <td className="p-3" data-testid={`${testIdPrefix}-updated-${campaign.id}`}>{formatDate(campaign.updated_at)}</td>
                      {campaignType === 'corporate' ? (
                        <td className="p-3" data-testid={`${testIdPrefix}-plan-${campaign.id}`}>
                          {campaign.eligible_dealer_plan || '-'} / {campaign.eligible_dealers_count || 0}
                        </td>
                      ) : (
                        <td className="p-3" data-testid={`${testIdPrefix}-users-${campaign.id}`}>
                          {campaign.eligible_users_count || 0}
                        </td>
                      )}
                      <td className="p-3 text-right" data-testid={`${testIdPrefix}-actions-${campaign.id}`}>
                        <div className="flex flex-wrap justify-end gap-2">
                          <button
                            type="button"
                            className="h-8 px-3 rounded-md border text-xs"
                            onClick={() => openDetail(campaign)}
                            data-testid={`${testIdPrefix}-view-${campaign.id}`}
                          >
                            View
                          </button>
                          <button
                            type="button"
                            className="h-8 px-3 rounded-md border text-xs"
                            onClick={() => openEdit(campaign)}
                            disabled={actionDisabled}
                            data-testid={`${testIdPrefix}-edit-${campaign.id}`}
                          >
                            Edit
                          </button>
                          {campaign.status === 'active' ? (
                            <button
                              type="button"
                              className="h-8 px-3 rounded-md border text-xs"
                              onClick={() => handleStatusAction(campaign, 'pause')}
                              disabled={actionDisabled}
                              data-testid={`${testIdPrefix}-pause-${campaign.id}`}
                            >
                              Pause
                            </button>
                          ) : campaign.status !== 'archived' ? (
                            <button
                              type="button"
                              className="h-8 px-3 rounded-md border text-xs"
                              onClick={() => handleStatusAction(campaign, 'activate')}
                              disabled={actionDisabled}
                              data-testid={`${testIdPrefix}-activate-${campaign.id}`}
                            >
                              Activate
                            </button>
                          ) : null}
                          {campaign.status !== 'archived' && (
                            <button
                              type="button"
                              className="h-8 px-3 rounded-md border text-xs"
                              onClick={() => handleArchive(campaign)}
                              disabled={actionDisabled}
                              data-testid={`${testIdPrefix}-archive-${campaign.id}`}
                            >
                              Archive
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="flex items-center justify-between" data-testid={`${testIdPrefix}-pagination`}>
        <button
          type="button"
          className="h-9 px-3 rounded-md border text-sm flex items-center gap-2 disabled:opacity-50"
          onClick={() => setPage((prev) => Math.max(prev - 1, 1))}
          disabled={page <= 1}
          data-testid={`${testIdPrefix}-prev`}
        >
          <ChevronLeft size={14} /> Önceki
        </button>
        <div className="text-sm text-muted-foreground" data-testid={`${testIdPrefix}-page-indicator`}>
          Sayfa {page} / {totalPages}
        </div>
        <button
          type="button"
          className="h-9 px-3 rounded-md border text-sm flex items-center gap-2 disabled:opacity-50"
          onClick={() => setPage((prev) => Math.min(prev + 1, totalPages))}
          disabled={page >= totalPages}
          data-testid={`${testIdPrefix}-next`}
        >
          Sonraki <ChevronRight size={14} />
        </button>
      </div>

      {formOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" data-testid={`${testIdPrefix}-form-modal`}>
          <div className="bg-background w-full max-w-3xl rounded-md p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold" data-testid={`${testIdPrefix}-form-title`}>
                {editing ? 'Kampanya Düzenle' : 'Yeni Kampanya'}
              </h2>
              <button type="button" onClick={() => setFormOpen(false)} data-testid={`${testIdPrefix}-form-close`}>
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleFormSubmit} className="grid gap-4 md:grid-cols-2">
              <div className="md:col-span-2">
                <label className="text-sm text-muted-foreground">Kampanya Adı</label>
                <input
                  value={formState.name}
                  onChange={(event) => setFormState((prev) => ({ ...prev, name: event.target.value }))}
                  className="h-10 w-full rounded-md border bg-background px-3 text-sm"
                  data-testid={`${testIdPrefix}-form-name`}
                  required
                />
              </div>
              <div className="md:col-span-2">
                <label className="text-sm text-muted-foreground">Açıklama</label>
                <textarea
                  value={formState.description}
                  onChange={(event) => setFormState((prev) => ({ ...prev, description: event.target.value }))}
                  className="min-h-[80px] w-full rounded-md border bg-background px-3 py-2 text-sm"
                  data-testid={`${testIdPrefix}-form-description`}
                />
              </div>
              <div>
                <label className="text-sm text-muted-foreground">Target</label>
                <select
                  value={formState.target}
                  onChange={(event) => setFormState((prev) => ({ ...prev, target: event.target.value }))}
                  className="h-10 w-full rounded-md border bg-background px-3 text-sm"
                  data-testid={`${testIdPrefix}-form-target`}
                >
                  {TARGET_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-sm text-muted-foreground">Status</label>
                <select
                  value={formState.status}
                  onChange={(event) => setFormState((prev) => ({ ...prev, status: event.target.value }))}
                  className="h-10 w-full rounded-md border bg-background px-3 text-sm"
                  data-testid={`${testIdPrefix}-form-status`}
                >
                  {STATUS_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-sm text-muted-foreground">Scope</label>
                <select
                  value={formState.countryScope}
                  onChange={(event) => setFormState((prev) => ({ ...prev, countryScope: event.target.value }))}
                  className="h-10 w-full rounded-md border bg-background px-3 text-sm"
                  data-testid={`${testIdPrefix}-form-scope`}
                >
                  <option value="global">Global</option>
                  <option value="country">Country</option>
                </select>
              </div>
              {formState.countryScope === 'country' && (
                <div>
                  <label className="text-sm text-muted-foreground">Country</label>
                  <select
                    value={formState.countryCode}
                    onChange={(event) => setFormState((prev) => ({ ...prev, countryCode: event.target.value }))}
                    className="h-10 w-full rounded-md border bg-background px-3 text-sm"
                    data-testid={`${testIdPrefix}-form-country`}
                    required
                  >
                    <option value="">Seçiniz</option>
                    {countries.map((country) => (
                      <option key={country.country_code} value={country.country_code}>
                        {country.name} ({country.country_code})
                      </option>
                    ))}
                  </select>
                </div>
              )}
              <div>
                <label className="text-sm text-muted-foreground">Start</label>
                <input
                  type="datetime-local"
                  value={formState.startAt}
                  onChange={(event) => setFormState((prev) => ({ ...prev, startAt: event.target.value }))}
                  className="h-10 w-full rounded-md border bg-background px-3 text-sm"
                  data-testid={`${testIdPrefix}-form-start`}
                  required
                />
              </div>
              <div>
                <label className="text-sm text-muted-foreground">End</label>
                <input
                  type="datetime-local"
                  value={formState.endAt}
                  onChange={(event) => setFormState((prev) => ({ ...prev, endAt: event.target.value }))}
                  className="h-10 w-full rounded-md border bg-background px-3 text-sm"
                  data-testid={`${testIdPrefix}-form-end`}
                  required
                />
              </div>
              <div>
                <label className="text-sm text-muted-foreground">Priority</label>
                <select
                  value={formState.priority}
                  onChange={(event) => setFormState((prev) => ({ ...prev, priority: event.target.value }))}
                  className="h-10 w-full rounded-md border bg-background px-3 text-sm"
                  data-testid={`${testIdPrefix}-form-priority`}
                >
                  {PRIORITY_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-sm text-muted-foreground">İndirim Türü</label>
                <select
                  value={formState.discountMode}
                  onChange={(event) => setFormState((prev) => ({ ...prev, discountMode: event.target.value }))}
                  className="h-10 w-full rounded-md border bg-background px-3 text-sm"
                  data-testid={`${testIdPrefix}-form-discount-mode`}
                >
                  <option value="percent">Percent</option>
                  <option value="amount">Amount</option>
                </select>
              </div>
              <div>
                <label className="text-sm text-muted-foreground">Discount</label>
                {formState.discountMode === 'percent' ? (
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={formState.discountPercent}
                    onChange={(event) => setFormState((prev) => ({ ...prev, discountPercent: event.target.value }))}
                    className="h-10 w-full rounded-md border bg-background px-3 text-sm"
                    data-testid={`${testIdPrefix}-form-discount-percent`}
                  />
                ) : (
                  <input
                    type="number"
                    min="0"
                    value={formState.discountAmount}
                    onChange={(event) => setFormState((prev) => ({ ...prev, discountAmount: event.target.value }))}
                    className="h-10 w-full rounded-md border bg-background px-3 text-sm"
                    data-testid={`${testIdPrefix}-form-discount-amount`}
                  />
                )}
              </div>
              <div>
                <label className="text-sm text-muted-foreground">Min Listing</label>
                <input
                  type="number"
                  min="0"
                  value={formState.minListingCount}
                  onChange={(event) => setFormState((prev) => ({ ...prev, minListingCount: event.target.value }))}
                  className="h-10 w-full rounded-md border bg-background px-3 text-sm"
                  data-testid={`${testIdPrefix}-form-min-listing`}
                />
              </div>
              <div>
                <label className="text-sm text-muted-foreground">Max Listing</label>
                <input
                  type="number"
                  min="0"
                  value={formState.maxListingCount}
                  onChange={(event) => setFormState((prev) => ({ ...prev, maxListingCount: event.target.value }))}
                  className="h-10 w-full rounded-md border bg-background px-3 text-sm"
                  data-testid={`${testIdPrefix}-form-max-listing`}
                />
              </div>
              <div>
                <label className="text-sm text-muted-foreground">Eligible Categories</label>
                <input
                  value={formState.eligibleCategories}
                  onChange={(event) => setFormState((prev) => ({ ...prev, eligibleCategories: event.target.value }))}
                  className="h-10 w-full rounded-md border bg-background px-3 text-sm"
                  placeholder="cat1, cat2"
                  data-testid={`${testIdPrefix}-form-categories`}
                />
              </div>
              <div>
                <label className="text-sm text-muted-foreground">Segment</label>
                <select
                  value={formState.eligibleUserSegment}
                  onChange={(event) => setFormState((prev) => ({ ...prev, eligibleUserSegment: event.target.value }))}
                  className="h-10 w-full rounded-md border bg-background px-3 text-sm"
                  data-testid={`${testIdPrefix}-form-segment`}
                >
                  {SEGMENT_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </div>
              {campaignType === 'corporate' ? (
                <>
                  <div>
                    <label className="text-sm text-muted-foreground">Plan</label>
                    <select
                      value={formState.eligibleDealerPlan}
                      onChange={(event) => setFormState((prev) => ({ ...prev, eligibleDealerPlan: event.target.value }))}
                      className="h-10 w-full rounded-md border bg-background px-3 text-sm"
                      data-testid={`${testIdPrefix}-form-plan`}
                    >
                      {DEALER_PLAN_OPTIONS.map((option) => (
                        <option key={option.value} value={option.value}>{option.label}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Selected Dealers</label>
                    <input
                      value={formState.eligibleDealers}
                      onChange={(event) => setFormState((prev) => ({ ...prev, eligibleDealers: event.target.value }))}
                      className="h-10 w-full rounded-md border bg-background px-3 text-sm"
                      placeholder="dealer_id1, dealer_id2"
                      data-testid={`${testIdPrefix}-form-dealers`}
                    />
                  </div>
                </>
              ) : (
                <>
                  <div>
                    <label className="text-sm text-muted-foreground">Selected Users</label>
                    <input
                      value={formState.eligibleUsers}
                      onChange={(event) => setFormState((prev) => ({ ...prev, eligibleUsers: event.target.value }))}
                      className="h-10 w-full rounded-md border bg-background px-3 text-sm"
                      placeholder="user_id1, user_id2"
                      data-testid={`${testIdPrefix}-form-users`}
                    />
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Free Listing Bonus</label>
                    <input
                      type="number"
                      min="0"
                      value={formState.freeListingQuotaBonus}
                      onChange={(event) => setFormState((prev) => ({ ...prev, freeListingQuotaBonus: event.target.value }))}
                      className="h-10 w-full rounded-md border bg-background px-3 text-sm"
                      data-testid={`${testIdPrefix}-form-quota`}
                    />
                  </div>
                </>
              )}

              <div className="md:col-span-2 flex justify-end gap-2">
                <button
                  type="button"
                  className="h-10 px-4 rounded-md border text-sm"
                  onClick={() => setFormOpen(false)}
                  data-testid={`${testIdPrefix}-form-cancel`}
                >
                  Vazgeç
                </button>
                <button
                  type="submit"
                  className="h-10 px-4 rounded-md bg-primary text-primary-foreground text-sm disabled:opacity-50"
                  disabled={saving}
                  data-testid={`${testIdPrefix}-form-save`}
                >
                  {saving ? 'Kaydediliyor' : 'Kaydet'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {detailOpen && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/40" data-testid={`${testIdPrefix}-detail-drawer`}>
          <div className="bg-background w-full max-w-lg h-full p-6 space-y-4 overflow-y-auto">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold" data-testid={`${testIdPrefix}-detail-title`}>Kampanya Detayı</h2>
              <button type="button" onClick={() => setDetailOpen(false)} data-testid={`${testIdPrefix}-detail-close`}>
                <X size={18} />
              </button>
            </div>
            {!detailData ? (
              <div className="text-sm text-muted-foreground" data-testid={`${testIdPrefix}-detail-loading`}>
                Yükleniyor...
              </div>
            ) : (
              <div className="space-y-3" data-testid={`${testIdPrefix}-detail-body`}>
                <div><strong>Ad:</strong> {detailData.name}</div>
                <div><strong>Tür:</strong> {detailData.type}</div>
                <div><strong>Status:</strong> {detailData.status}</div>
                <div><strong>Target:</strong> {detailData.target}</div>
                <div><strong>Scope:</strong> {detailData.country_scope} {detailData.country_code || ''}</div>
                <div><strong>Tarih:</strong> {formatDate(detailData.start_at)} - {formatDate(detailData.end_at)}</div>
                <div><strong>Discount:</strong> {formatDiscount(detailData)}</div>
                <div><strong>Segment:</strong> {detailData.eligible_user_segment}</div>
                {campaignType === 'corporate' ? (
                  <div><strong>Plan:</strong> {detailData.eligible_dealer_plan}</div>
                ) : (
                  <div><strong>Selected Users:</strong> {(detailData.eligible_users || []).length}</div>
                )}
                <div>
                  <strong>Audit:</strong>
                  <ul className="text-xs text-muted-foreground" data-testid={`${testIdPrefix}-detail-audit`}>
                    {(detailData.audit || []).length === 0 ? (
                      <li>Audit kaydı yok.</li>
                    ) : (
                      detailData.audit.map((item) => (
                        <li key={item.id}>{item.action} - {item.created_at}</li>
                      ))
                    )}
                  </ul>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
