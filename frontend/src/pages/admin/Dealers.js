import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { useLanguage } from '@/contexts/LanguageContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function DealersPage() {
  const { t } = useLanguage();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState('');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);
  const limit = 20;

  const authHeader = useMemo(() => ({
    Authorization: `Bearer ${localStorage.getItem('access_token')}`,
  }), []);

  const fetchDealers = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set('skip', String(page * limit));
      params.set('limit', String(limit));
      if (status) params.set('status', status);
      if (search) params.set('search', search);

      const res = await axios.get(`${API}/admin/dealers?${params.toString()}`, {
        headers: authHeader,
      });
      setItems(res.data.items || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDealers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, search, page]);

  const setDealerStatus = async (dealerId, newStatus) => {
    await axios.post(
      `${API}/admin/dealers/${dealerId}/status`,
      { dealer_status: newStatus },
      { headers: authHeader }
    );
    await fetchDealers();
  };

  return (
    <div className="space-y-6" data-testid="admin-dealers-page">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dealers</h1>
        <p className="text-sm text-muted-foreground">Dealer Management (Sprint 1)</p>
      </div>

      <div className="flex flex-wrap gap-3">
          <input
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(0); }}
            placeholder="Search by email"
            className="h-9 px-3 rounded-md border bg-background text-sm"
            data-testid="dealers-search-input"
          />
          <select
            value={status}
            onChange={(e) => { setStatus(e.target.value); setPage(0); }}
            className="h-9 px-3 rounded-md border bg-background text-sm"
            data-testid="dealers-status-select"
          >
          <option value="">All statuses</option>
          <option value="active">active</option>
          <option value="suspended">suspended</option>
        </select>
      </div>

      <div className="rounded-md border bg-card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-muted">
            <tr>
              <th className="text-left p-3">Email</th>
              <th className="text-left p-3">Country</th>
              <th className="text-left p-3">Status</th>
              <th className="text-right p-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={4} className="p-6 text-center">Loading…</td></tr>
            ) : items.length === 0 ? (
              <tr><td colSpan={4} className="p-6 text-center text-muted-foreground">No dealers</td></tr>
            ) : (
              items.map((d) => (
                <tr key={d.id} className="border-t" data-testid={`dealer-row-${d.id}`}>
                  <td className="p-3" data-testid={`dealer-email-${d.id}`}>{d.email}</td>
                  <td className="p-3 text-muted-foreground" data-testid={`dealer-country-${d.id}`}>{d.country_code || '-'}</td>
                  <td className="p-3">
                    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                      d.dealer_status === 'active'
                        ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400'
                        : 'bg-rose-100 text-rose-800 dark:bg-rose-900/30 dark:text-rose-400'
                    }`} data-testid={`dealer-status-${d.id}`}>{d.dealer_status}</span>
                  </td>
                  <td className="p-3 text-right">
                    {d.dealer_status === 'active' ? (
                      <button
                        onClick={() => setDealerStatus(d.id, 'suspended')}
                        className="h-8 px-3 rounded-md border text-xs hover:bg-muted"
                        data-testid={`dealer-suspend-${d.id}`}
                      >
                        Suspend
                      </button>
                    ) : (
                      <button
                        onClick={() => setDealerStatus(d.id, 'active')}
                        className="h-8 px-3 rounded-md border text-xs hover:bg-muted"
                        data-testid={`dealer-activate-${d.id}`}
                      >
                        Activate
                      </button>
                    )}
                    <Link
                      to={`/admin/dealers/${d.id}`}
                      className="ml-2 h-8 px-3 rounded-md border text-xs inline-flex items-center justify-center"
                      data-testid={`dealer-detail-link-${d.id}`}
                    >
                      Detay
                    </Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-end gap-2">
        <button
          onClick={() => setPage(Math.max(0, page - 1))}
          disabled={page === 0}
          className="h-9 px-3 rounded-md border text-sm disabled:opacity-50"
        >
          Prev
        </button>
        <button
          onClick={() => setPage(page + 1)}
          className="h-9 px-3 rounded-md border text-sm"
        >
          Next
        </button>
      </div>
    </div>
  );
}
