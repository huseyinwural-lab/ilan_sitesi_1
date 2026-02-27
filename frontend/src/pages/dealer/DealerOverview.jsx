import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { trackDealerEvent } from '@/lib/dealerAnalytics';
import { useAuth } from '@/contexts/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const safeValue = (value) => {
  const num = Number(value || 0);
  return Number.isFinite(num) ? num : 0;
};

export default function DealerOverview() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [widgets, setWidgets] = useState([]);
  const [dashboardSource, setDashboardSource] = useState('default');
  const [overview, setOverview] = useState(null);

  const applyDashboardConfig = (baseWidgets, configData) => {
    if (!configData || typeof configData !== 'object') {
      return { items: baseWidgets, source: 'default' };
    }

    const hidden = Array.isArray(configData.hidden_widgets) ? new Set(configData.hidden_widgets) : new Set();
    const filtered = baseWidgets.filter((item) => !hidden.has(item.key));
    const order = Array.isArray(configData.widget_order) ? configData.widget_order : [];
    const map = new Map(filtered.map((item) => [item.key, item]));

    const ordered = [];
    order.forEach((key) => {
      const widget = map.get(key);
      if (widget) {
        ordered.push(widget);
        map.delete(key);
      }
    });
    map.forEach((item) => ordered.push(item));

    const minWidgets = Number.parseInt(`${configData.min_widgets ?? 1}`, 10);
    if (!ordered.length || (Number.isFinite(minWidgets) && ordered.length < Math.max(minWidgets, 1))) {
      return { items: baseWidgets, source: 'default' };
    }
    return { items: ordered, source: 'ui_config' };
  };

  const fetchSummary = async () => {
    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`${API}/dealer/dashboard/summary`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(payload?.message || payload?.detail || 'Dashboard summary alınamadı');
      }
      const baseWidgets = Array.isArray(payload?.widgets) ? payload.widgets : [];

      let uiConfig = null;
      try {
        const uiResponse = await fetch(`${API}/ui/dashboard?segment=corporate`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const uiPayload = await uiResponse.json().catch(() => ({}));
        if (uiResponse.ok) {
          uiConfig = uiPayload?.config_data || null;
        }
      } catch (uiError) {
        uiConfig = null;
      }

      const resolved = applyDashboardConfig(baseWidgets, uiConfig);
      setWidgets(resolved.items);
      setDashboardSource(resolved.source);
      setOverview(payload?.overview || null);
    } catch (err) {
      setError(err?.message || 'Dashboard summary alınamadı');
      setWidgets([]);
      setDashboardSource('default');
      setOverview(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  const storePerformance = overview?.store_performance || {};
  const packageSummary = overview?.package_summary || {};
  const kpiCards = overview?.kpi_cards || {};
  const dataNotice = overview?.data_notice || {};
  const visitBreakdown = Array.isArray(storePerformance?.visit_breakdown) ? storePerformance.visit_breakdown : [];
  const userFullName = [user?.first_name, user?.last_name].filter(Boolean).join(' ') || user?.name || user?.email || 'Kurumsal Kullanıcı';

  return (
    <div className="space-y-4" data-testid="dealer-overview-page">
      <div className="flex flex-wrap items-center justify-between gap-3" data-testid="dealer-overview-header">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900" data-testid="dealer-overview-title">Özet</h1>
          <p className="text-sm font-medium text-slate-800" data-testid="dealer-overview-subtitle">{userFullName}</p>
          <div className="text-xs font-medium text-slate-700" data-testid="dealer-overview-source">
            Kaynak: {dashboardSource === 'ui_config' ? 'UI Config' : 'Default'}
          </div>
        </div>
        <div className="flex items-center gap-2" data-testid="dealer-overview-actions">
          <button
            type="button"
            onClick={() => navigate('/dealer/settings')}
            className="h-9 rounded-md border border-slate-300 px-3 text-sm font-semibold text-slate-900"
            data-testid="dealer-overview-edit-page-button"
          >
            Sayfayı Düzenle
          </button>
          <button
            type="button"
            onClick={() => navigate('/dealer/messages')}
            className="h-9 rounded-md border border-slate-300 px-3 text-sm font-semibold text-slate-900"
            data-testid="dealer-overview-announcements-button"
          >
            Duyurular
          </button>
          <button
            type="button"
            onClick={fetchSummary}
            className="h-9 rounded-md border border-slate-300 px-3 text-sm font-semibold text-slate-900"
            data-testid="dealer-overview-refresh-button"
          >
            Yenile
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700" data-testid="dealer-overview-error">
          {error}
        </div>
      )}

      {loading ? (
        <div className="rounded-md border p-4 text-sm text-slate-500" data-testid="dealer-overview-loading">Yükleniyor…</div>
      ) : (
        <div className="space-y-4" data-testid="dealer-overview-content">
          <div className="grid gap-4 xl:grid-cols-3" data-testid="dealer-overview-primary-grid">
            <section className="xl:col-span-2 rounded-xl border border-slate-200 bg-white p-4" data-testid="dealer-overview-store-performance-card">
              <div className="flex items-center justify-between" data-testid="dealer-overview-store-performance-header">
                <h2 className="text-base font-semibold text-slate-900" data-testid="dealer-overview-store-performance-title">Mağaza Performansı</h2>
                <button
                  type="button"
                  onClick={() => navigate('/dealer/reports')}
                  className="rounded-md border border-slate-300 px-3 py-1 text-xs font-semibold text-slate-900"
                  data-testid="dealer-overview-store-performance-detail-button"
                >
                  Raporlara Git
                </button>
              </div>

              <div className="mt-4 grid gap-3 md:grid-cols-2" data-testid="dealer-overview-store-performance-metrics-grid">
                <div className="rounded-lg border border-slate-200 bg-slate-50 p-3" data-testid="dealer-overview-visit-count-24h-card">
                  <div className="text-xs font-semibold text-slate-700" data-testid="dealer-overview-visit-count-24h-label">Ziyaret Sayısı (Son 24 Saat)</div>
                  <div className="mt-1 text-3xl font-semibold text-slate-900" data-testid="dealer-overview-visit-count-24h-value">{safeValue(storePerformance?.visit_count_last_24h)}</div>
                </div>
                <div className="rounded-lg border border-slate-200 bg-slate-50 p-3" data-testid="dealer-overview-visit-count-7d-card">
                  <div className="text-xs font-semibold text-slate-700" data-testid="dealer-overview-visit-count-7d-label">Ziyaret Sayısı (Son 7 Gün)</div>
                  <div className="mt-1 text-3xl font-semibold text-slate-900" data-testid="dealer-overview-visit-count-7d-value">{safeValue(storePerformance?.visit_count_last_7d)}</div>
                </div>
              </div>

              <div className="mt-4 rounded-lg border border-slate-200" data-testid="dealer-overview-visit-breakdown-table">
                <div className="grid grid-cols-[1fr_auto_auto] border-b border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-800" data-testid="dealer-overview-visit-breakdown-header-row">
                  <div data-testid="dealer-overview-visit-breakdown-header-listing">İlan</div>
                  <div className="pr-4" data-testid="dealer-overview-visit-breakdown-header-count">Ziyaret</div>
                  <div data-testid="dealer-overview-visit-breakdown-header-action">Detay</div>
                </div>
                <div className="divide-y divide-slate-100" data-testid="dealer-overview-visit-breakdown-body">
                  {visitBreakdown.map((row) => (
                    <div key={row.listing_id} className="grid grid-cols-[1fr_auto_auto] items-center gap-2 px-3 py-2" data-testid={`dealer-overview-visit-breakdown-row-${row.listing_id}`}>
                      <div className="truncate text-sm font-medium text-slate-900" data-testid={`dealer-overview-visit-breakdown-title-${row.listing_id}`}>{row.title}</div>
                      <div className="pr-4 text-sm font-semibold text-slate-900" data-testid={`dealer-overview-visit-breakdown-count-${row.listing_id}`}>{safeValue(row.visit_count)}</div>
                      <button
                        type="button"
                        onClick={() => navigate(row.route || '/dealer/listings')}
                        className="rounded border border-slate-300 px-2 py-1 text-xs font-semibold text-slate-900"
                        data-testid={`dealer-overview-visit-breakdown-detail-${row.listing_id}`}
                      >
                        Aç
                      </button>
                    </div>
                  ))}
                  {!visitBreakdown.length && (
                    <div className="px-3 py-3 text-xs font-medium text-slate-700" data-testid="dealer-overview-visit-breakdown-empty">
                      İlan ziyaret verisi bulunamadı.
                    </div>
                  )}
                </div>
              </div>
            </section>

            <section className="rounded-xl border border-slate-200 bg-white p-4" data-testid="dealer-overview-package-card">
              <h2 className="text-base font-semibold text-slate-900" data-testid="dealer-overview-package-title">{packageSummary?.name || 'Paket Bilgisi'}</h2>
              <div className="mt-2 text-xs font-semibold text-slate-700" data-testid="dealer-overview-package-status">Durum: {packageSummary?.status || '-'}</div>
              <div className="mt-4 grid gap-2" data-testid="dealer-overview-package-quota-grid">
                <div className="rounded-lg border border-slate-200 bg-slate-50 p-3" data-testid="dealer-overview-package-used-card">
                  <div className="text-xs font-semibold text-slate-700" data-testid="dealer-overview-package-used-label">Kullanılan</div>
                  <div className="text-2xl font-semibold text-slate-900" data-testid="dealer-overview-package-used-value">{safeValue(packageSummary?.listing_quota_used)}</div>
                </div>
                <div className="rounded-lg border border-slate-200 bg-slate-50 p-3" data-testid="dealer-overview-package-remaining-card">
                  <div className="text-xs font-semibold text-slate-700" data-testid="dealer-overview-package-remaining-label">Kalan</div>
                  <div className="text-2xl font-semibold text-slate-900" data-testid="dealer-overview-package-remaining-value">{safeValue(packageSummary?.listing_quota_remaining)}</div>
                </div>
              </div>
              <button
                type="button"
                onClick={() => navigate('/dealer/purchase')}
                className="mt-4 h-9 w-full rounded-md border border-slate-300 text-sm font-semibold text-slate-900"
                data-testid="dealer-overview-package-purchase-button"
              >
                Satın Alma Sayfasına Git
              </button>
            </section>
          </div>

          <div className="grid gap-3 md:grid-cols-3" data-testid="dealer-overview-kpi-card-grid">
            <button
              type="button"
              onClick={() => navigate('/dealer/listings')}
              className="rounded-xl border border-slate-200 bg-white p-4 text-left"
              data-testid="dealer-overview-kpi-published-listings"
            >
              <div className="text-xs font-semibold text-slate-700" data-testid="dealer-overview-kpi-published-listings-label">Yayındaki İlan Sayısı</div>
              <div className="mt-1 text-3xl font-semibold text-slate-900" data-testid="dealer-overview-kpi-published-listings-value">{safeValue(kpiCards?.published_listing_count)}</div>
            </button>
            <button
              type="button"
              onClick={() => navigate('/dealer/customers')}
              className="rounded-xl border border-slate-200 bg-white p-4 text-left"
              data-testid="dealer-overview-kpi-demand-customers"
            >
              <div className="text-xs font-semibold text-slate-700" data-testid="dealer-overview-kpi-demand-customers-label">Talebi Olan Müşteri</div>
              <div className="mt-1 text-3xl font-semibold text-slate-900" data-testid="dealer-overview-kpi-demand-customers-value">{safeValue(kpiCards?.demand_customer_count)}</div>
            </button>
            <button
              type="button"
              onClick={() => navigate('/dealer/customers')}
              className="rounded-xl border border-slate-200 bg-white p-4 text-left"
              data-testid="dealer-overview-kpi-matching-listings"
            >
              <div className="text-xs font-semibold text-slate-700" data-testid="dealer-overview-kpi-matching-listings-label">Müşteriye Uygun İlanlar</div>
              <div className="mt-1 text-3xl font-semibold text-slate-900" data-testid="dealer-overview-kpi-matching-listings-value">{safeValue(kpiCards?.matching_listing_count)}</div>
            </button>
          </div>

          {!dataNotice?.demand_data_available ? (
            <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-medium text-amber-800" data-testid="dealer-overview-data-notice">
              {dataNotice?.message || 'Müşteri veya talep kaydı olmadığı için veri gösterilemiyor.'}
            </div>
          ) : null}

          <section className="rounded-xl border border-slate-200 bg-white p-4" data-testid="dealer-overview-quick-navigation-section">
            <div className="mb-3 text-sm font-semibold text-slate-900" data-testid="dealer-overview-quick-navigation-title">Hızlı Geçiş</div>
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3" data-testid="dealer-overview-widget-grid">
              {widgets.map((widget) => (
                <button
                  key={widget.key}
                  type="button"
                  onClick={() => {
                    trackDealerEvent('dealer_widget_click', {
                      widget_key: widget.key,
                      route: widget.route,
                    });
                    navigate(widget.route);
                  }}
                  className="rounded-xl border border-slate-200 p-4 text-left transition hover:border-slate-300 hover:shadow-sm"
                  data-testid={`dealer-overview-widget-${widget.key}`}
                >
                  <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-700" data-testid={`dealer-overview-widget-title-${widget.key}`}>
                    {widget.title}
                  </div>
                  <div className="mt-2 text-2xl font-semibold text-slate-900" data-testid={`dealer-overview-widget-value-${widget.key}`}>
                    {widget.value}
                  </div>
                  <div className="mt-2 text-xs font-medium text-slate-700" data-testid={`dealer-overview-widget-subtitle-${widget.key}`}>
                    {widget.subtitle}
                  </div>
                </button>
              ))}
              {!widgets.length && (
                <div className="rounded-md border border-slate-200 p-4 text-sm font-medium text-slate-700" data-testid="dealer-overview-widget-empty">
                  Widget bulunamadı.
                </div>
              )}
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
