import React, { useEffect, useState } from 'react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function DealerReports() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [kpis, setKpis] = useState({ views_7d: 0, contact_clicks_7d: 0 });

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`${API}/dealer/reports`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(payload?.detail || 'Rapor verisi alınamadı');
      setKpis(payload?.kpis || { views_7d: 0, contact_clicks_7d: 0 });
    } catch (err) {
      setError(err?.message || 'Rapor verisi alınamadı');
      setKpis({ views_7d: 0, contact_clicks_7d: 0 });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="space-y-4" data-testid="dealer-reports-page">
      <div className="flex items-center justify-between" data-testid="dealer-reports-header">
        <h1 className="text-xl font-semibold" data-testid="dealer-reports-title">Raporlar</h1>
        <button onClick={fetchData} className="h-9 rounded-md border px-3 text-sm" data-testid="dealer-reports-refresh-button">Yenile</button>
      </div>

      {error && <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700" data-testid="dealer-reports-error">{error}</div>}

      {loading ? (
        <div className="rounded-md border p-4 text-sm text-slate-500" data-testid="dealer-reports-loading">Yükleniyor...</div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2" data-testid="dealer-reports-kpi-grid">
          <div className="rounded-xl border p-4" data-testid="dealer-reports-views-card">
            <div className="text-xs uppercase tracking-[0.2em] text-slate-500" data-testid="dealer-reports-views-label">Son 7 Gün Görüntülenme</div>
            <div className="mt-2 text-3xl font-semibold" data-testid="dealer-reports-views-value">{kpis.views_7d || 0}</div>
          </div>
          <div className="rounded-xl border p-4" data-testid="dealer-reports-contact-card">
            <div className="text-xs uppercase tracking-[0.2em] text-slate-500" data-testid="dealer-reports-contact-label">Lead/İletişim Tıklaması</div>
            <div className="mt-2 text-3xl font-semibold" data-testid="dealer-reports-contact-value">{kpis.contact_clicks_7d || 0}</div>
          </div>
        </div>
      )}
    </div>
  );
}
