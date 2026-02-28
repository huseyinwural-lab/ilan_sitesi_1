import { useEffect, useMemo, useState, Suspense, lazy } from 'react';
import axios from 'axios';
import { Link, useSearchParams } from 'react-router-dom';
import { useLanguage } from '../contexts/LanguageContext';
import { useCountry } from '../contexts/CountryContext';
import { useAuth } from '../contexts/AuthContext';
import {
  Users,
  Globe,
  Activity,
  Shield,
  Clock,
  ArrowUpRight,
  ArrowDownRight,
  Server,
  AlertTriangle,
  BarChart3,
  Lock,
  Download,
  Play,
  RefreshCw,
} from 'lucide-react';

const TrendsSection = lazy(() => import('../components/admin/dashboard/TrendsSection'));

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const formatNumber = (value) => {
  if (value === null || value === undefined) return '-';
  return Number(value).toLocaleString('tr-TR');
};

const formatCurrencyTotals = (totals) => {
  if (!totals || Object.keys(totals).length === 0) return '-';
  return Object.entries(totals)
    .map(([currency, amount]) => `${Number(amount).toLocaleString('tr-TR')} ${currency}`)
    .join(' · ');
};

const TREND_PRESETS = [7, 30, 90, 180, 365];
const DEFAULT_TREND_DAYS = 14;

const clampTrendDays = (value) => {
  const parsed = Number(value);
  if (Number.isNaN(parsed)) return DEFAULT_TREND_DAYS;
  return Math.min(365, Math.max(7, parsed));
};

