import React, { useEffect, useState } from 'react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AccountPrivacyCenter() {
  const [marketingConsent, setMarketingConsent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [exportLoading, setExportLoading] = useState(false);
  const [exportError, setExportError] = useState('');
  const [exportSuccess, setExportSuccess] = useState('');
  const [exportHistory, setExportHistory] = useState([]);
  const [exportHistoryLoading, setExportHistoryLoading] = useState(false);
  const [exportHistoryError, setExportHistoryError] = useState('');
  const [exportTab, setExportTab] = useState('request');
  const [deleteReason, setDeleteReason] = useState('');
  const [deleteStatus, setDeleteStatus] = useState('');

  const fetchProfile = async () => {
    try {
      const res = await fetch(`${API}/v1/users/me/profile`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      });
      if (!res.ok) return;
      const data = await res.json();
      setMarketingConsent(Boolean(data.marketing_consent));
    } catch (err) {
      // ignore
    }
  };

  const fetchExportHistory = async () => {
    setExportHistoryLoading(true);
    setExportHistoryError('');
    try {
      const res = await fetch(`${API}/v1/users/me/gdpr-exports`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      });
      if (!res.ok) {
        throw new Error('History fetch failed');
      }
      const data = await res.json();
      setExportHistory(data.items || []);
    } catch (err) {
      setExportHistoryError('Geçmiş yüklenemedi');
    } finally {
      setExportHistoryLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
    fetchExportHistory();
  }, []);

  const handleConsentToggle = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/v1/users/me/profile`, {
        method: 'PUT',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ marketing_consent: !marketingConsent }),
      });
      if (!res.ok) {
        throw new Error('Güncellenemedi');
      }
      setMarketingConsent((prev) => !prev);
    } catch (err) {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    setExportLoading(true);
    setExportError('');
    setExportSuccess('');
    try {
      const res = await fetch(`${API}/v1/users/me/data-export`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      });
      if (!res.ok) {
        throw new Error('Export başarısız');
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'gdpr-export.json';
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      setExportSuccess('Veri dışa aktarma tamamlandı. Dosya indiriliyor.');
      await fetchExportHistory();
    } catch (err) {
      setExportError('Export indirilemedi');
    } finally {
      setExportLoading(false);
    }
  };

  const handleDownloadExport = async (exportItem) => {
    setExportHistoryError('');
    try {
      const res = await fetch(`${API}/v1/users/me/gdpr-exports/${exportItem.id}/download`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      });
      if (res.status === 410) {
        setExportHistoryError('Dosya süresi dolmuş.');
        return;
      }
      if (!res.ok) {
        throw new Error('Download failed');
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = exportItem.file_path || 'gdpr-export.json';
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setExportHistoryError('Dosya indirilemedi');
    }
  };

  const exportStatusLabel = (status) => {
    switch ((status || '').toLowerCase()) {
      case 'ready':
        return { label: 'Hazır', tone: 'text-emerald-600 bg-emerald-50' };
      case 'pending':
        return { label: 'Hazırlanıyor', tone: 'text-amber-600 bg-amber-50' };
      case 'expired':
        return { label: 'Süresi Doldu', tone: 'text-slate-500 bg-slate-100' };
      default:
        return { label: status || 'Bilinmiyor', tone: 'text-slate-600 bg-slate-100' };
    }
  };

  const formatDate = (value) => {
    if (!value) return '-';
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return '-';
    return parsed.toLocaleString();
  };

  const handleDeleteAccount = async () => {
    setDeleteStatus('');
    try {
      const res = await fetch(`${API}/v1/users/me/account`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ reason: deleteReason || 'user_request' }),
      });
      if (!res.ok) {
        throw new Error('Silme talebi başarısız');
      }
      const data = await res.json();
      setDeleteStatus(`Silme planlandı: ${data.gdpr_deleted_at}`);
    } catch (err) {
      setDeleteStatus('Silme talebi alınamadı');
    }
  };

  return (
    <div className="space-y-6" data-testid="privacy-center-page">
      <div className="rounded-lg border bg-white p-6" data-testid="privacy-consent-card">
        <div className="text-sm font-semibold">Consent Ayarları</div>
        <p className="text-xs text-muted-foreground mt-1">
          Pazarlama iletişimleri için onayınızı yönetin.
        </p>
        <button
          type="button"
          onClick={handleConsentToggle}
          disabled={loading}
          className="mt-3 h-9 px-4 rounded-md border text-sm disabled:opacity-60"
          data-testid="privacy-consent-toggle"
        >
          {marketingConsent ? 'Marketing Consent: Açık' : 'Marketing Consent: Kapalı'}
        </button>
      </div>

      <div className="rounded-lg border bg-white p-6" data-testid="privacy-export-card">
        <div className="flex flex-wrap items-start justify-between gap-3" data-testid="privacy-export-header">
          <div>
            <div className="text-sm font-semibold" data-testid="privacy-export-title">Veri Dışa Aktarım</div>
            <p className="text-xs text-muted-foreground mt-1" data-testid="privacy-export-desc">GDPR export dosyanızı indirebilir ve geçmiş talepleri takip edebilirsiniz.</p>
          </div>
          <div className="flex items-center gap-2" data-testid="privacy-export-tabs">
            <button
              type="button"
              onClick={() => setExportTab('request')}
              className={`h-8 px-3 rounded-full text-xs border ${exportTab === 'request' ? 'bg-slate-900 text-white border-slate-900' : 'bg-white text-slate-600'}`}
              data-testid="privacy-export-tab-request"
            >
              Yeni Export
            </button>
            <button
              type="button"
              onClick={() => setExportTab('history')}
              className={`h-8 px-3 rounded-full text-xs border ${exportTab === 'history' ? 'bg-slate-900 text-white border-slate-900' : 'bg-white text-slate-600'}`}
              data-testid="privacy-export-tab-history"
            >
              Export Geçmişi
            </button>
          </div>
        </div>

        {exportTab === 'request' && (
          <div className="mt-4" data-testid="privacy-export-request-panel">
            {exportError && (
              <div className="text-xs text-rose-600" data-testid="privacy-export-error">{exportError}</div>
            )}
            {exportSuccess && (
              <div className="text-xs text-emerald-600" data-testid="privacy-export-success">{exportSuccess}</div>
            )}
            <button
              type="button"
              onClick={handleExport}
              disabled={exportLoading}
              className="mt-3 h-9 px-4 rounded-md border text-sm disabled:opacity-60"
              data-testid="privacy-export-button"
            >
              {exportLoading ? 'Hazırlanıyor...' : 'Veri Dışa Aktar'}
            </button>
          </div>
        )}

        {exportTab === 'history' && (
          <div className="mt-4 space-y-3" data-testid="privacy-export-history-panel">
            {exportHistoryError && (
              <div className="text-xs text-rose-600" data-testid="privacy-export-history-error">{exportHistoryError}</div>
            )}
            {exportHistoryLoading ? (
              <div className="text-xs text-muted-foreground" data-testid="privacy-export-history-loading">Yükleniyor…</div>
            ) : exportHistory.length === 0 ? (
              <div className="text-xs text-muted-foreground" data-testid="privacy-export-history-empty">Henüz export talebi yok.</div>
            ) : (
              <div className="rounded-md border overflow-hidden" data-testid="privacy-export-history-table">
                <div className="grid grid-cols-4 gap-2 bg-slate-50 px-3 py-2 text-[11px] font-semibold text-slate-500" data-testid="privacy-export-history-header">
                  <div data-testid="privacy-export-history-header-requested">İstek Tarihi</div>
                  <div data-testid="privacy-export-history-header-status">Durum</div>
                  <div data-testid="privacy-export-history-header-expires">Son Geçerlilik</div>
                  <div className="text-right" data-testid="privacy-export-history-header-download">Download</div>
                </div>
                <div className="divide-y">
                  {exportHistory.map((item) => {
                    const statusMeta = exportStatusLabel(item.status);
                    const isExpired = (item.status || '').toLowerCase() === 'expired';
                    const isReady = (item.status || '').toLowerCase() === 'ready';
                    return (
                      <div key={item.id} className="grid grid-cols-4 gap-2 px-3 py-3 text-xs" data-testid={`privacy-export-history-row-${item.id}`}>
                        <div data-testid={`privacy-export-history-requested-${item.id}`}>{formatDate(item.requested_at)}</div>
                        <div>
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium ${statusMeta.tone}`} data-testid={`privacy-export-history-status-${item.id}`}>
                            {statusMeta.label}
                          </span>
                        </div>
                        <div data-testid={`privacy-export-history-expires-${item.id}`}>{formatDate(item.expires_at)}</div>
                        <div className="text-right">
                          <button
                            type="button"
                            onClick={() => handleDownloadExport(item)}
                            disabled={!isReady || isExpired}
                            className="text-blue-600 underline text-xs disabled:text-slate-400 disabled:no-underline"
                            data-testid={`privacy-export-history-download-${item.id}`}
                          >
                            İndir
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="rounded-lg border bg-white p-6" data-testid="privacy-cookie-card">
        <div className="text-sm font-semibold">Çerez Tercihleri</div>
        <p className="text-xs text-muted-foreground mt-1">
          Çerez ayarlarınızı yönetin.
        </p>
        <a
          href="/cookies"
          className="mt-3 inline-block text-sm text-blue-600 underline"
          data-testid="privacy-cookie-link"
        >
          Çerez tercihlerini yönet
        </a>
      </div>

      <div className="rounded-lg border bg-white p-6" data-testid="privacy-delete-card">
        <div className="text-sm font-semibold">Hesap Silme (GDPR)</div>
        <p className="text-xs text-muted-foreground mt-1">
          Hesabınız 30 gün içinde kalıcı olarak silinir.
        </p>
        <input
          value={deleteReason}
          onChange={(e) => setDeleteReason(e.target.value)}
          className="mt-3 h-10 w-full rounded-md border px-3 text-sm"
          placeholder="Silme nedeni (opsiyonel)"
          data-testid="privacy-delete-reason"
        />
        <button
          type="button"
          onClick={handleDeleteAccount}
          className="mt-3 h-9 px-4 rounded-md border text-sm"
          data-testid="privacy-delete-button"
        >
          Hesap Silme Talebi Gönder
        </button>
        {deleteStatus && (
          <div className="text-xs text-muted-foreground mt-2" data-testid="privacy-delete-status">
            {deleteStatus}
          </div>
        )}
      </div>
    </div>
  );
}
