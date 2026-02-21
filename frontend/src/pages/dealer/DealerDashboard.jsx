import React, { useEffect, useMemo, useState } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const MetricCard = ({ title, value, subtitle, badge, testId }) => (
  <div className="rounded-xl border bg-white p-4 shadow-sm" data-testid={testId}>
    <div className="flex items-center justify-between">
      <p className="text-xs uppercase tracking-wide text-slate-500" data-testid={`${testId}-title`}>{title}</p>
      {badge ? (
        <span className="text-[11px] px-2 py-1 rounded-full bg-slate-100 text-slate-600" data-testid={`${testId}-badge`}>{badge}</span>
      ) : null}
    </div>
    <div className="mt-2 text-2xl font-semibold text-slate-900" data-testid={`${testId}-value`}>{value}</div>
    {subtitle ? (
      <p className="mt-1 text-xs text-slate-500" data-testid={`${testId}-subtitle`}>{subtitle}</p>
    ) : null}
  </div>
);

export default function DealerDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const authHeader = useMemo(
    () => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` }),
    []
  );

  const loadMetrics = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API}/dealer/dashboard/metrics`, { headers: authHeader });
      if (!res.ok) {
        throw new Error('Metrikler yüklenemedi');
      }
      const payload = await res.json();
      setData(payload);
    } catch (err) {
      setError(err?.message || 'Metrikler yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMetrics();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (loading) {
    return (
      <div className="text-sm text-slate-500" data-testid="dealer-dashboard-loading">Yükleniyor...</div>
    );
  }

  if (error) {
    return (
      <div className="space-y-3" data-testid="dealer-dashboard-error">
        <p className="text-sm text-rose-600" data-testid="dealer-dashboard-error-message">{error}</p>
        <button
          type="button"
          onClick={loadMetrics}
          className="h-9 px-3 rounded-md border text-sm"
          data-testid="dealer-dashboard-retry"
        >
          Tekrar Dene
        </button>
      </div>
    );
  }

  const quota = data?.quota || { used: 0, limit: 0, remaining: 0, utilization: 0, warning: false };
  const subscription = data?.subscription || { name: 'N/A', status: 'gated', current_period_end: null };

  return (
    <div className="space-y-6" data-testid="dealer-dashboard">
      <div className="flex flex-wrap items-start justify-between gap-3" data-testid="dealer-dashboard-header">
        <div>
          <h1 className="text-2xl font-bold" data-testid="dealer-dashboard-title">Kurumsal Dashboard</h1>
          <p className="text-sm text-slate-500" data-testid="dealer-dashboard-subtitle">
            İlan performansı ve plan durumunu canlı takip edin.
          </p>
        </div>
        <button
          type="button"
          className="h-10 px-4 rounded-md bg-slate-900 text-white text-sm"
          data-testid="dealer-dashboard-upgrade"
        >
          Planı Yükselt
        </button>
      </div>

      {quota.warning ? (
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700" data-testid="dealer-dashboard-quota-warning">
          Kota kullanımınız %80 seviyesini geçti. Lütfen planınızı yükseltin veya ilan arşivleyin.
        </div>
      ) : null}

      {subscription?.warning ? (
        <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700" data-testid="dealer-dashboard-plan-warning">
          Plan süresi yakında doluyor. Yenileme yapmanız önerilir.
        </div>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4" data-testid="dealer-dashboard-metrics">
        <MetricCard
          title="Aktif İlan"
          value={data?.active_listings ?? 0}
          subtitle={`Toplam ilan: ${data?.total_listings ?? 0}`}
          testId="dealer-dashboard-active-listings"
        />
        <MetricCard
          title="Kota"
          value={`${quota.remaining} / ${quota.limit}`}
          subtitle={`Kullanım: %${Math.round(quota.utilization || 0)}`}
          badge={quota.warning ? 'Uyarı' : null}
          testId="dealer-dashboard-quota"
        />
        <MetricCard
          title="Toplam Görüntülenme"
          value={data?.views?.gated ? 'N/A' : data?.views?.count ?? 0}
          subtitle={data?.views?.gated ? 'Gated' : 'SQL analytics'}
          badge={data?.views?.gated ? 'Gated' : null}
          testId="dealer-dashboard-views"
        />
        <MetricCard
          title="Toplam Mesaj"
          value={data?.messages?.gated ? 'N/A' : data?.messages?.count ?? 0}
          subtitle={data?.messages?.gated ? 'Gated' : 'SQL messages'}
          badge={data?.messages?.gated ? 'Gated' : null}
          testId="dealer-dashboard-messages"
        />
      </div>

      <div className="rounded-xl border bg-white p-4" data-testid="dealer-dashboard-plan-card">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-500" data-testid="dealer-dashboard-plan-label">Plan</p>
            <h2 className="text-lg font-semibold" data-testid="dealer-dashboard-plan-name">{subscription.name || 'N/A'}</h2>
            <p className="text-xs text-slate-500" data-testid="dealer-dashboard-plan-status">Status: {subscription.status || 'gated'}</p>
          </div>
          <div className="text-sm text-slate-600" data-testid="dealer-dashboard-plan-period">
            Dönem Sonu: {subscription.current_period_end || '-'}
          </div>
        </div>
      </div>
    </div>
  );
}
