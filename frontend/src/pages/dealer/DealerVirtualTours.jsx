import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const formatDate = (value) => {
  if (!value) return '-';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return '-';
  return parsed.toLocaleString('tr-TR');
};

export default function DealerVirtualTours() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [summary, setSummary] = useState({ total: 0, active: 0, draft: 0 });
  const [items, setItems] = useState([]);

  const fetchTours = async () => {
    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API}/dealer/virtual-tours`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload?.detail || 'Sanal tur verisi alınamadı');
      setSummary(payload?.summary || { total: 0, active: 0, draft: 0 });
      setItems(Array.isArray(payload?.items) ? payload.items : []);
    } catch (requestError) {
      setError(requestError?.message || 'Sanal tur verisi alınamadı');
      setSummary({ total: 0, active: 0, draft: 0 });
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTours();
  }, []);

  const activeRows = useMemo(() => items.filter((item) => item.status === 'active'), [items]);

  return (
    <div className="space-y-4" data-testid="dealer-virtual-tours-page">
      <div className="flex flex-wrap items-center justify-between gap-3" data-testid="dealer-virtual-tours-header">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900" data-testid="dealer-virtual-tours-title">Sanal Turlar</h1>
          <p className="text-sm font-medium text-slate-700" data-testid="dealer-virtual-tours-subtitle">İlan bazlı sanal tur hazırlık durumunu takip edin.</p>
        </div>
        <button type="button" onClick={fetchTours} className="h-9 rounded-md border border-slate-300 px-3 text-sm font-semibold text-slate-900" data-testid="dealer-virtual-tours-refresh-button">Yenile</button>
      </div>

      {error ? <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700" data-testid="dealer-virtual-tours-error">{error}</div> : null}

      <div className="grid gap-3 md:grid-cols-3" data-testid="dealer-virtual-tours-summary-grid">
        <div className="rounded-xl border border-slate-200 bg-white p-4" data-testid="dealer-virtual-tours-summary-total"><div className="text-xs font-semibold text-slate-700">Toplam</div><div className="mt-1 text-3xl font-semibold text-slate-900" data-testid="dealer-virtual-tours-summary-total-value">{summary.total || 0}</div></div>
        <div className="rounded-xl border border-slate-200 bg-white p-4" data-testid="dealer-virtual-tours-summary-active"><div className="text-xs font-semibold text-slate-700">Aktif</div><div className="mt-1 text-3xl font-semibold text-slate-900" data-testid="dealer-virtual-tours-summary-active-value">{summary.active || 0}</div></div>
        <div className="rounded-xl border border-slate-200 bg-white p-4" data-testid="dealer-virtual-tours-summary-draft"><div className="text-xs font-semibold text-slate-700">Taslak</div><div className="mt-1 text-3xl font-semibold text-slate-900" data-testid="dealer-virtual-tours-summary-draft-value">{summary.draft || 0}</div></div>
      </div>

      <div className="rounded-md border border-slate-200 overflow-x-auto" data-testid="dealer-virtual-tours-table-wrap">
        <table className="w-full text-sm" data-testid="dealer-virtual-tours-table">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-3 py-2 text-left text-slate-800">İlan</th>
              <th className="px-3 py-2 text-left text-slate-800">Durum</th>
              <th className="px-3 py-2 text-left text-slate-800">Hazırlık Skoru</th>
              <th className="px-3 py-2 text-left text-slate-800">Güncelleme</th>
              <th className="px-3 py-2 text-right text-slate-800">İşlem</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td className="px-3 py-4 text-slate-600" colSpan={5} data-testid="dealer-virtual-tours-loading">Yükleniyor...</td></tr>
            ) : items.length === 0 ? (
              <tr><td className="px-3 py-4 text-slate-600" colSpan={5} data-testid="dealer-virtual-tours-empty">Sanal tur için uygun kayıt bulunamadı.</td></tr>
            ) : items.map((item) => (
              <tr key={item.tour_id} className="border-t" data-testid={`dealer-virtual-tour-row-${item.tour_id}`}>
                <td className="px-3 py-2 font-medium text-slate-900" data-testid={`dealer-virtual-tour-title-${item.tour_id}`}>{item.listing_title || '-'}</td>
                <td className="px-3 py-2" data-testid={`dealer-virtual-tour-status-${item.tour_id}`}>
                  <span className={`rounded-full border px-2 py-1 text-xs font-semibold ${item.status === 'active' ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-slate-300 bg-slate-100 text-slate-700'}`}>{item.status || '-'}</span>
                </td>
                <td className="px-3 py-2 font-semibold text-slate-900" data-testid={`dealer-virtual-tour-score-${item.tour_id}`}>%{item.readiness_score || 0}</td>
                <td className="px-3 py-2 text-slate-700" data-testid={`dealer-virtual-tour-updated-${item.tour_id}`}>{formatDate(item.last_updated)}</td>
                <td className="px-3 py-2 text-right" data-testid={`dealer-virtual-tour-actions-${item.tour_id}`}>
                  <button type="button" onClick={() => navigate('/dealer/listings')} className="h-8 rounded-md border border-slate-300 px-3 text-xs font-semibold text-slate-900" data-testid={`dealer-virtual-tour-open-${item.tour_id}`}>İlana Git</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-xs text-slate-700" data-testid="dealer-virtual-tours-active-note">Aktif turlar: {activeRows.length}. İlan detaylarında medya kalitesini artırarak skor yükseltebilirsiniz.</div>
    </div>
  );
}
