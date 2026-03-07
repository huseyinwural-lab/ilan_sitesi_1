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

const normalizeErrorText = (value, fallback = '-') => {
  if (typeof value === 'string' && value.trim()) return value;
  if (value && typeof value === 'object') {
    if (typeof value.message === 'string' && value.message.trim()) return value.message;
    if (typeof value.error === 'string' && value.error.trim()) return value.error;
    try {
      return JSON.stringify(value);
    } catch {
      return fallback;
    }
  }
  return fallback;
};

export default function AdminPresetRuns() {
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

  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [limit] = useState(20);
  const [total, setTotal] = useState(0);
  const [statusFilter, setStatusFilter] = useState('');
  const [fromDateFilter, setFromDateFilter] = useState('');
  const [toDateFilter, setToDateFilter] = useState('');
  const [extendedExport, setExtendedExport] = useState(false);
  const [exportLoading, setExportLoading] = useState(false);
  const [jobsLoading, setJobsLoading] = useState(false);
  const [jobActionLoadingId, setJobActionLoadingId] = useState('');
  const [exportJobs, setExportJobs] = useState([]);
  const [expandedRunIds, setExpandedRunIds] = useState([]);

  const fetchRuns = useCallback(async ({ silent = false } = {}) => {
    setLoading(true);
    if (!silent) setError('');
    try {
      const response = await axios.get(`${API}/admin/preset-runs`, {
        headers: authHeaders,
        params: {
          page,
          limit,
          status: statusFilter || undefined,
          from: fromDateFilter || undefined,
          to: toDateFilter || undefined,
        },
      });
      const items = Array.isArray(response.data?.items) ? response.data.items : [];
      setRows(items);
      setTotal(Number(response.data?.total || 0));
      setExpandedRunIds((previous) => previous.filter((runId) => items.some((item) => item.id === runId)));
      setError('');
    } catch (requestError) {
      const fallback = requestError?.response?.data?.detail || requestError?.message || 'Preset run geçmişi alınamadı';
      setRows([]);
      setTotal(0);
      setError(String(fallback));
      if (!silent) toast.error(String(fallback));
    } finally {
      setLoading(false);
    }
  }, [authHeaders, page, limit, statusFilter, fromDateFilter, toDateFilter]);

  useEffect(() => {
    fetchRuns({ silent: true });
  }, [fetchRuns]);

  const fetchExportJobs = useCallback(async ({ silent = false } = {}) => {
    if (!silent) setJobsLoading(true);
    try {
      const response = await axios.get(`${API}/admin/preset-runs/export-jobs`, {
        headers: authHeaders,
        params: { page: 1, limit: 20 },
      });
      const items = Array.isArray(response.data?.items) ? response.data.items : [];
      setExportJobs(items);
    } catch (requestError) {
      if (!silent) {
        const fallback = requestError?.response?.data?.detail || requestError?.message || 'Export job listesi alınamadı';
        setError(String(fallback));
        toast.error(String(fallback));
      }
    } finally {
      if (!silent) setJobsLoading(false);
    }
  }, [authHeaders]);

  useEffect(() => {
    fetchExportJobs({ silent: true });
  }, [fetchExportJobs]);

  useEffect(() => {
    const hasRunningJobs = exportJobs.some((job) => ['queued', 'running'].includes(String(job?.status || '').toLowerCase()));
    if (!hasRunningJobs) return undefined;
    const timer = window.setInterval(() => {
      fetchExportJobs({ silent: true });
    }, 3000);
    return () => window.clearInterval(timer);
  }, [exportJobs, fetchExportJobs]);

  const totalPages = Math.max(1, Math.ceil(total / limit));
  const hasPrev = page > 1;
  const hasNext = page < totalPages;

  const toggleExpand = (runId) => {
    setExpandedRunIds((previous) => (
      previous.includes(runId)
        ? previous.filter((value) => value !== runId)
        : [...previous, runId]
    ));
  };

  const handleCreateExportJob = async () => {
    setExportLoading(true);
    setError('');
    try {
      await axios.post(`${API}/admin/preset-runs/export-jobs`, {
        status: statusFilter || undefined,
        from: fromDateFilter || undefined,
        to: toDateFilter || undefined,
        extended: extendedExport,
      }, {
        headers: authHeaders,
      });
      toast.success('Export job kuyruğa alındı. Durumu aşağıdaki panelden takip edebilirsiniz.');
      fetchExportJobs({ silent: true });
    } catch (requestError) {
      const fallback = requestError?.response?.data?.detail || requestError?.message || 'Export job oluşturulamadı';
      setError(String(fallback));
      toast.error(String(fallback));
    } finally {
      setExportLoading(false);
    }
  };

  const handleDownloadExportJob = async (jobId) => {
    if (!jobId) return;
    setJobActionLoadingId(String(jobId));
    try {
      const response = await axios.get(`${API}/admin/preset-runs/export-jobs/${jobId}/download`, {
        headers: authHeaders,
        responseType: 'blob',
      });

      const blobUrl = window.URL.createObjectURL(response.data);
      const link = document.createElement('a');
      const headerName = String(response.headers?.['content-disposition'] || '');
      const matchedName = headerName.match(/filename=([^;]+)/i);
      link.href = blobUrl;
      link.download = matchedName?.[1] ? String(matchedName[1]).trim() : `preset-runs-export-${jobId}.csv`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(blobUrl);
      toast.success('Export dosyası indirildi.');
    } catch (requestError) {
      const fallback = requestError?.response?.data?.detail || requestError?.message || 'Export dosyası indirilemedi';
      setError(String(fallback));
      toast.error(String(fallback));
    } finally {
      setJobActionLoadingId('');
    }
  };

  const handleCancelExportJob = async (jobId) => {
    if (!jobId) return;
    setJobActionLoadingId(String(jobId));
    try {
      await axios.post(`${API}/admin/preset-runs/export-jobs/${jobId}/cancel`, {}, { headers: authHeaders });
      toast.success('Export job iptal edildi.');
      fetchExportJobs({ silent: true });
    } catch (requestError) {
      const fallback = requestError?.response?.data?.detail || requestError?.message || 'Export job iptal edilemedi';
      setError(String(fallback));
      toast.error(String(fallback));
    } finally {
      setJobActionLoadingId('');
    }
  };

  return (
    <div className="space-y-5" data-testid="admin-preset-runs-page">
      <section className="rounded-xl border bg-white p-4" data-testid="admin-preset-runs-panel">
        <div className="flex flex-wrap items-center justify-between gap-3" data-testid="admin-preset-runs-header">
          <div>
            <h1 className="text-sm font-semibold" data-testid="admin-preset-runs-title">Template Preset Run History</h1>
            <p className="text-xs text-slate-500" data-testid="admin-preset-runs-subtitle">Çalıştırma geçmişi, başarı oranı ve hata logları.</p>
          </div>
          <div className="flex items-center gap-2" data-testid="admin-preset-runs-header-actions">
            <button
              type="button"
              className="h-9 rounded border px-3 text-xs"
              onClick={handleCreateExportJob}
              disabled={loading || exportLoading}
              data-testid="admin-preset-runs-export-button"
            >
              {exportLoading ? 'Kuyruğa Alınıyor...' : 'Async Export Job Oluştur'}
            </button>
            <button
              type="button"
              className="h-9 rounded border px-3 text-xs"
              onClick={() => {
                fetchRuns();
                fetchExportJobs();
              }}
              disabled={loading || jobsLoading}
              data-testid="admin-preset-runs-refresh-button"
            >
              Yenile
            </button>
          </div>
        </div>

        <div className="mt-3 grid grid-cols-1 gap-2 md:grid-cols-4" data-testid="admin-preset-runs-filters">
          <label className="text-xs" data-testid="admin-preset-runs-status-filter-wrap">
            Status
            <select
              className="mt-1 h-9 w-full rounded border px-2"
              value={statusFilter}
              onChange={(event) => {
                setPage(1);
                setStatusFilter(event.target.value);
              }}
              data-testid="admin-preset-runs-status-filter"
            >
              <option value="">Tümü</option>
              <option value="success">success</option>
              <option value="partial_success">partial_success</option>
              <option value="failed">failed</option>
            </select>
          </label>

          <label className="text-xs" data-testid="admin-preset-runs-from-filter-wrap">
            From
            <input
              className="mt-1 h-9 w-full rounded border px-2"
              type="date"
              value={fromDateFilter}
              onChange={(event) => {
                setPage(1);
                setFromDateFilter(event.target.value);
              }}
              data-testid="admin-preset-runs-from-filter"
            />
          </label>

          <label className="text-xs" data-testid="admin-preset-runs-to-filter-wrap">
            To
            <input
              className="mt-1 h-9 w-full rounded border px-2"
              type="date"
              value={toDateFilter}
              onChange={(event) => {
                setPage(1);
                setToDateFilter(event.target.value);
              }}
              data-testid="admin-preset-runs-to-filter"
            />
          </label>

          <div className="flex items-end" data-testid="admin-preset-runs-filter-apply-wrap">
            <div className="flex flex-wrap items-center gap-2">
              <label className="inline-flex items-center gap-1 text-[11px]" data-testid="admin-preset-runs-extended-export-wrap">
                <input
                  type="checkbox"
                  checked={extendedExport}
                  onChange={(event) => setExtendedExport(event.target.checked)}
                  data-testid="admin-preset-runs-extended-export-checkbox"
                />
                extended CSV (schema v2)
              </label>
              <button
                type="button"
                className="h-9 rounded border px-3 text-xs"
                onClick={() => fetchRuns()}
                disabled={loading}
                data-testid="admin-preset-runs-filter-apply-button"
              >
                Filtreyi Uygula
              </button>
            </div>
          </div>
        </div>

        <div className="mt-3 rounded border bg-slate-50 p-3" data-testid="admin-preset-runs-export-jobs-panel">
          <div className="flex flex-wrap items-center justify-between gap-2" data-testid="admin-preset-runs-export-jobs-header">
            <p className="text-xs font-semibold" data-testid="admin-preset-runs-export-jobs-title">CSV Export Job Queue</p>
            <span className="text-[11px] text-slate-600" data-testid="admin-preset-runs-export-jobs-config">
              lifecycle: queued → running → completed/failed/cancelled
            </span>
          </div>
          <div className="mt-2 overflow-x-auto" data-testid="admin-preset-runs-export-jobs-table-wrap">
            <table className="min-w-full text-left text-xs" data-testid="admin-preset-runs-export-jobs-table">
              <thead>
                <tr className="border-b bg-white" data-testid="admin-preset-runs-export-jobs-head-row">
                  <th className="px-2 py-2">job id</th>
                  <th className="px-2 py-2">created</th>
                  <th className="px-2 py-2">status</th>
                  <th className="px-2 py-2">rows</th>
                  <th className="px-2 py-2">filters</th>
                  <th className="px-2 py-2">actions</th>
                </tr>
              </thead>
              <tbody data-testid="admin-preset-runs-export-jobs-body">
                {jobsLoading ? (
                  <tr data-testid="admin-preset-runs-export-jobs-loading-row">
                    <td className="px-2 py-2 text-slate-500" colSpan={6} data-testid="admin-preset-runs-export-jobs-loading-cell">Yükleniyor...</td>
                  </tr>
                ) : exportJobs.length === 0 ? (
                  <tr data-testid="admin-preset-runs-export-jobs-empty-row">
                    <td className="px-2 py-2 text-slate-500" colSpan={6} data-testid="admin-preset-runs-export-jobs-empty-cell">Henüz export job yok.</td>
                  </tr>
                ) : exportJobs.map((job) => {
                  const statusValue = String(job?.status || '-').toLowerCase();
                  const canCancel = ['queued', 'running'].includes(statusValue);
                  const canDownload = statusValue === 'completed';
                  const isActionLoading = jobActionLoadingId === job.job_id;
                  const filterSummary = [job?.filters?.status, job?.filters?.from, job?.filters?.to].filter(Boolean).join(' • ');

                  return (
                    <tr key={`export-job-${job.job_id}`} className="border-b bg-white" data-testid={`admin-preset-runs-export-job-row-${job.job_id}`}>
                      <td className="px-2 py-2 font-mono text-[11px]" data-testid={`admin-preset-runs-export-job-id-${job.job_id}`}>{job.job_id}</td>
                      <td className="px-2 py-2" data-testid={`admin-preset-runs-export-job-created-${job.job_id}`}>{formatDateTime(job.created_at)}</td>
                      <td className="px-2 py-2" data-testid={`admin-preset-runs-export-job-status-${job.job_id}`}>
                        <div className={`inline-flex rounded border px-2 py-1 ${statusValue === 'completed' ? 'border-emerald-300 bg-emerald-50 text-emerald-700' : statusValue === 'failed' ? 'border-rose-300 bg-rose-50 text-rose-700' : statusValue === 'cancelled' ? 'border-slate-300 bg-slate-100 text-slate-700' : 'border-amber-300 bg-amber-50 text-amber-700'}`}>
                          {statusValue}
                        </div>
                        {job.error_message ? (
                          <p className="mt-1 text-[11px] text-rose-700" data-testid={`admin-preset-runs-export-job-error-${job.job_id}`}>{job.error_message}</p>
                        ) : null}
                      </td>
                      <td className="px-2 py-2" data-testid={`admin-preset-runs-export-job-row-count-${job.job_id}`}>{Number(job.row_count || 0)}</td>
                      <td className="px-2 py-2" data-testid={`admin-preset-runs-export-job-filters-${job.job_id}`}>{filterSummary || '-'}</td>
                      <td className="px-2 py-2" data-testid={`admin-preset-runs-export-job-actions-${job.job_id}`}>
                        <div className="flex flex-wrap items-center gap-2">
                          <button
                            type="button"
                            className="h-8 rounded border px-2 text-[11px]"
                            onClick={() => handleDownloadExportJob(job.job_id)}
                            disabled={!canDownload || isActionLoading}
                            data-testid={`admin-preset-runs-export-job-download-${job.job_id}`}
                          >
                            İndir
                          </button>
                          <button
                            type="button"
                            className="h-8 rounded border px-2 text-[11px]"
                            onClick={() => handleCancelExportJob(job.job_id)}
                            disabled={!canCancel || isActionLoading}
                            data-testid={`admin-preset-runs-export-job-cancel-${job.job_id}`}
                          >
                            Cancel Export
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        <div className="mt-3 overflow-x-auto" data-testid="admin-preset-runs-table-wrap">
          <table className="min-w-full text-left text-xs" data-testid="admin-preset-runs-table">
            <thead>
              <tr className="border-b bg-slate-50" data-testid="admin-preset-runs-head-row">
                <th className="px-2 py-2">run id</th>
                <th className="px-2 py-2">operator</th>
                <th className="px-2 py-2">timestamp</th>
                <th className="px-2 py-2">countries</th>
                <th className="px-2 py-2">success %</th>
                <th className="px-2 py-2">duration</th>
                <th className="px-2 py-2">status</th>
                <th className="px-2 py-2">actions</th>
              </tr>
            </thead>
            <tbody data-testid="admin-preset-runs-table-body">
              {loading ? (
                <tr data-testid="admin-preset-runs-loading-row">
                  <td className="px-2 py-3 text-slate-500" colSpan={8} data-testid="admin-preset-runs-loading-cell">Yükleniyor...</td>
                </tr>
              ) : rows.length === 0 ? (
                <tr data-testid="admin-preset-runs-empty-row">
                  <td className="px-2 py-3 text-slate-500" colSpan={8} data-testid="admin-preset-runs-empty-cell">Kayıt bulunamadı.</td>
                </tr>
              ) : rows.map((row) => {
                const expanded = expandedRunIds.includes(row.id);
                const successRatio = Number(row.success_ratio || 0);
                const errors = Array.isArray(row.error_logs) ? row.error_logs : [];
                return (
                  <tr key={row.id} className="border-b" data-testid={`admin-preset-runs-row-${row.id}`}>
                    <td className="px-2 py-2 font-mono text-[11px]" data-testid={`admin-preset-runs-run-id-${row.id}`}>{row.id}</td>
                    <td className="px-2 py-2" data-testid={`admin-preset-runs-operator-${row.id}`}>{row.executed_by_email || row.executed_by || '-'}</td>
                    <td className="px-2 py-2" data-testid={`admin-preset-runs-executed-at-${row.id}`}>{formatDateTime(row.executed_at)}</td>
                    <td className="px-2 py-2" data-testid={`admin-preset-runs-countries-${row.id}`}>{(row.target_countries || []).join(', ') || '-'}</td>
                    <td className="px-2 py-2" data-testid={`admin-preset-runs-success-ratio-${row.id}`}>{successRatio}%</td>
                    <td className="px-2 py-2" data-testid={`admin-preset-runs-duration-${row.id}`}>{Number(row.duration_ms || 0)} ms</td>
                    <td className="px-2 py-2" data-testid={`admin-preset-runs-status-${row.id}`}>
                      <div className={`inline-flex rounded border px-2 py-1 ${row.status === 'success' ? 'border-emerald-300 bg-emerald-50 text-emerald-700' : row.status === 'partial_success' ? 'border-amber-300 bg-amber-50 text-amber-700' : 'border-rose-300 bg-rose-50 text-rose-700'}`}>
                        {row.status}
                      </div>
                    </td>
                    <td className="px-2 py-2" data-testid={`admin-preset-runs-actions-${row.id}`}>
                      <button
                        type="button"
                        className="h-8 rounded border px-2 text-[11px]"
                        onClick={() => toggleExpand(row.id)}
                        data-testid={`admin-preset-runs-expand-button-${row.id}`}
                      >
                        {expanded ? 'Log Gizle' : 'Log Gör'}
                      </button>
                      {expanded ? (
                        <div className="mt-2 space-y-1 rounded border bg-slate-50 p-2" data-testid={`admin-preset-runs-error-list-${row.id}`}>
                          {errors.length === 0 ? (
                            <p className="text-xs text-slate-600" data-testid={`admin-preset-runs-expanded-empty-${row.id}`}>Bu run için hata logu yok.</p>
                          ) : (
                            errors.map((errorItem, index) => (
                              <p key={`run-error-${row.id}-${index}`} className="text-xs text-rose-700" data-testid={`admin-preset-runs-error-item-${row.id}-${index}`}>
                                {String(errorItem?.country || '-').toUpperCase()} • {normalizeErrorText(errorItem?.error || errorItem?.detail, 'error')}
                              </p>
                            ))
                          )}
                        </div>
                      ) : null}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div className="mt-3 flex flex-wrap items-center justify-between gap-2" data-testid="admin-preset-runs-pagination">
          <span className="text-xs text-slate-600" data-testid="admin-preset-runs-pagination-summary">
            Toplam: {total} • Sayfa: {page}/{totalPages}
          </span>
          <div className="flex items-center gap-2" data-testid="admin-preset-runs-pagination-actions">
            <button
              type="button"
              className="h-8 rounded border px-3 text-xs"
              onClick={() => setPage((previous) => Math.max(1, previous - 1))}
              disabled={!hasPrev || loading}
              data-testid="admin-preset-runs-pagination-prev"
            >
              Önceki
            </button>
            <button
              type="button"
              className="h-8 rounded border px-3 text-xs"
              onClick={() => setPage((previous) => previous + 1)}
              disabled={!hasNext || loading}
              data-testid="admin-preset-runs-pagination-next"
            >
              Sonraki
            </button>
          </div>
        </div>

        {error ? (
          <p className="mt-2 text-xs text-rose-700" data-testid="admin-preset-runs-error-message">{error}</p>
        ) : null}
      </section>
    </div>
  );
}
