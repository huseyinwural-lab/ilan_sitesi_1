import { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const asMoney = (value, currency) => `${Number(value || 0).toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${currency}`;

export default function AdminFinanceOverviewPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [country, setCountry] = useState('');
  const [currency, setCurrency] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [data, setData] = useState(null);

  const authHeader = useMemo(() => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` }), []);

  const loadOverview = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (country) params.set('country', country);
      if (currency) params.set('currency', currency);
      if (startDate) params.set('start_date', `${startDate}T00:00:00+00:00`);
      if (endDate) params.set('end_date', `${endDate}T23:59:59+00:00`);
      const res = await axios.get(`${API}/admin/finance/overview?${params.toString()}`, { headers: authHeader });
      setData(res.data);
      setError('');
    } catch (e) {
      setError('Finans özeti yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const exportFinanceCsv = async (type) => {
    const params = new URLSearchParams({ type });
    if (country) params.set('country', country);
    if (currency) params.set('currency', currency);
    if (startDate) params.set('start_date', `${startDate}T00:00:00+00:00`);
    if (endDate) params.set('end_date', `${endDate}T23:59:59+00:00`);
    const res = await axios.get(`${API}/admin/finance/export?${params.toString()}`, { headers: authHeader, responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement('a');
    link.href = url;
    link.download = `${type}.csv`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  };

  useEffect(() => {
    loadOverview();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const revenueList = Object.entries(data?.cards?.revenue_by_currency || {});
  const mrrList = Object.entries(data?.cards?.mrr_by_currency || {});

  return (
    <div className="p-6 space-y-4" data-testid="admin-finance-overview-page">
      <div className="flex items-start justify-between gap-3 flex-wrap" data-testid="admin-finance-overview-header">
        <div>
          <h1 className="text-2xl font-semibold" data-testid="admin-finance-overview-title">Finans Overview</h1>
          <p className="text-sm text-muted-foreground" data-testid="admin-finance-overview-subtitle">Read-only metrik görünümü</p>
          <p className="text-xs text-muted-foreground" data-testid="admin-finance-overview-scope-badge">
            Scope: {user?.role === 'country_admin' ? (user?.country_code || 'COUNTRY') : 'Global'}
          </p>
        </div>
        <div className="flex gap-2 flex-wrap" data-testid="admin-finance-overview-links">
          <button className="h-9 px-3 rounded-md border text-sm" data-testid="admin-finance-link-payments" onClick={() => navigate('/admin/payments')}>Payments</button>
          <button className="h-9 px-3 rounded-md border text-sm" data-testid="admin-finance-link-invoices" onClick={() => navigate('/admin/invoices')}>Invoices</button>
          <button className="h-9 px-3 rounded-md border text-sm" data-testid="admin-finance-link-subscriptions" onClick={() => navigate('/admin/subscriptions')}>Subscriptions</button>
          <button className="h-9 px-3 rounded-md border text-sm" data-testid="admin-finance-link-ledger" onClick={() => navigate('/admin/ledger')}>Ledger</button>
        </div>
      </div>

      {error ? <div className="border border-red-200 bg-red-50 text-red-700 rounded-md p-3" data-testid="admin-finance-overview-error">{error}</div> : null}

      <div className="grid md:grid-cols-5 gap-3" data-testid="admin-finance-overview-filters">
        <input className="h-9 px-3 rounded-md border bg-background text-sm" value={startDate} onChange={(e) => setStartDate(e.target.value)} type="date" data-testid="admin-finance-filter-start" />
        <input className="h-9 px-3 rounded-md border bg-background text-sm" value={endDate} onChange={(e) => setEndDate(e.target.value)} type="date" data-testid="admin-finance-filter-end" />
        <input className="h-9 px-3 rounded-md border bg-background text-sm" value={country} onChange={(e) => setCountry(e.target.value.toUpperCase())} placeholder="country" data-testid="admin-finance-filter-country" />
        <input className="h-9 px-3 rounded-md border bg-background text-sm" value={currency} onChange={(e) => setCurrency(e.target.value.toUpperCase())} placeholder="currency" data-testid="admin-finance-filter-currency" />
        <button className="h-9 px-3 rounded-md bg-primary text-primary-foreground text-sm" onClick={loadOverview} data-testid="admin-finance-filter-apply">Uygula</button>
      </div>

      {['super_admin', 'country_admin'].includes(user?.role) ? (
        <div className="flex gap-2 flex-wrap" data-testid="admin-finance-overview-export-actions">
          <button className="h-9 px-3 rounded-md border text-sm" onClick={() => exportFinanceCsv('payments')} data-testid="admin-finance-export-payments">Export Payments</button>
          <button className="h-9 px-3 rounded-md border text-sm" onClick={() => exportFinanceCsv('invoices')} data-testid="admin-finance-export-invoices">Export Invoices</button>
          <button className="h-9 px-3 rounded-md border text-sm" onClick={() => exportFinanceCsv('ledger')} data-testid="admin-finance-export-ledger">Export Ledger</button>
        </div>
      ) : null}

      <div className="grid md:grid-cols-2 xl:grid-cols-4 gap-3" data-testid="admin-finance-overview-cards">
        <div className="rounded-lg border p-4" data-testid="admin-finance-card-revenue">
          <div className="text-xs text-muted-foreground">Revenue</div>
          {revenueList.length === 0 ? <div className="text-sm" data-testid="admin-finance-card-revenue-empty">0</div> : revenueList.map(([code, value]) => <div key={code} className="text-sm font-medium" data-testid={`admin-finance-card-revenue-${code.toLowerCase()}`}>{asMoney(value, code)}</div>)}
        </div>
        <div className="rounded-lg border p-4" data-testid="admin-finance-card-mrr">
          <div className="text-xs text-muted-foreground">MRR</div>
          {mrrList.length === 0 ? <div className="text-sm" data-testid="admin-finance-card-mrr-empty">0</div> : mrrList.map(([code, value]) => <div key={code} className="text-sm font-medium" data-testid={`admin-finance-card-mrr-${code.toLowerCase()}`}>{asMoney(value, code)}</div>)}
        </div>
        <div className="rounded-lg border p-4" data-testid="admin-finance-card-failed-rate">
          <div className="text-xs text-muted-foreground">Failed Payment Rate</div>
          <div className="text-xl font-semibold" data-testid="admin-finance-card-failed-rate-value">{Number(data?.cards?.failed_payment_rate || 0).toFixed(2)}%</div>
        </div>
        <div className="rounded-lg border p-4" data-testid="admin-finance-card-refund-rate">
          <div className="text-xs text-muted-foreground">Refund Rate</div>
          <div className="text-xl font-semibold" data-testid="admin-finance-card-refund-rate-value">{Number(data?.cards?.refund_rate || 0).toFixed(2)}%</div>
          <div className="text-xs text-muted-foreground mt-2" data-testid="admin-finance-card-active-subscriptions">Active Subscriptions: {data?.cards?.active_subscription_count || 0}</div>
        </div>
      </div>

      {loading ? <div className="text-sm text-muted-foreground" data-testid="admin-finance-overview-loading">Yükleniyor...</div> : null}
    </div>
  );
}
