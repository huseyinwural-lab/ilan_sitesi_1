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

const statusOptions = [
  { value: 'all', label: 'Tümü' },
  { value: 'unpaid', label: 'unpaid' },
  { value: 'paid', label: 'paid' },
  { value: 'cancelled', label: 'cancelled' },
];

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
  const [plans, setPlans] = useState([]);

  const [detailOpen, setDetailOpen] = useState(false);
  const [detailData, setDetailData] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [statusTarget, setStatusTarget] = useState('paid');
  const [statusNote, setStatusNote] = useState('');
  const [statusError, setStatusError] = useState(null);

  const [createOpen, setCreateOpen] = useState(false);
  const [createPayload, setCreatePayload] = useState({
    dealer_user_id: '',
    plan_id: '',
    amount_net: '',
    tax_rate: '',
    currency: 'EUR',
    issued_at: '',
  });
  const [createError, setCreateError] = useState(null);
  const [createLoading, setCreateLoading] = useState(false);

  const authHeader = useMemo(() => ({
    Authorization: `Bearer ${localStorage.getItem('access_token')}`,
  }), []);

  const toTestId = (value) => String(value || 'all')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-');

  const fetchInvoices = async () => {
    if (!urlCountry) {
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
      if (dealerId) params.set('dealer_user_id', dealerId);
      if (status !== 'all') params.set('status', status);
      const res = await axios.get(`${API}/admin/invoices?${params.toString()}`, {
        headers: authHeader,
      });
      setItems(res.data.items || []);
      setTotal(res.data.pagination?.total ?? 0);
    } catch (e) {
      console.error('Failed to fetch invoices', e);
    } finally {
      setLoading(false);
    }
  };

  const fetchPlans = async () => {
    if (!urlCountry) return;
    try {
      const res = await axios.get(`${API}/admin/plans?country=${urlCountry}`, {
        headers: authHeader,
      });
      setPlans(res.data.items || []);
    } catch (e) {
      console.error('Failed to fetch plans', e);
    }
  };

  const openDetail = async (invoiceId) => {
    setDetailOpen(true);
    setDetailLoading(true);
    setStatusError(null);
    try {
      const res = await axios.get(`${API}/admin/invoices/${invoiceId}`, {
        headers: authHeader,
      });
      setDetailData(res.data);
      setStatusTarget('paid');
      setStatusNote('');
    } catch (e) {
      console.error('Failed to load invoice detail', e);
    } finally {
      setDetailLoading(false);
    }
  };

  const closeDetail = () => {
    setDetailOpen(false);
    setDetailData(null);
  };

  const submitStatusChange = async () => {
    if (!detailData?.invoice?.id) return;
    setStatusError(null);
    try {
      await axios.post(
        `${API}/admin/invoices/${detailData.invoice.id}/status`,
        { target_status: statusTarget, note: statusNote || undefined },
        { headers: authHeader }
      );
      await fetchInvoices();
      await openDetail(detailData.invoice.id);
    } catch (e) {
      setStatusError(e.response?.data?.detail || 'Güncelleme başarısız');
    }
  };

  const openCreate = () => {
    setCreateOpen(true);
    setCreateError(null);
    setCreatePayload({
      dealer_user_id: '',
      plan_id: '',
      amount_net: '',
      tax_rate: '',
      currency: 'EUR',
      issued_at: '',
    });
  };

  const submitCreate = async () => {
    if (!urlCountry) {
      setCreateError('Ülke seçimi zorunlu');
      return;
    }
    if (!createPayload.dealer_user_id || !createPayload.plan_id) {
      setCreateError('Dealer ve plan zorunlu');
      return;
    }
    setCreateLoading(true);
    setCreateError(null);
    try {
      await axios.post(
        `${API}/admin/invoices`,
        {
          dealer_user_id: createPayload.dealer_user_id,
          country_code: urlCountry,
          plan_id: createPayload.plan_id,
          amount_net: Number(createPayload.amount_net),
          tax_rate: Number(createPayload.tax_rate),
          currency: createPayload.currency,
          issued_at: createPayload.issued_at || undefined,
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
    fetchInvoices();
    fetchPlans();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, dealerId, page, urlCountry]);

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
          className="h-9 px-3 rounded-md bg-primary text-primary-foreground text-sm"
          data-testid="invoice-create-open-button"
        >
          Yeni Invoice
        </button>
      </div>

      {!urlCountry && (
        <div className="border rounded-md p-4 text-sm text-muted-foreground" data-testid="invoice-country-required">
          Invoice listelemek için üstten country seçimi yapın.
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
          <SelectTrigger className="h-9 w-[180px]" data-testid="invoice-status-select">
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
      </div>

      <div className="flex items-center justify-between text-sm text-muted-foreground" data-testid="invoice-summary">
        <span data-testid="invoice-total-count">Toplam: {total}</span>
        <span data-testid="invoice-page-indicator">Sayfa: {page + 1}</span>
      </div>

      <div className="rounded-md border bg-card overflow-hidden" data-testid="invoice-table">
        <div className="hidden lg:grid grid-cols-[1.4fr_1fr_1fr_0.8fr_1fr_1fr] gap-4 bg-muted px-4 py-3 text-sm font-medium">
          <div>Dealer</div>
          <div>Plan</div>
          <div>Amount</div>
          <div>Status</div>
          <div>Issued</div>
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
                className="grid grid-cols-1 gap-4 px-4 py-4 lg:grid-cols-[1.4fr_1fr_1fr_0.8fr_1fr_1fr]"
                data-testid={`invoice-row-${inv.id}`}
              >
                <div>
                  <div className="text-xs uppercase text-muted-foreground lg:hidden">Dealer</div>
                  <div className="font-medium" data-testid={`invoice-dealer-${inv.id}`}>{inv.dealer_email || inv.dealer_user_id}</div>
                  <div className="text-xs text-muted-foreground">{inv.dealer_user_id}</div>
                </div>
                <div>
                  <div className="text-xs uppercase text-muted-foreground lg:hidden">Plan</div>
                  <div className="font-medium" data-testid={`invoice-plan-${inv.id}`}>{inv.plan_name || inv.plan_id}</div>
                </div>
                <div>
                  <div className="text-xs uppercase text-muted-foreground lg:hidden">Amount</div>
                  <div className="font-medium" data-testid={`invoice-amount-${inv.id}`}>{inv.amount_gross} {inv.currency}</div>
                  <div className="text-xs text-muted-foreground">Net: {inv.amount_net}</div>
                </div>
                <div data-testid={`invoice-status-${inv.id}`}>
                  <div className="text-xs uppercase text-muted-foreground lg:hidden">Status</div>
                  <span className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium bg-muted">{inv.status}</span>
                </div>
                <div>
                  <div className="text-xs uppercase text-muted-foreground lg:hidden">Issued</div>
                  <div className="text-xs" data-testid={`invoice-issued-${inv.id}`}>{inv.issued_at}</div>
                </div>
                <div className="flex justify-end">
                  <button
                    onClick={() => openDetail(inv.id)}
                    className="h-8 px-2.5 rounded-md border text-xs hover:bg-muted"
                    data-testid={`invoice-detail-${inv.id}`}
                  >
                    Detay
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
                  <p className="text-xs text-muted-foreground" data-testid="invoice-detail-id">{detailData.invoice.id}</p>
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
                      <div className="text-xs text-muted-foreground" data-testid="invoice-detail-dealer">{detailData.dealer?.email || detailData.invoice.dealer_user_id}</div>
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold">Plan</h4>
                      <div className="text-xs text-muted-foreground" data-testid="invoice-detail-plan">{detailData.plan?.name || detailData.invoice.plan_id}</div>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <h4 className="text-sm font-semibold">Amounts</h4>
                      <div className="text-xs text-muted-foreground" data-testid="invoice-detail-gross">Gross: {detailData.invoice.amount_gross} {detailData.invoice.currency}</div>
                      <div className="text-xs text-muted-foreground">Net: {detailData.invoice.amount_net}</div>
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold">Status</h4>
                      <div className="text-xs text-muted-foreground" data-testid="invoice-detail-status">{detailData.invoice.status}</div>
                    </div>
                  </div>
                  <div className="border rounded-md p-3 space-y-3">
                    <h4 className="text-sm font-semibold">Status Change</h4>
                    <Select value={statusTarget} onValueChange={setStatusTarget}>
                      <SelectTrigger className="h-9" data-testid="invoice-status-target-select">
                        <SelectValue placeholder="Status" />
                      </SelectTrigger>
                      <SelectContent>
                        {[{ value: 'paid', label: 'paid' }, { value: 'cancelled', label: 'cancelled' }].map((opt) => (
                          <SelectItem key={opt.value} value={opt.value} data-testid={`invoice-status-target-${toTestId(opt.value)}`}>
                            {opt.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <textarea
                      value={statusNote}
                      onChange={(e) => setStatusNote(e.target.value)}
                      className="w-full min-h-[80px] p-3 rounded-md border bg-background text-sm"
                      placeholder="Not (opsiyonel)"
                      data-testid="invoice-status-note"
                    />
                    {statusError && (
                      <div className="text-xs text-destructive" data-testid="invoice-status-error">{statusError}</div>
                    )}
                    <button
                      onClick={submitStatusChange}
                      className="h-9 px-3 rounded-md bg-primary text-primary-foreground text-sm"
                      data-testid="invoice-status-submit"
                    >
                      Status Güncelle
                    </button>
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
                value={createPayload.dealer_user_id}
                onChange={(e) => setCreatePayload({ ...createPayload, dealer_user_id: e.target.value })}
                placeholder="Dealer User ID"
                className="h-9 px-3 rounded-md border bg-background text-sm w-full"
                data-testid="invoice-create-dealer"
              />
              <Select value={createPayload.plan_id} onValueChange={(value) => setCreatePayload({ ...createPayload, plan_id: value })}>
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
                  value={createPayload.amount_net}
                  onChange={(e) => setCreatePayload({ ...createPayload, amount_net: e.target.value })}
                  placeholder="Amount Net"
                  className="h-9 px-3 rounded-md border bg-background text-sm"
                  data-testid="invoice-create-amount-net"
                />
                <input
                  value={createPayload.tax_rate}
                  onChange={(e) => setCreatePayload({ ...createPayload, tax_rate: e.target.value })}
                  placeholder="Tax Rate"
                  className="h-9 px-3 rounded-md border bg-background text-sm"
                  data-testid="invoice-create-tax-rate"
                />
              </div>
              <input
                value={createPayload.currency}
                onChange={(e) => setCreatePayload({ ...createPayload, currency: e.target.value })}
                placeholder="Currency"
                className="h-9 px-3 rounded-md border bg-background text-sm w-full"
                data-testid="invoice-create-currency"
              />
              <input
                value={createPayload.issued_at}
                onChange={(e) => setCreatePayload({ ...createPayload, issued_at: e.target.value })}
                placeholder="Issued At (ISO8601, optional)"
                className="h-9 px-3 rounded-md border bg-background text-sm w-full"
                data-testid="invoice-create-issued-at"
              />
              {createError && (
                <div className="text-xs text-destructive" data-testid="invoice-create-error">{createError}</div>
              )}
              <button
                onClick={submitCreate}
                className="h-9 px-3 rounded-md bg-primary text-primary-foreground text-sm"
                disabled={createLoading}
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
