import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const statusOptions = [
  { value: 'all', label: 'Tümü' },
  { value: 'draft', label: 'draft' },
  { value: 'issued', label: 'issued' },
  { value: 'paid', label: 'paid' },
  { value: 'cancelled', label: 'cancelled' },
  { value: 'refunded', label: 'refunded' },
  { value: 'overdue', label: 'overdue' },
];

const formatDate = (value) => {
  if (!value) return '-';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return '-';
  return parsed.toLocaleDateString('tr-TR');
};

const formatDateTime = (value) => {
  if (!value) return '-';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return '-';
  return parsed.toLocaleString('tr-TR');
};

const resolveStatusBadgeClass = (value) => {
  switch ((value || '').toLowerCase()) {
    case 'paid':
      return 'bg-green-100 text-green-700';
    case 'issued':
      return 'bg-orange-100 text-orange-700';
    case 'overdue':
      return 'bg-red-200 text-red-800';
    case 'cancelled':
      return 'bg-red-100 text-red-700';
    case 'refunded':
      return 'bg-blue-100 text-blue-700';
    case 'draft':
      return 'bg-slate-100 text-slate-700';
    default:
      return 'bg-slate-100 text-slate-700';
  }
};

const resolvePaymentBadgeClass = (value) => {
  switch ((value || '').toLowerCase()) {
    case 'paid':
    case 'succeeded':
      return 'bg-green-100 text-green-700';
    case 'pending':
      return 'bg-orange-100 text-orange-700';
    case 'refunded':
    case 'partially_refunded':
      return 'bg-blue-100 text-blue-700';
    case 'failed':
    case 'cancelled':
      return 'bg-red-100 text-red-700';
    case 'overdue':
      return 'bg-red-200 text-red-800';
    case 'unpaid':
    default:
      return 'bg-slate-100 text-slate-700';
  }
};

const resolveInvoiceTooltip = (inv) => {
  if (!inv) return '';
  if (inv.status === 'issued') return `Invoice issued at ${formatDateTime(inv.issued_at)}`;
  if (inv.status === 'overdue') return `Overdue since ${formatDateTime(inv.due_at)}`;
  if (inv.status === 'paid') return `Invoice paid at ${formatDateTime(inv.paid_at)}`;
  if (inv.status === 'refunded') return `Refund processed at ${formatDateTime(inv.updated_at)}`;
  if (inv.status === 'cancelled') return 'Invoice cancelled';
  return '';
};

const resolvePaymentTooltip = (inv) => {
  if (!inv) return '';
  const paymentStatus = (inv.payment_status || '').toLowerCase();
  if (paymentStatus === 'paid') return `Payment received at ${formatDateTime(inv.paid_at)}`;
  if (paymentStatus === 'refunded') return `Refund processed at ${formatDateTime(inv.updated_at)}`;
  if (paymentStatus === 'partially_refunded') return `Partial refund processed at ${formatDateTime(inv.updated_at)}`;
  if (paymentStatus === 'pending') return 'Payment pending';
  if (paymentStatus === 'failed') return 'Payment failed';
  if (paymentStatus === 'unpaid') return 'Payment unpaid';
  return '';
};

