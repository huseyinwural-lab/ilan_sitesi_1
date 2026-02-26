import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { trackDealerEvent } from '@/lib/dealerAnalytics';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function DealerOverview() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [widgets, setWidgets] = useState([]);
  const [dashboardSource, setDashboardSource] = useState('default');

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
    } catch (err) {
      setError(err?.message || 'Dashboard summary alınamadı');
      setWidgets([]);
      setDashboardSource('default');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  return (
    <div className="space-y-4" data-testid="dealer-overview-page">
      <div className="flex items-center justify-between gap-3" data-testid="dealer-overview-header">
        <div>
          <h1 className="text-2xl font-semibold" data-testid="dealer-overview-title">Kurumsal Dashboard</h1>
          <p className="text-sm text-slate-600" data-testid="dealer-overview-subtitle">Widget tabanlı özet görünüm.</p>
          <div className="text-xs text-slate-500" data-testid="dealer-overview-source">
            Kaynak: {dashboardSource === 'ui_config' ? 'UI Config' : 'Default'}
          </div>
        </div>
        <button
          onClick={fetchSummary}
          className="h-9 rounded-md border px-3 text-sm"
          data-testid="dealer-overview-refresh-button"
        >
          Yenile
        </button>
      </div>

      {error && (
        <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700" data-testid="dealer-overview-error">
          {error}
        </div>
      )}

      {loading ? (
        <div className="rounded-md border p-4 text-sm text-slate-500" data-testid="dealer-overview-loading">Yükleniyor…</div>
      ) : (
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
              className="rounded-xl border p-4 text-left transition hover:border-slate-300 hover:shadow-sm"
              data-testid={`dealer-overview-widget-${widget.key}`}
            >
              <div className="text-xs uppercase tracking-[0.2em] text-slate-500" data-testid={`dealer-overview-widget-title-${widget.key}`}>
                {widget.title}
              </div>
              <div className="mt-2 text-2xl font-semibold" data-testid={`dealer-overview-widget-value-${widget.key}`}>
                {widget.value}
              </div>
              <div className="mt-2 text-xs text-slate-500" data-testid={`dealer-overview-widget-subtitle-${widget.key}`}>
                {widget.subtitle}
              </div>
            </button>
          ))}
          {!widgets.length && (
            <div className="rounded-md border p-4 text-sm text-slate-500" data-testid="dealer-overview-widget-empty">
              Widget bulunamadı.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
