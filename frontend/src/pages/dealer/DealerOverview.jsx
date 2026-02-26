import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { trackDealerEvent } from '@/lib/dealerAnalytics';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function DealerOverview() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [widgets, setWidgets] = useState([]);

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
      setWidgets(Array.isArray(payload?.widgets) ? payload.widgets : []);
    } catch (err) {
      setError(err?.message || 'Dashboard summary alınamadı');
      setWidgets([]);
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