export default function DealerInvoices() {
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

  const fetchInvoices = async () => {
    if (!dbReady) {
      setItems([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (status !== 'all') params.set('status', status);
      const res = await axios.get(`${API}/dealer/invoices?${params.toString()}`, { headers: authHeader });
      setItems(res.data.items || []);
      setError('');
    } catch (e) {
      setError('Faturalar yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const startCheckout = async (invoice) => {
    if (!dbReady) return;
    if (invoice.country_code !== 'DE') {
      setError('Ödeme sadece DE için aktif.');
      return;
    }
    try {
      const res = await axios.post(
        `${API}/payments/create-checkout-session`,
        {
          invoice_id: invoice.id,
          origin_url: window.location.origin,
        },
        { headers: authHeader }
      );
      window.location.href = res.data.checkout_url;
    } catch (e) {
      setError(e.response?.data?.detail || 'Ödeme başlatılamadı');
    }
  };

  useEffect(() => {
    checkDb();
  }, []);

  useEffect(() => {
    fetchInvoices();
  }, [dbReady, status]);

  return (
    <div className="p-6 space-y-4" data-testid="dealer-invoices-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold" data-testid="dealer-invoices-title">Faturalarım</h1>
          <p className="text-sm text-muted-foreground" data-testid="dealer-invoices-subtitle">Ödeme durumunu buradan takip edin.</p>
        </div>
      </div>

      {!dbReady && (
        <div className="border border-amber-200 bg-amber-50 text-amber-900 rounded-md p-4" data-testid="dealer-invoices-db-banner">
          DB hazır değil → işlemler devre dışı.
        </div>
      )}

      {error && (
        <div className="border border-red-200 bg-red-50 text-red-700 rounded-md p-3" data-testid="dealer-invoices-error">
          {error}
        </div>
      )}

      <div className="flex items-center gap-3" data-testid="dealer-invoices-filters">
        <select
          className="border rounded p-2"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          data-testid="dealer-invoices-status-filter"
        >
          {statusOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>

      <div className="border rounded-lg overflow-hidden" data-testid="dealer-invoices-table">
        <table className="w-full text-sm">
          <thead className="bg-muted">
            <tr>
              <th className="text-left px-3 py-2" data-testid="dealer-invoices-header-no">Invoice No</th>
              <th className="text-left px-3 py-2" data-testid="dealer-invoices-header-amount">Amount</th>
              <th className="text-left px-3 py-2" data-testid="dealer-invoices-header-status">Status</th>
              <th className="text-left px-3 py-2" data-testid="dealer-invoices-header-payment">Payment</th>
              <th className="text-left px-3 py-2" data-testid="dealer-invoices-header-due">Due</th>
              <th className="text-right px-3 py-2" data-testid="dealer-invoices-header-actions">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td className="px-3 py-4" colSpan="6">Yükleniyor...</td></tr>
            ) : items.length === 0 ? (
              <tr><td className="px-3 py-4" colSpan="6">Kayıt yok</td></tr>
            ) : (
              items.map((inv) => (
                <tr key={inv.id} className="border-t" data-testid={`dealer-invoices-row-${inv.id}`}>
                  <td className="px-3 py-2" data-testid={`dealer-invoices-no-${inv.id}`}>{inv.invoice_no || '-'}</td>
                  <td className="px-3 py-2" data-testid={`dealer-invoices-amount-${inv.id}`}>{inv.amount} {inv.currency_code}</td>
                  <td className="px-3 py-2" data-testid={`dealer-invoices-status-${inv.id}`}>
                    <span
                      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${resolveStatusBadgeClass(inv.status)}`}
                      data-testid={`dealer-invoices-status-badge-${inv.id}`}
                      title={resolveInvoiceTooltip(inv)}
                    >
                      {inv.status}
                    </span>
                  </td>
                  <td className="px-3 py-2" data-testid={`dealer-invoices-payment-${inv.id}`}>
                    <span
                      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${resolvePaymentBadgeClass(inv.payment_status)}`}
                      data-testid={`dealer-invoices-payment-badge-${inv.id}`}
                      title={resolvePaymentTooltip(inv)}
                    >
                      {inv.payment_status || '-'}
                    </span>
                  </td>
                  <td className="px-3 py-2" data-testid={`dealer-invoices-due-${inv.id}`}>{formatDate(inv.due_at)}</td>
                  <td className="px-3 py-2 text-right" data-testid={`dealer-invoices-actions-${inv.id}`}>
                    <button
                      className="px-3 py-1 border rounded text-sm"
                      onClick={() => startCheckout(inv)}
                      disabled={!dbReady || inv.status !== 'issued' || inv.payment_status !== 'unpaid'}
                      title={inv.country_code !== 'DE' ? 'Ödeme sadece DE için aktif' : ''}
                      data-testid={`dealer-invoices-pay-${inv.id}`}
                    >
                      Öde
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
