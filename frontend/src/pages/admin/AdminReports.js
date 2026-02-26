import { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
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
  { value: 'open', label: 'open' },
  { value: 'in_review', label: 'in_review' },
  { value: 'resolved', label: 'resolved' },
  { value: 'dismissed', label: 'dismissed' },
];

const reasonOptions = [
  { value: 'all', label: 'Tümü' },
  { value: 'spam', label: 'spam' },
  { value: 'scam_fraud', label: 'scam_fraud' },
  { value: 'prohibited_item', label: 'prohibited_item' },
  { value: 'wrong_category', label: 'wrong_category' },
  { value: 'harassment', label: 'harassment' },
  { value: 'copyright', label: 'copyright' },
  { value: 'other', label: 'other' },
];

const messageReasonOptions = [
  { value: 'all', label: 'Tümü' },
  { value: 'spam', label: 'spam' },
  { value: 'scam', label: 'scam' },
  { value: 'abuse', label: 'abuse' },
  { value: 'other', label: 'other' },
];

const statusTransitions = {
  open: ['in_review'],
  in_review: ['resolved', 'dismissed'],
  resolved: [],
  dismissed: [],
};

export default function AdminReportsPage() {
  const [searchParams] = useSearchParams();
  const urlCountry = (searchParams.get('country') || '').toUpperCase();

  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const limit = 20;

  const [status, setStatus] = useState('all');
  const [reason, setReason] = useState('all');
  const [reportType, setReportType] = useState('listing');
  const [listingId, setListingId] = useState('');
  const [messageId, setMessageId] = useState('');

  const [detailOpen, setDetailOpen] = useState(false);
  const [detailData, setDetailData] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [statusTarget, setStatusTarget] = useState('');
  const [statusNote, setStatusNote] = useState('');
  const [statusError, setStatusError] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);

  const authHeader = useMemo(() => ({
    Authorization: `Bearer ${localStorage.getItem('access_token')}`,
  }), []);

  const toTestId = (value) => String(value || 'all')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-');

  const fetchReports = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set('skip', String(page * limit));
      params.set('limit', String(limit));
      if (status !== 'all') params.set('status', status);
      if (reason !== 'all') params.set('reason', reason);
      if (reportType === 'listing' && listingId) params.set('listing_id', listingId);
      if (reportType === 'message' && messageId) params.set('message_id', messageId);
      if (urlCountry) params.set('country', urlCountry);

      const endpoint = reportType === 'message' ? '/admin/reports/messages' : '/admin/reports';
      const res = await axios.get(`${API}${endpoint}?${params.toString()}`, {
        headers: authHeader,
      });
      setItems(res.data.items || []);
      setTotal(res.data.pagination?.total ?? 0);
    } catch (e) {
      console.error('Failed to fetch reports', e);
    } finally {
      setLoading(false);
    }
  };

  const openDetail = async (reportId, snapshot) => {
    setDetailOpen(true);
    setDetailLoading(true);
    setStatusError(null);
    try {
      if (reportType === 'message') {
        setDetailData(snapshot || null);
        const nextTargets = statusTransitions[snapshot?.status] || [];
        setStatusTarget(nextTargets[0] || '');
        setStatusNote('');
        return;
      }
      const params = new URLSearchParams();
      if (urlCountry) params.set('country', urlCountry);
      const res = await axios.get(`${API}/admin/reports/${reportId}?${params.toString()}`, {
        headers: authHeader,
      });
      setDetailData(res.data);
      const nextTargets = statusTransitions[res.data.status] || [];
      setStatusTarget(nextTargets[0] || '');
      setStatusNote('');
    } catch (e) {
      console.error('Failed to load report detail', e);
    } finally {
      setDetailLoading(false);
    }
  };

  const closeDetail = () => {
    setDetailOpen(false);
    setDetailData(null);
  };

  const submitStatusChange = async () => {
    if (!detailData) return;
    const note = statusNote.trim();
    if (!statusTarget) {
      setStatusError('Hedef durum seçin');
      return;
    }
    if (!note) {
      setStatusError('Not alanı zorunlu');
      return;
    }
    setStatusError(null);
    try {
      const params = new URLSearchParams();
      if (urlCountry) params.set('country', urlCountry);
      const endpoint = reportType === 'message'
        ? `${API}/admin/reports/messages/${detailData.id}/status`
        : `${API}/admin/reports/${detailData.id}/status`;
      await axios.post(
        `${endpoint}?${params.toString()}`,
        { target_status: statusTarget, note },
        { headers: authHeader }
      );
      await fetchReports();
      await openDetail(detailData.id);
    } catch (e) {
      setStatusError(e.response?.data?.detail || 'Güncelleme başarısız');
    }
  };

  const handleSoftDeleteListing = async () => {
    if (!detailData?.listing_id) return;
    const note = statusNote.trim() || 'Report action: soft delete';
    setActionLoading(true);
    setStatusError(null);
    try {
      await axios.post(
        `${API}/admin/listings/${detailData.listing_id}/soft-delete`,
        { reason: detailData.reason || 'other', reason_note: note },
        { headers: authHeader }
      );
      await fetchReports();
      await openDetail(detailData.id, detailData);
    } catch (e) {
      setStatusError(e.response?.data?.detail || 'Soft delete başarısız');
    } finally {
      setActionLoading(false);
    }
  };

  const handleSuspendSeller = async () => {
    const sellerId = detailData?.seller_summary?.id;
    if (!sellerId) {
      setStatusError('Suspend için seller id bulunamadı');
      return;
    }
    const note = statusNote.trim() || 'Report action: suspend';
    setActionLoading(true);
    setStatusError(null);
    try {
      await axios.post(
        `${API}/admin/users/${sellerId}/suspend`,
        { reason_code: detailData.reason || 'other', reason_detail: note },
        { headers: authHeader }
      );
      await fetchReports();
      await openDetail(detailData.id, detailData);
    } catch (e) {
      setStatusError(e.response?.data?.detail || 'Suspend başarısız');
    } finally {
      setActionLoading(false);
    }
  };

  const clearFilters = () => {
    setStatus('all');
    setReason('all');
    setListingId('');
    setMessageId('');
    setPage(0);
  };

  useEffect(() => {
    fetchReports();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, reason, listingId, messageId, page, urlCountry, reportType]);

  return (
    <div className="space-y-6" data-testid="admin-reports-page">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-bold" data-testid="admin-reports-title">Şikayetler</h1>
        <div className="text-xs text-muted-foreground" data-testid="admin-reports-context">
          Mod: <span className="font-semibold">{urlCountry ? `Country (${urlCountry})` : 'Global'}</span>
        </div>
      </div>

      <div className="flex flex-wrap gap-3 items-center" data-testid="reports-filters">
        <div className="inline-flex items-center rounded-md border overflow-hidden" data-testid="reports-type-toggle">
          <button
            onClick={() => { setReportType('listing'); setPage(0); }}
            className={`h-9 px-3 text-sm ${reportType === 'listing' ? 'bg-primary text-primary-foreground' : 'bg-background'}`}
            data-testid="reports-type-listing"
          >
            Raporlanan İlanlar
          </button>
          <button
            onClick={() => { setReportType('message'); setPage(0); }}
            className={`h-9 px-3 text-sm ${reportType === 'message' ? 'bg-primary text-primary-foreground' : 'bg-background'}`}
            data-testid="reports-type-message"
          >
            Raporlanan Mesajlar
          </button>
        </div>
        {reportType === 'listing' ? (
          <input
            value={listingId}
            onChange={(e) => { setListingId(e.target.value); setPage(0); }}
            placeholder="Listing ID"
            className="h-9 px-3 rounded-md border bg-background text-sm"
            data-testid="reports-listing-id-input"
          />
        ) : (
          <input
            value={messageId}
            onChange={(e) => { setMessageId(e.target.value); setPage(0); }}
            placeholder="Message ID"
            className="h-9 px-3 rounded-md border bg-background text-sm"
            data-testid="reports-message-id-input"
          />
        )}
        <Select value={status} onValueChange={(value) => { setStatus(value); setPage(0); }}>
          <SelectTrigger className="h-9 w-[180px]" data-testid="reports-status-select">
            <SelectValue placeholder="Tümü" />
          </SelectTrigger>
          <SelectContent>
            {statusOptions.map((opt) => (
              <SelectItem
                key={opt.value}
                value={opt.value}
                data-testid={`reports-status-option-${toTestId(opt.value)}`}
              >
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={reason} onValueChange={(value) => { setReason(value); setPage(0); }}>
          <SelectTrigger className="h-9 w-[220px]" data-testid="reports-reason-select">
            <SelectValue placeholder="Tümü" />
          </SelectTrigger>
          <SelectContent>
            {(reportType === 'message' ? messageReasonOptions : reasonOptions).map((opt) => (
              <SelectItem
                key={opt.value}
                value={opt.value}
                data-testid={`reports-reason-option-${toTestId(opt.value)}`}
              >
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <button
          onClick={clearFilters}
          className="h-9 px-3 rounded-md border text-sm hover:bg-muted"
          data-testid="reports-clear-filters-button"
        >
          Filtreleri Temizle
        </button>
      </div>

      <div className="flex items-center justify-between text-sm text-muted-foreground" data-testid="reports-summary">
        <span data-testid="reports-total-count">Toplam: {total}</span>
        <span data-testid="reports-page-indicator">Sayfa: {page + 1}</span>
      </div>

      <div className="rounded-md border bg-card overflow-hidden" data-testid="reports-table">
        <div className="hidden lg:grid grid-cols-[2fr_1.2fr_0.8fr_0.8fr_1fr] gap-4 bg-muted px-4 py-3 text-sm font-medium">
          <div>{reportType === 'message' ? 'Message' : 'Listing'}</div>
          <div>Reason</div>
          <div>Durum</div>
          <div>Ülke</div>
          <div className="text-right">Aksiyon</div>
        </div>
        <div className="divide-y">
          {loading ? (
            <div className="p-6 text-center" data-testid="reports-loading-state">Yükleniyor…</div>
          ) : items.length === 0 ? (
            <div className="p-6 text-center text-muted-foreground" data-testid="reports-empty-state">Kayıt yok</div>
          ) : (
            items.map((report) => (
              <div
                key={report.id}
                className="grid grid-cols-1 gap-4 px-4 py-4 lg:grid-cols-[2fr_1.2fr_0.8fr_0.8fr_1fr]"
                data-testid={`report-row-${report.id}`}
              >
                <div>
                  <div className="text-xs uppercase text-muted-foreground lg:hidden">Listing</div>
                  <div className="font-medium" data-testid={`report-listing-title-${report.id}`}>
                    {reportType === 'message' ? (report.message_preview || report.message_id) : (report.listing_title || report.listing_id)}
                  </div>
                  <div className="text-xs text-muted-foreground" data-testid={`report-listing-id-${report.id}`}>
                    {reportType === 'message' ? report.message_id : report.listing_id}
                  </div>
                  <div className="text-xs text-muted-foreground" data-testid={`report-seller-${report.id}`}>
                    {reportType === 'message' ? (report.reporter_email || '—') : (report.seller_email || '—')}
                  </div>
                </div>
                <div>
                  <div className="text-xs uppercase text-muted-foreground lg:hidden">Reason</div>
                  <div className="font-medium" data-testid={`report-reason-${report.id}`}>{report.reason}</div>
                  {report.reason_note && (
                    <div className="text-xs text-muted-foreground" data-testid={`report-reason-note-${report.id}`}>
                      {report.reason_note}
                    </div>
                  )}
                </div>
                <div data-testid={`report-status-${report.id}`}>
                  <div className="text-xs uppercase text-muted-foreground lg:hidden">Durum</div>
                  <span className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium bg-muted">
                    {report.status}
                  </span>
                </div>
                <div data-testid={`report-country-${report.id}`}>
                  <div className="text-xs uppercase text-muted-foreground lg:hidden">Ülke</div>
                  <div className="font-medium">{report.country_code || '—'}</div>
                  <div className="text-xs text-muted-foreground" data-testid={`report-reporter-${report.id}`}>
                    {report.reporter_email || 'anon'}
                  </div>
                </div>
                <div className="flex flex-col gap-2 lg:items-end">
                  <div className="text-xs uppercase text-muted-foreground lg:hidden">Aksiyon</div>
                  <div className="flex flex-wrap gap-2 lg:justify-end">
                    <button
                      onClick={() => openDetail(report.id, report)}
                      className="h-8 px-2.5 rounded-md border text-xs hover:bg-muted"
                      data-testid={`report-detail-${report.id}`}
                    >
                      Detay
                    </button>
                    {reportType === 'listing' && (
                      <>
                        <Link
                          to={urlCountry ? `/admin/moderation?country=${urlCountry}` : '/admin/moderation'}
                          className="h-8 px-2.5 rounded-md border text-xs hover:bg-muted"
                          data-testid={`report-moderation-link-${report.id}`}
                        >
                          Moderation’a Git
                        </Link>
                        <a
                          href={`/ilan/${report.listing_id}`}
                          target="_blank"
                          rel="noreferrer"
                          className="h-8 px-2.5 rounded-md border text-xs hover:bg-muted"
                          data-testid={`report-listing-link-${report.id}`}
                        >
                          Listing’e Git
                        </a>
                      </>
                    )}
                  </div>
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
          data-testid="reports-prev-page-button"
        >
          Prev
        </button>
        <button
          onClick={() => setPage(page + 1)}
          className="h-9 px-3 rounded-md border text-sm"
          data-testid="reports-next-page-button"
        >
          Next
        </button>
      </div>

      {detailOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" data-testid="report-detail-modal">
          <div className="bg-card rounded-lg border shadow-xl w-full max-w-2xl">
            <div className="p-4 border-b flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold" data-testid="report-detail-title">Report Detail</h3>
                {detailData && (
                  <p className="text-xs text-muted-foreground" data-testid="report-detail-id">{detailData.id}</p>
                )}
              </div>
              <button
                onClick={closeDetail}
                className="h-8 px-2.5 rounded-md border text-xs"
                data-testid="report-detail-close"
              >
                Kapat
              </button>
            </div>

            <div className="p-4 space-y-4">
              {detailLoading ? (
                <div className="text-sm" data-testid="report-detail-loading">Yükleniyor…</div>
              ) : detailData ? (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <h4 className="text-sm font-semibold">Report</h4>
                      <div className="text-xs text-muted-foreground" data-testid="report-detail-reason">Reason: {detailData.reason}</div>
                      {detailData.reason_note && (
                        <div className="text-xs text-muted-foreground" data-testid="report-detail-reason-note">Note: {detailData.reason_note}</div>
                      )}
                      <div className="text-xs text-muted-foreground" data-testid="report-detail-status">Status: {detailData.status}</div>
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold">Reporter</h4>
                      <div className="text-xs text-muted-foreground" data-testid="report-detail-reporter">
                        {detailData.reporter_summary?.email || 'anon'}
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <h4 className="text-sm font-semibold">Listing</h4>
                      <div className="text-xs text-muted-foreground" data-testid="report-detail-listing-title">
                        {detailData.listing_snapshot?.title || detailData.listing_id}
                      </div>
                      <div className="text-xs text-muted-foreground" data-testid="report-detail-listing-status">
                        Status: {detailData.listing_snapshot?.status || '—'}
                      </div>
                      <div className="text-xs text-muted-foreground" data-testid="report-detail-listing-price">
                        {detailData.listing_snapshot?.price ? `${detailData.listing_snapshot.price.toLocaleString()} ${detailData.listing_snapshot.currency}` : '—'}
                      </div>
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold">Seller</h4>
                      <div className="text-xs text-muted-foreground" data-testid="report-detail-seller-email">
                        {detailData.seller_summary?.email || '—'}
                      </div>
                      <div className="text-xs text-muted-foreground" data-testid="report-detail-seller-role">
                        {detailData.seller_summary?.role || '—'}
                      </div>
                    </div>
                  </div>

                  <div className="border rounded-md p-3 space-y-3">
                    <h4 className="text-sm font-semibold">Status Change</h4>
                    <Select
                      value={statusTarget}
                      onValueChange={(value) => setStatusTarget(value)}
                    >
                      <SelectTrigger className="h-9" data-testid="report-status-target-select">
                        <SelectValue placeholder="Hedef durum" />
                      </SelectTrigger>
                      <SelectContent>
                        {(statusTransitions[detailData.status] || []).map((opt) => (
                          <SelectItem
                            key={opt}
                            value={opt}
                            data-testid={`report-status-target-option-${toTestId(opt)}`}
                          >
                            {opt}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-muted-foreground" data-testid="report-status-note-label">Not (zorunlu)</p>
                    <textarea
                      value={statusNote}
                      onChange={(e) => setStatusNote(e.target.value)}
                      className="w-full min-h-[80px] p-3 rounded-md border bg-background text-sm"
                      placeholder="Not giriniz (zorunlu)"
                      data-testid="report-status-note-input"
                    />
                    {statusError && (
                      <div className="text-xs text-destructive" data-testid="report-status-error">{statusError}</div>
                    )}
                    <button
                      onClick={submitStatusChange}
                      className="h-9 px-3 rounded-md bg-primary text-primary-foreground text-sm"
                      data-testid="report-status-submit-button"
                      disabled={(statusTransitions[detailData.status] || []).length === 0}
                    >
                      Status Güncelle
                    </button>
                  </div>
                </>
              ) : (
                <div className="text-sm" data-testid="report-detail-empty">Detay bulunamadı</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
