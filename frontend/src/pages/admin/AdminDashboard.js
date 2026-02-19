import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AdminDashboardPage() {
  const [searchParams] = useSearchParams();
  const urlCountry = (searchParams.get('country') || '').toUpperCase();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const authHeader = useMemo(() => ({
    Authorization: `Bearer ${localStorage.getItem('access_token')}`,
  }), []);

  const fetchSummary = async () => {
    setLoading(true);
    try {
      const qs = urlCountry ? `?country=${urlCountry}` : '';
      const res = await axios.get(`${API}/admin/dashboard/summary${qs}`, { headers: authHeader });
      setData(res.data);
    } catch (e) {
      console.error('Failed to fetch dashboard summary', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [urlCountry]);

  return (
    <div className="space-y-6" data-testid="admin-dashboard-page">
      <div>
        <h1 className="text-2xl font-bold" data-testid="admin-dashboard-title">Genel Bakış</h1>
        <div className="text-xs text-muted-foreground" data-testid="admin-dashboard-context">
          Country: <span className="font-semibold">{urlCountry || 'Global'}</span>
        </div>
      </div>

      {loading ? (
        <div className="p-6 text-center" data-testid="dashboard-loading">Yükleniyor…</div>
      ) : data?.metrics ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-4" data-testid="dashboard-kpis">
          <div className="border rounded-md p-4" data-testid="kpi-total-listings">
            <div className="text-xs text-muted-foreground">Total Listings</div>
            <div className="text-2xl font-bold">{data.metrics.total_listings}</div>
          </div>
          <div className="border rounded-md p-4" data-testid="kpi-published-listings">
            <div className="text-xs text-muted-foreground">Published</div>
            <div className="text-2xl font-bold">{data.metrics.published_listings}</div>
          </div>
          <div className="border rounded-md p-4" data-testid="kpi-pending-moderation">
            <div className="text-xs text-muted-foreground">Pending Moderation</div>
            <div className="text-2xl font-bold">{data.metrics.pending_moderation}</div>
          </div>
          <div className="border rounded-md p-4" data-testid="kpi-active-dealers">
            <div className="text-xs text-muted-foreground">Active Dealers</div>
            <div className="text-2xl font-bold">{data.metrics.active_dealers}</div>
          </div>
          <div className="border rounded-md p-4" data-testid="kpi-revenue-mtd">
            <div className="text-xs text-muted-foreground">Revenue MTD (UTC)</div>
            <div className="text-2xl font-bold">{data.metrics.revenue_mtd}</div>
            <div className="text-xs text-muted-foreground">Month start: {data.metrics.month_start_utc}</div>
          </div>
        </div>
      ) : (
        <div className="p-6 text-center text-muted-foreground" data-testid="dashboard-empty">KPI verisi yok</div>
      )}
    </div>
  );
}
