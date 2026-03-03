import React, { useEffect, useState } from 'react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function DealerAcademy() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [modules, setModules] = useState([]);
  const [source, setSource] = useState('mocked');

  const fetchAcademy = async () => {
    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API}/dealer/dashboard/navigation-summary`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload?.detail || 'Akademi verisi alınamadı');
      const academy = payload?.academy || {};
      setModules(Array.isArray(academy.modules) ? academy.modules : []);
      setSource(academy.data_source || 'mocked');
    } catch (requestError) {
      setError(requestError?.message || 'Akademi verisi alınamadı');
      setModules([]);
      setSource('mocked');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAcademy();
  }, []);

  return (
    <div className="space-y-4" data-testid="dealer-academy-page">
      <div className="flex flex-wrap items-center justify-between gap-3" data-testid="dealer-academy-header">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900" data-testid="dealer-academy-title">Sahibinden Akademi</h1>
          <p className="text-sm font-medium text-slate-700" data-testid="dealer-academy-subtitle">Kurumsal ekip için hızlı eğitim modülleri ve sertifika yolu.</p>
        </div>
        <button type="button" onClick={fetchAcademy} className="h-9 rounded-md border border-slate-300 px-3 text-sm font-semibold text-slate-900" data-testid="dealer-academy-refresh-button">Yenile</button>
      </div>

      <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-700" data-testid="dealer-academy-source">Veri kaynağı: {source}</div>

      {error ? <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700" data-testid="dealer-academy-error">{error}</div> : null}

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3" data-testid="dealer-academy-grid">
        {loading ? (
          <div className="rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-600" data-testid="dealer-academy-loading">Yükleniyor...</div>
        ) : modules.length === 0 ? (
          <div className="rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-600" data-testid="dealer-academy-empty">Henüz eğitim modülü bulunamadı.</div>
        ) : modules.map((module) => (
          <article key={module.id} className="rounded-xl border border-slate-200 bg-white p-4" data-testid={`dealer-academy-card-${module.id}`}>
            <div className="flex items-center justify-between" data-testid={`dealer-academy-card-header-${module.id}`}>
              <h2 className="text-sm font-semibold text-slate-900" data-testid={`dealer-academy-card-title-${module.id}`}>{module.title}</h2>
              <span className="rounded-full bg-slate-100 px-2 py-1 text-[10px] font-semibold text-slate-600" data-testid={`dealer-academy-card-tag-${module.id}`}>{module.tag || 'Modül'}</span>
            </div>
            <p className="mt-2 text-xs text-slate-600" data-testid={`dealer-academy-card-description-${module.id}`}>{module.description}</p>
            <div className="mt-3 h-2 w-full rounded bg-slate-100" data-testid={`dealer-academy-card-progress-track-${module.id}`}>
              <div className="h-2 rounded bg-slate-900" style={{ width: `${Math.max(0, Math.min(100, Number(module.progress || 0)))}%` }} data-testid={`dealer-academy-card-progress-bar-${module.id}`} />
            </div>
            <div className="mt-2 flex items-center justify-between text-xs text-slate-600" data-testid={`dealer-academy-card-meta-${module.id}`}>
              <span data-testid={`dealer-academy-card-progress-text-${module.id}`}>İlerleme %{module.progress || 0}</span>
              <span data-testid={`dealer-academy-card-duration-${module.id}`}>{module.duration_minutes || 0} dk</span>
            </div>
            <button type="button" className="mt-3 h-8 rounded-md border border-slate-300 px-3 text-xs font-semibold text-slate-900" data-testid={`dealer-academy-card-action-${module.id}`}>Özellikleri Keşfet</button>
          </article>
        ))}
      </div>
    </div>
  );
}
