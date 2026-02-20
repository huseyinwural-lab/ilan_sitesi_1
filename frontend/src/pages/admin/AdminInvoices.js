import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import axios from 'axios';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const COUNTRY_OPTIONS = [
  { code: 'DE', label: 'DE', currency: 'EUR' },
  { code: 'AT', label: 'AT', currency: 'EUR' },
  { code: 'FR', label: 'FR', currency: 'EUR' },
  { code: 'CH', label: 'CH', currency: 'CHF' },
];

const statusOptions = [
  { value: 'all', label: 'Tümü' },
  { value: 'draft', label: 'draft' },
  { value: 'issued', label: 'issued' },
  { value: 'paid', label: 'paid' },
  { value: 'cancelled', label: 'cancelled' },
  { value: 'refunded', label: 'refunded' },
  { value: 'overdue', label: 'overdue' },
];

const resolveCurrency = (countryCode, scope = 'country') => {
  if (scope === 'global') return 'EUR';
  const match = COUNTRY_OPTIONS.find((item) => item.code === countryCode);
  return match?.currency || 'EUR';
};

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

const toDateInputValue = (date) => {
  const offset = date.getTimezoneOffset();
  const local = new Date(date.getTime() - offset * 60000);
  return local.toISOString().split('T')[0];
};

