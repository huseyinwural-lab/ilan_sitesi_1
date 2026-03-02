import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { FinanceStatusBadge } from '@/components/finance/FinanceStatusBadge';
import { FinanceEmptyState, FinanceErrorState, FinanceLoadingState } from '@/components/finance/FinanceStateView';
import { formatMoneyMinor, resolveLocaleByCountry } from '@/utils/financeFormat';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AccountInvoicesPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [status, setStatus] = useState('all');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [detail, setDetail] = useState(null);
  const [downloadingId, setDownloadingId] = useState('');

  const authHeader = useMemo(() => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` }), []);
  const locale = resolveLocaleByCountry(localStorage.getItem('selectedCountry') || 'TR');

  const loadInvoices = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (status !== 'all') params.set('status', status);
      if (startDate) params.set('start_date', `${startDate}T00:00:00+00:00`);
      if (endDate) params.set('end_date', `${endDate}T23:59:59+00:00`);
      const res = await axios.get(`${API}/account/invoices?${params.toString()}`, { headers: authHeader });
      setItems(res.data.items || []);
      setError('');
    } catch {
      setError('Fatura kayıtları yüklenemedi. Lütfen daha sonra tekrar deneyiniz.');
    } finally {
      setLoading(false);
    }
  };

  const loadDetail = async (invoiceId) => {
    try {
      const res = await axios.get(`${API}/account/invoices/${invoiceId}`, { headers: authHeader });
      setDetail(res.data);
    } catch {
      setError('Fatura detayı alınamadı. Lütfen daha sonra tekrar deneyiniz.');
    }
  };

  const downloadPdf = async (invoiceId, invoiceNo) => {
    setDownloadingId(invoiceId);
    try {
      const res = await axios.get(`${API}/account/invoices/${invoiceId}/download-pdf`, { headers: authHeader, responseType: 'blob' });
      const blobUrl = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = `${invoiceNo || 'invoice'}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(blobUrl);
    } catch {
      setError('PDF indirilemedi. Lütfen daha sonra tekrar deneyiniz.');
    } finally {
      setDownloadingId('');
    }
  };

  const resolveInvoiceDate = (item) => {
    const source = item.issued_at || item.created_at;
    if (!source) return '-';
    return new Date(source).toLocaleDateString(locale);
  };

  useEffect(() => {
    loadInvoices();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, startDate, endDate]);

  return (
    <div className="space-y-4" data-testid="account-invoices-page">
      <div className="flex flex-wrap items-center justify-between gap-3" data-testid="account-invoices-header">
        <div>
          <h1 className="text-2xl font-bold" data-testid="account-invoices-title">Faturalarım</h1>
          <p className="text-sm text-muted-foreground" data-testid="account-invoices-subtitle">Fatura kayıtlarınızı görüntüleyebilir ve hazır PDF dosyalarını indirebilirsiniz.</p>
        </div>
        <div className="text-xs text-muted-foreground" data-testid="account-invoices-count">
          Toplam kayıt: {items.length}
        </div>
      </div>

      {error ? <FinanceErrorState testId="account-invoices-error" message={error} /> : null}

      <div className="grid gap-3 md:grid-cols-4" data-testid="account-invoices-filters">
        <select className="h-9 rounded-md border px-3 text-sm" value={status} onChange={(e) => setStatus(e.target.value)} data-testid="account-invoices-filter-status">
          <option value="all">Tüm durumlar</option>
          <option value="issued">Düzenlendi</option>
          <option value="paid">Ödendi</option>
          <option value="void">İptal</option>
          <option value="refunded">İade</option>
        </select>
        <input type="date" className="h-9 rounded-md border px-3 text-sm" value={startDate} onChange={(e) => setStartDate(e.target.value)} data-testid="account-invoices-filter-start" />
        <input type="date" className="h-9 rounded-md border px-3 text-sm" value={endDate} onChange={(e) => setEndDate(e.target.value)} data-testid="account-invoices-filter-end" />
        <button type="button" className="h-9 rounded-md bg-primary text-primary-foreground px-3 text-sm" onClick={loadInvoices} data-testid="account-invoices-filter-apply">Uygula</button>
      </div>

      <div className="rounded-lg border bg-white overflow-hidden" data-testid="account-invoices-table">
        <table className="w-full text-sm">
          <thead className="bg-muted">
            <tr>
              <th className="text-left p-3" data-testid="account-invoices-col-no">Fatura No</th>
              <th className="text-left p-3" data-testid="account-invoices-col-status">Durum</th>
              <th className="text-left p-3" data-testid="account-invoices-col-amount">Tutar</th>
              <th className="text-left p-3" data-testid="account-invoices-col-date">Tarih</th>
              <th className="text-left p-3" data-testid="account-invoices-col-pdf">PDF</th>
              <th className="text-right p-3" data-testid="account-invoices-col-actions">İşlem</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan="6" className="p-3"><FinanceLoadingState testId="account-invoices-loading" /></td></tr>
            ) : items.length === 0 ? (
              <tr><td colSpan="6" className="p-3"><FinanceEmptyState testId="account-invoices-empty" message="Henüz fatura kaydı bulunmamaktadır." /></td></tr>
            ) : items.map((item) => (
              <tr key={item.id} className="border-t" data-testid={`account-invoices-row-${item.id}`}>
                <td className="p-3" data-testid={`account-invoices-no-${item.id}`}>{item.invoice_no}</td>
                <td className="p-3"><FinanceStatusBadge status={item.status} testId={`account-invoices-status-${item.id}`} /></td>
                <td className="p-3" data-testid={`account-invoices-amount-${item.id}`}>{formatMoneyMinor(item.amount_minor, item.currency, locale)}</td>
                <td className="p-3" data-testid={`account-invoices-date-${item.id}`}>{resolveInvoiceDate(item)}</td>
                <td className="p-3" data-testid={`account-invoices-pdf-${item.id}`}>{item.pdf_url ? 'Hazır' : 'Hazır Değil'}</td>
                <td className="p-3 text-right">
                  <button type="button" className="h-8 px-2 rounded-md border text-xs mr-2" onClick={() => loadDetail(item.id)} data-testid={`account-invoices-detail-${item.id}`}>Detay</button>
                  {item.pdf_url ? (
                    <button type="button" className="h-8 px-2 rounded-md border text-xs" onClick={() => downloadPdf(item.id, item.invoice_no)} disabled={downloadingId === item.id} data-testid={`account-invoices-download-${item.id}`}>{downloadingId === item.id ? 'İndiriliyor...' : 'PDF İndir'}</button>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {detail ? (
        <div className="rounded-lg border bg-white p-4" data-testid="account-invoice-detail-panel">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold" data-testid="account-invoice-detail-title">{detail.invoice?.invoice_no}</h2>
            <button type="button" className="h-8 px-2 rounded-md border text-xs" onClick={() => setDetail(null)} data-testid="account-invoice-detail-close">Kapat</button>
          </div>
          <div className="mt-3 grid gap-2 text-sm">
            <div data-testid="account-invoice-detail-status">Durum: <FinanceStatusBadge status={detail.invoice?.status} testId="account-invoice-detail-status-badge" /></div>
            <div data-testid="account-invoice-detail-gross">Brüt: {formatMoneyMinor(detail.invoice?.gross_amount_minor, detail.invoice?.currency, locale)}</div>
            <div data-testid="account-invoice-detail-tax">Vergi: {formatMoneyMinor(detail.invoice?.tax_amount_minor, detail.invoice?.currency, locale)}</div>
            <div data-testid="account-invoice-detail-net">Net: {formatMoneyMinor(detail.invoice?.net_amount_minor, detail.invoice?.currency, locale)}</div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
