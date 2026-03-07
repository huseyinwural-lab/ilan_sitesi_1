import React, { useCallback, useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const formatDateTime = (value) => {
  if (!value) return '-';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return '-';
  return parsed.toLocaleString('tr-TR');
};

export default function AdminReleaseRetention() {
  const resolveRequestLocale = () => {
    const pathLocale = String(window.location.pathname || '').split('/').filter(Boolean)[0]?.toLowerCase();
    if (['tr', 'de', 'fr'].includes(pathLocale)) return pathLocale;
    const stored = String(localStorage.getItem('language') || '').toLowerCase();
    if (['tr', 'de', 'fr'].includes(stored)) return stored;
    return 'tr';
  };

  const authHeaders = useMemo(() => {
    const locale = resolveRequestLocale();
    const pathLocale = String(window.location.pathname || '').split('/').filter(Boolean)[0]?.toLowerCase();
    return {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`,
      'Accept-Language': locale,
      'X-URL-Locale': ['tr', 'de', 'fr'].includes(pathLocale) ? pathLocale : locale,
    };
  }, []);

  const [retentionDays, setRetentionDays] = useState('21');
  const [loading, setLoading] = useState(false);
  const [executeLoading, setExecuteLoading] = useState(false);
  const [error, setError] = useState('');
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [dryRun, setDryRun] = useState(null);
  const [auditRows, setAuditRows] = useState([]);
  const [integritySummary, setIntegritySummary] = useState(null);

  const fetchDryRun = useCallback(async ({ silent = false } = {}) => {
    if (!silent) setLoading(true);
    if (!silent) setError('');
    try {
      const response = await axios.get(`${API}/admin/release-retention/dry-run`, {
        headers: authHeaders,
        params: { retention_window_days: Number(retentionDays) || 21 },
      });
      setDryRun(response.data?.dry_run || null);
      if (!silent) toast.success('Dry-run tamamlandı.');
    } catch (requestError) {
      const fallback = requestError?.response?.data?.detail || requestError?.message || 'Dry-run başarısız';
      setError(String(fallback));
      if (!silent) toast.error(String(fallback));
    } finally {
      if (!silent) setLoading(false);
    }
  }, [authHeaders, retentionDays]);

  const fetchAuditLogs = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/admin/release-retention/audit-logs`, {
        headers: authHeaders,
        params: { page: 1, limit: 10 },
      });
      setAuditRows(Array.isArray(response.data?.items) ? response.data.items : []);
    } catch {
      setAuditRows([]);
    }
  }, [authHeaders]);

  const fetchIntegrity = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/admin/release-retention/integrity-scan`, {
        headers: authHeaders,
        params: { write_report: 'true' },
      });
      setIntegritySummary(response.data?.report?.summary || null);
    } catch {
      setIntegritySummary(null);
    }
  }, [authHeaders]);

  useEffect(() => {
    fetchDryRun({ silent: true });
    fetchAuditLogs();
    fetchIntegrity();
  }, [fetchDryRun, fetchAuditLogs, fetchIntegrity]);

  const handleExecuteCleanup = async () => {
    setExecuteLoading(true);
    setError('');
    try {
      const expectedDeleteCount = Number(dryRun?.delete_candidates_count || 0);
      await axios.post(`${API}/admin/release-retention/execute`, {
        retention_window_days: Number(retentionDays) || 21,
        expected_delete_count: expectedDeleteCount,
        confirm: true,
        trigger_source: 'admin_panel',
      }, { headers: authHeaders });
      toast.success('Cleanup tamamlandı.');
      setConfirmOpen(false);
      fetchDryRun({ silent: true });
      fetchAuditLogs();
      fetchIntegrity();
    } catch (requestError) {
      const fallback = requestError?.response?.data?.detail || requestError?.message || 'Cleanup başarısız';
      setError(String(fallback));
      toast.error(String(fallback));
    } finally {
      setExecuteLoading(false);
    }
  };

  const keepItems = Array.isArray(dryRun?.keep) ? dryRun.keep : [];
  const deleteItems = Array.isArray(dryRun?.delete) ? dryRun.delete : [];

  return (
    <div className="space-y-5" data-testid="admin-release-retention-page">
      <section className="rounded-xl border bg-white p-4" data-testid="admin-release-retention-panel">
        <div className="flex flex-wrap items-center justify-between gap-3" data-testid="admin-release-retention-header">
          <div>
            <h1 className="text-sm font-semibold" data-testid="admin-release-retention-title">Release Retention</h1>
            <p className="text-xs text-slate-500" data-testid="admin-release-retention-subtitle">Dry-run, KEEP/DELETE önizleme diff, admin onaylı cleanup ve audit log.</p>
          </div>
          <div className="flex items-end gap-2" data-testid="admin-release-retention-actions">
            <label className="text-xs" data-testid="admin-release-retention-window-wrap">
              retention window (gün)
              <input
                type="number"
                min={1}
                max={3650}
                className="mt-1 h-9 w-32 rounded border px-2"
                value={retentionDays}
                onChange={(event) => setRetentionDays(event.target.value)}
                data-testid="admin-release-retention-window-input"
              />
            </label>
            <button
              type="button"
              className="h-9 rounded border px-3 text-xs"
              onClick={() => fetchDryRun()}
              disabled={loading}
              data-testid="admin-release-retention-dry-run-button"
            >
              {loading ? 'Çalışıyor...' : 'Dry-Run'}
            </button>
            <button
              type="button"
              className="h-9 rounded border px-3 text-xs"
              onClick={() => setConfirmOpen(true)}
              disabled={loading || executeLoading || deleteItems.length === 0}
              data-testid="admin-release-retention-execute-button"
            >
              Cleanup Execute
            </button>
          </div>
        </div>

        <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-4" data-testid="admin-release-retention-summary-grid">
          <article className="rounded border bg-slate-50 p-3" data-testid="admin-release-retention-total-card">
            <p className="text-[11px] text-slate-500">toplam artefact</p>
            <p className="text-lg font-semibold" data-testid="admin-release-retention-total-value">{Number(dryRun?.total_artifacts || 0)}</p>
          </article>
          <article className="rounded border bg-emerald-50 p-3" data-testid="admin-release-retention-keep-card">
            <p className="text-[11px] text-emerald-700">KEEP</p>
            <p className="text-lg font-semibold text-emerald-700" data-testid="admin-release-retention-keep-value">{Number(dryRun?.protected_count || 0)}</p>
          </article>
          <article className="rounded border bg-rose-50 p-3" data-testid="admin-release-retention-delete-card">
            <p className="text-[11px] text-rose-700">DELETE</p>
            <p className="text-lg font-semibold text-rose-700" data-testid="admin-release-retention-delete-value">{Number(dryRun?.delete_candidates_count || 0)}</p>
          </article>
          <article className="rounded border bg-slate-50 p-3" data-testid="admin-release-retention-window-card">
            <p className="text-[11px] text-slate-500">retention window</p>
            <p className="text-lg font-semibold" data-testid="admin-release-retention-window-value">{Number(dryRun?.retention_window_days || retentionDays)} gün</p>
          </article>
        </div>

        <div className="mt-3 grid grid-cols-1 gap-3 lg:grid-cols-2" data-testid="admin-release-retention-diff-wrap">
          <div className="rounded border bg-emerald-50 p-3" data-testid="admin-release-retention-keep-list-wrap">
            <p className="text-xs font-semibold text-emerald-700" data-testid="admin-release-retention-keep-list-title">KEEP</p>
            <div className="mt-2 max-h-64 overflow-y-auto" data-testid="admin-release-retention-keep-list">
              {keepItems.length === 0 ? (
                <p className="text-xs text-slate-500" data-testid="admin-release-retention-keep-empty">Kayıt yok</p>
              ) : keepItems.map((item, index) => (
                <div key={`keep-${item.release_id}-${index}`} className="mb-2 rounded border bg-white px-2 py-2 text-xs" data-testid={`admin-release-retention-keep-item-${index}`}>
                  <p className="font-semibold" data-testid={`admin-release-retention-keep-item-id-${index}`}>{item.release_id}</p>
                  <p className="text-slate-600" data-testid={`admin-release-retention-keep-item-reason-${index}`}>{item.reason}</p>
                  <p className="text-slate-500" data-testid={`admin-release-retention-keep-item-created-${index}`}>{formatDateTime(item.created_at)}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded border bg-rose-50 p-3" data-testid="admin-release-retention-delete-list-wrap">
            <p className="text-xs font-semibold text-rose-700" data-testid="admin-release-retention-delete-list-title">DELETE</p>
            <div className="mt-2 max-h-64 overflow-y-auto" data-testid="admin-release-retention-delete-list">
              {deleteItems.length === 0 ? (
                <p className="text-xs text-slate-500" data-testid="admin-release-retention-delete-empty">Silinecek aday yok</p>
              ) : deleteItems.map((item, index) => (
                <div key={`delete-${item.release_id}-${index}`} className="mb-2 rounded border bg-white px-2 py-2 text-xs" data-testid={`admin-release-retention-delete-item-${index}`}>
                  <p className="font-semibold" data-testid={`admin-release-retention-delete-item-id-${index}`}>{item.release_id}</p>
                  <p className="text-slate-600" data-testid={`admin-release-retention-delete-item-reason-${index}`}>{item.reason}</p>
                  <p className="text-slate-500" data-testid={`admin-release-retention-delete-item-created-${index}`}>{formatDateTime(item.created_at)}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-3 rounded border bg-slate-50 p-3" data-testid="admin-release-retention-integrity-summary-wrap">
          <div className="flex flex-wrap items-center justify-between gap-2" data-testid="admin-release-retention-integrity-summary-header">
            <p className="text-xs font-semibold" data-testid="admin-release-retention-integrity-summary-title">Artifact Integrity</p>
            <button
              type="button"
              className="h-8 rounded border px-2 text-xs"
              onClick={() => fetchIntegrity()}
              data-testid="admin-release-retention-integrity-refresh-button"
            >
              Integrity Tara
            </button>
          </div>
          <div className="mt-2 grid grid-cols-1 gap-2 md:grid-cols-4" data-testid="admin-release-retention-integrity-summary-grid">
            <div className="rounded border bg-white px-2 py-2" data-testid="admin-release-retention-integrity-total">
              <p className="text-[11px] text-slate-500">toplam</p>
              <p className="text-sm font-semibold">{Number(integritySummary?.total_artifacts || 0)}</p>
            </div>
            <div className="rounded border bg-white px-2 py-2" data-testid="admin-release-retention-integrity-valid">
              <p className="text-[11px] text-emerald-700">valid</p>
              <p className="text-sm font-semibold text-emerald-700">{Number(integritySummary?.valid_artifacts || 0)}</p>
            </div>
            <div className="rounded border bg-white px-2 py-2" data-testid="admin-release-retention-integrity-missing-meta">
              <p className="text-[11px] text-amber-700">missing metadata</p>
              <p className="text-sm font-semibold text-amber-700">{Number(integritySummary?.missing_metadata || 0)}</p>
            </div>
            <div className="rounded border bg-white px-2 py-2" data-testid="admin-release-retention-integrity-corrupted">
              <p className="text-[11px] text-rose-700">corrupted</p>
              <p className="text-sm font-semibold text-rose-700">{Number(integritySummary?.corrupted_artifacts || 0)}</p>
            </div>
          </div>
        </div>

        <div className="mt-3 rounded border bg-slate-50 p-3" data-testid="admin-release-retention-audit-wrap">
          <p className="text-xs font-semibold" data-testid="admin-release-retention-audit-title">Cleanup Audit Log</p>
          <div className="mt-2 max-h-52 overflow-y-auto space-y-2" data-testid="admin-release-retention-audit-list">
            {auditRows.length === 0 ? (
              <p className="text-xs text-slate-500" data-testid="admin-release-retention-audit-empty">Henüz cleanup kaydı yok.</p>
            ) : auditRows.map((row, index) => (
              <div key={`audit-${row.id}-${index}`} className="rounded border bg-white px-2 py-2 text-xs" data-testid={`admin-release-retention-audit-item-${index}`}>
                <p className="font-semibold" data-testid={`admin-release-retention-audit-id-${index}`}>{row.id}</p>
                <p data-testid={`admin-release-retention-audit-meta-${index}`}>
                  deleted: {Array.isArray(row.deleted_artifacts) ? row.deleted_artifacts.length : 0} • protected: {Array.isArray(row.protected_artifacts) ? row.protected_artifacts.length : 0}
                </p>
                <p className="text-slate-500" data-testid={`admin-release-retention-audit-time-${index}`}>{formatDateTime(row.cleanup_timestamp)}</p>
              </div>
            ))}
          </div>
        </div>

        {error ? (
          <p className="mt-3 text-xs text-rose-700" data-testid="admin-release-retention-error-message">{error}</p>
        ) : null}
      </section>

      {confirmOpen ? (
        <div className="fixed inset-0 z-50 bg-black/40 p-4" data-testid="admin-release-retention-confirm-overlay">
          <div className="mx-auto mt-24 max-w-lg rounded-lg border bg-white p-4" data-testid="admin-release-retention-confirm-modal">
            <h2 className="text-sm font-semibold" data-testid="admin-release-retention-confirm-title">Cleanup Onayı</h2>
            <p className="mt-2 text-xs text-slate-600" data-testid="admin-release-retention-confirm-description">
              Silinecek artefact sayısı: <span className="font-semibold" data-testid="admin-release-retention-confirm-delete-count">{deleteItems.length}</span>
            </p>
            <p className="mt-1 text-xs text-rose-700" data-testid="admin-release-retention-confirm-warning">Bu işlem geri alınamaz.</p>
            <div className="mt-4 flex items-center justify-end gap-2" data-testid="admin-release-retention-confirm-actions">
              <button
                type="button"
                className="h-9 rounded border px-3 text-xs"
                onClick={() => setConfirmOpen(false)}
                disabled={executeLoading}
                data-testid="admin-release-retention-confirm-cancel"
              >
                Vazgeç
              </button>
              <button
                type="button"
                className="h-9 rounded bg-rose-600 px-3 text-xs text-white"
                onClick={handleExecuteCleanup}
                disabled={executeLoading}
                data-testid="admin-release-retention-confirm-execute"
              >
                {executeLoading ? 'İşleniyor...' : 'Onayla ve Çalıştır'}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
