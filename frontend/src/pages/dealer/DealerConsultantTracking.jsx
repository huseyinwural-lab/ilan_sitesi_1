import React, { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const formatDate = (value) => {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '-';
  return date.toLocaleString('tr-TR');
};

export default function DealerConsultantTracking() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [consultants, setConsultants] = useState([]);
  const [evaluations, setEvaluations] = useState([]);
  const [summary, setSummary] = useState({ consultants_count: 0, evaluations_count: 0 });

  const [sortBy, setSortBy] = useState('rating_desc');
  const [query, setQuery] = useState('');

  const activeTab = useMemo(() => {
    const tab = searchParams.get('tab');
    return tab === 'evaluations' ? 'evaluations' : 'overview';
  }, [searchParams]);

  const selectedConsultant = searchParams.get('consultant') || '';

  const fetchData = async (nextSortBy = sortBy) => {
    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`${API}/dealer/consultant-tracking?sort_by=${nextSortBy}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(payload?.detail || 'Danışman verisi alınamadı');
      setConsultants(Array.isArray(payload?.consultants) ? payload.consultants : []);
      setEvaluations(Array.isArray(payload?.evaluations) ? payload.evaluations : []);
      setSummary(payload?.summary || { consultants_count: 0, evaluations_count: 0 });
    } catch (err) {
      setError(err?.message || 'Danışman verisi alınamadı');
      setConsultants([]);
      setEvaluations([]);
      setSummary({ consultants_count: 0, evaluations_count: 0 });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const filteredConsultants = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return consultants;
    return consultants.filter((item) => `${item.full_name || ''} ${item.email || ''}`.toLowerCase().includes(q));
  }, [consultants, query]);

  const filteredEvaluations = useMemo(() => {
    const q = query.trim().toLowerCase();
    return evaluations.filter((item) => {
      const consultantMatch = selectedConsultant ? item.consultant_id === selectedConsultant : true;
      if (!consultantMatch) return false;
      if (!q) return true;
      return `${item.username || ''} ${item.comment || ''} ${item.consultant_name || ''}`.toLowerCase().includes(q);
    });
  }, [evaluations, query, selectedConsultant]);

  const setTab = (tabKey) => {
    const next = new URLSearchParams(searchParams);
    next.set('tab', tabKey);
    setSearchParams(next);
  };

  const openConsultantDetail = (consultantId) => {
    const next = new URLSearchParams(searchParams);
    next.set('tab', 'evaluations');
    next.set('consultant', consultantId);
    setSearchParams(next);
  };

  return (
    <div className="space-y-4" data-testid="dealer-consultant-tracking-page">
      <div className="flex flex-wrap items-center justify-between gap-3" data-testid="dealer-consultant-tracking-header">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900" data-testid="dealer-consultant-tracking-title">Danışman Takibi</h1>
          <p className="text-sm font-medium text-slate-700" data-testid="dealer-consultant-tracking-subtitle">
            Danışman performansı ve hizmet değerlendirmeleri.
          </p>
        </div>
        <button
          type="button"
          onClick={() => fetchData(sortBy)}
          className="h-9 rounded-md border border-slate-300 px-3 text-sm font-semibold text-slate-900"
          data-testid="dealer-consultant-tracking-refresh"
        >
          Yenile
        </button>
      </div>

      {error ? (
        <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700" data-testid="dealer-consultant-tracking-error">
          {error}
        </div>
      ) : null}

      <div className="rounded-lg border border-slate-200 bg-white p-4" data-testid="dealer-consultant-tracking-toolbar">
        <div className="flex flex-wrap items-center gap-2" data-testid="dealer-consultant-tracking-tabs">
          <button
            type="button"
            onClick={() => setTab('overview')}
            className={`rounded-full border px-3 py-1.5 text-xs font-semibold ${activeTab === 'overview' ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-300 text-slate-800'}`}
            data-testid="dealer-consultant-tracking-tab-overview"
          >
            Danışmanlar ({summary.consultants_count || 0})
          </button>
          <button
            type="button"
            onClick={() => setTab('evaluations')}
            className={`rounded-full border px-3 py-1.5 text-xs font-semibold ${activeTab === 'evaluations' ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-300 text-slate-800'}`}
            data-testid="dealer-consultant-tracking-tab-evaluations"
          >
            Danışman Hizmet Değerlendirmeleri ({summary.evaluations_count || 0})
          </button>
        </div>

        <div className="mt-3 grid gap-2 md:grid-cols-3" data-testid="dealer-consultant-tracking-filters">
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Ad soyad / e-posta / yorum ara"
            className="h-10 rounded-md border border-slate-300 px-3 text-sm text-slate-900"
            data-testid="dealer-consultant-tracking-search-input"
          />
          <select
            value={sortBy}
            onChange={(event) => {
              const nextSort = event.target.value;
              setSortBy(nextSort);
              fetchData(nextSort);
            }}
            className="h-10 rounded-md border border-slate-300 px-3 text-sm text-slate-900"
            data-testid="dealer-consultant-tracking-sort-select"
          >
            <option value="rating_desc">Gelişmiş Sıralama: Puan (Yüksekten)</option>
            <option value="message_change_desc">Gelişmiş Sıralama: 7 Gün Değişim</option>
            <option value="messages_desc">Gelişmiş Sıralama: Mesaj Sayısı</option>
            <option value="name_asc">Gelişmiş Sıralama: İsim A-Z</option>
          </select>
          <button
            type="button"
            onClick={() => {
              setQuery('');
              setSortBy('rating_desc');
              fetchData('rating_desc');
            }}
            className="h-10 rounded-md border border-slate-300 px-3 text-sm font-semibold text-slate-900"
            data-testid="dealer-consultant-tracking-reset-filters"
          >
            Sıfırla
          </button>
        </div>
      </div>

      {loading ? (
        <div className="rounded-md border border-slate-200 bg-white p-4 text-sm text-slate-600" data-testid="dealer-consultant-tracking-loading">Yükleniyor...</div>
      ) : null}

      {!loading && activeTab === 'overview' ? (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3" data-testid="dealer-consultant-tracking-cards-grid">
          {filteredConsultants.length === 0 ? (
            <div className="rounded-md border border-slate-200 bg-white p-4 text-sm text-slate-600" data-testid="dealer-consultant-tracking-empty-cards">Kayıt yok</div>
          ) : filteredConsultants.map((item) => (
            <div key={item.consultant_id} className="rounded-xl border border-slate-200 bg-white p-4" data-testid={`dealer-consultant-card-${item.consultant_id}`}>
              <div className="text-base font-semibold text-slate-900" data-testid={`dealer-consultant-name-${item.consultant_id}`}>{item.full_name || '-'}</div>
              <div className="text-xs text-slate-600" data-testid={`dealer-consultant-email-${item.consultant_id}`}>{item.email || '-'}</div>
              <div className="mt-3 flex items-center justify-between" data-testid={`dealer-consultant-change-${item.consultant_id}`}>
                <span className="text-xs font-semibold text-slate-700">Önceki 7 güne göre</span>
                <span className="text-xs font-semibold text-slate-900">{item.message_change_label}</span>
              </div>
              <div className="mt-2 flex items-center justify-between" data-testid={`dealer-consultant-score-${item.consultant_id}`}>
                <span className="text-xs font-semibold text-slate-700">Danışmanlık puanı</span>
                <span className="text-sm font-semibold text-slate-900">{item.service_score} ({item.review_count})</span>
              </div>
              <button
                type="button"
                onClick={() => openConsultantDetail(item.consultant_id)}
                className="mt-3 h-8 rounded-md border border-slate-300 px-2 text-xs font-semibold text-slate-900"
                data-testid={`dealer-consultant-detail-${item.consultant_id}`}
              >
                Detaylı rapora git
              </button>
            </div>
          ))}
        </div>
      ) : null}

      {!loading && activeTab === 'evaluations' ? (
        <div className="rounded-md border border-slate-200 overflow-x-auto" data-testid="dealer-consultant-evaluations-table-wrap">
          <table className="w-full text-sm" data-testid="dealer-consultant-evaluations-table">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-3 py-2 text-left text-slate-800">Danışman</th>
                <th className="px-3 py-2 text-left text-slate-800">Kullanıcı Adı</th>
                <th className="px-3 py-2 text-left text-slate-800">Değerlendirme Tarihi</th>
                <th className="px-3 py-2 text-left text-slate-800">Puan</th>
                <th className="px-3 py-2 text-left text-slate-800">Yorum</th>
              </tr>
            </thead>
            <tbody>
              {filteredEvaluations.length === 0 ? (
                <tr><td className="px-3 py-4 text-slate-600" colSpan={5} data-testid="dealer-consultant-evaluations-empty">Kayıt yok</td></tr>
              ) : filteredEvaluations.map((item) => (
                <tr key={item.evaluation_id} className="border-t" data-testid={`dealer-consultant-evaluation-row-${item.evaluation_id}`}>
                  <td className="px-3 py-2 font-medium text-slate-900" data-testid={`dealer-consultant-evaluation-consultant-${item.evaluation_id}`}>{item.consultant_name || '-'}</td>
                  <td className="px-3 py-2" data-testid={`dealer-consultant-evaluation-username-${item.evaluation_id}`}>{item.username || '-'}</td>
                  <td className="px-3 py-2" data-testid={`dealer-consultant-evaluation-date-${item.evaluation_id}`}>{formatDate(item.evaluation_date)}</td>
                  <td className="px-3 py-2 font-semibold" data-testid={`dealer-consultant-evaluation-score-${item.evaluation_id}`}>{item.score || 0}</td>
                  <td className="px-3 py-2" data-testid={`dealer-consultant-evaluation-comment-${item.evaluation_id}`}>{item.comment || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  );
}