export default function AdminInvoicesPage() {
  const [searchParams] = useSearchParams();
  const urlCountry = (searchParams.get('country') || '').toUpperCase();

  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const limit = 20;

  const [status, setStatus] = useState('all');
  const [dealerId, setDealerId] = useState('');
  const [planFilter, setPlanFilter] = useState('all');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [amountMin, setAmountMin] = useState('');
  const [amountMax, setAmountMax] = useState('');
  const [plans, setPlans] = useState([]);

  const [detailOpen, setDetailOpen] = useState(false);
  const [detailData, setDetailData] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [statusError, setStatusError] = useState(null);

  const [createOpen, setCreateOpen] = useState(false);
  const [createPayload, setCreatePayload] = useState({
    dealer_id: '',
    plan_id: '',
    amount: '',
    currency_code: 'EUR',
    due_at: '',
    notes: '',
    issue_now: true,
  });
  const [createError, setCreateError] = useState(null);
  const [createLoading, setCreateLoading] = useState(false);

  const [dbReady, setDbReady] = useState(false);
  const [error, setError] = useState('');

  const authHeader = useMemo(() => ({
    Authorization: `Bearer ${localStorage.getItem('access_token')}`,
  }), []);

  const toTestId = (value) => String(value || 'all')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-');

  const disabledActions = !dbReady;
  const createDisabled = !urlCountry || disabledActions;

  const applyDatePreset = (days) => {
    const today = new Date();
    const from = new Date();
    from.setDate(today.getDate() - (days - 1));
    setDateFrom(toDateInputValue(from));
    setDateTo(toDateInputValue(today));
    setPage(0);
  };

  const clearDatePreset = () => {
    setDateFrom('');
    setDateTo('');
    setPage(0);
  };

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
    if (!urlCountry || !dbReady) {
      setItems([]);
      setTotal(0);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set('country', urlCountry);
      params.set('skip', String(page * limit));
      params.set('limit', String(limit));
      if (dealerId) params.set('dealer', dealerId);
      if (status !== 'all') params.set('status', status);
      if (planFilter !== 'all') params.set('plan_id', planFilter);
      if (dateFrom) params.set('date_from', dateFrom);
      if (dateTo) params.set('date_to', dateTo);
      if (amountMin) params.set('amount_min', amountMin);
      if (amountMax) params.set('amount_max', amountMax);
      const res = await axios.get(`${API}/admin/invoices?${params.toString()}`, {
        headers: authHeader,
      });
      setItems(res.data.items || []);
      setTotal(res.data.pagination?.total ?? 0);
      setError('');
    } catch (e) {
      setError('Invoices yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const fetchPlans = async () => {
    if (!urlCountry || !dbReady) {
      setPlans([]);
      return;
    }
    try {
      const params = new URLSearchParams();
      params.set('scope', 'country');
      params.set('country_code', urlCountry);
      const res = await axios.get(`${API}/admin/plans?${params.toString()}`, {
        headers: authHeader,
      });
      setPlans(res.data.items || []);
    } catch (e) {
      setPlans([]);
    }
  };

  const openDetail = async (invoiceId) => {
    if (disabledActions) return;
    setDetailOpen(true);
    setDetailLoading(true);
    setStatusError(null);
    try {
      const res = await axios.get(`${API}/admin/invoices/${invoiceId}`, {
        headers: authHeader,
      });
      setDetailData(res.data);
    } catch (e) {
      setStatusError('Detay yüklenemedi');
    } finally {
      setDetailLoading(false);
    }
  };

  const closeDetail = () => {
    setDetailOpen(false);
    setDetailData(null);
  };

  const markPaid = async (invoiceId) => {
    if (disabledActions) return;
    setStatusError(null);
    try {
      await axios.post(`${API}/admin/invoices/${invoiceId}/mark-paid`, {}, { headers: authHeader });
      await fetchInvoices();
      await openDetail(invoiceId);
    } catch (e) {
      setStatusError(e.response?.data?.detail || 'Ödeme işlenemedi');
    }
  };

  const cancelInvoice = async (invoiceId) => {
    if (disabledActions) return;
    setStatusError(null);
    try {
      await axios.post(`${API}/admin/invoices/${invoiceId}/cancel`, {}, { headers: authHeader });
      await fetchInvoices();
      await openDetail(invoiceId);
    } catch (e) {
      setStatusError(e.response?.data?.detail || 'Fatura iptal edilemedi');
    }
  };

  const refundInvoice = async (invoiceId) => {
    if (disabledActions) return;
    setStatusError(null);
    try {
      await axios.post(`${API}/admin/invoices/${invoiceId}/refund`, {}, { headers: authHeader });
      await fetchInvoices();
      await openDetail(invoiceId);
    } catch (e) {
      setStatusError(e.response?.data?.detail || 'İade başarısız');
    }
  };

  const openCreate = () => {
    if (createDisabled) return;
    setCreateOpen(true);
    setCreateError(null);
    setCreatePayload({
      dealer_id: '',
      plan_id: '',
      amount: '',
      currency_code: resolveCurrency(urlCountry || 'DE'),
      due_at: '',
      notes: '',
      issue_now: true,
    });
  };

  const submitCreate = async () => {
    if (!urlCountry) {
      setCreateError('Ülke seçimi zorunlu');
      return;
    }
    if (!createPayload.dealer_id || !createPayload.plan_id) {
      setCreateError('Dealer ve plan zorunlu');
      return;
    }
    setCreateLoading(true);
    setCreateError(null);
    try {
      await axios.post(
        `${API}/admin/invoices`,
        {
          dealer_id: createPayload.dealer_id,
          plan_id: createPayload.plan_id,
          amount: Number(createPayload.amount),
          currency_code: createPayload.currency_code,
          due_at: createPayload.due_at || undefined,
          notes: createPayload.notes || undefined,
          issue_now: createPayload.issue_now,
        },
        { headers: authHeader }
      );
      setCreateOpen(false);
      await fetchInvoices();
    } catch (e) {
      setCreateError(e.response?.data?.detail || 'Invoice oluşturulamadı');
    } finally {
      setCreateLoading(false);
    }
  };

  useEffect(() => {
    checkDb();
  }, []);

  useEffect(() => {
    fetchInvoices();
    fetchPlans();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, dealerId, page, urlCountry, planFilter, dateFrom, dateTo, amountMin, amountMax, dbReady]);

  return (
    <div className="space-y-6" data-testid="admin-invoices-page">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold" data-testid="admin-invoices-title">Invoices</h1>
          <div className="text-xs text-muted-foreground" data-testid="admin-invoices-context">
            Country: <span className="font-semibold">{urlCountry || 'Seçilmedi'}</span>
          </div>
        </div>
        <button
          onClick={openCreate}
          className="h-9 px-3 rounded-md bg-primary text-primary-foreground text-sm disabled:opacity-60"
          data-testid="invoice-create-open-button"
          disabled={createDisabled}
          title={!urlCountry ? 'Önce ülke seçin' : 'DB hazır değil'}
        >
          Yeni Invoice
        </button>
      </div>

      {!dbReady && (
        <div className="border border-amber-200 bg-amber-50 text-amber-900 rounded-md p-4" data-testid="invoice-db-banner">
          DB hazır değil → işlemler devre dışı. Ops ekibine DATABASE_URL + migration kontrolü gerekiyor.
        </div>
      )}

      {!urlCountry && (
        <div className="border rounded-md p-4 text-sm text-muted-foreground" data-testid="invoice-country-required">
          Invoice listelemek için üstten country seçimi yapın.
        </div>
      )}

      {error && (
        <div className="border border-red-200 bg-red-50 text-red-700 rounded-md p-3" data-testid="invoice-error">
          {error}
        </div>
      )}

      <div className="flex flex-wrap items-center gap-3" data-testid="invoice-filters">
        <input
          value={dealerId}
          onChange={(e) => { setDealerId(e.target.value); setPage(0); }}
          placeholder="Dealer User ID"
          className="h-9 px-3 rounded-md border bg-background text-sm"
          data-testid="invoice-dealer-filter-input"
        />
        <Select value={status} onValueChange={(value) => { setStatus(value); setPage(0); }}>
          <SelectTrigger className="h-9 w-[160px]" data-testid="invoice-status-select">
            <SelectValue placeholder="Tümü" />
          </SelectTrigger>
          <SelectContent>
            {statusOptions.map((opt) => (
              <SelectItem
                key={opt.value}
                value={opt.value}
                data-testid={`invoice-status-option-${toTestId(opt.value)}`}
              >
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={planFilter} onValueChange={(value) => { setPlanFilter(value); setPage(0); }}>
          <SelectTrigger className="h-9 w-[200px]" data-testid="invoice-plan-filter">
            <SelectValue placeholder="Plan" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all" data-testid="invoice-plan-filter-all">Tümü</SelectItem>
            {plans.map((plan) => (
              <SelectItem key={plan.id} value={plan.id} data-testid={`invoice-plan-filter-${toTestId(plan.id)}`}>
                {plan.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <input
          type="date"
          value={dateFrom}
          onChange={(e) => { setDateFrom(e.target.value); setPage(0); }}
          className="h-9 px-3 rounded-md border bg-background text-sm"
          data-testid="invoice-date-from"
        />
        <input
          type="date"
          value={dateTo}
          onChange={(e) => { setDateTo(e.target.value); setPage(0); }}
          className="h-9 px-3 rounded-md border bg-background text-sm"
          data-testid="invoice-date-to"
        />
        <input
          type="number"
          value={amountMin}
          onChange={(e) => { setAmountMin(e.target.value); setPage(0); }}
          placeholder="Min"
          className="h-9 px-3 rounded-md border bg-background text-sm w-[120px]"
          data-testid="invoice-amount-min"
        />
        <input
          type="number"
          value={amountMax}
          onChange={(e) => { setAmountMax(e.target.value); setPage(0); }}
          placeholder="Max"
          className="h-9 px-3 rounded-md border bg-background text-sm w-[120px]"
          data-testid="invoice-amount-max"
        />
      </div>

      <div className="flex items-center justify-between text-sm text-muted-foreground" data-testid="invoice-summary">
        <span data-testid="invoice-total-count">Toplam: {total}</span>
        <span data-testid="invoice-page-indicator">Sayfa: {page + 1}</span>
      </div>

      <div className="rounded-md border bg-card overflow-hidden" data-testid="invoice-table">
        <div className="hidden lg:grid grid-cols-[0.8fr_1.2fr_1fr_0.8fr_0.6fr_0.8fr_0.9fr_0.9fr_0.9fr_0.9fr_0.8fr_0.9fr] gap-4 bg-muted px-4 py-3 text-sm font-medium">
          <div>Invoice No</div>
          <div>Dealer</div>
          <div>Plan</div>
          <div>Amount</div>
          <div>Currency</div>
          <div>Status</div>
          <div>Issued</div>
          <div>Due Date</div>
          <div>Paid At</div>
          <div>Payment</div>
          <div>Scope</div>
          <div className="text-right">Aksiyon</div>
        </div>
        <div className="divide-y">
          {loading ? (
            <div className="p-6 text-center" data-testid="invoice-loading">Yükleniyor…</div>
          ) : items.length === 0 ? (
            <div className="p-6 text-center text-muted-foreground" data-testid="invoice-empty">Kayıt yok</div>
          ) : (
            items.map((inv) => (
              <div
                key={inv.id}
                className="grid grid-cols-1 gap-4 px-4 py-4 lg:grid-cols-[0.8fr_1.2fr_1fr_0.8fr_0.6fr_0.8fr_0.9fr_0.9fr_0.9fr_0.9fr_0.8fr_0.9fr]"
                data-testid={`invoice-row-${inv.id}`}
              >
                <div>
                  <div className="text-xs uppercase text-muted-foreground lg:hidden">Invoice No</div>
                  <div className="font-medium" data-testid={`invoice-no-${inv.id}`}>{inv.invoice_no || '-'}</div>
                </div>
                <div>
                  <div className="text-xs uppercase text-muted-foreground lg:hidden">Dealer</div>
                  <div className="font-medium" data-testid={`invoice-dealer-${inv.id}`}>{inv.dealer_email || inv.dealer_id}</div>
                  <div className="text-xs text-muted-foreground">{inv.dealer_id}</div>
                </div>
                <div>
                  <div className="text-xs uppercase text-muted-foreground lg:hidden">Plan</div>
                  <div className="font-medium" data-testid={`invoice-plan-${inv.id}`}>{inv.plan_name || inv.plan_id}</div>
                </div>
                <div>
                  <div className="text-xs uppercase text-muted-foreground lg:hidden">Amount</div>
                  <div className="font-medium" data-testid={`invoice-amount-${inv.id}`}>{inv.amount} </div>
                </div>
                <div>
                  <div className="text-xs uppercase text-muted-foreground lg:hidden">Currency</div>
                  <div className="font-medium" data-testid={`invoice-currency-${inv.id}`}>{inv.currency_code}</div>
                </div>
                <div data-testid={`invoice-status-${inv.id}`}>
                  <div className="text-xs uppercase text-muted-foreground lg:hidden">Status</div>
                  <span className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium bg-muted">{inv.status}</span>
                </div>
                <div>
                  <div className="text-xs uppercase text-muted-foreground lg:hidden">Issued</div>
                  <div className="text-xs" data-testid={`invoice-issued-${inv.id}`}>{formatDate(inv.issued_at)}</div>
                </div>
                <div>
                  <div className="text-xs uppercase text-muted-foreground lg:hidden">Due</div>
                  <div className="text-xs" data-testid={`invoice-due-${inv.id}`}>{formatDate(inv.due_at)}</div>
                </div>
                <div>
                  <div className="text-xs uppercase text-muted-foreground lg:hidden">Paid At</div>
                  <div className="text-xs" data-testid={`invoice-paid-${inv.id}`}>{formatDateTime(inv.paid_at)}</div>
                </div>
                <div>
                  <div className="text-xs uppercase text-muted-foreground lg:hidden">Payment</div>
                  <div className="text-xs" data-testid={`invoice-payment-${inv.id}`}>{inv.payment_method || '-'}</div>
                </div>
                <div>
                  <div className="text-xs uppercase text-muted-foreground lg:hidden">Scope</div>
                  <div className="text-xs" data-testid={`invoice-scope-${inv.id}`}>{inv.scope === 'country' ? `Country / ${inv.country_code}` : 'Global'}</div>
                </div>
                <div className="flex justify-end flex-wrap gap-2">
                  <button
                    onClick={() => openDetail(inv.id)}
                    className="h-8 px-2.5 rounded-md border text-xs hover:bg-muted disabled:opacity-60"
                    data-testid={`invoice-detail-${inv.id}`}
                    disabled={disabledActions}
                    title={disabledActions ? 'DB hazır değil' : 'Detay'}
                  >
                    Görüntüle
                  </button>
                  {(inv.status === 'issued' || inv.status === 'overdue') && (
                    <button
                      onClick={() => markPaid(inv.id)}
                      className="h-8 px-2.5 rounded-md border text-xs hover:bg-muted disabled:opacity-60"
                      data-testid={`invoice-mark-paid-${inv.id}`}
                      disabled={disabledActions}
                    >
                      Ödendi
                    </button>
                  )}
                  {inv.status === 'issued' && (
                    <button
                      onClick={() => cancelInvoice(inv.id)}
                      className="h-8 px-2.5 rounded-md border text-xs hover:bg-muted disabled:opacity-60"
                      data-testid={`invoice-cancel-${inv.id}`}
                      disabled={disabledActions}
                    >
                      İptal
                    </button>
                  )}
                  {inv.status === 'paid' && (
                    <button
                      onClick={() => refundInvoice(inv.id)}
                      className="h-8 px-2.5 rounded-md border text-xs hover:bg-muted disabled:opacity-60"
                      data-testid={`invoice-refund-${inv.id}`}
                      disabled={disabledActions}
                    >
                      İade
                    </button>
                  )}
                  <button
                    className="h-8 px-2.5 rounded-md border text-xs hover:bg-muted disabled:opacity-60"
                    data-testid={`invoice-pdf-${inv.id}`}
                    disabled
                  >
                    PDF
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="flex items-center justify-end gap-2">
        <button
          onClick={() => setPage(Math.max(0, page - 1))}
          disabled={page === 0}
          className="h-9 px-3 rounded-md border text-sm disabled:opacity-50"
          data-testid="invoice-prev-page"
        >
          Prev
        </button>
        <button
          onClick={() => setPage(page + 1)}
          className="h-9 px-3 rounded-md border text-sm"
          data-testid="invoice-next-page"
        >
          Next
        </button>
      </div>

      {detailOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" data-testid="invoice-detail-modal">
          <div className="bg-card rounded-lg border shadow-xl w-full max-w-2xl">
            <div className="p-4 border-b flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold" data-testid="invoice-detail-title">Invoice Detail</h3>
                {detailData?.invoice && (
                  <p className="text-xs text-muted-foreground" data-testid="invoice-detail-id">{detailData.invoice.invoice_no}</p>
                )}
              </div>
              <button
                onClick={closeDetail}
                className="h-8 px-2.5 rounded-md border text-xs"
                data-testid="invoice-detail-close"
              >
                Kapat
              </button>
            </div>
            <div className="p-4 space-y-4">
              {detailLoading ? (
                <div className="text-sm" data-testid="invoice-detail-loading">Yükleniyor…</div>
              ) : detailData?.invoice ? (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <h4 className="text-sm font-semibold">Dealer</h4>
                      <div className="text-xs text-muted-foreground" data-testid="invoice-detail-dealer">{detailData.dealer?.email || detailData.invoice.dealer_id}</div>
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold">Plan</h4>
                      <div className="text-xs text-muted-foreground" data-testid="invoice-detail-plan">{detailData.plan?.name || detailData.invoice.plan_id}</div>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <h4 className="text-sm font-semibold">Amount</h4>
                      <div className="text-xs text-muted-foreground" data-testid="invoice-detail-amount">{detailData.invoice.amount} {detailData.invoice.currency_code}</div>
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold">Status</h4>
                      <div className="text-xs text-muted-foreground" data-testid="invoice-detail-status">{detailData.invoice.status}</div>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <h4 className="text-sm font-semibold">Due Date</h4>
                      <div className="text-xs text-muted-foreground" data-testid="invoice-detail-due">{formatDate(detailData.invoice.due_at)}</div>
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold">Paid At</h4>
                      <div className="text-xs text-muted-foreground" data-testid="invoice-detail-paid">{formatDateTime(detailData.invoice.paid_at)}</div>
                    </div>
                  </div>
                  {statusError && (
                    <div className="text-xs text-destructive" data-testid="invoice-status-error">{statusError}</div>
                  )}
                  <div className="flex flex-wrap gap-2" data-testid="invoice-detail-actions">
                    {(detailData.invoice.status === 'issued' || detailData.invoice.status === 'overdue') && (
                      <button
                        onClick={() => markPaid(detailData.invoice.id)}
                        className="h-9 px-3 rounded-md bg-primary text-primary-foreground text-sm"
                        data-testid="invoice-detail-mark-paid"
                        disabled={disabledActions}
                      >
                        Mark Paid
                      </button>
                    )}
                    {detailData.invoice.status === 'issued' && (
                      <button
                        onClick={() => cancelInvoice(detailData.invoice.id)}
                        className="h-9 px-3 rounded-md border text-sm"
                        data-testid="invoice-detail-cancel"
                        disabled={disabledActions}
                      >
                        Cancel
                      </button>
                    )}
                    {detailData.invoice.status === 'paid' && (
                      <button
                        onClick={() => refundInvoice(detailData.invoice.id)}
                        className="h-9 px-3 rounded-md border text-sm"
                        data-testid="invoice-detail-refund"
                        disabled={disabledActions}
                      >
                        Refund
                      </button>
                    )}
                  </div>
                </>
              ) : (
                <div className="text-sm" data-testid="invoice-detail-empty">Detay bulunamadı</div>
              )}
            </div>
          </div>
        </div>
      )}

      {createOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" data-testid="invoice-create-modal">
          <div className="bg-card rounded-lg border shadow-xl w-full max-w-xl">
            <div className="p-4 border-b flex items-center justify-between">
              <h3 className="text-lg font-semibold" data-testid="invoice-create-title">Invoice Oluştur</h3>
              <button
                onClick={() => setCreateOpen(false)}
                className="h-8 px-2.5 rounded-md border text-xs"
                data-testid="invoice-create-close"
              >
                Kapat
              </button>
            </div>
            <div className="p-4 space-y-3">
              <div className="text-xs text-muted-foreground" data-testid="invoice-create-country">Country: {urlCountry || 'Seçilmedi'}</div>
              <input
                value={createPayload.dealer_id}
                onChange={(e) => setCreatePayload({ ...createPayload, dealer_id: e.target.value })}
                placeholder="Dealer User ID"
                className="h-9 px-3 rounded-md border bg-background text-sm w-full"
                data-testid="invoice-create-dealer"
              />
              <Select
                value={createPayload.plan_id}
                onValueChange={(value) => {
                  const plan = plans.find((item) => item.id === value);
                  setCreatePayload({
                    ...createPayload,
                    plan_id: value,
                    amount: plan?.price_amount ?? createPayload.amount,
                    currency_code: plan?.currency_code || resolveCurrency(urlCountry || 'DE'),
                  });
                }}
              >
                <SelectTrigger className="h-9" data-testid="invoice-create-plan-select">
                  <SelectValue placeholder="Plan seçin" />
                </SelectTrigger>
                <SelectContent>
                  {plans.map((plan) => (
                    <SelectItem key={plan.id} value={plan.id} data-testid={`invoice-create-plan-${toTestId(plan.id)}`}>
                      {plan.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <input
                  value={createPayload.amount}
                  onChange={(e) => setCreatePayload({ ...createPayload, amount: e.target.value })}
                  placeholder="Amount"
                  className="h-9 px-3 rounded-md border bg-background text-sm"
                  data-testid="invoice-create-amount"
                  type="number"
                />
                <input
                  value={createPayload.currency_code}
                  readOnly
                  placeholder="Currency"
                  className="h-9 px-3 rounded-md border bg-muted text-sm"
                  data-testid="invoice-create-currency"
                />
              </div>
              <input
                value={createPayload.due_at}
                onChange={(e) => setCreatePayload({ ...createPayload, due_at: e.target.value })}
                placeholder="Due Date"
                type="date"
                className="h-9 px-3 rounded-md border bg-background text-sm w-full"
                data-testid="invoice-create-due"
              />
              <textarea
                value={createPayload.notes}
                onChange={(e) => setCreatePayload({ ...createPayload, notes: e.target.value })}
                placeholder="Notlar"
                className="w-full min-h-[80px] p-3 rounded-md border bg-background text-sm"
                data-testid="invoice-create-notes"
              />
              <label className="flex items-center gap-2 text-sm" data-testid="invoice-create-issue-now">
                <input
                  type="checkbox"
                  checked={createPayload.issue_now}
                  onChange={(e) => setCreatePayload({ ...createPayload, issue_now: e.target.checked })}
                  data-testid="invoice-create-issue-now-checkbox"
                />
                Issue now
              </label>
              {createError && (
                <div className="text-xs text-destructive" data-testid="invoice-create-error">{createError}</div>
              )}
              <button
                onClick={submitCreate}
                className="h-9 px-3 rounded-md bg-primary text-primary-foreground text-sm"
                disabled={createLoading || disabledActions}
                data-testid="invoice-create-submit"
              >
                {createLoading ? 'Oluşturuluyor…' : 'Oluştur'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
