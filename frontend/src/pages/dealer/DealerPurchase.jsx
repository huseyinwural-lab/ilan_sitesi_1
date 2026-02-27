import React, { useEffect, useMemo, useState } from 'react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const invoiceStatuses = ['all', 'issued', 'paid', 'overdue', 'cancelled', 'refunded', 'draft'];

const formatDate = (value) => {
  if (!value) return '-';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return '-';
  return parsed.toLocaleDateString('tr-TR');
};

const formatMoney = (amount, currency = 'EUR') => {
  const numeric = Number(amount || 0);
  if (!Number.isFinite(numeric)) return `0 ${currency}`;
  return new Intl.NumberFormat('tr-TR', { style: 'currency', currency, maximumFractionDigits: 2 }).format(numeric);
};

const isPayableInvoice = (invoice) => {
  const status = `${invoice?.status || ''}`.toLowerCase();
  const paymentStatus = `${invoice?.payment_status || ''}`.toLowerCase();
  return status === 'issued' && ['unpaid', 'requires_payment_method', 'pending'].includes(paymentStatus || 'unpaid');
};

export default function DealerPurchase() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');
  const [checkoutError, setCheckoutError] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [invoices, setInvoices] = useState([]);
  const [packages, setPackages] = useState([]);
  const [checkoutLoadingInvoiceId, setCheckoutLoadingInvoiceId] = useState('');

  const fetchData = async (isManualRefresh = false) => {
    if (isManualRefresh) setRefreshing(true);
    else setLoading(true);

    setError('');
    try {
      const token = localStorage.getItem('access_token');
      const [invoiceRes, packageRes] = await Promise.all([
        fetch(`${API}/dealer/invoices`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`${API}/pricing/packages`),
      ]);

      const invoicePayload = await invoiceRes.json().catch(() => ({}));
      const packagePayload = await packageRes.json().catch(() => ({}));

      if (!invoiceRes.ok) throw new Error(invoicePayload?.detail || 'Satın alma verisi alınamadı');
      if (!packageRes.ok) throw new Error(packagePayload?.detail || 'Paket listesi alınamadı');

      setInvoices(Array.isArray(invoicePayload?.items) ? invoicePayload.items : []);
      setPackages(Array.isArray(packagePayload?.packages) ? packagePayload.packages : []);
    } catch (err) {
      setError(err?.message || 'Satın alma verisi alınamadı');
      setInvoices([]);
      setPackages([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const startCheckout = async (invoice) => {
    if (!isPayableInvoice(invoice)) return;
    setCheckoutError('');
    setCheckoutLoadingInvoiceId(invoice.id);
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`${API}/payments/create-checkout-session`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          invoice_id: invoice.id,
          origin_url: window.location.origin,
        }),
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(payload?.detail || 'Ödeme başlatılamadı');
      if (!payload?.checkout_url) throw new Error('Checkout URL alınamadı');
      window.location.href = payload.checkout_url;
    } catch (err) {
      setCheckoutError(err?.message || 'Ödeme başlatılamadı');
      setCheckoutLoadingInvoiceId('');
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const filteredInvoices = useMemo(() => {
    if (statusFilter === 'all') return invoices;
    return invoices.filter((item) => `${item.status || ''}`.toLowerCase() === statusFilter);
  }, [invoices, statusFilter]);

  const summary = useMemo(() => {
    const totalCount = invoices.length;
    const payableCount = invoices.filter((item) => isPayableInvoice(item)).length;
    const paidTotal = invoices
      .filter((item) => `${item.status || ''}`.toLowerCase() === 'paid')
      .reduce((acc, item) => acc + Number(item.amount_total || item.amount || 0), 0);
    return { totalCount, payableCount, paidTotal };
  }, [invoices]);

  return (
    <div className="space-y-4" data-testid="dealer-purchase-page">
      <div className="flex flex-wrap items-center justify-between gap-3" data-testid="dealer-purchase-header">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900" data-testid="dealer-purchase-title">Satın Al</h1>
          <p className="text-sm font-medium text-slate-700" data-testid="dealer-purchase-subtitle">Paket seçenekleri ve faturalarınızı tek ekrandan yönetin.</p>
        </div>
        <button
          type="button"
          onClick={() => fetchData(true)}
          className="h-9 rounded-md border border-slate-300 px-3 text-sm font-semibold text-slate-900"
          disabled={refreshing}
          data-testid="dealer-purchase-refresh-button"
        >
          {refreshing ? 'Yenileniyor...' : 'Yenile'}
        </button>
      </div>

      {(error || checkoutError) ? (
        <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700" data-testid="dealer-purchase-error">
          {error || checkoutError}
        </div>
      ) : null}

      <div className="grid gap-3 md:grid-cols-3" data-testid="dealer-purchase-summary-grid">
        <div className="rounded-xl border border-slate-200 bg-white p-4" data-testid="dealer-purchase-summary-total-invoices">
          <div className="text-xs font-semibold text-slate-700">Toplam Fatura</div>
          <div className="mt-1 text-3xl font-semibold text-slate-900" data-testid="dealer-purchase-summary-total-invoices-value">{summary.totalCount}</div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4" data-testid="dealer-purchase-summary-payable">
          <div className="text-xs font-semibold text-slate-700">Ödeme Bekleyen</div>
          <div className="mt-1 text-3xl font-semibold text-slate-900" data-testid="dealer-purchase-summary-payable-value">{summary.payableCount}</div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4" data-testid="dealer-purchase-summary-paid-total">
          <div className="text-xs font-semibold text-slate-700">Ödenen Toplam</div>
          <div className="mt-1 text-2xl font-semibold text-slate-900" data-testid="dealer-purchase-summary-paid-total-value">{formatMoney(summary.paidTotal, 'EUR')}</div>
        </div>
      </div>

      <section className="rounded-lg border border-slate-200 bg-white p-4" data-testid="dealer-purchase-packages-section">
        <div className="flex items-center justify-between" data-testid="dealer-purchase-packages-header">
          <h2 className="text-base font-semibold text-slate-900" data-testid="dealer-purchase-packages-title">Toplu Doping Satın Al Paketleri</h2>
          <span className="text-xs font-semibold text-slate-600" data-testid="dealer-purchase-packages-count">{packages.length} paket</span>
        </div>
        <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-3" data-testid="dealer-purchase-packages-grid">
          {loading ? (
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm text-slate-600" data-testid="dealer-purchase-loading-packages">Yükleniyor...</div>
          ) : packages.length === 0 ? (
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm text-slate-600" data-testid="dealer-purchase-empty-packages">Aktif paket bulunamadı.</div>
          ) : packages.map((pkg) => (
            <article key={pkg.id} className="rounded-lg border border-slate-200 bg-slate-50 p-3" data-testid={`dealer-purchase-package-card-${pkg.id}`}>
              <div className="text-sm font-semibold text-slate-900" data-testid={`dealer-purchase-package-name-${pkg.id}`}>{pkg.name || 'Paket'}</div>
              <div className="mt-2 text-xs text-slate-600" data-testid={`dealer-purchase-package-quota-${pkg.id}`}>İlan Kotası: {pkg.listing_quota || 0}</div>
              <div className="text-xs text-slate-600" data-testid={`dealer-purchase-package-days-${pkg.id}`}>Yayın Süresi: {pkg.publish_days || 0} gün</div>
              <div className="mt-2 text-lg font-semibold text-slate-900" data-testid={`dealer-purchase-package-price-${pkg.id}`}>{formatMoney(pkg.price_amount, pkg.currency || 'EUR')}</div>
            </article>
          ))}
        </div>
      </section>

      <section className="rounded-md border border-slate-200 overflow-hidden" data-testid="dealer-purchase-invoices-section">
        <div className="border-b border-slate-200 bg-slate-50 px-3 py-2" data-testid="dealer-purchase-invoices-toolbar">
          <div className="flex flex-wrap items-center gap-2" data-testid="dealer-purchase-status-filters">
            {invoiceStatuses.map((statusKey) => (
              <button
                key={statusKey}
                type="button"
                onClick={() => setStatusFilter(statusKey)}
                className={`rounded-full border px-3 py-1 text-xs font-semibold ${statusFilter === statusKey ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-300 text-slate-800'}`}
                data-testid={`dealer-purchase-status-filter-${statusKey}`}
              >
                {statusKey === 'all' ? 'Tümü' : statusKey}
              </button>
            ))}
          </div>
        </div>
        <div className="overflow-x-auto" data-testid="dealer-purchase-table-wrap">
          <table className="w-full text-sm" data-testid="dealer-purchase-table">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-3 py-2 text-left text-slate-800">Invoice</th>
                <th className="px-3 py-2 text-left text-slate-800">Paket</th>
                <th className="px-3 py-2 text-left text-slate-800">Durum</th>
                <th className="px-3 py-2 text-left text-slate-800">Tutar</th>
                <th className="px-3 py-2 text-left text-slate-800">Tarih</th>
                <th className="px-3 py-2 text-right text-slate-800">İşlem</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td className="px-3 py-4 text-slate-600" colSpan={6} data-testid="dealer-purchase-loading">Yükleniyor...</td></tr>
              ) : filteredInvoices.length === 0 ? (
                <tr><td className="px-3 py-4 text-slate-600" colSpan={6} data-testid="dealer-purchase-empty">Kayıt yok</td></tr>
              ) : (
                filteredInvoices.map((row) => {
                  const payable = isPayableInvoice(row);
                  return (
                    <tr key={row.id} className="border-t" data-testid={`dealer-purchase-row-${row.id}`}>
                      <td className="px-3 py-2" data-testid={`dealer-purchase-invoice-${row.id}`}>{row.invoice_no || row.id}</td>
                      <td className="px-3 py-2" data-testid={`dealer-purchase-plan-${row.id}`}>{row.plan_name || row.notes || 'Kurumsal Paket'}</td>
                      <td className="px-3 py-2" data-testid={`dealer-purchase-status-${row.id}`}>{row.status || '-'}</td>
                      <td className="px-3 py-2 font-semibold" data-testid={`dealer-purchase-amount-${row.id}`}>{formatMoney(row.amount_total || row.amount, row.currency || 'EUR')}</td>
                      <td className="px-3 py-2" data-testid={`dealer-purchase-date-${row.id}`}>{formatDate(row.created_at || row.issued_at)}</td>
                      <td className="px-3 py-2 text-right" data-testid={`dealer-purchase-actions-${row.id}`}>
                        <button
                          type="button"
                          onClick={() => startCheckout(row)}
                          disabled={!payable || checkoutLoadingInvoiceId === row.id}
                          className="h-8 rounded-md border border-slate-300 px-3 text-xs font-semibold text-slate-900 disabled:cursor-not-allowed disabled:opacity-60"
                          data-testid={`dealer-purchase-pay-button-${row.id}`}
                        >
                          {checkoutLoadingInvoiceId === row.id ? 'Yönlendiriliyor...' : 'Öde'}
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
