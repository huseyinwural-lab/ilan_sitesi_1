import { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from '@/components/ui/use-toast';
import { Search, X, ChevronLeft, ChevronRight } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const SORT_OPTIONS = [
  { value: 'company_asc', label: 'Firma Adı (A→Z)' },
  { value: 'company_desc', label: 'Firma Adı (Z→A)' },
  { value: 'email_asc', label: 'E-posta (A→Z)' },
];

const STATUS_OPTIONS = [
  { value: 'all', label: 'Tümü' },
  { value: 'active', label: 'Aktif' },
  { value: 'suspended', label: 'Askıda' },
  { value: 'deleted', label: 'Silindi' },
];

const REASON_OPTIONS = [
  { value: 'spam', label: 'Spam' },
  { value: 'fraud', label: 'Dolandırıcılık' },
  { value: 'adult', label: 'Müstehcen içerik' },
  { value: 'policy', label: 'Politika ihlali' },
  { value: 'other', label: 'Diğer' },
];

const ACTION_LABELS = {
  suspend: 'Kullanıcı askıya alınacak. Devam edilsin mi?',
  activate: 'Kullanıcı yeniden aktif edilecek. Devam edilsin mi?',
  delete: 'Kullanıcı silinecek (geri alınamaz). Devam edilsin mi?',
};

const AUDIT_LABELS = {
  dealer_suspended: 'Askıya Alındı',
  dealer_reactivated: 'Tekrar Aktif',
  dealer_deleted: 'Silindi',
  user_suspended: 'Askıya Alındı',
  user_reactivated: 'Tekrar Aktif',
  user_deleted: 'Silindi',
};

const statusBadge = (status) => {
  if (status === 'deleted') {
    return { label: 'Silindi', className: 'bg-rose-100 text-rose-700' };
  }
  if (status === 'suspended') {
    return { label: 'Askıda', className: 'bg-amber-100 text-amber-700' };
  }
  return { label: 'Aktif', className: 'bg-emerald-100 text-emerald-700' };
};

const formatDate = (value) => {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '-';
  return date.toLocaleString();
};

const resolveCompanyName = (dealer) => dealer?.company_name || '—';

const resolveContactName = (dealer) => {
  if (dealer?.contact_name) return dealer.contact_name;
  const fallback = [dealer?.first_name, dealer?.last_name].filter(Boolean).join(' ');
  return fallback || '—';
};

const formatAuditReason = (log) => {
  const code = log?.metadata?.reason_code || '';
  const detail = log?.metadata?.reason_detail || '';
  const combined = [code, detail].filter(Boolean).join(' • ');
  return combined || '—';
};

const getSortParams = (value) => {
  if (value === 'company_desc') {
    return { sort_by: 'company_name', sort_dir: 'desc' };
  }
  if (value === 'email_asc') {
    return { sort_by: 'email', sort_dir: 'asc' };
  }
  return { sort_by: 'company_name', sort_dir: 'asc' };
};

export default function DealersPage() {
  const { user: currentUser } = useAuth();
  const [items, setItems] = useState([]);
  const [countries, setCountries] = useState([]);
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortOption, setSortOption] = useState('company_asc');
  const [statusFilter, setStatusFilter] = useState('all');
  const [countryFilter, setCountryFilter] = useState('all');
  const [planFilter, setPlanFilter] = useState('all');
  const [page, setPage] = useState(1);
  const [limit] = useState(25);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [actionDialog, setActionDialog] = useState(null);
  const [reasonCode, setReasonCode] = useState('');
  const [reasonDetail, setReasonDetail] = useState('');
  const [suspensionUntil, setSuspensionUntil] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedDealer, setSelectedDealer] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const [auditLoading, setAuditLoading] = useState(false);
  const [auditError, setAuditError] = useState('');

  const canSuspend = ['super_admin', 'moderator'].includes(currentUser?.role);
  const canDelete = currentUser?.role === 'super_admin';

  const authHeader = useMemo(() => ({
    Authorization: `Bearer ${localStorage.getItem('access_token')}`,
  }), []);

  const fetchDealers = async () => {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams();
      params.set('page', String(page));
      params.set('limit', String(limit));
      params.set('include_filters', 'true');
      const { sort_by, sort_dir } = getSortParams(sortOption);
      params.set('sort_by', sort_by);
      params.set('sort_dir', sort_dir);
      if (searchQuery) params.set('search', searchQuery);
      if (statusFilter && statusFilter !== 'all') params.set('status', statusFilter);
      if (countryFilter && countryFilter !== 'all') params.set('country', countryFilter);
      if (planFilter && planFilter !== 'all') params.set('plan_id', planFilter);

      const res = await axios.get(`${API}/admin/dealers?${params.toString()}`, {
        headers: authHeader,
      });
      const nextItems = res.data.items || [];
      setItems(nextItems);
      if (selectedDealer) {
        const updated = nextItems.find((dealer) => dealer.id === selectedDealer.id);
        if (updated) {
          setSelectedDealer(updated);
        }
      }
      setTotalCount(res.data.total_count ?? 0);
      setTotalPages(res.data.total_pages ?? 1);
      if (res.data.filters?.countries) {
        setCountries(res.data.filters.countries || []);
      }
      if (res.data.filters?.plans) {
        setPlans(res.data.filters.plans || []);
      }
    } catch (e) {
      setError('Kurumsal kullanıcı listesi yüklenemedi.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDealers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter, searchQuery, countryFilter, planFilter, sortOption, page]);

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

  const fetchAuditLogs = async (dealerId) => {
    if (!dealerId) return;
    setAuditLoading(true);
    setAuditError('');
    try {
      const res = await axios.get(`${API}/admin/dealers/${dealerId}/audit-logs?limit=5`, {
        headers: authHeader,
      });
      setAuditLogs(res.data.items || []);
    } catch (e) {
      setAuditError('Moderasyon geçmişi yüklenemedi.');
    } finally {
      setAuditLoading(false);
    }
  };

  const openDrawer = (dealer) => {
    setSelectedDealer(dealer);
    setDrawerOpen(true);
    fetchAuditLogs(dealer.id);
  };

  const closeDrawer = () => {
    setDrawerOpen(false);
    setSelectedDealer(null);
    setAuditLogs([]);
    setAuditError('');
  };

  const openActionDialog = (type, dealer) => {
    setActionDialog({ type, dealer });
    setReasonCode('');
    setReasonDetail('');
    setSuspensionUntil('');
  };

  const closeActionDialog = () => {
    setActionDialog(null);
    setReasonCode('');
    setReasonDetail('');
    setSuspensionUntil('');
  };

  const handleActionConfirm = async () => {
    if (!actionDialog) return;
    if (!reasonCode) {
      toast({ title: 'Gerekçe zorunludur.', variant: 'destructive' });
      return;
    }
    setActionLoading(true);
    try {
      const payload = {
        reason_code: reasonCode,
        reason_detail: reasonDetail || undefined,
      };
      if (actionDialog.type === 'suspend' && suspensionUntil) {
        payload.suspension_until = new Date(suspensionUntil).toISOString();
      }
      if (actionDialog.type === 'delete') {
        await axios.delete(`${API}/admin/users/${actionDialog.dealer.id}`, {
          headers: authHeader,
          data: payload,
        });
      } else if (actionDialog.type === 'suspend') {
        await axios.post(`${API}/admin/users/${actionDialog.dealer.id}/suspend`, payload, { headers: authHeader });
      } else if (actionDialog.type === 'activate') {
        await axios.post(`${API}/admin/users/${actionDialog.dealer.id}/activate`, payload, { headers: authHeader });
      }
      toast({ title: 'İşlem tamamlandı.' });
      const targetId = actionDialog.dealer.id;
      const actionType = actionDialog.type;
      closeActionDialog();
      await fetchDealers();
      if (selectedDealer && selectedDealer.id === targetId) {
        if (actionType === 'delete') {
          setSelectedDealer({ ...selectedDealer, status: 'deleted', deleted_at: new Date().toISOString() });
        }
        if (actionType === 'suspend') {
          setSelectedDealer({ ...selectedDealer, status: 'suspended' });
        }
        if (actionType === 'activate') {
          setSelectedDealer({ ...selectedDealer, status: 'active' });
        }
        fetchAuditLogs(targetId);
      }
    } catch (e) {
      const message = e.response?.data?.detail || 'İşlem başarısız. Lütfen tekrar deneyin.';
      toast({ title: typeof message === 'string' ? message : 'İşlem başarısız. Lütfen tekrar deneyin.', variant: 'destructive' });
    } finally {
      setActionLoading(false);
    }
  };

  const resultLabel = searchQuery ? `${totalCount} sonuç bulundu` : `Toplam ${totalCount} kayıt`;

  return (
    <div className="space-y-6" data-testid="dealers-page">
      <div>
        <h1 className="text-2xl font-bold" data-testid="dealers-title">Kurumsal Kullanıcılar</h1>
        <p className="text-sm text-muted-foreground" data-testid="dealers-subtitle">Kurumsal kullanıcı yönetimi ve moderasyon aksiyonları</p>
      </div>

      <div className="bg-card border rounded-md p-4 space-y-4" data-testid="dealers-controls">
        <form onSubmit={handleSearchSubmit} className="flex flex-wrap items-center gap-3">
          <div className="relative flex items-center gap-2 border rounded-md px-3 h-10 bg-background w-full sm:w-96">
            <Search size={16} className="text-muted-foreground" />
            <input
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Firma, yetkili, e-posta veya telefon ara"
              className="bg-transparent outline-none text-sm flex-1"
              data-testid="dealers-search-input"
            />
            {searchInput && (
              <button
                type="button"
                onClick={handleClearSearch}
                className="text-muted-foreground hover:text-foreground"
                data-testid="dealers-search-clear"
              >
                <X size={14} />
              </button>
            )}
          </div>
          <button type="submit" className="h-10 px-4 rounded-md border text-sm" data-testid="dealers-search-button">
            Ara
          </button>
          <div className="text-xs text-muted-foreground" data-testid="dealers-result-count">{resultLabel}</div>
        </form>

        <div className="grid gap-3 md:grid-cols-4" data-testid="dealers-filters">
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">Sıralama</div>
            <select
              value={sortOption}
              onChange={(e) => setSortOption(e.target.value)}
              className="h-10 rounded-md border bg-background px-3 text-sm w-full"
              data-testid="dealers-sort-select"
            >
              {SORT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">Durum</div>
            <select
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
              className="h-10 rounded-md border bg-background px-3 text-sm w-full"
              data-testid="dealers-status-select"
            >
              {STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">Ülke</div>
            <select
              value={countryFilter}
              onChange={(e) => { setCountryFilter(e.target.value); setPage(1); }}
              className="h-10 rounded-md border bg-background px-3 text-sm w-full"
              data-testid="dealers-country-select"
            >
              <option value="all">Tümü</option>
              {countries.map((country) => (
                <option key={country.country_code} value={country.country_code}>{country.name} ({country.country_code})</option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">Paket</div>
            <select
              value={planFilter}
              onChange={(e) => { setPlanFilter(e.target.value); setPage(1); }}
              className="h-10 rounded-md border bg-background px-3 text-sm w-full"
              data-testid="dealers-plan-select"
            >
              <option value="all">Tümü</option>
              {plans.map((plan) => (
                <option key={plan.id} value={plan.id}>{plan.name}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {error && (
        <div className="text-sm text-rose-600" data-testid="dealers-error">{error}</div>
      )}

      <div className="rounded-md border bg-card overflow-hidden" data-testid="dealers-table">
        <div className="overflow-x-auto">
          <table className="min-w-[1400px] w-full text-sm">
            <thead className="bg-muted">
              <tr>
                <th className="p-3 text-left" data-testid="dealers-header-company">Firma Adı</th>
                <th className="p-3 text-left" data-testid="dealers-header-contact">Yetkili</th>
                <th className="p-3 text-left" data-testid="dealers-header-email">E-posta</th>
                <th className="p-3 text-left" data-testid="dealers-header-phone">Telefon</th>
                <th className="p-3 text-left" data-testid="dealers-header-country">Ülke</th>
                <th className="p-3 text-left" data-testid="dealers-header-status">Durum</th>
                <th className="p-3 text-left" data-testid="dealers-header-verify">Doğrulama</th>
                <th className="p-3 text-left" data-testid="dealers-header-created">Kayıt Tarihi</th>
                <th className="p-3 text-left" data-testid="dealers-header-last-login">Son Giriş</th>
                <th className="p-3 text-left" data-testid="dealers-header-listings">İlan</th>
                <th className="p-3 text-left" data-testid="dealers-header-plan">Paket</th>
                <th className="p-3 text-right" data-testid="dealers-header-actions">Aksiyon</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={12} className="p-6 text-center text-muted-foreground" data-testid="dealers-loading">Yükleniyor...</td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={12} className="p-6 text-center text-muted-foreground" data-testid="dealers-empty">Kurumsal kullanıcı bulunamadı.</td>
                </tr>
              ) : (
                items.map((dealer) => {
                  const statusValue = dealer.status || 'active';
                  const badge = statusBadge(statusValue);
                  const allowSuspend = canSuspend && statusValue !== 'deleted';
                  const allowDelete = canDelete && statusValue !== 'deleted';
                  const showActions = allowSuspend || allowDelete;
                  return (
                    <tr key={dealer.id} className="border-b last:border-none" data-testid={`dealer-row-${dealer.id}`}>
                      <td className="p-3" data-testid={`dealer-company-${dealer.id}`}>{resolveCompanyName(dealer)}</td>
                      <td className="p-3" data-testid={`dealer-contact-${dealer.id}`}>{resolveContactName(dealer)}</td>
                      <td className="p-3" data-testid={`dealer-email-${dealer.id}`}>{dealer.email}</td>
                      <td className="p-3" data-testid={`dealer-phone-${dealer.id}`}>{dealer.phone_e164 || '—'}</td>
                      <td className="p-3" data-testid={`dealer-country-${dealer.id}`}>{dealer.country_code || '-'}</td>
                      <td className="p-3" data-testid={`dealer-status-${dealer.id}`}>
                        <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs ${badge.className}`}>{badge.label}</span>
                      </td>
                      <td className="p-3" data-testid={`dealer-verify-${dealer.id}`}>
                        <div className="text-xs">E-posta: {dealer.email_verified ? 'Onaylı' : 'Onaysız'}</div>
                        <div className="text-xs">Telefon: {dealer.phone_verified ? 'Onaylı' : 'Onaysız'}</div>
                      </td>
                      <td className="p-3" data-testid={`dealer-created-${dealer.id}`}>{formatDate(dealer.created_at)}</td>
                      <td className="p-3" data-testid={`dealer-last-login-${dealer.id}`}>{formatDate(dealer.last_login)}</td>
                      <td className="p-3" data-testid={`dealer-listings-${dealer.id}`}>{dealer.total_listings ?? 0} / {dealer.active_listings ?? 0}</td>
                      <td className="p-3" data-testid={`dealer-plan-${dealer.id}`}>{dealer.plan_name || '-'}</td>
                      <td className="p-3 text-right" data-testid={`dealer-actions-${dealer.id}`}>
                        {statusValue === 'deleted' ? (
                          <div className="flex items-center justify-end gap-2">
                            <span className="text-xs text-muted-foreground" data-testid={`dealer-actions-deleted-${dealer.id}`}>Silindi</span>
                            <button
                              type="button"
                              onClick={() => openDrawer(dealer)}
                              className="h-8 px-3 rounded-md border text-xs inline-flex items-center justify-center"
                              data-testid={`dealer-detail-link-${dealer.id}`}
                            >
                              Detay
                            </button>
                          </div>
                        ) : (
                          <div className="flex items-center justify-end gap-2">
                            {allowSuspend && (statusValue === 'suspended' ? (
                              <button type="button" className="h-8 px-3 rounded-md border text-xs" onClick={() => openActionDialog('activate', dealer)} data-testid={`dealer-reactivate-${dealer.id}`}>
                                Aktif Et
                              </button>
                            ) : (
                              <button type="button" className="h-8 px-3 rounded-md border text-xs" onClick={() => openActionDialog('suspend', dealer)} data-testid={`dealer-suspend-${dealer.id}`}>
                                Askıya Al
                              </button>
                            ))}
                            {allowDelete && (
                              <button type="button" className="h-8 px-3 rounded-md border text-xs text-rose-600" onClick={() => openActionDialog('delete', dealer)} data-testid={`dealer-delete-${dealer.id}`}>
                                Sil
                              </button>
                            )}
                            {!showActions && (
                              <span className="text-xs text-muted-foreground" data-testid={`dealer-actions-disabled-${dealer.id}`}>Yetkisiz</span>
                            )}
                            <button
                              type="button"
                              onClick={() => openDrawer(dealer)}
                              className="h-8 px-3 rounded-md border text-xs inline-flex items-center justify-center"
                              data-testid={`dealer-detail-link-${dealer.id}`}
                            >
                              Detay
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="flex items-center justify-between" data-testid="dealers-pagination">
        <button
          type="button"
          className="h-9 px-3 rounded-md border text-sm flex items-center gap-2 disabled:opacity-50"
          onClick={() => setPage((prev) => Math.max(prev - 1, 1))}
          disabled={page <= 1}
          data-testid="dealers-prev"
        >
          <ChevronLeft size={14} /> Önceki
        </button>
        <div className="text-sm text-muted-foreground" data-testid="dealers-page-indicator">Sayfa {page} / {totalPages}</div>
        <button
          type="button"
          className="h-9 px-3 rounded-md border text-sm flex items-center gap-2 disabled:opacity-50"
          onClick={() => setPage((prev) => Math.min(prev + 1, totalPages))}
          disabled={page >= totalPages}
          data-testid="dealers-next"
        >
          Sonraki <ChevronRight size={14} />
        </button>
      </div>

      {drawerOpen && selectedDealer && (
        <div
          className="fixed inset-0 bg-black/40 z-50 flex justify-end"
          onClick={closeDrawer}
          data-testid="dealer-drawer-overlay"
        >
          <div
            className="w-full max-w-xl bg-card h-full shadow-xl overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
            data-testid="dealer-drawer"
          >
            <div className="flex items-start justify-between p-6 border-b">
              <div>
                <h3 className="text-xl font-semibold" data-testid="dealer-drawer-title">
                  {resolveCompanyName(selectedDealer)}
                </h3>
                <p className="text-sm text-muted-foreground" data-testid="dealer-drawer-subtitle">
                  Kurumsal kullanıcı profili
                </p>
              </div>
              <button
                type="button"
                onClick={closeDrawer}
                className="text-sm text-muted-foreground"
                data-testid="dealer-drawer-close"
              >
                Kapat
              </button>
            </div>

            <div className="p-6 space-y-6">
              <section className="space-y-3" data-testid="dealer-drawer-identity">
                <h4 className="text-sm font-semibold">Kimlik</h4>
                <div className="grid gap-2 text-sm">
                  <div data-testid="dealer-drawer-company">Firma: {resolveCompanyName(selectedDealer)}</div>
                  <div data-testid="dealer-drawer-contact">Yetkili: {resolveContactName(selectedDealer)}</div>
                  <div data-testid="dealer-drawer-email">E-posta: {selectedDealer.email}</div>
                  <div data-testid="dealer-drawer-phone">Telefon: {selectedDealer.phone_e164 || '—'}</div>
                  <div data-testid="dealer-drawer-country">Ülke: {selectedDealer.country_code || '-'}</div>
                  <div data-testid="dealer-drawer-status">
                    Durum: <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs ${statusBadge(selectedDealer.status || 'active').className}`}>
                      {statusBadge(selectedDealer.status || 'active').label}
                    </span>
                  </div>
                </div>
              </section>

              <section className="space-y-3" data-testid="dealer-drawer-metrics">
                <h4 className="text-sm font-semibold">Metrikler</h4>
                <div className="grid gap-2 text-sm">
                  <div data-testid="dealer-drawer-created">Kayıt Tarihi: {formatDate(selectedDealer.created_at)}</div>
                  <div data-testid="dealer-drawer-last-login">Son Giriş: {formatDate(selectedDealer.last_login)}</div>
                  <div data-testid="dealer-drawer-listings">İlan: {selectedDealer.total_listings ?? 0} / {selectedDealer.active_listings ?? 0}</div>
                  <div data-testid="dealer-drawer-plan">Paket: {selectedDealer.plan_name || '-'}</div>
                </div>
              </section>

              <section className="space-y-3" data-testid="dealer-drawer-actions">
                <h4 className="text-sm font-semibold">Aksiyonlar</h4>
                <div className="flex flex-wrap gap-2">
                  {canSuspend && selectedDealer.status !== 'deleted' && (selectedDealer.status === 'suspended' ? (
                    <button
                      type="button"
                      className="h-9 px-4 rounded-md border text-sm"
                      onClick={() => openActionDialog('activate', selectedDealer)}
                      data-testid="dealer-drawer-reactivate"
                    >
                      Aktif Et
                    </button>
                  ) : (
                    <button
                      type="button"
                      className="h-9 px-4 rounded-md border text-sm"
                      onClick={() => openActionDialog('suspend', selectedDealer)}
                      data-testid="dealer-drawer-suspend"
                    >
                      Askıya Al
                    </button>
                  ))}
                  {canDelete && selectedDealer.status !== 'deleted' && (
                    <button
                      type="button"
                      className="h-9 px-4 rounded-md border text-sm text-rose-600"
                      onClick={() => openActionDialog('delete', selectedDealer)}
                      data-testid="dealer-drawer-delete"
                    >
                      Sil
                    </button>
                  )}
                </div>
              </section>

              <section className="space-y-3" data-testid="dealer-drawer-audit">
                <h4 className="text-sm font-semibold">Moderasyon Geçmişi</h4>
                {auditLoading ? (
                  <div className="text-sm text-muted-foreground" data-testid="dealer-drawer-audit-loading">Yükleniyor...</div>
                ) : auditError ? (
                  <div className="text-sm text-rose-600" data-testid="dealer-drawer-audit-error">{auditError}</div>
                ) : auditLogs.length === 0 ? (
                  <div className="text-sm text-muted-foreground" data-testid="dealer-drawer-audit-empty">Kayıt yok</div>
                ) : (
                  <div className="space-y-2">
                    {auditLogs.map((log) => (
                      <div key={log.id} className="rounded-md border p-3 text-xs" data-testid={`dealer-drawer-audit-item-${log.id}`}>
                        <div className="font-medium" data-testid={`dealer-drawer-audit-action-${log.id}`}>
                          {AUDIT_LABELS[log.event_type] || log.event_type}
                        </div>
                        <div className="text-muted-foreground" data-testid={`dealer-drawer-audit-meta-${log.id}`}>
                          {formatDate(log.created_at)} • {log.user_email || '—'}
                        </div>
                        <div className="text-muted-foreground" data-testid={`dealer-drawer-audit-reason-${log.id}`}>
                          {formatAuditReason(log)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </section>
            </div>
          </div>
        </div>
      )}

      {actionDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" data-testid="dealers-action-modal">
          <div className="bg-card rounded-lg shadow-lg max-w-lg w-full">
            <div className="p-4 border-b">
              <h3 className="text-lg font-semibold" data-testid="dealers-action-title">Onay</h3>
            </div>
            <div className="p-4 space-y-4">
              <p className="text-sm text-muted-foreground" data-testid="dealers-action-message">
                {ACTION_LABELS[actionDialog.type]}
              </p>
              <div className="space-y-2">
                <label className="text-xs text-muted-foreground">Gerekçe (zorunlu)</label>
                <select
                  value={reasonCode}
                  onChange={(e) => setReasonCode(e.target.value)}
                  className="h-10 rounded-md border bg-background px-3 text-sm w-full"
                  data-testid="dealers-reason-select"
                >
                  <option value="">Seçiniz</option>
                  {REASON_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-xs text-muted-foreground">Detay (opsiyonel)</label>
                <textarea
                  value={reasonDetail}
                  onChange={(e) => setReasonDetail(e.target.value)}
                  className="min-h-[90px] w-full rounded-md border bg-background px-3 py-2 text-sm"
                  placeholder="Ek açıklama"
                  data-testid="dealers-reason-detail"
                />
              </div>
              {actionDialog.type === 'suspend' && (
                <div className="space-y-2">
                  <label className="text-xs text-muted-foreground">Askı bitiş tarihi (opsiyonel)</label>
                  <input
                    type="datetime-local"
                    value={suspensionUntil}
                    onChange={(e) => setSuspensionUntil(e.target.value)}
                    className="h-10 rounded-md border bg-background px-3 text-sm w-full"
                    data-testid="dealers-suspension-until"
                  />
                </div>
              )}
            </div>
            <div className="flex items-center justify-end gap-2 p-4 border-t">
              <button type="button" className="h-9 px-4 rounded-md border text-sm" onClick={closeActionDialog} data-testid="dealers-action-cancel">
                İptal
              </button>
              <button type="button" className="h-9 px-4 rounded-md bg-primary text-primary-foreground text-sm" onClick={handleActionConfirm} disabled={actionLoading} data-testid="dealers-action-confirm">
                {actionLoading ? 'İşleniyor' : 'Onayla'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
