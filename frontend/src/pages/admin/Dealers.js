import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { useLanguage } from '@/contexts/LanguageContext';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from '@/components/ui/use-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

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

const statusBadge = (status) => {
  if (status === 'deleted') {
    return { label: 'Silindi', className: 'bg-rose-100 text-rose-700' };
  }
  if (status === 'suspended') {
    return { label: 'Askıda', className: 'bg-amber-100 text-amber-700' };
  }
  return { label: 'Aktif', className: 'bg-emerald-100 text-emerald-700' };
};

export default function DealersPage() {
  const { t } = useLanguage();
  const { user: currentUser } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);
  const [actionDialog, setActionDialog] = useState(null);
  const [reasonCode, setReasonCode] = useState('');
  const [reasonDetail, setReasonDetail] = useState('');
  const [suspensionUntil, setSuspensionUntil] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const limit = 20;

  const canSuspend = ['super_admin', 'moderator'].includes(currentUser?.role);
  const canDelete = currentUser?.role === 'super_admin';

  const authHeader = useMemo(() => ({
    Authorization: `Bearer ${localStorage.getItem('access_token')}`,
  }), []);

  const fetchDealers = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set('skip', String(page * limit));
      params.set('limit', String(limit));
      if (statusFilter && statusFilter !== 'all') params.set('status', statusFilter);
      if (search) params.set('search', search);

      const res = await axios.get(`${API}/admin/dealers?${params.toString()}`, {
        headers: authHeader,
      });
      setItems(res.data.items || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDealers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter, search, page]);

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
      closeActionDialog();
      fetchDealers();
    } catch (e) {
      const message = e.response?.data?.detail || 'İşlem başarısız. Lütfen tekrar deneyin.';
      toast({ title: typeof message === 'string' ? message : 'İşlem başarısız. Lütfen tekrar deneyin.', variant: 'destructive' });
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="admin-dealers-page">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dealers</h1>
        <p className="text-sm text-muted-foreground">Dealer Management (Sprint 1)</p>
      </div>

        <div className="flex flex-wrap gap-3">
          <input
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(0); }}
            placeholder="E-posta ile ara"
            className="h-9 px-3 rounded-md border bg-background text-sm"
            data-testid="dealers-search-input"
          />
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(0); }}
            className="h-9 px-3 rounded-md border bg-background text-sm"
            data-testid="dealers-status-select"
          >
            {STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
        </div>

      <div className="rounded-md border bg-card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-muted">
            <tr>
              <th className="text-left p-3" data-testid="dealers-header-email">E-posta</th>
              <th className="text-left p-3" data-testid="dealers-header-country">Ülke</th>
              <th className="text-left p-3" data-testid="dealers-header-status">Durum</th>
              <th className="text-right p-3" data-testid="dealers-header-actions">Aksiyon</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={4} className="p-6 text-center">Loading…</td></tr>
            ) : items.length === 0 ? (
              <tr><td colSpan={4} className="p-6 text-center text-muted-foreground">No dealers</td></tr>
            ) : (
              items.map((d) => {
                const statusValue = d.status || d.dealer_status || 'active';
                const badge = statusBadge(statusValue);
                const allowSuspend = canSuspend && statusValue !== 'deleted';
                const allowDelete = canDelete && statusValue !== 'deleted';
                const showActions = allowSuspend || allowDelete;
                return (
                <tr key={d.id} className="border-t" data-testid={`dealer-row-${d.id}`}>
                  <td className="p-3" data-testid={`dealer-email-${d.id}`}>{d.email}</td>
                  <td className="p-3 text-muted-foreground" data-testid={`dealer-country-${d.id}`}>{d.country_code || '-'}</td>
                  <td className="p-3" data-testid={`dealer-status-${d.id}`}>
                    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${badge.className}`}>{badge.label}</span>
                  </td>
                  <td className="p-3 text-right">
                    {d.dealer_status === 'active' ? (
                      <button
                        onClick={() => setDealerStatus(d.id, 'suspended')}
                        className="h-8 px-3 rounded-md border text-xs hover:bg-muted"
                        data-testid={`dealer-suspend-${d.id}`}
                      >
                        Suspend
                      </button>
                    ) : (
                      <button
                        onClick={() => setDealerStatus(d.id, 'active')}
                        className="h-8 px-3 rounded-md border text-xs hover:bg-muted"
                        data-testid={`dealer-activate-${d.id}`}
                      >
                        Activate
                      </button>
                    )}
                    <Link
                      to={`/admin/dealers/${d.id}`}
                      className="ml-2 h-8 px-3 rounded-md border text-xs inline-flex items-center justify-center"
                      data-testid={`dealer-detail-link-${d.id}`}
                    >
                      Detay
                    </Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-end gap-2">
        <button
          onClick={() => setPage(Math.max(0, page - 1))}
          disabled={page === 0}
          className="h-9 px-3 rounded-md border text-sm disabled:opacity-50"
          data-testid="dealers-prev-page"
        >
          Prev
        </button>
        <button
          onClick={() => setPage(page + 1)}
          className="h-9 px-3 rounded-md border text-sm"
          data-testid="dealers-next-page"
        >
          Next
        </button>
      </div>
    </div>
  );
}