const StatCard = ({ icon: Icon, title, value, subtitle, trend, trendUp, testId }) => (
  <div className="stat-card" data-testid={testId}>
    <div className="flex items-start justify-between">
      <div>
        <p className="text-sm font-medium text-muted-foreground" data-testid={`${testId}-title`}>{title}</p>
        <p className="text-3xl font-bold mt-2 tracking-tight" data-testid={`${testId}-value`}>{value}</p>
        {subtitle && <p className="text-xs text-muted-foreground mt-1" data-testid={`${testId}-subtitle`}>{subtitle}</p>}
      </div>
      <div className="p-2 rounded-md bg-primary/10">
        <Icon className="text-primary" size={20} />
      </div>
    </div>
    {trend && (
      <div className={`flex items-center gap-1 mt-3 text-xs font-medium ${trendUp ? 'text-emerald-600' : 'text-rose-600'}`}>
        {trendUp ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
        {trend}
      </div>
    )}
  </div>
);

const SkeletonCard = ({ testId }) => (
  <div className="stat-card animate-pulse" data-testid={testId}>
    <div className="h-4 w-24 bg-muted rounded" />
    <div className="h-8 w-20 bg-muted rounded mt-3" />
    <div className="h-3 w-32 bg-muted rounded mt-2" />
  </div>
);

const RoleDistribution = ({ data, t }) => {
  const roles = [
    { key: 'super_admin', color: 'bg-blue-500' },
    { key: 'country_admin', color: 'bg-indigo-500' },
    { key: 'moderator', color: 'bg-purple-500' },
    { key: 'support', color: 'bg-amber-500' },
    { key: 'finance', color: 'bg-emerald-500' },
  ];

  const total = Object.values(data).reduce((a, b) => a + b, 0) || 1;

  return (
    <div className="bg-card rounded-md border p-6" data-testid="dashboard-role-distribution">
      <h3 className="font-semibold mb-4">{t('role')} Distribution</h3>
      <div className="space-y-3">
        {roles.map(({ key, color }) => (
          <div key={key} className="flex items-center gap-3">
            <div className={`w-3 h-3 rounded-full ${color}`} />
            <span className="text-sm flex-1">{t(key)}</span>
            <span className="text-sm font-medium" data-testid={`dashboard-role-${key}`}>{data[key] || 0}</span>
            <div className="w-20 h-2 bg-muted rounded-full overflow-hidden">
              <div
                className={`h-full ${color}`}
                style={{ width: `${((data[key] || 0) / total) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const RecentActivity = ({ logs }) => {
  const actionColors = {
    CREATE: 'text-emerald-600 bg-emerald-100 dark:bg-emerald-900/30',
    UPDATE: 'text-blue-600 bg-blue-100 dark:bg-blue-900/30',
    DELETE: 'text-rose-600 bg-rose-100 dark:bg-rose-900/30',
    LOGIN: 'text-indigo-600 bg-indigo-100 dark:bg-indigo-900/30',
    TOGGLE: 'text-amber-600 bg-amber-100 dark:bg-amber-900/30',
    SUSPEND: 'text-orange-600 bg-orange-100 dark:bg-orange-900/30',
    ACTIVATE: 'text-teal-600 bg-teal-100 dark:bg-teal-900/30',
  };

  return (
    <div className="bg-card rounded-md border p-6" data-testid="dashboard-recent-activity">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold">Son Aktivite</h3>
        <Activity size={18} className="text-muted-foreground" />
      </div>
      <div className="space-y-3">
        {logs.length === 0 ? (
          <div className="text-sm text-muted-foreground text-center py-4" data-testid="dashboard-activity-empty">
            Son aktivite bulunamadı.
            <Link to="/admin/audit" className="block mt-2 text-primary font-medium" data-testid="dashboard-activity-cta">
              Denetim Kayıtlarına Git
            </Link>
          </div>
        ) : (
          logs.slice(0, 10).map((log, idx) => (
            <div key={log.id || idx} className="flex items-start gap-3 text-sm" data-testid={`dashboard-activity-row-${idx}`}>
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${actionColors[log.action] || 'bg-muted'}`}>
                {log.action || log.event_type}
              </span>
              <div className="flex-1 min-w-0">
                <p className="truncate">
                  <span className="font-medium">{log.resource_type || '-'}</span>
                  {log.user_email && (
                    <span className="text-muted-foreground"> · {log.user_email}</span>
                  )}
                </p>
                <p className="text-xs text-muted-foreground">
                  {log.created_at ? new Date(log.created_at).toLocaleString() : '-'}
                </p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

const ActivitySummaryCard = ({ summary }) => (
  <div className="bg-card rounded-md border p-6" data-testid="dashboard-activity-summary">
    <div className="flex items-center justify-between mb-4">
      <h3 className="font-semibold">Son 24 Saat İşlem Özeti</h3>
      <Clock size={18} className="text-muted-foreground" />
    </div>
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
      <div>
        <div className="text-muted-foreground">Yeni ilan</div>
        <div className="text-xl font-semibold" data-testid="dashboard-activity-new-listings">{summary?.new_listings || 0}</div>
      </div>
      <div>
        <div className="text-muted-foreground">Yeni kullanıcı</div>
        <div className="text-xl font-semibold" data-testid="dashboard-activity-new-users">{summary?.new_users || 0}</div>
      </div>
      <div>
        <div className="text-muted-foreground">Silinen içerik</div>
        <div className="text-xl font-semibold" data-testid="dashboard-activity-deleted">{summary?.deleted_content || 0}</div>
      </div>
    </div>
  </div>
);

const BatchPublishCard = ({ stats, running, onRunNow, onRefresh }) => {
  const latest = stats?.latest;
  const recent = Array.isArray(stats?.recent_runs) ? stats.recent_runs : [];
  return (
    <div className="bg-card rounded-md border p-6" data-testid="dashboard-batch-publish-card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold">Batch Publish Scheduler</h3>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onRefresh}
            className="rounded border px-2 py-1 text-xs"
            data-testid="dashboard-batch-publish-refresh"
          >
            <RefreshCw size={14} />
          </button>
          <button
            type="button"
            onClick={onRunNow}
            disabled={running}
            className="rounded bg-primary px-3 py-1 text-xs font-semibold text-primary-foreground disabled:opacity-60"
            data-testid="dashboard-batch-publish-run-now"
          >
            <Play size={14} className="inline mr-1" />
            {running ? 'Çalışıyor...' : 'Şimdi Çalıştır'}
          </button>
        </div>
      </div>
      <div className="text-xs text-muted-foreground" data-testid="dashboard-batch-publish-interval">
        Otomatik aralık: {stats?.interval_seconds || 300} sn
      </div>
      <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
        <div data-testid="dashboard-batch-publish-processed"><div className="text-muted-foreground text-xs">İşlenen</div><div className="font-semibold">{latest?.processed ?? 0}</div></div>
        <div data-testid="dashboard-batch-publish-published"><div className="text-muted-foreground text-xs">Yayınlanan</div><div className="font-semibold">{latest?.published ?? 0}</div></div>
        <div data-testid="dashboard-batch-publish-skipped"><div className="text-muted-foreground text-xs">Atlanan</div><div className="font-semibold">{latest?.skipped ?? 0}</div></div>
        <div data-testid="dashboard-batch-publish-errors"><div className="text-muted-foreground text-xs">Hata</div><div className="font-semibold">{latest?.errors ?? 0}</div></div>
      </div>
      <div className="mt-4 space-y-2" data-testid="dashboard-batch-publish-recent-runs">
        {recent.slice(0, 5).map((run, idx) => (
          <div key={`${run.run_at}-${idx}`} className="flex items-center justify-between rounded border px-2 py-1 text-xs" data-testid={`dashboard-batch-publish-run-${idx}`}>
            <span>{run.source === 'manual' ? 'Manuel' : 'Otomatik'} · {run.run_at ? new Date(run.run_at).toLocaleTimeString() : '-'}</span>
            <span>{run.published}/{run.processed}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

const HealthCard = ({ health }) => (
  <div className="bg-card rounded-md border p-6" data-testid="dashboard-health-card">
    <div className="flex items-center justify-between mb-4">
      <h3 className="font-semibold">Sistem Sağlığı</h3>
      <Server size={18} className="text-muted-foreground" />
    </div>
    <div className="space-y-3 text-sm">
      <div className="flex items-center justify-between">
        <span>API status</span>
        <span className={`font-semibold ${health?.api_status === 'ok' ? 'text-emerald-600' : 'text-rose-600'}`} data-testid="dashboard-health-api">
          {health?.api_status || 'unknown'}
        </span>
      </div>
      <div className="flex items-center justify-between">
        <span>DB bağlantı</span>
        <span className={`font-semibold ${health?.db_status === 'ok' ? 'text-emerald-600' : 'text-rose-600'}`} data-testid="dashboard-health-db">
          {health?.db_status || 'unknown'}
        </span>
      </div>
      <div className="flex items-center justify-between">
        <span>API gecikmesi</span>
        <span className="font-semibold" data-testid="dashboard-health-api-latency">
          {health?.api_latency_ms !== null && health?.api_latency_ms !== undefined ? `${health.api_latency_ms} ms` : 'unknown'}
        </span>
      </div>
      <div className="flex items-center justify-between">
        <span>DB yanıt süresi</span>
        <span className="font-semibold" data-testid="dashboard-health-db-latency">
          {health?.db_latency_ms !== null && health?.db_latency_ms !== undefined ? `${health.db_latency_ms} ms` : 'unknown'}
        </span>
      </div>
      <div className="flex items-center justify-between">
        <span>Son deploy</span>
        <span className="font-semibold" data-testid="dashboard-health-deploy">
          {health?.deployed_at || 'unknown'}
        </span>
      </div>
      <div className="flex items-center justify-between">
        <span>Son restart</span>
        <span className="font-semibold" data-testid="dashboard-health-restart">
          {health?.restart_at ? new Date(health.restart_at).toLocaleString() : 'unknown'}
        </span>
      </div>
      <div className="flex items-center justify-between">
        <span>Uptime</span>
        <span className="font-semibold" data-testid="dashboard-health-uptime">
          {health?.uptime_human || 'unknown'}
        </span>
      </div>
    </div>
  </div>
);

const KpiCard = ({ title, subtitle, data, canViewFinance, testId, to }) => (
  <Link
    to={to}
    className="block bg-card rounded-md border p-6 transition-colors hover:bg-muted/30"
    data-testid={`${testId}-link`}
  >
    <div className="flex items-start justify-between mb-4">
      <div>
        <p className="text-xs text-muted-foreground" data-testid={`${testId}-subtitle`}>{subtitle}</p>
        <h3 className="text-lg font-semibold" data-testid={`${testId}-title`}>{title}</h3>
      </div>
      <div className="p-2 rounded-md bg-primary/10">
        <BarChart3 size={18} className="text-primary" />
      </div>
    </div>
    <div className="space-y-3 text-sm">
      <div className="flex items-center justify-between">
        <span>Yeni ilan</span>
        <span className="font-semibold" data-testid={`${testId}-listings`}>{formatNumber(data?.new_listings || 0)}</span>
      </div>
      <div className="flex items-center justify-between">
        <span>Yeni kullanıcı</span>
        <span className="font-semibold" data-testid={`${testId}-users`}>{formatNumber(data?.new_users || 0)}</span>
      </div>
      <div className="flex items-center justify-between">
        <span>Gelir</span>
        {canViewFinance ? (
          <span className="font-semibold" data-testid={`${testId}-revenue`}>{formatNumber(data?.revenue_total || 0)}</span>
        ) : (
          <span className="text-xs text-muted-foreground flex items-center gap-1" data-testid={`${testId}-revenue-locked`}>
            <Lock size={14} /> Yetki yok
          </span>
        )}
      </div>
      {canViewFinance && (
        <div className="text-xs text-muted-foreground" data-testid={`${testId}-revenue-currency`}>
          {formatCurrencyTotals(data?.revenue_currency_totals)}
        </div>
      )}
      <div className="text-xs text-primary font-medium" data-testid={`${testId}-cta`}>
        Detaya git
      </div>
    </div>
  </Link>
);

const RiskPanel = ({ data, canViewFinance }) => {
  const suspicious = data?.suspicious_logins;
  const sla = data?.sla_breaches;
  const pending = data?.pending_payments;

  return (
    <div className="bg-card rounded-md border p-6" data-testid="dashboard-risk-panel">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold">Risk & Alarm Merkezi</h3>
        <AlertTriangle size={18} className="text-muted-foreground" />
      </div>
      <div className="space-y-4 text-sm">
        <div className="border rounded-md p-3" data-testid="risk-multi-ip">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">Çoklu IP girişleri</div>
              <div className="text-xs text-muted-foreground">≥ {suspicious?.threshold || '-'} IP / {suspicious?.window_hours || '-'} saat</div>
            </div>
            <div className="text-lg font-semibold" data-testid="risk-multi-ip-count">{formatNumber(suspicious?.count || 0)}</div>
          </div>
          {suspicious?.items?.length ? (
            <div className="mt-2 space-y-1">
              {suspicious.items.map((item, idx) => (
                <div key={`${item.user_id}-${idx}`} className="text-xs text-muted-foreground" data-testid={`risk-multi-ip-item-${idx}`}>
                  {item.user_email || item.user_id} · {item.ip_count} IP
                </div>
              ))}
            </div>
          ) : (
            <div className="mt-2 text-xs text-muted-foreground" data-testid="risk-multi-ip-empty">Kayıt yok</div>
          )}
        </div>

        <div className="border rounded-md p-3" data-testid="risk-sla">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">Moderasyon SLA ihlali</div>
              <div className="text-xs text-muted-foreground">{'>'} {sla?.threshold || '-'} saat bekleyen ilan</div>
            </div>
            <div className="text-lg font-semibold" data-testid="risk-sla-count">{formatNumber(sla?.count || 0)}</div>
          </div>
          {sla?.items?.length ? (
            <div className="mt-2 space-y-1">
              {sla.items.map((item, idx) => (
                <div key={`${item.listing_id}-${idx}`} className="text-xs text-muted-foreground" data-testid={`risk-sla-item-${idx}`}>
                  {item.listing_id} · {item.country || '-'} · {item.created_at ? new Date(item.created_at).toLocaleDateString() : '-'}
                </div>
              ))}
            </div>
          ) : (
            <div className="mt-2 text-xs text-muted-foreground" data-testid="risk-sla-empty">Kayıt yok</div>
          )}
        </div>

        <div className="border rounded-md p-3" data-testid="risk-payments">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">Bekleyen ödemeler</div>
              <div className="text-xs text-muted-foreground">{'>'} {pending?.threshold_days || '-'} gün geciken faturalar</div>
            </div>
            <div className="text-lg font-semibold" data-testid="risk-payments-count">
              {canViewFinance ? formatNumber(pending?.count || 0) : '-'}
            </div>
          </div>
          {canViewFinance ? (
            <>
              <div className="mt-2 text-xs text-muted-foreground" data-testid="risk-payments-total">
                Toplam: {formatNumber(pending?.total_amount || 0)}
              </div>
              <div className="text-xs text-muted-foreground" data-testid="risk-payments-currency">
                {formatCurrencyTotals(pending?.currency_totals)}
              </div>
            </>
          ) : (
            <div className="mt-2 text-xs text-muted-foreground flex items-center gap-1" data-testid="risk-payments-locked">
              <Lock size={14} /> Finans verisi için yetki gerekiyor
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default function Dashboard({ title = 'Kontrol Paneli' }) {
  const [summary, setSummary] = useState(null);
  const [batchPublishStats, setBatchPublishStats] = useState(null);
  const [runningBatchPublish, setRunningBatchPublish] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [trendDays, setTrendDays] = useState(DEFAULT_TREND_DAYS);
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState('');
  const { t } = useLanguage();
  const { selectedCountry } = useCountry();
  const { user } = useAuth();
  const [searchParams] = useSearchParams();

  const adminMode = useMemo(() => {
    return localStorage.getItem('admin_mode') || (searchParams.get('country') ? 'country' : 'global');
  }, [searchParams]);

  const isCountryMode = adminMode === 'country';
  const urlCountry = searchParams.get('country');
  const effectiveCountry = (urlCountry || selectedCountry || 'DE').toUpperCase();

  useEffect(() => {
    fetchSummary();
  }, [isCountryMode, effectiveCountry, trendDays]);

  const fetchSummary = async () => {
    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('access_token');
      const params = new URLSearchParams();
      if (isCountryMode) {
        params.set('country', effectiveCountry);
      }
      if (trendDays) {
        params.set('trend_days', String(trendDays));
      }
      const qs = params.toString() ? `?${params.toString()}` : '';
      const [summaryResponse, batchResponse] = await Promise.all([
        axios.get(`${API}/admin/dashboard/summary${qs}`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        axios.get(`${API}/admin/listings/batch-publish/stats`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);
      setSummary(summaryResponse.data);
      setBatchPublishStats(batchResponse.data);
    } catch (error) {
      setError('Dashboard verileri yüklenemedi.');
    } finally {
      setLoading(false);
    }
  };

  const handleTrendDaysInput = (value) => {
    setTrendDays(clampTrendDays(value));
  };

  const handleExportPdf = async () => {
    setExportError('');
    setExporting(true);
    try {
      const token = localStorage.getItem('access_token');
      const params = new URLSearchParams();
      if (isCountryMode) {
        params.set('country', effectiveCountry);
      }
      if (trendDays) {
        params.set('trend_days', String(trendDays));
      }
      const qs = params.toString() ? `?${params.toString()}` : '';
      const response = await axios.get(`${API}/admin/dashboard/export/pdf${qs}`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob',
      });
      const disposition = response.headers?.['content-disposition'] || '';
      const match = disposition.match(/filename="([^"]+)"/);
      const fallbackName = `dashboard-${trendDays}d-${new Date().toISOString().slice(0, 10)}.pdf`;
      const filename = match?.[1] || fallbackName;
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      setExportError('PDF dışa aktarma başarısız.');
    } finally {
      setExporting(false);
    }
  };

  const handleRunBatchPublishNow = async () => {
    setRunningBatchPublish(true);
    try {
      const token = localStorage.getItem('access_token');
      await axios.post(`${API}/admin/listings/batch-publish/run`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      });
      await fetchSummary();
    } catch (err) {
      setError('Batch publish çalıştırılamadı.');
    } finally {
      setRunningBatchPublish(false);
    }
  };

  const activeModulesLabel = summary?.active_modules?.items?.join(', ') || '-';
  const activeCountriesLabel = summary?.active_countries?.codes?.join(', ') || '-';
  const canViewFinance = summary?.finance_visible ?? ['finance', 'super_admin'].includes(user?.role);
  const isSuperAdmin = user?.role === 'super_admin';

  if (loading) {
    return (
      <div className="space-y-6" data-testid="dashboard-loading">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <SkeletonCard key={index} testId={`dashboard-skeleton-${index}`} />
          ))}
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="bg-card rounded-md border p-6 animate-pulse h-48" data-testid="dashboard-kpi-skeleton-1" />
          <div className="bg-card rounded-md border p-6 animate-pulse h-48" data-testid="dashboard-kpi-skeleton-2" />
        </div>
        <div className="bg-card rounded-md border p-6 animate-pulse h-64" data-testid="dashboard-trends-skeleton" />
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="bg-card rounded-md border p-6 animate-pulse h-64" data-testid="dashboard-risk-skeleton" />
          <div className="bg-card rounded-md border p-6 animate-pulse h-64" data-testid="dashboard-health-skeleton" />
          <div className="bg-card rounded-md border p-6 animate-pulse h-64" data-testid="dashboard-roles-skeleton" />
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="bg-card rounded-md border p-6 animate-pulse h-64" data-testid="dashboard-activity-skeleton" />
          <div className="bg-card rounded-md border p-6 animate-pulse h-64" data-testid="dashboard-quick-actions-skeleton" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="dashboard">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-gray-900" data-testid="dashboard-title">{title}</h1>
        <div className="text-xs text-muted-foreground" data-testid="dashboard-scope">
          Kapsam: {isCountryMode ? `Country (${effectiveCountry})` : 'Global'}
        </div>
      </div>

      {error && (
        <div className="text-sm text-rose-600 flex items-center gap-2" data-testid="dashboard-error">
          <AlertTriangle size={16} /> {error}
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          icon={Users}
          title={t('total_users')}
          value={summary?.users?.total || 0}
          subtitle={`Aktif ${summary?.users?.active || 0} / Pasif ${summary?.users?.inactive || 0}`}
          testId="dashboard-total-users"
        />
        <StatCard
          icon={Globe}
          title="Aktif Ülkeler"
          value={summary?.active_countries?.count || 0}
          subtitle={activeCountriesLabel}
          testId="dashboard-active-countries"
        />
        <StatCard
          icon={Shield}
          title="Active Modules"
          value={summary?.active_modules?.count || 0}
          subtitle={activeModulesLabel}
          testId="dashboard-active-modules"
        />
        <StatCard
          icon={Activity}
          title="Toplam İlan"
          value={summary?.metrics?.total_listings || 0}
          subtitle={`Yayınlı ${summary?.metrics?.published_listings || 0}`}
          testId="dashboard-total-listings"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2" data-testid="dashboard-kpi-section">
        <KpiCard
          title="Bugün"
          subtitle="Günlük KPI"
          data={summary?.kpis?.today}
          canViewFinance={canViewFinance}
          testId="dashboard-kpi-today"
          to={summary?.kpi_links?.today || '/admin/listings?period=today'}
        />
        <KpiCard
          title="Son 7 Gün"
          subtitle="Haftalık KPI"
          data={summary?.kpis?.last_7_days}
          canViewFinance={canViewFinance}
          testId="dashboard-kpi-week"
          to={summary?.kpi_links?.last_7_days || '/admin/listings?period=last_7_days'}
        />
      </div>

      <div className="flex flex-wrap items-center justify-between gap-4 bg-card rounded-md border p-4" data-testid="dashboard-trend-controls">
        <div>
          <div className="text-xs text-muted-foreground" data-testid="dashboard-trend-controls-label">Trend aralığı (gün)</div>
          <div className="flex flex-wrap items-center gap-2 mt-2">
            {TREND_PRESETS.map((preset) => (
              <button
                key={preset}
                type="button"
                onClick={() => setTrendDays(preset)}
                className={`px-3 py-1 rounded-full text-xs border transition-colors ${trendDays === preset ? 'bg-primary text-primary-foreground border-primary' : 'border-muted text-muted-foreground hover:bg-muted/60'}`}
                data-testid={`dashboard-trend-preset-${preset}`}
              >
                {preset}
              </button>
            ))}
            <div className="flex items-center gap-2">
              <input
                type="number"
                min={7}
                max={365}
                value={trendDays}
                onChange={(e) => handleTrendDaysInput(e.target.value)}
                className="w-24 h-8 rounded-md border bg-background text-xs px-2"
                data-testid="dashboard-trend-days-input"
              />
              <span className="text-xs text-muted-foreground">gün</span>
            </div>
          </div>
        </div>
        {isSuperAdmin && (
          <button
            type="button"
            onClick={handleExportPdf}
            disabled={exporting}
            className="flex items-center gap-2 px-4 py-2 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
            data-testid="dashboard-export-pdf-button"
          >
            <Download size={16} />
            {exporting ? (
              <span data-testid="dashboard-export-pdf-loading">PDF hazırlanıyor...</span>
            ) : (
              'PDF Dışa Aktar'
            )}
          </button>
        )}
      </div>
      {exportError && (
        <div className="text-sm text-rose-600" data-testid="dashboard-export-error">
          {exportError}
        </div>
      )}

      {summary?.trends ? (
        <Suspense
          fallback={
            <div className="bg-card rounded-md border p-6 animate-pulse h-64" data-testid="dashboard-trends-loading" />
          }
        >
          <TrendsSection trends={summary.trends} canViewFinance={canViewFinance} />
        </Suspense>
      ) : (
        <div className="bg-card rounded-md border p-6 text-sm text-muted-foreground" data-testid="dashboard-trends-empty">
          Trend verisi bulunamadı.
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        <RiskPanel data={summary?.risk_panel} canViewFinance={canViewFinance} />
        <HealthCard health={summary?.health} />
        <RoleDistribution data={summary?.role_distribution || {}} t={t} />
      </div>

      <BatchPublishCard
        stats={batchPublishStats}
        running={runningBatchPublish}
        onRunNow={handleRunBatchPublishNow}
        onRefresh={fetchSummary}
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <RecentActivity logs={summary?.recent_activity || []} />
        <ActivitySummaryCard summary={summary?.activity_24h} />
      </div>

      <div className="bg-card rounded-md border p-6" data-testid="dashboard-quick-actions">
        <h3 className="font-semibold mb-4">Quick Actions</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <Link
            to="/admin/admin-users"
            className="flex items-center gap-2 p-3 rounded-md border hover:bg-muted/50 transition-colors"
            data-testid="quick-action-admin-users"
          >
            <Users size={18} className="text-primary" />
            <span className="text-sm font-medium">Admin Kullanıcıları</span>
          </Link>
          <Link
            to="/admin/countries"
            className="flex items-center gap-2 p-3 rounded-md border hover:bg-muted/50 transition-colors"
            data-testid="quick-action-countries"
          >
            <Globe size={18} className="text-primary" />
            <span className="text-sm font-medium">{t('countries')}</span>
          </Link>
          <Link
            to="/admin/audit"
            className="flex items-center gap-2 p-3 rounded-md border hover:bg-muted/50 transition-colors"
            data-testid="quick-action-audit"
          >
            <Clock size={18} className="text-primary" />
            <span className="text-sm font-medium">Denetim Kayıtları</span>
          </Link>
          <Link
            to="/admin/moderation"
            className="flex items-center gap-2 p-3 rounded-md border hover:bg-muted/50 transition-colors"
            data-testid="quick-action-moderation"
          >
            <Shield size={18} className="text-primary" />
            <span className="text-sm font-medium">Moderasyon Kuyruğu</span>
          </Link>
        </div>
      </div>
    </div>
  );
}
