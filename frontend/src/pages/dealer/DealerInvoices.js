import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { FinanceStatusBadge } from '@/components/finance/FinanceStatusBadge';
import { FinanceEmptyState, FinanceErrorState, FinanceLoadingState } from '@/components/finance/FinanceStateView';
import { formatMoneyMinor, normalizePaymentMessage, resolveLocaleByCountry } from '@/utils/financeFormat';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const invoiceStatusOptions = [
  { value: 'all', label: 'Tümü' },
  { value: 'draft', label: 'Taslak' },
  { value: 'issued', label: 'Düzenlendi' },
  { value: 'paid', label: 'Ödendi' },
  { value: 'void', label: 'İptal' },
  { value: 'refunded', label: 'İade' },
  { value: 'overdue', label: 'Gecikmiş' },
];

const paymentStatusOptions = [
  { value: 'all', label: 'Tümü' },
  { value: 'succeeded', label: 'Başarılı' },
  { value: 'processing', label: 'İşleniyor' },
  { value: 'pending', label: 'Beklemede' },
  { value: 'failed', label: 'Başarısız' },
  { value: 'refunded', label: 'İade' },
];

const formatDate = (value, locale) => {
  if (!value) return '-';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return '-';
  return parsed.toLocaleDateString(locale || 'tr-TR');
};

const resolveDateSource = (item) => item.issued_at || item.created_at;

