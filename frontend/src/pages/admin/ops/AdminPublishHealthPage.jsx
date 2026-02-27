import React, { useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const channelLabels = {
  slack: 'Slack',
  smtp: 'SMTP',
  pd: 'PagerDuty',
};

const getReliabilityTone = (rate) => {
  const numeric = Number(rate || 0);
  if (numeric >= 99) {
    return {
      badgeClass: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      status: 'normal',
      textClass: 'text-emerald-700',
    };
  }
  if (numeric >= 95) {
    return {
      badgeClass: 'bg-amber-50 text-amber-700 border-amber-200',
      status: 'warning',
      textClass: 'text-amber-700',
    };
  }
  return {
    badgeClass: 'bg-rose-50 text-rose-700 border-rose-200',
    status: 'critical',
    textClass: 'text-rose-700',
  };
};

const formatDateTime = (value) => {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '-';
  return date.toLocaleString('tr-TR');
};

export default function AdminPublishHealthPage() {
  const authHeader = useMemo(() => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` }), []);

  const [publishHealth, setPublishHealth] = useState(null);
  const [alertMetrics, setAlertMetrics] = useState(null);
  const [lastSimulation, setLastSimulation] = useState(null);

  const [loadingPublishHealth, setLoadingPublishHealth] = useState(false);
  const [loadingAlertMetrics, setLoadingAlertMetrics] = useState(false);
  const [runningSimulation, setRunningSimulation] = useState(false);

  const [publishHealthError, setPublishHealthError] = useState('');
  const [alertMetricsError, setAlertMetricsError] = useState('');
  const [simulationError, setSimulationError] = useState('');
  const [retryAfterSeconds, setRetryAfterSeconds] = useState(0);
  const [secretChecklist, setSecretChecklist] = useState(null);
  const [channelSelection, setChannelSelection] = useState(['smtp']);

  const loadPublishHealth = async () => {
    setLoadingPublishHealth(true);
    setPublishHealthError('');
    try {
      const response = await fetch(
        `${API}/admin/ui/configs/dashboard/publish-audits?segment=corporate&scope=system&limit=25`,
        { headers: authHeader },
      );
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload?.detail?.message || payload?.detail || 'Publish health verisi alınamadı');
      }
      setPublishHealth(payload);
    } catch (error) {
      setPublishHealthError(error.message || 'Publish health verisi alınamadı');
      setPublishHealth(null);
    } finally {
      setLoadingPublishHealth(false);
    }
  };

  const loadAlertDeliveryMetrics = async () => {
    setLoadingAlertMetrics(true);
    setAlertMetricsError('');
    try {
      const response = await fetch(`${API}/admin/ops/alert-delivery-metrics?window=24h`, { headers: authHeader });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload?.detail?.message || payload?.detail || 'Alert delivery metrikleri alınamadı');
      }
      setAlertMetrics(payload);
    } catch (error) {
      setAlertMetricsError(error.message || 'Alert delivery metrikleri alınamadı');
      setAlertMetrics(null);
    } finally {
      setLoadingAlertMetrics(false);
    }
  };

  const loadSecretChecklist = async () => {
    try {
      const response = await fetch(`${API}/admin/ui/configs/dashboard/ops-alerts/secret-checklist`, { headers: authHeader });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload?.detail?.message || payload?.detail || 'Secret checklist alınamadı');
      }
      setSecretChecklist(payload);
    } catch (_error) {
      setSecretChecklist(null);
    }
  };

  const rerunAlertSimulation = async (channels = ['smtp', 'slack', 'pagerduty']) => {
    setRunningSimulation(true);
    setSimulationError('');
    try {
      const response = await fetch(`${API}/admin/ops/alert-delivery/rerun-simulation`, {
        method: 'POST',
        headers: {
          ...authHeader,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ config_type: 'dashboard', channels }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        if (response.status === 429) {
          const waitSeconds = Number(payload?.detail?.retry_after_seconds || 60);
          setRetryAfterSeconds(waitSeconds);
          throw new Error(payload?.detail?.message || `Rate limit aktif. ${waitSeconds}s sonra tekrar deneyin.`);
        }
        throw new Error(payload?.detail?.message || payload?.detail || 'Simülasyon yeniden çalıştırılamadı');
      }
      setLastSimulation(payload);
      toast.success('Alert simulation yeniden çalıştırıldı');
      await loadAlertDeliveryMetrics();
    } catch (error) {
      setSimulationError(error.message || 'Simülasyon yeniden çalıştırılamadı');
      toast.error(error.message || 'Simülasyon yeniden çalıştırılamadı');
    } finally {
      setRunningSimulation(false);
    }
  };

  useEffect(() => {
    loadPublishHealth();
    loadAlertDeliveryMetrics();
    loadSecretChecklist();
  }, []);

  useEffect(() => {
    if (retryAfterSeconds <= 0) return undefined;
    const interval = window.setInterval(() => {
      setRetryAfterSeconds((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => window.clearInterval(interval);
  }, [retryAfterSeconds]);

  const successRate = Number(alertMetrics?.success_rate || 0);
  const reliabilityTone = getReliabilityTone(successRate);
  const channelBreakdown = alertMetrics?.channel_breakdown || { slack: null, smtp: null, pd: null };

  const toggleChannel = (channelKey) => {
    setChannelSelection((prev) => {
      const set = new Set(prev);
      if (set.has(channelKey)) set.delete(channelKey);
      else set.add(channelKey);
      if (set.size === 0) return ['smtp'];
      return Array.from(set);
    });
  };

  const openHtmlReport = () => {
    const params = new URLSearchParams({ channels: channelSelection.join(','), window: '24h' });
    const reportUrl = `${API}/admin/ui/configs/dashboard/ops-alerts/html-report?${params.toString()}`;
    window.open(reportUrl, '_blank', 'noopener,noreferrer');
  };

  return (
    <div className="min-w-0 space-y-6" data-testid="ops-publish-health-page">
      <div className="rounded-2xl border border-slate-200 bg-gradient-to-r from-slate-50 via-white to-slate-50 p-6" data-testid="ops-publish-health-header">
        <h1 className="text-3xl font-semibold text-slate-900" data-testid="ops-publish-health-title">Publish Health & Alert Reliability</h1>
        <p className="mt-2 text-sm text-slate-600" data-testid="ops-publish-health-subtitle">
          Publish pipeline telemetrisi ve alarm teslimat güvenilirliği tek ekranda izlenir.
        </p>
      </div>

      <section className="grid gap-4 xl:grid-cols-3" data-testid="ops-alert-reliability-grid">
        <article className="min-w-0 overflow-hidden xl:col-span-2 rounded-2xl border bg-white p-5" data-testid="ops-alert-success-rate-card">
          <div className="flex flex-wrap items-center justify-between gap-3" data-testid="ops-alert-success-rate-card-header">
            <div>
              <div className="text-sm font-semibold text-slate-900" data-testid="ops-alert-success-rate-title">Son 24s Alarm Teslimat Başarı Oranı</div>
              <div className="break-all text-xs text-slate-500" data-testid="ops-alert-success-rate-definition">alert_delivery_success_rate_24s = successful_deliveries / total_attempts</div>
            </div>
            <div className={`rounded-full border px-3 py-1 text-xs font-semibold ${reliabilityTone.badgeClass}`} data-testid="ops-alert-success-rate-status-badge">
              {reliabilityTone.status.toUpperCase()}
            </div>
          </div>

          <div className="mt-4 flex flex-wrap items-end gap-3" data-testid="ops-alert-success-rate-main-values">
            <div className={`text-5xl font-semibold ${reliabilityTone.textClass}`} data-testid="ops-alert-success-rate-value">{successRate.toFixed(2)}%</div>
            <div className="text-xs text-slate-500" data-testid="ops-alert-success-rate-total">
              total={alertMetrics?.total_attempts ?? 0} • success={alertMetrics?.successful_deliveries ?? 0} • fail={alertMetrics?.failed_deliveries ?? 0}
            </div>
          </div>

          {loadingAlertMetrics ? <div className="mt-3 text-xs text-slate-500" data-testid="ops-alert-success-rate-loading">Yükleniyor...</div> : null}
          {alertMetricsError ? <div className="mt-3 text-xs text-rose-600" data-testid="ops-alert-success-rate-error">{alertMetricsError}</div> : null}

          <div className="mt-4 grid gap-2 sm:grid-cols-3" data-testid="ops-alert-channel-breakdown-grid">
            {['slack', 'smtp', 'pd'].map((channelKey) => {
              const bucket = channelBreakdown?.[channelKey] || {};
              const rate = Number(bucket.success_rate || 0);
              const tone = getReliabilityTone(rate);
              return (
                <div key={channelKey} className="rounded-xl border bg-slate-50 p-3" data-testid={`ops-alert-channel-card-${channelKey}`}>
                  <div className="text-xs font-semibold text-slate-700" data-testid={`ops-alert-channel-name-${channelKey}`}>{channelLabels[channelKey]}</div>
                  <div className={`mt-1 text-lg font-semibold ${tone.textClass}`} data-testid={`ops-alert-channel-rate-${channelKey}`}>{rate.toFixed(2)}%</div>
                  <div className="text-[11px] text-slate-500" data-testid={`ops-alert-channel-counts-${channelKey}`}>
                    total={bucket.total_attempts ?? 0} • fail={bucket.failed_deliveries ?? 0}
                  </div>
                </div>
              );
            })}
          </div>

          <div className="mt-3 text-xs text-slate-500" data-testid="ops-alert-last-failure-timestamp">
            Son failure: {formatDateTime(alertMetrics?.last_failure_timestamp)}
          </div>
        </article>

        <article className="min-w-0 overflow-hidden rounded-2xl border bg-white p-5" data-testid="ops-alert-rerun-card">
          <div className="text-sm font-semibold text-slate-900" data-testid="ops-alert-rerun-title">Tek Tık Yeniden Simülasyon</div>
          <div className="mt-1 text-xs text-slate-500" data-testid="ops-alert-rerun-description">
            Sadece Admin/Ops rolü erişebilir. Rate limit: dakikada en fazla 3.
          </div>

          <div className="mt-3 flex flex-wrap gap-2" data-testid="ops-alert-rerun-channel-selection">
            {['smtp', 'slack', 'pagerduty'].map((channelKey) => {
              const active = channelSelection.includes(channelKey);
              return (
                <button
                  key={channelKey}
                  type="button"
                  onClick={() => toggleChannel(channelKey)}
                  className={`h-8 rounded-full border px-3 text-xs font-semibold ${active ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-300 text-slate-700'}`}
                  data-testid={`ops-alert-rerun-channel-toggle-${channelKey}`}
                >
                  {channelKey.toUpperCase()}
                </button>
              );
            })}
          </div>

          <div className="mt-4 flex flex-wrap gap-2" data-testid="ops-alert-rerun-actions">
            <button
              type="button"
              onClick={() => rerunAlertSimulation(channelSelection)}
              disabled={runningSimulation || retryAfterSeconds > 0}
              className="h-10 rounded-md bg-slate-900 px-4 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
              title={retryAfterSeconds > 0 ? `Rate limit aktif. ${retryAfterSeconds}s sonra tekrar deneyin.` : 'Re-run Alert Simulation'}
              data-testid="ops-alert-rerun-button"
            >
              {runningSimulation ? 'Çalıştırılıyor...' : 'Re-run Alert Simulation'}
            </button>
            <button
              type="button"
              onClick={loadAlertDeliveryMetrics}
              className="h-10 rounded-md border px-4 text-sm"
              data-testid="ops-alert-metrics-refresh-button"
            >
              KPI Yenile
            </button>
            <button
              type="button"
              onClick={openHtmlReport}
              className="h-10 rounded-md border border-slate-300 px-4 text-sm font-medium text-slate-800"
              data-testid="ops-alert-open-html-report-button"
            >
              HTML Rapor Aç
            </button>
          </div>

          {retryAfterSeconds > 0 ? (
            <div className="mt-3 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700" data-testid="ops-alert-rerun-rate-limit-warning">
              Retry disabled: {retryAfterSeconds}s
            </div>
          ) : null}

          {simulationError ? <div className="mt-3 text-xs text-rose-600" data-testid="ops-alert-rerun-error">{simulationError}</div> : null}
          {lastSimulation ? (
            <div className="mt-3 rounded-md border bg-slate-50 p-3" data-testid="ops-alert-rerun-result-card">
              <div className="break-all text-xs text-slate-700" data-testid="ops-alert-rerun-result-correlation">correlation_id: {lastSimulation.correlation_id}</div>
              <div className="text-xs text-slate-700" data-testid="ops-alert-rerun-result-delivery-status">delivery_status: {lastSimulation.delivery_status}</div>
              <div className="text-xs text-slate-700" data-testid="ops-alert-rerun-result-channels">channels: {(lastSimulation.channels_requested || []).join(', ') || '-'}</div>
              <div className="mt-2 space-y-2" data-testid="ops-alert-rerun-channel-results">
                {Object.keys(lastSimulation.channel_results || {}).length === 0 ? (
                  <div className="text-[11px] text-slate-500" data-testid="ops-alert-rerun-channel-results-empty">
                    Kanal sonucu yok (muhtemel neden: Missing Secrets)
                  </div>
                ) : Object.entries(lastSimulation.channel_results || {}).map(([channel, detail]) => (
                  <div key={channel} className="rounded border bg-white px-2 py-2 text-[11px]" data-testid={`ops-alert-rerun-channel-result-${channel}`}>
                    <div data-testid={`ops-alert-rerun-channel-result-status-${channel}`}>
                      {channel}: {detail.delivery_status}
                    </div>
                    <div className="break-all text-slate-500" data-testid={`ops-alert-rerun-channel-result-provider-${channel}`}>
                      provider_code={detail.provider_code ?? detail.smtp_response_code ?? '-'}
                    </div>
                    <div className="break-all text-slate-500" data-testid={`ops-alert-rerun-channel-result-failure-${channel}`}>
                      failure_reason={detail.last_failure_classification || '-'}
                    </div>
                  </div>
                ))}
              </div>
              {lastSimulation.fail_fast?.missing_keys?.length ? (
                <div className="mt-2 break-all text-[11px] text-amber-700" data-testid="ops-alert-rerun-fail-fast-missing-keys">
                  Missing keys: {lastSimulation.fail_fast.missing_keys.join(', ')}
                </div>
              ) : null}
            </div>
          ) : null}

          {secretChecklist?.channels ? (
            <div className="mt-3 rounded-md border bg-slate-50 p-3" data-testid="ops-alert-secret-checklist-card">
              <div className="text-xs font-semibold text-slate-800" data-testid="ops-alert-secret-checklist-title">Secret Checklist</div>
              <div className="mt-2 space-y-1 text-[11px] text-slate-600" data-testid="ops-alert-secret-checklist-items">
                {channelSelection.map((channelKey) => {
                  const data = secretChecklist.channels?.[channelKey];
                  const keys = Array.isArray(data?.required_secrets) ? data.required_secrets : [];
                  return (
                    <div key={channelKey} data-testid={`ops-alert-secret-checklist-item-${channelKey}`}>
                      {channelKey}: {keys.join(', ') || '-'}
                    </div>
                  );
                })}
              </div>
            </div>
          ) : null}
        </article>
      </section>

      <section className="rounded-2xl border bg-white p-5" data-testid="ops-publish-health-summary-card">
        <div className="flex flex-wrap items-center justify-between gap-2" data-testid="ops-publish-health-summary-header">
          <div>
            <div className="text-sm font-semibold text-slate-900" data-testid="ops-publish-health-summary-title">Publish Health Özeti</div>
            <div className="text-xs text-slate-500" data-testid="ops-publish-health-summary-subtitle">Conflict, lock wait ve publish başarı KPI görünümü</div>
          </div>
          <button
            type="button"
            onClick={loadPublishHealth}
            className="h-9 rounded-md border px-3 text-xs"
            data-testid="ops-publish-health-refresh-button"
          >
            Publish KPI Yenile
          </button>
        </div>

        {loadingPublishHealth ? <div className="mt-3 text-xs text-slate-500" data-testid="ops-publish-health-loading">Yükleniyor...</div> : null}
        {publishHealthError ? <div className="mt-3 text-xs text-rose-600" data-testid="ops-publish-health-error">{publishHealthError}</div> : null}

        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4" data-testid="ops-publish-health-kpi-grid">
          <div className="rounded-xl border bg-slate-50 p-3" data-testid="ops-publish-health-kpi-success-rate">
            <div className="text-[11px] text-slate-500">publish_success_rate</div>
            <div className="text-lg font-semibold text-slate-900">{publishHealth?.kpi?.publish_success_rate ?? 0}%</div>
          </div>
          <div className="rounded-xl border bg-slate-50 p-3" data-testid="ops-publish-health-kpi-conflict-rate">
            <div className="text-[11px] text-slate-500">conflict_rate</div>
            <div className="text-lg font-semibold text-slate-900">{publishHealth?.telemetry?.conflict_rate ?? 0}%</div>
          </div>
          <div className="rounded-xl border bg-slate-50 p-3" data-testid="ops-publish-health-kpi-avg-lock">
            <div className="text-[11px] text-slate-500">avg_lock_wait_ms</div>
            <div className="text-lg font-semibold text-slate-900">{publishHealth?.telemetry?.avg_lock_wait_ms ?? 0}</div>
          </div>
          <div className="rounded-xl border bg-slate-50 p-3" data-testid="ops-publish-health-kpi-p95-duration">
            <div className="text-[11px] text-slate-500">publish_duration_ms_p95</div>
            <div className="text-lg font-semibold text-slate-900">{publishHealth?.telemetry?.publish_duration_ms_p95 ?? 0}</div>
          </div>
        </div>
      </section>
    </div>
  );
}