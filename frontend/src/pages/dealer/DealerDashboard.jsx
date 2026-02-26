import React, { useEffect, useMemo, useState } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const COL_SPAN_MAP = {
  1: 'lg:col-span-1',
  2: 'lg:col-span-2',
  3: 'lg:col-span-3',
  4: 'lg:col-span-4',
  5: 'lg:col-span-5',
  6: 'lg:col-span-6',
  7: 'lg:col-span-7',
  8: 'lg:col-span-8',
  9: 'lg:col-span-9',
  10: 'lg:col-span-10',
  11: 'lg:col-span-11',
  12: 'lg:col-span-12',
};

const WIDGET_DEFAULT_WIDTH = {
  kpi: 3,
  chart: 6,
  list: 6,
  package_summary: 3,
  doping_summary: 3,
};

const DEFAULT_DASHBOARD = {
  widgets: [
    { widget_id: 'kpi-1', widget_type: 'kpi', title: 'KPI', enabled: true },
    { widget_id: 'package-summary', widget_type: 'package_summary', title: 'Paket Özeti', enabled: true },
    { widget_id: 'doping-summary', widget_type: 'doping_summary', title: 'Doping Özeti', enabled: true },
    { widget_id: 'chart-main', widget_type: 'chart', title: 'Performans Grafiği', enabled: true },
    { widget_id: 'list-main', widget_type: 'list', title: 'Özet Liste', enabled: true },
  ],
  layout: [
    { widget_id: 'kpi-1', x: 0, y: 0, w: 3, h: 1 },
    { widget_id: 'package-summary', x: 3, y: 0, w: 3, h: 1 },
    { widget_id: 'doping-summary', x: 6, y: 0, w: 3, h: 1 },
    { widget_id: 'chart-main', x: 0, y: 1, w: 6, h: 1 },
    { widget_id: 'list-main', x: 6, y: 1, w: 6, h: 1 },
  ],
  source_scope: 'default',
  source_scope_id: null,
};

const normalizeWidgetType = (type) => {
  const safe = `${type || ''}`.trim().toLowerCase();
  if (safe === 'package-summary') return 'package_summary';
  if (safe === 'doping-summary') return 'doping_summary';
  return safe;
};

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

const DashboardWidgetCard = ({ widget, width, children }) => (
  <div
    className={`col-span-1 ${COL_SPAN_MAP[Math.min(12, Math.max(1, Number(width || 3)))] || 'lg:col-span-3'} rounded-xl border bg-white p-4 shadow-sm`}
    data-testid={`dealer-dashboard-widget-${widget.widget_id}`}
  >
    <div className="mb-2 flex items-center justify-between" data-testid={`dealer-dashboard-widget-header-${widget.widget_id}`}>
      <h3 className="text-sm font-semibold text-slate-900" data-testid={`dealer-dashboard-widget-title-${widget.widget_id}`}>{widget.title}</h3>
      <span className="rounded-full bg-slate-100 px-2 py-1 text-[10px] uppercase text-slate-500" data-testid={`dealer-dashboard-widget-type-${widget.widget_id}`}>
        {widget.widget_type}
      </span>
    </div>
    {children}
  </div>
);