export default function DealerInvoices() {
  const [activeTab, setActiveTab] = useState('invoices');
  const [invoiceStatus, setInvoiceStatus] = useState('all');
  const [paymentStatus, setPaymentStatus] = useState('all');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  const [invoices, setInvoices] = useState([]);
  const [payments, setPayments] = useState([]);
  const [loadingInvoices, setLoadingInvoices] = useState(false);
  const [loadingPayments, setLoadingPayments] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [checkoutLoadingId, setCheckoutLoadingId] = useState('');
  const [downloadLoadingId, setDownloadLoadingId] = useState('');
  const [error, setError] = useState('');

  const [detailData, setDetailData] = useState(null);

  const authHeader = useMemo(() => ({
    Authorization: `Bearer ${localStorage.getItem('access_token')}`,
  }), []);

  const locale = resolveLocaleByCountry(localStorage.getItem('selectedCountry') || 'TR');

  const parseError = (err, fallback) => {
    const detail = err?.response?.data?.detail;
    if (typeof detail === 'string' && detail.trim()) return detail;
    return fallback;
  };

  const loadInvoices = async () => {
    setLoadingInvoices(true);
    setError('');
    try {
      const params = new URLSearchParams();
      if (invoiceStatus !== 'all') params.set('status', invoiceStatus);
      const res = await axios.get(`${API}/dealer/invoices?${params.toString()}`, { headers: authHeader });
      const rows = Array.isArray(res.data?.items) ? res.data.items : [];
      setInvoices(rows);
    } catch (err) {
      setError(parseError(err, 'Fatura kayıtları alınamadı. Lütfen daha sonra tekrar deneyiniz.'));
      setInvoices([]);
    } finally {
      setLoadingInvoices(false);
    }
  };

  const loadPayments = async () => {
    setLoadingPayments(true);
    setError('');
    try {
      const params = new URLSearchParams();
      if (paymentStatus !== 'all') params.set('status', paymentStatus);
      const res = await axios.get(`${API}/dealer/payments?${params.toString()}`, { headers: authHeader });
      setPayments(Array.isArray(res.data?.items) ? res.data.items : []);
    } catch (err) {
      setError(parseError(err, 'Hesap hareketleri alınamadı. Lütfen daha sonra tekrar deneyiniz.'));
      setPayments([]);
    } finally {
      setLoadingPayments(false);
    }
  };

  const loadInvoiceDetail = async (invoiceId) => {
    setDetailLoading(true);
    setError('');
    try {
      const res = await axios.get(`${API}/dealer/invoices/${invoiceId}`, { headers: authHeader });
      setDetailData(res.data || null);
    } catch (err) {
      setError(parseError(err, 'Fatura detayı alınamadı.'));
      setDetailData(null);
    } finally {
      setDetailLoading(false);
    }
  };

  const downloadPdf = async (invoice) => {
    if (!invoice?.id) return;
    setDownloadLoadingId(invoice.id);
    setError('');
    try {
      const res = await axios.get(`${API}/dealer/invoices/${invoice.id}/download-pdf`, {
        headers: authHeader,
        responseType: 'blob',
      });
      const blobUrl = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = `${invoice.invoice_no || `invoice-${invoice.id}`}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(blobUrl);
    } catch (err) {
      setError(parseError(err, 'PDF indirilemedi.'));
    } finally {
      setDownloadLoadingId('');
    }
  };

  const startCheckout = async (invoice) => {
    if (!invoice?.id) return;
    if (invoice.country_code !== 'DE') {
      setError('Ödeme işlemi yalnızca DE kapsamındaki faturalar için aktiftir.');
      return;
    }
    setCheckoutLoadingId(invoice.id);
    setError('');
    try {
      const res = await axios.post(
        `${API}/payments/create-checkout-session`,
        { invoice_id: invoice.id, origin_url: window.location.origin },
        { headers: authHeader },
      );
      if (!res.data?.checkout_url) throw new Error('Ödeme oturumu başlatılamadı.');
      window.location.href = res.data.checkout_url;
    } catch (err) {
      setError(parseError(err, 'Ödeme başlatılamadı.'));
      setCheckoutLoadingId('');
    }
  };

  useEffect(() => {
    loadInvoices();
    loadPayments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    loadInvoices();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [invoiceStatus]);

  useEffect(() => {
    loadPayments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paymentStatus]);

  const filteredInvoices = useMemo(() => {
    const start = startDate ? new Date(`${startDate}T00:00:00`) : null;
    const end = endDate ? new Date(`${endDate}T23:59:59`) : null;
    return invoices.filter((item) => {
      const sourceDate = resolveDateSource(item);
      if (!sourceDate || (!start && !end)) return true;
      const date = new Date(sourceDate);
      if (Number.isNaN(date.getTime())) return true;
      if (start && date < start) return false;
      if (end && date > end) return false;
      return true;
    });
  }, [invoices, startDate, endDate]);

  return (
    <div className="space-y-4" data-testid="dealer-invoices-page">
      <div className="flex flex-wrap items-center justify-between gap-3" data-testid="dealer-invoices-header">
        <div>
          <h1 className="text-2xl font-semibold" data-testid="dealer-invoices-title">Faturalar ve Hesap Hareketleri</h1>
          <p className="text-sm text-muted-foreground" data-testid="dealer-invoices-subtitle">
            Fatura kayıtlarınızı ve ödeme hareketlerinizi kurumsal panelden yönetebilirsiniz.
          </p>
        </div>
        <div className="text-xs text-muted-foreground" data-testid="dealer-invoices-counts">
          Fatura: {filteredInvoices.length} • Hareket: {payments.length}
        </div>
      </div>

      {error ? <FinanceErrorState testId="dealer-invoices-error" message={error} /> : null}

      <div className="rounded-lg border bg-white p-4 space-y-3" data-testid="dealer-finance-tabs-card">
        <div className="flex flex-wrap items-center gap-2" data-testid="dealer-finance-tabs">
          <button
            type="button"
            onClick={() => setActiveTab('invoices')}
            className={`rounded-full border px-3 py-1.5 text-xs font-semibold ${activeTab === 'invoices' ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-300 text-slate-800'}`}
            data-testid="dealer-finance-tab-invoices"
          >
            Faturalarım
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('movements')}
            className={`rounded-full border px-3 py-1.5 text-xs font-semibold ${activeTab === 'movements' ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-300 text-slate-800'}`}
            data-testid="dealer-finance-tab-movements"
          >
            Hesap Hareketlerim
          </button>
        </div>

        {activeTab === 'invoices' ? (
          <>
            <div className="flex flex-wrap items-center gap-2" data-testid="dealer-invoices-filters">
              <select
                className="h-9 rounded-md border px-3 text-sm"
                value={invoiceStatus}
                onChange={(event) => setInvoiceStatus(event.target.value)}
                data-testid="dealer-invoices-status-filter"
              >
                {invoiceStatusOptions.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
              <input type="date" className="h-9 rounded-md border px-3 text-sm" value={startDate} onChange={(event) => setStartDate(event.target.value)} data-testid="dealer-invoices-start-date" />
              <input type="date" className="h-9 rounded-md border px-3 text-sm" value={endDate} onChange={(event) => setEndDate(event.target.value)} data-testid="dealer-invoices-end-date" />
              <button
                type="button"
                onClick={() => {
                  setStartDate('');
                  setEndDate('');
                }}
                className="h-9 rounded-md border px-3 text-sm"
                data-testid="dealer-invoices-clear-date-filters"
              >
                Tarihi Temizle
              </button>
            </div>

            <div className="rounded-md border overflow-hidden" data-testid="dealer-invoices-table-wrap">
              <table className="w-full text-sm" data-testid="dealer-invoices-table">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="text-left px-3 py-2" data-testid="dealer-invoices-col-no">Fatura No</th>
                    <th className="text-left px-3 py-2" data-testid="dealer-invoices-col-status">Durum</th>
                    <th className="text-left px-3 py-2" data-testid="dealer-invoices-col-payment">Ödeme</th>
                    <th className="text-left px-3 py-2" data-testid="dealer-invoices-col-amount">Tutar</th>
                    <th className="text-left px-3 py-2" data-testid="dealer-invoices-col-date">Tarih</th>
                    <th className="text-right px-3 py-2" data-testid="dealer-invoices-col-actions">İşlemler</th>
                  </tr>
                </thead>
                <tbody>
                  {loadingInvoices ? (
                    <tr><td colSpan={6} className="px-3 py-4"><FinanceLoadingState testId="dealer-invoices-loading" /></td></tr>
                  ) : filteredInvoices.length === 0 ? (
                    <tr><td colSpan={6} className="px-3 py-4"><FinanceEmptyState testId="dealer-invoices-empty" message="Bu kriterlere uygun fatura kaydı bulunmamaktadır." /></td></tr>
                  ) : (
                    filteredInvoices.map((invoice) => {
                      const payable = invoice.status === 'issued' && ['unpaid', 'requires_payment_method', 'pending'].includes((invoice.payment_status || '').toLowerCase());
                      return (
                        <tr key={invoice.id} className="border-t" data-testid={`dealer-invoice-row-${invoice.id}`}>
                          <td className="px-3 py-2" data-testid={`dealer-invoice-no-${invoice.id}`}>{invoice.invoice_no || '-'}</td>
                          <td className="px-3 py-2" data-testid={`dealer-invoice-status-${invoice.id}`}><FinanceStatusBadge status={invoice.status} testId={`dealer-invoice-status-badge-${invoice.id}`} /></td>
                          <td className="px-3 py-2" data-testid={`dealer-invoice-payment-${invoice.id}`}><FinanceStatusBadge status={invoice.payment_status || '-'} testId={`dealer-invoice-payment-badge-${invoice.id}`} /></td>
                          <td className="px-3 py-2 font-semibold" data-testid={`dealer-invoice-amount-${invoice.id}`}>{formatMoneyMinor(invoice.amount_minor, invoice.currency_code || invoice.currency || 'EUR', locale)}</td>
                          <td className="px-3 py-2" data-testid={`dealer-invoice-date-${invoice.id}`}>{formatDate(resolveDateSource(invoice), locale)}</td>
                          <td className="px-3 py-2 text-right" data-testid={`dealer-invoice-actions-${invoice.id}`}>
                            <div className="inline-flex items-center gap-2">
                              <button type="button" className="h-8 rounded-md border px-2 text-xs" onClick={() => loadInvoiceDetail(invoice.id)} data-testid={`dealer-invoice-detail-${invoice.id}`}>Detay</button>
                              {invoice.pdf_url ? (
                                <button
                                  type="button"
                                  className="h-8 rounded-md border px-2 text-xs"
                                  onClick={() => downloadPdf(invoice)}
                                  disabled={downloadLoadingId === invoice.id}
                                  data-testid={`dealer-invoice-download-${invoice.id}`}
                                >
                                  {downloadLoadingId === invoice.id ? 'İndiriliyor...' : 'PDF İndir'}
                                </button>
                              ) : null}
                              <button
                                type="button"
                                className="h-8 rounded-md border px-2 text-xs"
                                onClick={() => startCheckout(invoice)}
                                disabled={!payable || checkoutLoadingId === invoice.id}
                                data-testid={`dealer-invoice-pay-${invoice.id}`}
                                title={invoice.country_code !== 'DE' ? 'Ödeme yalnızca DE faturaları için aktiftir.' : ''}
                              >
                                {checkoutLoadingId === invoice.id ? 'Yönlendiriliyor...' : 'Öde'}
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </>
        ) : (
          <>
            <div className="flex flex-wrap items-center gap-2" data-testid="dealer-payments-filters">
              <select
                className="h-9 rounded-md border px-3 text-sm"
                value={paymentStatus}
                onChange={(event) => setPaymentStatus(event.target.value)}
                data-testid="dealer-payments-status-filter"
              >
                {paymentStatusOptions.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            </div>

            <div className="rounded-md border overflow-hidden" data-testid="dealer-payments-table-wrap">
              <table className="w-full text-sm" data-testid="dealer-payments-table">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="text-left px-3 py-2" data-testid="dealer-payments-col-ref">İşlem No</th>
                    <th className="text-left px-3 py-2" data-testid="dealer-payments-col-status">Durum</th>
                    <th className="text-left px-3 py-2" data-testid="dealer-payments-col-amount">Tutar</th>
                    <th className="text-left px-3 py-2" data-testid="dealer-payments-col-message">Açıklama</th>
                    <th className="text-left px-3 py-2" data-testid="dealer-payments-col-date">Tarih</th>
                  </tr>
                </thead>
                <tbody>
                  {loadingPayments ? (
                    <tr><td colSpan={5} className="px-3 py-4"><FinanceLoadingState testId="dealer-payments-loading" /></td></tr>
                  ) : payments.length === 0 ? (
                    <tr><td colSpan={5} className="px-3 py-4"><FinanceEmptyState testId="dealer-payments-empty" message="Hesap hareketi kaydı bulunmamaktadır." /></td></tr>
                  ) : (
                    payments.map((payment) => (
                      <tr key={payment.id} className="border-t" data-testid={`dealer-payment-row-${payment.id}`}>
                        <td className="px-3 py-2 font-mono text-xs" data-testid={`dealer-payment-ref-${payment.id}`}>{payment.provider_ref || payment.id}</td>
                        <td className="px-3 py-2" data-testid={`dealer-payment-status-${payment.id}`}><FinanceStatusBadge status={payment.status} testId={`dealer-payment-status-badge-${payment.id}`} /></td>
                        <td className="px-3 py-2 font-semibold" data-testid={`dealer-payment-amount-${payment.id}`}>{formatMoneyMinor(payment.amount_minor, payment.currency || 'EUR', locale)}</td>
                        <td className="px-3 py-2" data-testid={`dealer-payment-message-${payment.id}`}>{payment.normalized_message || normalizePaymentMessage(payment.status)}</td>
                        <td className="px-3 py-2" data-testid={`dealer-payment-date-${payment.id}`}>{formatDate(payment.created_at, locale)}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>

      {detailLoading ? <FinanceLoadingState testId="dealer-invoice-detail-loading" /> : null}
      {detailData?.invoice ? (
        <section className="rounded-lg border bg-white p-4 space-y-3" data-testid="dealer-invoice-detail-card">
          <div className="flex items-center justify-between" data-testid="dealer-invoice-detail-header">
            <h2 className="text-base font-semibold" data-testid="dealer-invoice-detail-title">Fatura Detayı • {detailData.invoice.invoice_no || '-'}</h2>
            <button type="button" className="h-8 rounded-md border px-2 text-xs" onClick={() => setDetailData(null)} data-testid="dealer-invoice-detail-close">Kapat</button>
          </div>
          <div className="grid gap-3 md:grid-cols-3" data-testid="dealer-invoice-detail-grid">
            <div className="rounded-md border p-3" data-testid="dealer-invoice-detail-status"><div className="text-xs text-muted-foreground">Durum</div><div className="mt-1"><FinanceStatusBadge status={detailData.invoice.status} testId="dealer-invoice-detail-status-badge" /></div></div>
            <div className="rounded-md border p-3" data-testid="dealer-invoice-detail-payment-status"><div className="text-xs text-muted-foreground">Ödeme Durumu</div><div className="mt-1"><FinanceStatusBadge status={detailData.invoice.payment_status || '-'} testId="dealer-invoice-detail-payment-status-badge" /></div></div>
            <div className="rounded-md border p-3" data-testid="dealer-invoice-detail-total"><div className="text-xs text-muted-foreground">Toplam Tutar</div><div className="mt-1 font-semibold">{formatMoneyMinor(detailData.invoice.amount_minor, detailData.invoice.currency_code || detailData.invoice.currency, locale)}</div></div>
          </div>

          <div className="rounded-md border overflow-hidden" data-testid="dealer-invoice-detail-payments-table-wrap">
            <table className="w-full text-sm" data-testid="dealer-invoice-detail-payments-table">
              <thead className="bg-slate-50">
                <tr>
                  <th className="text-left px-3 py-2">İşlem Ref</th>
                  <th className="text-left px-3 py-2">Durum</th>
                  <th className="text-left px-3 py-2">Tutar</th>
                  <th className="text-left px-3 py-2">Tarih</th>
                </tr>
              </thead>
              <tbody>
                {(detailData.payments || []).length === 0 ? (
                  <tr><td colSpan={4} className="px-3 py-3"><FinanceEmptyState testId="dealer-invoice-detail-payments-empty" message="Bu faturaya bağlı ödeme kaydı bulunmamaktadır." /></td></tr>
                ) : (
                  (detailData.payments || []).map((payment) => (
                    <tr key={payment.id} className="border-t" data-testid={`dealer-invoice-detail-payment-row-${payment.id}`}>
                      <td className="px-3 py-2 font-mono text-xs" data-testid={`dealer-invoice-detail-payment-ref-${payment.id}`}>{payment.provider_ref || payment.id}</td>
                      <td className="px-3 py-2" data-testid={`dealer-invoice-detail-payment-status-${payment.id}`}><FinanceStatusBadge status={payment.status} testId={`dealer-invoice-detail-payment-status-badge-${payment.id}`} /></td>
                      <td className="px-3 py-2" data-testid={`dealer-invoice-detail-payment-amount-${payment.id}`}>{formatMoneyMinor(payment.amount_minor, payment.currency, locale)}</td>
                      <td className="px-3 py-2" data-testid={`dealer-invoice-detail-payment-date-${payment.id}`}>{formatDate(payment.created_at, locale)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}
    </div>
  );
}
