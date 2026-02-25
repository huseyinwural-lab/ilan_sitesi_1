import React, { useMemo, useState } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function DealerPrivacyCenter() {
  const [exporting, setExporting] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteReason, setDeleteReason] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const authHeader = useMemo(() => ({
    Authorization: `Bearer ${localStorage.getItem('access_token')}`,
  }), []);

  const handleExport = async () => {
    setExporting(true);
    setError('');
    setSuccess('');
    try {
      const res = await fetch(`${API}/v1/users/me/data-export`, { headers: authHeader });
      if (!res.ok) {
        throw new Error('Export oluşturulamadı');
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = 'gdpr-export.json';
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.URL.revokeObjectURL(url);
      setSuccess('Veri dışa aktarma tamamlandı.');
    } catch (err) {
      setError(err?.message || 'Export başarısız');
    } finally {
      setExporting(false);
    }
  };

  const handleDelete = async () => {
    setDeleting(true);
    setError('');
    setSuccess('');
    try {
      const res = await fetch(`${API}/v1/users/me/account`, {
        method: 'DELETE',
        headers: {
          ...authHeader,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ reason: deleteReason || 'user_request' }),
      });
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail?.detail || 'Silme isteği başarısız');
      }
      setSuccess('Hesap silme talebiniz alındı (30 gün bekleme süresi).');
    } catch (err) {
      setError(err?.message || 'Silme isteği başarısız');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="dealer-privacy-center">
      <div>
        <h1 className="text-2xl font-bold" data-testid="dealer-privacy-title">Gizlilik Merkezi</h1>
        <p className="text-sm text-muted-foreground" data-testid="dealer-privacy-subtitle">
          GDPR uyumlu veri erişimi ve hesap yönetimi.
        </p>
      </div>

      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700" data-testid="dealer-privacy-error">
          {error}
        </div>
      )}
      {success && (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700" data-testid="dealer-privacy-success">
          {success}
        </div>
      )}

      <div className="rounded-xl border p-4" data-testid="dealer-privacy-export">
        <h2 className="text-lg font-semibold" data-testid="dealer-privacy-export-title">Veri Dışa Aktarım</h2>
        <p className="text-sm text-muted-foreground" data-testid="dealer-privacy-export-desc">
          Hesabınıza ait tüm kişisel verileri JSON formatında indirebilirsiniz.
        </p>
        <button
          type="button"
          className="mt-3 rounded-md bg-[var(--brand-navy)] px-4 py-2 text-sm text-white"
          onClick={handleExport}
          disabled={exporting}
          data-testid="dealer-privacy-export-button"
        >
          {exporting ? 'Hazırlanıyor...' : 'Verileri indir'}
        </button>
      </div>

      <div className="rounded-xl border p-4" data-testid="dealer-privacy-delete">
        <h2 className="text-lg font-semibold" data-testid="dealer-privacy-delete-title">Hesap Silme</h2>
        <p className="text-sm text-muted-foreground" data-testid="dealer-privacy-delete-desc">
          Talep gönderildiğinde hesap 30 gün sonra kalıcı olarak silinir.
        </p>
        <textarea
          className="mt-3 w-full rounded-md border p-3 text-sm"
          rows={3}
          value={deleteReason}
          onChange={(e) => setDeleteReason(e.target.value)}
          placeholder="Silme nedeni (opsiyonel)"
          data-testid="dealer-privacy-delete-reason"
        />
        <button
          type="button"
          className="mt-3 rounded-md border border-rose-300 px-4 py-2 text-sm text-rose-700"
          onClick={handleDelete}
          disabled={deleting}
          data-testid="dealer-privacy-delete-button"
        >
          {deleting ? 'Talep gönderiliyor...' : 'Hesap silme talebi gönder'}
        </button>
      </div>
    </div>
  );
}