export default function DealerDashboard() {
  const [data, setData] = useState(null);
  const [dashboardConfig, setDashboardConfig] = useState(DEFAULT_DASHBOARD);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const authHeader = useMemo(
    () => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` }),
    []
  );

  const getTenantId = () => {
    const fromStorage = localStorage.getItem('tenant_id') || localStorage.getItem('dealer_tenant_id');
    return `${fromStorage || ''}`.trim();
  };

  const normalizeDashboardConfigPayload = (payload) => {
    const rawWidgets = Array.isArray(payload?.widgets)
      ? payload.widgets
      : Array.isArray(payload?.config_data?.widgets)
        ? payload.config_data.widgets
        : [];
    const rawLayout = Array.isArray(payload?.layout)
      ? payload.layout
      : Array.isArray(payload?.config_data?.layout)
        ? payload.config_data.layout
        : [];

    const widgets = rawWidgets
      .filter((widget) => widget && typeof widget === 'object')
      .map((widget, index) => ({
        widget_id: `${widget.widget_id || widget.id || `widget-${index + 1}`}`,
        widget_type: normalizeWidgetType(widget.widget_type || widget.type || 'list'),
        title: `${widget.title || widget.widget_type || widget.type || 'Widget'}`,
        enabled: widget.enabled !== false,
      }));

    const layout = rawLayout
      .filter((layoutItem) => layoutItem && typeof layoutItem === 'object' && layoutItem.widget_id)
      .map((layoutItem) => ({
        widget_id: `${layoutItem.widget_id}`,
        x: Number(layoutItem.x || 0),
        y: Number(layoutItem.y || 0),
        w: Number(layoutItem.w || WIDGET_DEFAULT_WIDTH[normalizeWidgetType(layoutItem.widget_type)] || 3),
        h: Number(layoutItem.h || 1),
      }));

    if (!widgets.length) {
      return DEFAULT_DASHBOARD;
    }

    return {
      widgets,
      layout,
      source_scope: payload?.source_scope || 'default',
      source_scope_id: payload?.source_scope_id || null,
    };
  };

  const loadMetrics = async () => {
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
      return null;
    }
  };

  const loadDashboardLayout = async () => {
    try {
      const tenantId = getTenantId();
      const tenantQuery = tenantId ? `&tenant_id=${encodeURIComponent(tenantId)}` : '';
      const response = await fetch(`${API}/ui/dashboard?segment=corporate${tenantQuery}`, { headers: authHeader });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload?.detail || 'Dashboard layout okunamadı');
      }
      setDashboardConfig(normalizeDashboardConfigPayload(payload));
    } catch (requestError) {
      setDashboardConfig(DEFAULT_DASHBOARD);
      setError(requestError?.message || 'Dashboard layout okunamadı');
    } finally {
      return null;
    }
  };

  useEffect(() => {
    setLoading(true);
    setError('');
    Promise.all([loadMetrics(), loadDashboardLayout()]).finally(() => setLoading(false));
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
  const layoutMap = new Map((dashboardConfig?.layout || []).map((item) => [item.widget_id, item]));
  const orderedWidgets = [...(dashboardConfig?.widgets || [])]
    .filter((widget) => widget.enabled !== false)
    .sort((a, b) => {
      const layoutA = layoutMap.get(a.widget_id) || { y: 999, x: 999 };
      const layoutB = layoutMap.get(b.widget_id) || { y: 999, x: 999 };
      if (layoutA.y !== layoutB.y) return layoutA.y - layoutB.y;
      return layoutA.x - layoutB.x;
    });

  const renderWidget = (widget) => {
    if (widget.widget_type === 'kpi') {
      return (
        <div className="space-y-2" data-testid={`dealer-dashboard-widget-kpi-content-${widget.widget_id}`}>
          <div className="text-2xl font-semibold text-slate-900" data-testid={`dealer-dashboard-widget-kpi-active-${widget.widget_id}`}>{data?.active_listings ?? 0}</div>
          <div className="text-xs text-slate-500" data-testid={`dealer-dashboard-widget-kpi-total-${widget.widget_id}`}>Toplam İlan: {data?.total_listings ?? 0}</div>
          <div className="text-xs text-slate-500" data-testid={`dealer-dashboard-widget-kpi-quota-${widget.widget_id}`}>Kalan Kota: {quota.remaining}</div>
        </div>
      );
    }

    if (widget.widget_type === 'chart') {
      return (
        <div className="space-y-2" data-testid={`dealer-dashboard-widget-chart-content-${widget.widget_id}`}>
          <div className="h-24 rounded-md bg-gradient-to-r from-slate-100 to-slate-200" data-testid={`dealer-dashboard-widget-chart-placeholder-${widget.widget_id}`} />
          <div className="text-xs text-slate-500" data-testid={`dealer-dashboard-widget-chart-meta-${widget.widget_id}`}>
            Görüntülenme: {data?.views?.gated ? 'N/A' : data?.views?.count ?? 0} • Mesaj: {data?.messages?.gated ? 'N/A' : data?.messages?.count ?? 0}
          </div>
        </div>
      );
    }

    if (widget.widget_type === 'list') {
      return (
        <ul className="space-y-1 text-xs text-slate-600" data-testid={`dealer-dashboard-widget-list-content-${widget.widget_id}`}>
          <li data-testid={`dealer-dashboard-widget-list-item-active-${widget.widget_id}`}>Aktif İlan: {data?.active_listings ?? 0}</li>
          <li data-testid={`dealer-dashboard-widget-list-item-quota-${widget.widget_id}`}>Kota Kullanımı: %{Math.round(quota.utilization || 0)}</li>
          <li data-testid={`dealer-dashboard-widget-list-item-plan-${widget.widget_id}`}>Plan: {subscription.name || 'N/A'}</li>
        </ul>
      );
    }

    if (widget.widget_type === 'package_summary') {
      return (
        <div className="space-y-2" data-testid={`dealer-dashboard-widget-package-content-${widget.widget_id}`}>
          <div className="text-lg font-semibold" data-testid={`dealer-dashboard-widget-package-name-${widget.widget_id}`}>{subscription.name || 'N/A'}</div>
          <div className="text-xs text-slate-500" data-testid={`dealer-dashboard-widget-package-status-${widget.widget_id}`}>Status: {subscription.status || 'gated'}</div>
          <div className="text-xs text-slate-500" data-testid={`dealer-dashboard-widget-package-period-${widget.widget_id}`}>Dönem Sonu: {subscription.current_period_end || '-'}</div>
        </div>
      );
    }

    if (widget.widget_type === 'doping_summary') {
      return (
        <div className="space-y-2" data-testid={`dealer-dashboard-widget-doping-content-${widget.widget_id}`}>
          <div className="text-xs text-slate-500" data-testid={`dealer-dashboard-widget-doping-info-${widget.widget_id}`}>Aktif Doping: {data?.doping?.active ?? 0}</div>
          <div className="text-xs text-slate-500" data-testid={`dealer-dashboard-widget-doping-expiring-${widget.widget_id}`}>Süresi Yaklaşan: {data?.doping?.expiring ?? 0}</div>
          <div className="text-xs text-slate-500" data-testid={`dealer-dashboard-widget-doping-budget-${widget.widget_id}`}>Bütçe: {data?.doping?.budget ?? 0}</div>
        </div>
      );
    }

    return <div className="text-xs text-slate-500" data-testid={`dealer-dashboard-widget-generic-${widget.widget_id}`}>Widget verisi bulunamadı.</div>;
  };

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

      <div className="rounded-xl border bg-white p-3" data-testid="dealer-dashboard-layout-source-card">
        <div className="text-xs text-slate-500" data-testid="dealer-dashboard-layout-source">
          UI Kaynağı: {dashboardConfig?.source_scope || 'default'} / {dashboardConfig?.source_scope_id || 'system'}
        </div>
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

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12" data-testid="dealer-dashboard-grid-render">
        {orderedWidgets.map((widget) => {
          const width = layoutMap.get(widget.widget_id)?.w || WIDGET_DEFAULT_WIDTH[widget.widget_type] || 3;
          return (
            <DashboardWidgetCard key={widget.widget_id} widget={widget} width={width}>
              {renderWidget(widget)}
            </DashboardWidgetCard>
          );
        })}
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4" data-testid="dealer-dashboard-metrics-fallback-row">
        <MetricCard title="Aktif İlan" value={data?.active_listings ?? 0} subtitle={`Toplam ilan: ${data?.total_listings ?? 0}`} testId="dealer-dashboard-active-listings" />
        <MetricCard title="Kota" value={`${quota.remaining} / ${quota.limit}`} subtitle={`Kullanım: %${Math.round(quota.utilization || 0)}`} badge={quota.warning ? 'Uyarı' : null} testId="dealer-dashboard-quota" />
        <MetricCard title="Toplam Görüntülenme" value={data?.views?.gated ? 'N/A' : data?.views?.count ?? 0} subtitle={data?.views?.gated ? 'Gated' : 'SQL analytics'} badge={data?.views?.gated ? 'Gated' : null} testId="dealer-dashboard-views" />
        <MetricCard title="Toplam Mesaj" value={data?.messages?.gated ? 'N/A' : data?.messages?.count ?? 0} subtitle={data?.messages?.gated ? 'Gated' : 'SQL messages'} badge={data?.messages?.gated ? 'Gated' : null} testId="dealer-dashboard-messages" />
      </div>
    </div>
  );
}
