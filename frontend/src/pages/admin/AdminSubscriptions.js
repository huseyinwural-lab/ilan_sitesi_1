import { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { useAuth } from '../../contexts/AuthContext';
import { FinanceStatusBadge } from '../../components/finance/FinanceStatusBadge';
import { FinanceEmptyState, FinanceErrorState, FinanceLoadingState } from '../../components/finance/FinanceStateView';
import { formatMoneyMinor, resolveLocaleByCountry } from '../../utils/financeFormat';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const STATUS_OPTIONS = ['all', 'trialing', 'active', 'past_due', 'canceled', 'unpaid'];

const formatDateTime = (value, locale = 'tr-TR') => {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '-';
  return date.toLocaleString(locale);
};

export default function AdminSubscriptionsPage() {
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [selectedDetail, setSelectedDetail] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [status, setStatus] = useState('all');

  const authHeader = useMemo(() => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` }), []);
  const locale = resolveLocaleByCountry(user?.country_code || 'TR');

  const loadSubscriptions = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (status !== 'all') params.set('status', status);
      const res = await axios.get(`${API}/admin/finance/subscriptions?${params.toString()}`, { headers: authHeader });
      setItems(res.data.items || []);
      setError('');
    } catch {
      setError('Subscription kayıtları yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const loadDetail = async (subscriptionId) => {
    try {
      const res = await axios.get(`${API}/admin/finance/subscriptions/${subscriptionId}`, { headers: authHeader });
      setSelectedDetail(res.data);
    } catch {
      setError('Subscription detayı yüklenemedi');
    }
  };

  useEffect(() => {
    loadSubscriptions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status]);

  return (
    <div className="p-6 space-y-4" data-testid="admin-subscriptions-page">
      <div className="flex items-center justify-between gap-3 flex-wrap" data-testid="admin-subscriptions-header">
        <div>
          <h1 className="text-2xl font-semibold" data-testid="admin-subscriptions-title">Subscriptions</h1>
          <p className="text-sm text-muted-foreground" data-testid="admin-subscriptions-subtitle">Read-only abonelik listesi</p>
          <p className="text-xs text-muted-foreground" data-testid="admin-subscriptions-scope-badge">
            Scope: {user?.role === 'country_admin' ? (user?.country_code || 'COUNTRY') : 'Global'}
          </p>
        </div>
        <select className="h-9 px-3 rounded-md border bg-background text-sm" value={status} onChange={(e) => setStatus(e.target.value)} data-testid="admin-subscriptions-status-filter">
          {STATUS_OPTIONS.map((item) => <option key={item} value={item}>{item}</option>)}
        </select>
      </div>

      {error ? <FinanceErrorState testId="admin-subscriptions-error" message={error} /> : null}

      <div className="border rounded-lg overflow-hidden" data-testid="admin-subscriptions-table">
        <table className="w-full text-sm">
          <thead className="bg-muted">
            <tr>
              <th className="text-left px-3 py-2">user</th>
              <th className="text-left px-3 py-2">plan</th>
              <th className="text-left px-3 py-2">status</th>
              <th className="text-left px-3 py-2">period_end</th>
              <th className="text-left px-3 py-2">provider_subscription_id</th>
              <th className="text-left px-3 py-2">actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan="6" className="px-3 py-4"><FinanceLoadingState testId="admin-subscriptions-loading" /></td></tr>
            ) : items.length === 0 ? (
              <tr><td colSpan="6" className="px-3 py-4"><FinanceEmptyState testId="admin-subscriptions-empty" message="Henüz abonelik kaydı bulunmamaktadır." /></td></tr>
            ) : items.map((item) => (
              <tr key={item.id} className="border-t" data-testid={`admin-subscriptions-row-${item.id}`}>
                <td className="px-3 py-2" data-testid={`admin-subscriptions-user-${item.id}`}>{item.user_email || item.user_id}</td>
                <td className="px-3 py-2" data-testid={`admin-subscriptions-plan-${item.id}`}>
                  <div>{item.plan_name || '-'}</div>
                  <div className="text-xs text-muted-foreground" data-testid={`admin-subscriptions-plan-price-${item.id}`}>
                    {item.plan_price !== null && item.plan_price !== undefined
                      ? formatMoneyMinor(Math.round(Number(item.plan_price || 0) * 100), item.plan_currency || 'EUR', locale)
                      : '-'}
                  </div>
                </td>
                <td className="px-3 py-2" data-testid={`admin-subscriptions-status-${item.id}`}>
                  <FinanceStatusBadge status={item.status} testId={`admin-subscriptions-status-badge-${item.id}`} />
                </td>
                <td className="px-3 py-2" data-testid={`admin-subscriptions-period-end-${item.id}`}>{formatDateTime(item.current_period_end, locale)}</td>
                <td className="px-3 py-2 font-mono text-xs" data-testid={`admin-subscriptions-provider-${item.id}`}>{item.provider_subscription_id || '-'}</td>
                <td className="px-3 py-2" data-testid={`admin-subscriptions-actions-${item.id}`}>
                  <button type="button" className="h-8 px-2 rounded-md border text-xs" onClick={() => loadDetail(item.id)} data-testid={`admin-subscriptions-detail-button-${item.id}`}>Detay</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selectedDetail ? (
        <div className="border rounded-lg p-4 space-y-2" data-testid="admin-subscriptions-detail-panel">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold" data-testid="admin-subscriptions-detail-title">Subscription Detay</h2>
            <button type="button" className="h-8 px-2 rounded-md border text-xs" onClick={() => setSelectedDetail(null)} data-testid="admin-subscriptions-detail-close">Kapat</button>
          </div>
          <div className="text-sm" data-testid="admin-subscriptions-detail-status">Status: <FinanceStatusBadge status={selectedDetail.subscription?.status} testId="admin-subscriptions-detail-status-badge" /></div>
          <div className="text-sm" data-testid="admin-subscriptions-detail-user">User: {selectedDetail.user?.email || '-'}</div>
          <div className="text-sm" data-testid="admin-subscriptions-detail-plan">Plan: {selectedDetail.plan?.name || '-'}</div>
          <div className="text-sm" data-testid="admin-subscriptions-detail-provider">Provider Subscription: {selectedDetail.subscription?.provider_subscription_id || '-'}</div>
          <div className="text-xs text-muted-foreground" data-testid="admin-subscriptions-detail-invoice-count">Invoice count: {selectedDetail.invoices?.length || 0}</div>
        </div>
      ) : null}
    </div>
  );
}
