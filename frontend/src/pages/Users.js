import { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { Search, Filter, Shield, Trash2, Ban, CheckCircle, Eye } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { useAuth } from '../contexts/AuthContext';
import { toast } from '../components/ui/use-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const STATUS_OPTIONS = [
  { value: 'all', label: 'Tümü' },
  { value: 'active', label: 'Aktif' },
  { value: 'inactive', label: 'Pasif' },
  { value: 'deleted', label: 'Silindi' },
];

const TYPE_OPTIONS = [
  { value: 'all', label: 'Tümü' },
  { value: 'individual', label: 'Bireysel' },
  { value: 'dealer', label: 'Ticari (Dealer)' },
  { value: 'admin', label: 'Admin' },
];

const SORT_OPTIONS = [
  { value: 'created_at', label: 'Kayıt Tarihi' },
  { value: 'last_login', label: 'Son Giriş' },
  { value: 'email', label: 'E-posta' },
];

const ROLE_LABELS = {
  super_admin: 'Super Admin',
  country_admin: 'Ülke Admin',
  moderator: 'Moderatör',
  support: 'Destek',
  finance: 'Finans',
  dealer: 'Dealer',
  individual: 'Bireysel',
};

const TYPE_LABELS = {
  individual: 'Bireysel',
  dealer: 'Ticari (Dealer)',
  admin: 'Admin',
};

const formatDate = (value) => {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '-';
  return date.toLocaleString();
};

const formatPlan = (user) => {
  if (!user?.plan_name) return '-';
  return user.plan_expires_at
    ? `${user.plan_name} · ${formatDate(user.plan_expires_at)}`
    : user.plan_name;
};

const statusBadge = (status) => {
  if (status === 'deleted') return { label: 'Silindi', className: 'bg-rose-100 text-rose-700' };
  if (status === 'suspended') return { label: 'Pasif', className: 'bg-amber-100 text-amber-700' };
  return { label: 'Aktif', className: 'bg-emerald-100 text-emerald-700' };
};

