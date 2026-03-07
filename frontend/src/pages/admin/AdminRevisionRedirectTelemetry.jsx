import React, { useCallback, useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const FAILURE_REASON_OPTIONS = [
  '',
  'REVISION_NOT_FOUND',
  'REVISION_NOT_PUBLISHED',
  'TARGET_ROUTE_INVALID',
  'PERMISSION_DENIED',
];

const formatDateTime = (value) => {
  if (!value) return '-';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return '-';
  return parsed.toLocaleString('tr-TR');
};

const formatTrendDate = (value) => {
  if (!value) return '-';
  const parsed = new Date(`${value}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleDateString('tr-TR', { day: '2-digit', month: '2-digit' });
};

const formatPercent = (value) => {
  const safe = Number(value || 0);
  if (!Number.isFinite(safe)) return '0%';
  return `${safe.toFixed(2)}%`;
};

export default function AdminRevisionRedirectTelemetry() {
  const resolveRequestLocale = () => {
    const pathLocale = String(window.location.pathname || '').split('/').filter(Boolean)[0]?.toLowerCase();
    if (['tr', 'de', 'fr'].includes(pathLocale)) return pathLocale;
    const stored = String(localStorage.getItem('language') || '').toLowerCase();
    if (['tr', 'de', 'fr'].includes(stored)) return stored;
    return 'tr';
  };

  const authHeaders = useMemo(() => {
    const locale = resolveRequestLocale();
    const pathLocale = String(window.location.pathname || '').split('/').filter(Boolean)[0]?.toLowerCase();
    return {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`,
      'Accept-Language': locale,
      'X-URL-Locale': ['tr', 'de', 'fr'].includes(pathLocale) ? pathLocale : locale,
    };
  }, []);

  const [rows, setRows] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [failureReasonFilter, setFailureReasonFilter] = useState('');
  const [trendDays, setTrendDays] = useState('14');

  const fetchTelemetry = useCallback(async ({ silent = false } = {}) => {
    setLoading(true);
    if (!silent) setError('');
    try {
      const response = await axios.get(`${API}/admin/revision-redirect-telemetry`, {
        headers: authHeaders,
        params: {
          limit: 50,
          status: statusFilter || undefined,
          failure_reason: failureReasonFilter || undefined,
          trend_days: Number(trendDays) || 14,
        },
      });
      setRows(Array.isArray(response.data?.items) ? response.data.items : []);
      setSummary(response.data?.summary || null);
      setError('');
    } catch (requestError) {
      const message = requestError?.response?.data?.detail || requestError?.message || 'Telemetry verisi alınamadı';
      setRows([]);
      setSummary(null);
      setError(String(message));
      if (!silent) toast.error(String(message));
    } finally {
      setLoading(false);
    }
  }, [authHeaders, statusFilter, failureReasonFilter, trendDays]);

  useEffect(() => {
    fetchTelemetry({ silent: true });
  }, [fetchTelemetry]);

  const durationHistogram = summary?.duration_histogram || {};
  const failureReasonCounts = summary?.failure_reason_counts || {};
  const dailyTrend = Array.isArray(summary?.daily_trend) ? summary.daily_trend : [];
  const maxDailyTrendCount = dailyTrend.reduce((maxValue, item) => {
    const total = Number(item?.total || 0);
    return total > maxValue ? total : maxValue;
  }, 0);
  const slo = summary?.slo || null;

  return (
    <div className="space-y-5" data-testid="admin-revision-redirect-telemetry-page">
      <section className="rounded-xl border bg-white p-4" data-testid="admin-revision-redirect-telemetry-panel">
        <div className="flex flex-wrap items-center justify-between gap-3" data-testid="admin-revision-redirect-telemetry-header">
          <div>
            <h1 className="text-sm font-semibold" data-testid="admin-revision-redirect-telemetry-title">Revision Redirect Telemetry</h1>
            <p className="text-xs text-slate-500" data-testid="admin-revision-redirect-telemetry-subtitle">p95 latency, success/failure rate, failure reason dağılımı ve günlük trend görünümü.</p>
          </div>
          <button
            type="button"
            className="h-9 rounded border px-3 text-xs"
            onClick={() => fetchTelemetry()}
            disabled={loading}
            data-testid="admin-revision-redirect-telemetry-refresh-button"
          >
            Yenile
          </button>
        </div>

        <div className="mt-3 grid grid-cols-1 gap-2 md:grid-cols-4" data-testid="admin-revision-redirect-telemetry-filters">
          <label className="text-xs" data-testid="admin-revision-redirect-telemetry-status-filter-wrap">
            Status
            <select
              className="mt-1 h-9 w-full rounded border px-2"
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value)}
              data-testid="admin-revision-redirect-telemetry-status-filter"
            >
              <option value="">Tümü</option>
              <option value="success">success</option>
              <option value="failed">failed</option>
            </select>
          </label>

          <label className="text-xs" data-testid="admin-revision-redirect-telemetry-failure-filter-wrap">
            Failure reason
            <select
              className="mt-1 h-9 w-full rounded border px-2"
              value={failureReasonFilter}
              onChange={(event) => setFailureReasonFilter(event.target.value)}
              data-testid="admin-revision-redirect-telemetry-failure-filter"
            >
              {FAILURE_REASON_OPTIONS.map((option) => (
                <option key={`failure-option-${option || 'all'}`} value={option}>
                  {option || 'Tümü'}
                </option>
              ))}
            </select>
          </label>

          <label className="text-xs" data-testid="admin-revision-redirect-telemetry-trend-days-filter-wrap">
            Trend gün sayısı
            <select
              className="mt-1 h-9 w-full rounded border px-2"
              value={trendDays}
              onChange={(event) => setTrendDays(event.target.value)}
              data-testid="admin-revision-redirect-telemetry-trend-days-filter"
            >
              <option value="7">7 gün</option>
              <option value="14">14 gün</option>
              <option value="30">30 gün</option>
            </select>
          </label>

          <div className="flex items-end" data-testid="admin-revision-redirect-telemetry-apply-wrap">
            <button
              type="button"
              className="h-9 rounded border px-3 text-xs"
              onClick={() => fetchTelemetry()}
              disabled={loading}
              data-testid="admin-revision-redirect-telemetry-apply-button"
            >
              Filtreyi Uygula
            </button>
          </div>
        </div>

        <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-6" data-testid="admin-revision-redirect-telemetry-summary-cards">
          <article className="rounded border bg-slate-50 p-3" data-testid="admin-revision-redirect-telemetry-summary-total">
            <p className="text-[11px] text-slate-500">total</p>
            <p className="text-lg font-semibold" data-testid="admin-revision-redirect-telemetry-summary-total-value">{Number(summary?.total || 0)}</p>
          </article>
          <article className="rounded border bg-emerald-50 p-3" data-testid="admin-revision-redirect-telemetry-summary-success">
            <p className="text-[11px] text-emerald-700">success</p>
            <p className="text-lg font-semibold text-emerald-700" data-testid="admin-revision-redirect-telemetry-summary-success-value">{Number(summary?.success || 0)}</p>
          </article>
          <article className="rounded border bg-rose-50 p-3" data-testid="admin-revision-redirect-telemetry-summary-failed">
            <p className="text-[11px] text-rose-700">failed</p>
            <p className="text-lg font-semibold text-rose-700" data-testid="admin-revision-redirect-telemetry-summary-failed-value">{Number(summary?.failed || 0)}</p>
          </article>
          <article className="rounded border bg-slate-50 p-3" data-testid="admin-revision-redirect-telemetry-summary-duration">
            <p className="text-[11px] text-slate-500">avg / p95 (ms)</p>
            <p className="text-lg font-semibold" data-testid="admin-revision-redirect-telemetry-summary-duration-value">{Number(summary?.avg_duration_ms || 0)} / {Number(summary?.p95_duration_ms || 0)}</p>
          </article>
          <article className="rounded border bg-emerald-50 p-3" data-testid="admin-revision-redirect-telemetry-summary-success-rate">
            <p className="text-[11px] text-emerald-700">success rate</p>
            <p className="text-lg font-semibold text-emerald-700" data-testid="admin-revision-redirect-telemetry-summary-success-rate-value">{formatPercent(summary?.success_rate_pct)}</p>
          </article>
          <article className="rounded border bg-rose-50 p-3" data-testid="admin-revision-redirect-telemetry-summary-failure-rate">
            <p className="text-[11px] text-rose-700">failure rate</p>
            <p className="text-lg font-semibold text-rose-700" data-testid="admin-revision-redirect-telemetry-summary-failure-rate-value">{formatPercent(summary?.failure_rate_pct)}</p>
          </article>
        </div>

        <div className="mt-3 rounded border bg-slate-50 p-3" data-testid="admin-revision-redirect-telemetry-slo-wrap">
          <div className="flex flex-wrap items-center justify-between gap-2" data-testid="admin-revision-redirect-telemetry-slo-header">
            <p className="text-xs font-semibold" data-testid="admin-revision-redirect-telemetry-slo-title">SLO durumu</p>
            <span
              className={`rounded-full px-2 py-1 text-[11px] font-semibold ${slo?.status?.p95_latency_ok && slo?.status?.failure_rate_ok ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}`}
              data-testid="admin-revision-redirect-telemetry-slo-badge"
            >
              {slo?.status?.p95_latency_ok && slo?.status?.failure_rate_ok ? 'SLO OK' : 'SLO İhlali'}
            </span>
          </div>
          <div className="mt-2 grid grid-cols-1 gap-2 md:grid-cols-2" data-testid="admin-revision-redirect-telemetry-slo-grid">
            <div className="rounded border bg-white px-3 py-2" data-testid="admin-revision-redirect-telemetry-slo-latency-item">
              <p className="text-[11px] text-slate-500">p95 hedef</p>
              <p className="text-sm font-semibold" data-testid="admin-revision-redirect-telemetry-slo-latency-value">
                {Number(slo?.current?.p95_duration_ms || 0)} / {Number(slo?.targets?.p95_latency_ms || 0)} ms
              </p>
            </div>
            <div className="rounded border bg-white px-3 py-2" data-testid="admin-revision-redirect-telemetry-slo-failure-rate-item">
              <p className="text-[11px] text-slate-500">failure rate hedef</p>
              <p className="text-sm font-semibold" data-testid="admin-revision-redirect-telemetry-slo-failure-rate-value">
                {formatPercent(slo?.current?.failure_rate_pct)} / {formatPercent(slo?.targets?.failure_rate_pct)}
              </p>
            </div>
          </div>
        </div>

        <div className="mt-3 rounded border bg-slate-50 p-3" data-testid="admin-revision-redirect-telemetry-histogram-wrap">
          <p className="text-xs font-semibold" data-testid="admin-revision-redirect-telemetry-histogram-title">Redirect duration histogram</p>
          <div className="mt-2 grid grid-cols-1 gap-2 md:grid-cols-5" data-testid="admin-revision-redirect-telemetry-histogram-grid">
            {['0_250', '251_500', '501_1000', '1001_2000', '2001_plus'].map((bucketKey) => (
              <div key={`bucket-${bucketKey}`} className="rounded border bg-white px-2 py-2" data-testid={`admin-revision-redirect-telemetry-histogram-${bucketKey}`}>
                <p className="text-[11px] text-slate-500">{bucketKey}</p>
                <p className="text-base font-semibold">{Number(durationHistogram[bucketKey] || 0)}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-3 rounded border bg-slate-50 p-3" data-testid="admin-revision-redirect-telemetry-failure-reasons-wrap">
          <p className="text-xs font-semibold" data-testid="admin-revision-redirect-telemetry-failure-reasons-title">Failure reason distribution</p>
          {Object.keys(failureReasonCounts).length === 0 ? (
            <p className="mt-2 text-xs text-slate-500" data-testid="admin-revision-redirect-telemetry-failure-reasons-empty">Kayıt yok</p>
          ) : (
            <div className="mt-2 grid grid-cols-1 gap-2 md:grid-cols-2" data-testid="admin-revision-redirect-telemetry-failure-reasons-grid">
              {Object.entries(failureReasonCounts)
                .sort((a, b) => Number(b[1]) - Number(a[1]))
                .map(([reason, count]) => (
                  <div key={`reason-${reason}`} className="rounded border bg-white px-2 py-2" data-testid={`admin-revision-redirect-telemetry-failure-reason-${reason.toLowerCase()}`}>
                    <p className="text-[11px] text-slate-500">{reason}</p>
                    <p className="text-base font-semibold">{Number(count || 0)}</p>
                  </div>
                ))}
            </div>
          )}
        </div>

        <div className="mt-3 rounded border bg-slate-50 p-3" data-testid="admin-revision-redirect-telemetry-trend-wrap">
          <p className="text-xs font-semibold" data-testid="admin-revision-redirect-telemetry-trend-title">Günlük redirect event trendi</p>
          <div className="mt-2 space-y-2" data-testid="admin-revision-redirect-telemetry-trend-list">
            {dailyTrend.map((item, index) => {
              const total = Number(item?.total || 0);
              const success = Number(item?.success || 0);
              const failed = Number(item?.failed || 0);
              const totalWidth = maxDailyTrendCount > 0 ? Math.max((total / maxDailyTrendCount) * 100, total > 0 ? 6 : 0) : 0;
              const successWidth = total > 0 ? (success / total) * 100 : 0;
              const failedWidth = total > 0 ? (failed / total) * 100 : 0;

              return (
                <div className="rounded border bg-white px-2 py-2" key={`trend-${item?.date || index}`} data-testid={`admin-revision-redirect-telemetry-trend-item-${index}`}>
                  <div className="flex flex-wrap items-center justify-between gap-2" data-testid={`admin-revision-redirect-telemetry-trend-meta-${index}`}>
                    <span className="text-[11px] text-slate-500" data-testid={`admin-revision-redirect-telemetry-trend-date-${index}`}>{formatTrendDate(item?.date)}</span>
                    <span className="text-[11px] text-slate-500" data-testid={`admin-revision-redirect-telemetry-trend-counts-${index}`}>toplam {total} · success {success} · failed {failed}</span>
                  </div>
                  <div className="mt-1 h-2 w-full rounded bg-slate-200" data-testid={`admin-revision-redirect-telemetry-trend-total-track-${index}`}>
                    <div className="h-full rounded bg-slate-400" style={{ width: `${totalWidth}%` }} data-testid={`admin-revision-redirect-telemetry-trend-total-bar-${index}`} />
                  </div>
                  <div className="mt-1 flex h-2 w-full overflow-hidden rounded bg-slate-200" data-testid={`admin-revision-redirect-telemetry-trend-status-track-${index}`}>
                    <div className="bg-emerald-500" style={{ width: `${successWidth}%` }} data-testid={`admin-revision-redirect-telemetry-trend-success-bar-${index}`} />
                    <div className="bg-rose-500" style={{ width: `${failedWidth}%` }} data-testid={`admin-revision-redirect-telemetry-trend-failed-bar-${index}`} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="mt-3 overflow-x-auto" data-testid="admin-revision-redirect-telemetry-table-wrap">
          <table className="min-w-full text-left text-xs" data-testid="admin-revision-redirect-telemetry-table">
            <thead>
              <tr className="border-b bg-slate-50" data-testid="admin-revision-redirect-telemetry-head-row">
                <th className="px-2 py-2">timestamp</th>
                <th className="px-2 py-2">revision_id</th>
                <th className="px-2 py-2">status</th>
                <th className="px-2 py-2">failure_reason</th>
                <th className="px-2 py-2">duration(ms)</th>
                <th className="px-2 py-2">redirect_target</th>
              </tr>
            </thead>
            <tbody data-testid="admin-revision-redirect-telemetry-table-body">
              {loading ? (
                <tr data-testid="admin-revision-redirect-telemetry-loading-row">
                  <td className="px-2 py-3 text-slate-500" colSpan={6}>Yükleniyor...</td>
                </tr>
              ) : rows.length === 0 ? (
                <tr data-testid="admin-revision-redirect-telemetry-empty-row">
                  <td className="px-2 py-3 text-slate-500" colSpan={6}>Kayıt bulunamadı.</td>
                </tr>
              ) : rows.map((row, index) => (
                <tr key={`redirect-row-${row.id || index}`} className="border-b" data-testid={`admin-revision-redirect-telemetry-row-${index}`}>
                  <td className="px-2 py-2" data-testid={`admin-revision-redirect-telemetry-timestamp-${index}`}>{formatDateTime(row.timestamp)}</td>
                  <td className="px-2 py-2 font-mono text-[11px]" data-testid={`admin-revision-redirect-telemetry-revision-${index}`}>{row.revision_id || '-'}</td>
                  <td className="px-2 py-2" data-testid={`admin-revision-redirect-telemetry-status-${index}`}>{row.status || '-'}</td>
                  <td className="px-2 py-2" data-testid={`admin-revision-redirect-telemetry-reason-${index}`}>{row.failure_reason || '-'}</td>
                  <td className="px-2 py-2" data-testid={`admin-revision-redirect-telemetry-duration-${index}`}>{row.redirect_duration_ms ?? '-'}</td>
                  <td className="px-2 py-2" data-testid={`admin-revision-redirect-telemetry-target-${index}`}>{row.redirect_target || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {error ? (
          <p className="mt-2 text-xs text-rose-700" data-testid="admin-revision-redirect-telemetry-error-message">{error}</p>
        ) : null}
      </section>
    </div>
  );
}
