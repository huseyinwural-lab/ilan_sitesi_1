import React, { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const statusOptions = [
  { value: 'all', label: 'Tümü' },
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
  const [searchParams] = useSearchParams();
  const urlCountry = (searchParams.get('country') || '').toUpperCase();

  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [dbReady, setDbReady] = useState(false);

  const [status, setStatus] = useState('all');

  const authHeader = useMemo(() => ({
    Authorization: `Bearer ${localStorage.getItem('access_token')}`,
  }), []);

  const checkDb = async () => {
    try {
      const res = await axios.get(`${API}/health/db`);
      setDbReady(res.status === 200);
      if (res.status === 200) setError('');
    } catch (err) {
      setDbReady(false);
    }
  };

  const fetchPayments = async () => {
    if (!dbReady) {
      setItems([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (urlCountry) params.set('country', urlCountry);
      if (dealerId) params.set('dealer', dealerId);
      if (status !== 'all') params.set('status', status);
      if (dateFrom) params.set('date_from', dateFrom);
      if (dateTo) params.set('date_to', dateTo);
      const res = await axios.get(`${API}/admin/payments?${params.toString()}`, { headers: authHeader });
      setItems(res.data.items || []);
      setError('');
    } catch (e) {
      setError('Payments yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkDb();
  }, []);

  useEffect(() => {
    fetchPayments();
  }, [dbReady, urlCountry, dealerId, status, dateFrom, dateTo]);

  return (
    <div className="p-6 space-y-4" data-testid="admin-payments-page">
      <div className="flex items-start justify-between" data-testid="admin-payments-header">
        <div>
          <h1 className="text-2xl font-semibold" data-testid="admin-payments-title">Ödemeler</h1>
          <p className="text-sm text-muted-foreground" data-testid="admin-payments-subtitle">Country: {urlCountry || 'Global'}</p>
        </div>
      </div>

      {!dbReady && (
        <div className="border border-amber-200 bg-amber-50 text-amber-900 rounded-md p-4" data-testid="admin-payments-db-banner">
          DB hazır değil → işlemler devre dışı.
        </div>
      )}

      {error && (
        <div className="border border-red-200 bg-red-50 text-red-700 rounded-md p-3" data-testid="admin-payments-error">
          {error}
        </div>
      )}

      <div className="flex flex-wrap items-center gap-3" data-testid="admin-payments-filters">
        <input
          value={dealerId}
          onChange={(e) => setDealerId(e.target.value)}
          placeholder="Dealer ID"
          className="h-9 px-3 rounded-md border bg-background text-sm"
          data-testid="admin-payments-filter-dealer"
        />
        <select
          className="h-9 px-3 rounded-md border bg-background text-sm"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          data-testid="admin-payments-filter-status"
        >
          {statusOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
        <input
          type="date"
          value={dateFrom}
          onChange={(e) => setDateFrom(e.target.value)}
          className="h-9 px-3 rounded-md border bg-background text-sm"
          data-testid="admin-payments-filter-date-from"
        />
        <input
          type="date"
          value={dateTo}
          onChange={(e) => setDateTo(e.target.value)}
          className="h-9 px-3 rounded-md border bg-background text-sm"
          data-testid="admin-payments-filter-date-to"
        />
      </div>

      <div className="border rounded-lg overflow-hidden" data-testid="admin-payments-table">
        <table className="w-full text-sm">
          <thead className="bg-muted">
            <tr>
              <th className="text-left px-3 py-2" data-testid="admin-payments-header-invoice">Invoice No</th>
              <th className="text-left px-3 py-2" data-testid="admin-payments-header-dealer">Dealer</th>
              <th className="text-left px-3 py-2" data-testid="admin-payments-header-amount">Amount</th>
              <th className="text-left px-3 py-2" data-testid="admin-payments-header-currency">Currency</th>
              <th className="text-left px-3 py-2" data-testid="admin-payments-header-status">Status</th>
              <th className="text-left px-3 py-2" data-testid="admin-payments-header-provider">Provider</th>
              <th className="text-left px-3 py-2" data-testid="admin-payments-header-paid">Paid At</th>
              <th className="text-left px-3 py-2" data-testid="admin-payments-header-created">Created</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td className="px-3 py-4" colSpan="8">Yükleniyor...</td></tr>
            ) : items.length === 0 ? (
              <tr><td className="px-3 py-4" colSpan="8">Kayıt yok</td></tr>
            ) : (
              items.map((item) => (
                <tr key={item.id} className="border-t" data-testid={`admin-payments-row-${item.id}`}>
                  <td className="px-3 py-2" data-testid={`admin-payments-invoice-${item.id}`}>{item.invoice_no || '-'}</td>
                  <td className="px-3 py-2" data-testid={`admin-payments-dealer-${item.id}`}>{item.dealer_email || item.dealer_id}</td>
                  <td className="px-3 py-2" data-testid={`admin-payments-amount-${item.id}`}>{item.amount}</td>
                  <td className="px-3 py-2" data-testid={`admin-payments-currency-${item.id}`}>{item.currency}</td>
                  <td className="px-3 py-2" data-testid={`admin-payments-status-${item.id}`}>{item.status}</td>
                  <td className="px-3 py-2" data-testid={`admin-payments-provider-${item.id}`}>{item.provider}</td>
                  <td className="px-3 py-2" data-testid={`admin-payments-paid-${item.id}`}>{formatDateTime(item.paid_at)}</td>
                  <td className="px-3 py-2" data-testid={`admin-payments-created-${item.id}`}>{formatDateTime(item.created_at)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
