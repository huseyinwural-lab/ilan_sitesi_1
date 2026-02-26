import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const statusOptions = [
  { value: 'all', label: 'Durum: Tümü' },
  { value: 'requires_payment_method', label: 'requires_payment_method' },
  { value: 'requires_confirmation', label: 'requires_confirmation' },
  { value: 'processing', label: 'processing' },
  { value: 'succeeded', label: 'succeeded' },
  { value: 'failed', label: 'failed' },
  { value: 'canceled', label: 'canceled' },
  { value: 'refunded', label: 'refunded' },
];

const formatDateTime = (value) => {
  if (!value) return '-';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return '-';
  return parsed.toLocaleString('tr-TR');
};

export default function AdminPaymentsPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [status, setStatus] = useState('all');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [query, setQuery] = useState('');
  const [userId, setUserId] = useState('');
  const [listingId, setListingId] = useState('');

  const authHeader = useMemo(() => ({
    Authorization: `Bearer ${localStorage.getItem('access_token')}`,
  }), []);

  const buildParams = () => {
    const params = new URLSearchParams();
    if (status !== 'all') params.set('status', status);
    if (startDate) params.set('start_date', `${startDate}T00:00:00+00:00`);
    if (endDate) params.set('end_date', `${endDate}T23:59:59+00:00`);
    if (query.trim()) params.set('q', query.trim());
    if (userId.trim()) params.set('user_id', userId.trim());
    if (listingId.trim()) params.set('listing_id', listingId.trim());
    return params;
  };

  const fetchPayments = async () => {
    setLoading(true);
    try {
      const params = buildParams();
      const res = await axios.get(`${API}/admin/payments?${params.toString()}`, { headers: authHeader });
      setItems(res.data.items || []);
      setError('');
    } catch (e) {
      setError('Transactions log yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const handleExportCsv = async () => {
    try {
      const params = buildParams();
      const res = await axios.get(`${API}/admin/payments/export/csv?${params.toString()}`, {
        headers: authHeader,
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'text/csv;charset=utf-8;' }));
      const link = document.createElement('a');
      link.href = url;
      link.download = 'transactions-log.csv';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch {
      setError('CSV export başarısız');
    }
  };

  useEffect(() => {
    fetchPayments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, startDate, endDate]);

  return (
    <div className="p-6 space-y-4" data-testid="admin-transactions-page">
      <div className="flex items-start justify-between gap-3 flex-wrap" data-testid="admin-transactions-header">
        <div>
          <h1 className="text-2xl font-semibold" data-testid="admin-transactions-title">Transactions Log</h1>
          <p className="text-sm text-muted-foreground" data-testid="admin-transactions-subtitle">Read-only monetization kayıtları.</p>
        </div>
        <button
          onClick={handleExportCsv}
          className="h-9 px-3 rounded-md border text-sm"
          data-testid="admin-transactions-export-csv"
        >
          CSV Export
        </button>
      </div>

      {error && (
        <div className="border border-red-200 bg-red-50 text-red-700 rounded-md p-3" data-testid="admin-transactions-error">
          {error}
        </div>
      )}

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-6" data-testid="admin-transactions-filters">
        <select
          className="h-9 px-3 rounded-md border bg-background text-sm"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          data-testid="admin-transactions-filter-status"
        >
          {statusOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>

        <input
          type="date"
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
          className="h-9 px-3 rounded-md border bg-background text-sm"
          data-testid="admin-transactions-filter-start-date"
        />

        <input
          type="date"
          value={endDate}
          onChange={(e) => setEndDate(e.target.value)}
          className="h-9 px-3 rounded-md border bg-background text-sm"
          data-testid="admin-transactions-filter-end-date"
        />

        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Provider ref / payment id"
          className="h-9 px-3 rounded-md border bg-background text-sm"
          data-testid="admin-transactions-filter-query"
        />

        <input
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
          placeholder="user_id"
          className="h-9 px-3 rounded-md border bg-background text-sm"
          data-testid="admin-transactions-filter-user-id"
        />

        <div className="flex gap-2">
          <input
            value={listingId}
            onChange={(e) => setListingId(e.target.value)}
            placeholder="listing_id"
            className="h-9 px-3 rounded-md border bg-background text-sm flex-1"
            data-testid="admin-transactions-filter-listing-id"
          />
          <button
            onClick={fetchPayments}
            className="h-9 px-3 rounded-md bg-primary text-primary-foreground text-sm"
            data-testid="admin-transactions-apply-filters"
          >
            Uygula
          </button>
        </div>
      </div>

      <div className="border rounded-lg overflow-hidden" data-testid="admin-transactions-table">
        <table className="w-full text-sm">
          <thead className="bg-muted">
            <tr>
              <th className="text-left px-3 py-2">transaction_id</th>
              <th className="text-left px-3 py-2">user_id</th>
              <th className="text-left px-3 py-2">listing_id</th>
              <th className="text-left px-3 py-2">provider_ref</th>
              <th className="text-left px-3 py-2">amount</th>
              <th className="text-left px-3 py-2">currency</th>
              <th className="text-left px-3 py-2">status</th>
              <th className="text-left px-3 py-2">created_at</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td className="px-3 py-4" colSpan="8" data-testid="admin-transactions-loading">Yükleniyor...</td></tr>
            ) : items.length === 0 ? (
              <tr><td className="px-3 py-4" colSpan="8" data-testid="admin-transactions-empty">Kayıt yok</td></tr>
            ) : (
              items.map((item) => (
                <tr key={item.id} className="border-t" data-testid={`admin-transactions-row-${item.id}`}>
                  <td className="px-3 py-2 font-mono text-xs" data-testid={`admin-transactions-id-${item.id}`}>{item.transaction_id || item.id}</td>
                  <td className="px-3 py-2 font-mono text-xs" data-testid={`admin-transactions-user-${item.id}`}>{item.user_id}</td>
                  <td className="px-3 py-2 font-mono text-xs" data-testid={`admin-transactions-listing-${item.id}`}>{item.listing_id || '-'}</td>
                  <td className="px-3 py-2 font-mono text-xs" data-testid={`admin-transactions-provider-ref-${item.id}`}>{item.provider_ref || '-'}</td>
                  <td className="px-3 py-2" data-testid={`admin-transactions-amount-${item.id}`}>{item.amount_total}</td>
                  <td className="px-3 py-2" data-testid={`admin-transactions-currency-${item.id}`}>{item.currency}</td>
                  <td className="px-3 py-2" data-testid={`admin-transactions-status-${item.id}`}>{item.status}</td>
                  <td className="px-3 py-2" data-testid={`admin-transactions-created-${item.id}`}>{formatDateTime(item.created_at)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
