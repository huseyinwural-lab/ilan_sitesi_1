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
        <div className="text-sm font-semibold">Veri İndirme (JSON)</div>
        <p className="text-xs text-muted-foreground mt-1">GDPR export dosyanızı indirebilirsiniz.</p>
        {exportError && (
          <div className="text-xs text-rose-600 mt-2" data-testid="privacy-export-error">{exportError}</div>
        )}
        {exportSuccess && (
          <div className="text-xs text-emerald-600 mt-2" data-testid="privacy-export-success">{exportSuccess}</div>
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