export default function Users() {
  const { t } = useLanguage();
  const { user } = useAuth();
  const [users, setUsers] = useState([]);
  const [countries, setCountries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [countryFilter, setCountryFilter] = useState('all');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortDir, setSortDir] = useState('desc');
  const [confirmAction, setConfirmAction] = useState(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailData, setDetailData] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const canManage = user?.role === 'super_admin';

  const authHeader = useMemo(
    () => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` }),
    []
  );

  const fetchCountries = async () => {
    try {
      const res = await axios.get(`${API}/admin/countries`, { headers: authHeader });
      const active = (res.data.items || []).filter((item) => item.active_flag);
      setCountries(active.map((item) => item.country_code));
    } catch (err) {
      setCountries([]);
    }
  };

  const fetchUsers = async () => {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams();
      if (search) params.set('search', search);
      if (statusFilter !== 'all') params.set('status', statusFilter);
      if (typeFilter !== 'all') params.set('user_type', typeFilter);
      if (countryFilter !== 'all') params.set('country', countryFilter);
      if (sortBy) params.set('sort_by', sortBy);
      if (sortDir) params.set('sort_dir', sortDir);
      const qs = params.toString() ? `?${params.toString()}` : '';
      const res = await axios.get(`${API}/users${qs}`, { headers: authHeader });
      setUsers(res.data.items || []);
    } catch (err) {
      setError('Kullanıcı listesi yüklenemedi.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCountries();
  }, []);

  useEffect(() => {
    fetchUsers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter, typeFilter, countryFilter, sortBy, sortDir]);

  const handleSearchSubmit = (event) => {
    event.preventDefault();
    fetchUsers();
  };

  const handleSuspend = (userItem) => {
    setConfirmAction({ type: 'suspend', user: userItem });
  };

  const handleDelete = (userItem) => {
    setConfirmAction({ type: 'delete', user: userItem });
  };

  const handleActivate = (userItem) => {
    setConfirmAction({ type: 'activate', user: userItem });
  };

  const handleConfirmAction = async () => {
    if (!confirmAction) return;
    const { type, user: target } = confirmAction;
    try {
      if (type === 'suspend') {
        await axios.post(`${API}/admin/users/${target.id}/suspend`, {}, { headers: authHeader });
        toast({ title: 'Kullanıcı pasife alındı.' });
      }
      if (type === 'delete') {
        await axios.delete(`${API}/admin/users/${target.id}`, { headers: authHeader });
        toast({ title: 'Kullanıcı silindi.' });
      }
      setConfirmAction(null);
      fetchUsers();
    } catch (err) {
      const message = err.response?.data?.detail || 'İşlem başarısız.';
      toast({ title: typeof message === 'string' ? message : 'İşlem başarısız.', variant: 'destructive' });
    }
  };

  const handleOpenDetail = async (userItem) => {
    setDetailOpen(true);
    setDetailLoading(true);
    try {
      const res = await axios.get(`${API}/admin/users/${userItem.id}/detail`, { headers: authHeader });
      setDetailData(res.data);
    } catch (err) {
      toast({ title: 'Detay yüklenemedi.', variant: 'destructive' });
    } finally {
      setDetailLoading(false);
    }
  };

  const closeDetail = () => {
    setDetailOpen(false);
    setDetailData(null);
  };

  const confirmMessage = confirmAction?.type === 'delete'
    ? 'Kullanıcı silinecek (geri alınamaz). Devam edilsin mi?'
    : 'Kullanıcı pasife alınacak. Devam edilsin mi?';

  return (
    <div className="space-y-6" data-testid="users-page">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold" data-testid="users-title">Kullanıcı Yönetimi</h1>
          <p className="text-sm text-muted-foreground" data-testid="users-subtitle">
            {t('users')} listesi, filtreler ve yönetim aksiyonları
          </p>
        </div>
      </div>

      <div className="bg-card border rounded-md p-4 space-y-4" data-testid="users-filters">
        <form onSubmit={handleSearchSubmit} className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 border rounded-md px-3 h-10 bg-background">
            <Search size={16} className="text-muted-foreground" />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder={`${t('search')}...`}
              className="bg-transparent outline-none text-sm"
              data-testid="users-search-input"
            />
          </div>
          <button
            type="submit"
            className="h-10 px-4 rounded-md border text-sm"
            data-testid="users-search-button"
          >
            Ara
          </button>
          <div className="flex items-center gap-2 text-xs text-muted-foreground" data-testid="users-filter-icon">
            <Filter size={14} /> Filtreler
          </div>
        </form>

        <div className="grid gap-3 md:grid-cols-4">
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">Durum</div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="h-10 rounded-md border bg-background px-3 text-sm w-full"
              data-testid="users-status-filter"
            >
              {STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">Kullanıcı Tipi</div>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="h-10 rounded-md border bg-background px-3 text-sm w-full"
              data-testid="users-type-filter"
            >
              {TYPE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">Ülke</div>
            <select
              value={countryFilter}
              onChange={(e) => setCountryFilter(e.target.value)}
              className="h-10 rounded-md border bg-background px-3 text-sm w-full"
              data-testid="users-country-filter"
            >
              <option value="all">Tümü</option>
              {countries.map((code) => (
                <option key={code} value={code}>{code}</option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">Sıralama</div>
            <div className="flex items-center gap-2">
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="h-10 rounded-md border bg-background px-3 text-sm w-full"
                data-testid="users-sort-select"
              >
                {SORT_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
              <button
                type="button"
                onClick={() => setSortDir(sortDir === 'desc' ? 'asc' : 'desc')}
                className="h-10 w-10 rounded-md border flex items-center justify-center"
                data-testid="users-sort-direction"
              >
                <Shield size={16} />
              </button>
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div className="text-sm text-rose-600" data-testid="users-error">{error}</div>
      )}

      <div className="rounded-md border bg-card overflow-hidden" data-testid="users-table">
        <div className="overflow-x-auto">
          <table className="min-w-[1400px] w-full text-sm">
            <thead className="bg-muted">
              <tr>
                <th className="p-3 text-left">Ad Soyad</th>
                <th className="p-3 text-left">E-posta</th>
                <th className="p-3 text-left">Kullanıcı Tipi</th>
                <th className="p-3 text-left">Rol</th>
                <th className="p-3 text-left">Durum</th>
                <th className="p-3 text-left">Doğrulama</th>
                <th className="p-3 text-left">Kayıt Tarihi</th>
                <th className="p-3 text-left">Son Giriş</th>
                <th className="p-3 text-left">İlan Sayısı</th>
                <th className="p-3 text-left">Aktif İlan</th>
                <th className="p-3 text-left">Üyelik/Paket</th>
                <th className="p-3 text-left">Aksiyon</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={12} className="p-6 text-center text-muted-foreground" data-testid="users-loading">
                    Yükleniyor...
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={12} className="p-6 text-center text-muted-foreground" data-testid="users-empty">
                    Kullanıcı bulunamadı.
                  </td>
                </tr>
              ) : (
                users.map((userItem) => {
                  const badge = statusBadge(userItem.status);
                  return (
                    <tr key={userItem.id} className="border-b last:border-none" data-testid={`user-row-${userItem.id}`}>
                      <td className="p-3" data-testid={`user-name-${userItem.id}`}>{userItem.full_name || '-'}</td>
                      <td className="p-3" data-testid={`user-email-${userItem.id}`}>{userItem.email}</td>
                      <td className="p-3" data-testid={`user-type-${userItem.id}`}>{TYPE_LABELS[userItem.user_type] || userItem.user_type}</td>
                      <td className="p-3" data-testid={`user-role-${userItem.id}`}>{ROLE_LABELS[userItem.role] || userItem.role}</td>
                      <td className="p-3" data-testid={`user-status-${userItem.id}`}>
                        <span className={`px-2 py-1 rounded-full text-xs ${badge.className}`}>{badge.label}</span>
                      </td>
                      <td className="p-3" data-testid={`user-verification-${userItem.id}`}>
                        <div className="text-xs">
                          E-posta: {userItem.email_verified ? 'Onaylı' : 'Onaysız'}
                        </div>
                        <div className="text-xs">
                          Telefon: {userItem.phone_verified ? 'Onaylı' : 'Onaysız'}
                        </div>
                      </td>
                      <td className="p-3" data-testid={`user-created-${userItem.id}`}>{formatDate(userItem.created_at)}</td>
                      <td className="p-3" data-testid={`user-last-login-${userItem.id}`}>{formatDate(userItem.last_login)}</td>
                      <td className="p-3" data-testid={`user-listings-total-${userItem.id}`}>{userItem.total_listings ?? 0}</td>
                      <td className="p-3" data-testid={`user-listings-active-${userItem.id}`}>{userItem.active_listings ?? 0}</td>
                      <td className="p-3" data-testid={`user-plan-${userItem.id}`}>{formatPlan(userItem)}</td>
                      <td className="p-3" data-testid={`user-actions-${userItem.id}`}>
                        <div className="flex flex-wrap items-center gap-2">
                          <button
                            type="button"
                            className="text-xs text-primary inline-flex items-center gap-1"
                            onClick={() => handleOpenDetail(userItem)}
                            data-testid={`user-detail-${userItem.id}`}
                          >
                            <Eye size={14} /> Detay
                          </button>
                          {canManage && userItem.status !== 'deleted' && (
                            <>
                              {userItem.status === 'suspended' ? (
                                <button
                                  type="button"
                                  className="text-xs text-emerald-600 inline-flex items-center gap-1"
                                  onClick={() => handleActivate(userItem)}
                                  data-testid={`user-activate-${userItem.id}`}
                                >
                                  <CheckCircle size={14} /> Aktif Et
                                </button>
                              ) : (
                                <button
                                  type="button"
                                  className="text-xs text-amber-600 inline-flex items-center gap-1"
                                  onClick={() => handleSuspend(userItem)}
                                  data-testid={`user-suspend-${userItem.id}`}
                                >
                                  <Ban size={14} /> Pasife Al
                                </button>
                              )}
                              <button
                                type="button"
                                className="text-xs text-rose-600 inline-flex items-center gap-1"
                                onClick={() => handleDelete(userItem)}
                                data-testid={`user-delete-${userItem.id}`}
                              >
                                <Trash2 size={14} /> Sil
                              </button>
                            </>
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

      {confirmAction && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" data-testid="users-confirm-modal">
          <div className="bg-card rounded-lg shadow-lg max-w-md w-full">
            <div className="p-4 border-b">
              <h3 className="text-lg font-semibold" data-testid="users-confirm-title">Onay</h3>
            </div>
            <div className="p-4 text-sm text-muted-foreground" data-testid="users-confirm-message">
              {confirmMessage}
            </div>
            <div className="flex items-center justify-end gap-2 p-4 border-t">
              <button
                type="button"
                className="h-9 px-4 rounded-md border text-sm"
                onClick={() => setConfirmAction(null)}
                data-testid="users-confirm-cancel"
              >
                Vazgeç
              </button>
              <button
                type="button"
                className="h-9 px-4 rounded-md bg-primary text-primary-foreground text-sm"
                onClick={handleConfirmAction}
                data-testid="users-confirm-approve"
              >
                Onayla
              </button>
            </div>
          </div>
        </div>
      )}

      {detailOpen && (
        <div className="fixed inset-0 bg-black/30 flex justify-end z-40" data-testid="users-detail-drawer">
          <div className="w-full max-w-md bg-card h-full shadow-xl p-6 overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold" data-testid="users-detail-title">Kullanıcı Detayı</h3>
              <button
                type="button"
                onClick={closeDetail}
                className="text-sm text-muted-foreground"
                data-testid="users-detail-close"
              >
                Kapat
              </button>
            </div>
            {detailLoading ? (
              <div className="text-sm text-muted-foreground" data-testid="users-detail-loading">Yükleniyor...</div>
            ) : detailData ? (
              <div className="space-y-4">
                <div className="space-y-1" data-testid="users-detail-summary">
                  <div className="text-xs text-muted-foreground">Ad Soyad</div>
                  <div className="font-semibold">{detailData.user.full_name || '-'}</div>
                  <div className="text-xs text-muted-foreground">E-posta</div>
                  <div>{detailData.user.email}</div>
                  <div className="text-xs text-muted-foreground">Tip / Rol</div>
                  <div>{TYPE_LABELS[detailData.user.user_type] || detailData.user.user_type} · {ROLE_LABELS[detailData.user.role] || detailData.user.role}</div>
                  <div className="text-xs text-muted-foreground">Durum</div>
                  <div>{statusBadge(detailData.user.status).label}</div>
                </div>

                <div className="space-y-1" data-testid="users-detail-meta">
                  <div className="text-xs text-muted-foreground">Kayıt Tarihi</div>
                  <div>{formatDate(detailData.user.created_at)}</div>
                  <div className="text-xs text-muted-foreground">Son Giriş</div>
                  <div>{formatDate(detailData.user.last_login)}</div>
                  <div className="text-xs text-muted-foreground">İlanlar</div>
                  <div>{detailData.user.total_listings} toplam · {detailData.user.active_listings} aktif</div>
                </div>

                <div className="space-y-1" data-testid="users-detail-plan">
                  <div className="text-xs text-muted-foreground">Üyelik/Paket</div>
                  <div>{formatPlan(detailData.user)}</div>
                </div>

                <a
                  href={detailData.listings_link}
                  className="inline-flex items-center gap-2 text-sm text-primary"
                  data-testid="users-detail-listings-link"
                >
                  İlanları Gör
                </a>

                <div className="space-y-2" data-testid="users-detail-audit">
                  <div className="text-xs text-muted-foreground">Audit Geçmişi</div>
                  {detailData.audit_logs?.length ? (
                    detailData.audit_logs.map((log, idx) => (
                      <div key={`${log.event_type}-${idx}`} className="text-sm" data-testid={`users-detail-audit-${idx}`}>
                        {log.event_type} · {formatDate(log.created_at)}
                      </div>
                    ))
                  ) : (
                    <div className="text-sm text-muted-foreground" data-testid="users-detail-audit-empty">Kayıt yok</div>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-sm text-muted-foreground" data-testid="users-detail-empty">Detay bulunamadı.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
