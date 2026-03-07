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
  const [moduleFilter, setModuleFilter] = useState('');
  const [expandedRunIds, setExpandedRunIds] = useState([]);

  const fetchRuns = useCallback(async ({ silent = false } = {}) => {
    setLoading(true);
    if (!silent) setError('');
    try {
      const response = await axios.get(`${API}/admin/site/content-layout/preset-runs`, {
        headers: authHeaders,
        params: {
          page,
          limit,
          status: statusFilter || undefined,
          module: moduleFilter || undefined,
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
  }, [authHeaders, page, limit, statusFilter, moduleFilter]);

  useEffect(() => {
    fetchRuns({ silent: true });
  }, [fetchRuns]);

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

  return (
    <div className="space-y-5" data-testid="admin-preset-runs-page">
      <section className="rounded-xl border bg-white p-4" data-testid="admin-preset-runs-panel">
        <div className="flex flex-wrap items-center justify-between gap-3" data-testid="admin-preset-runs-header">
          <div>
            <h1 className="text-sm font-semibold" data-testid="admin-preset-runs-title">Template Preset Run History</h1>
            <p className="text-xs text-slate-500" data-testid="admin-preset-runs-subtitle">Çalıştırma geçmişi, başarı oranı ve hata logları.</p>
          </div>
          <button
            type="button"
            className="h-9 rounded border px-3 text-xs"
            onClick={() => fetchRuns()}
            disabled={loading}
            data-testid="admin-preset-runs-refresh-button"
          >
            Yenile
          </button>
        </div>

        <div className="mt-3 grid grid-cols-1 gap-2 md:grid-cols-3" data-testid="admin-preset-runs-filters">
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

          <label className="text-xs" data-testid="admin-preset-runs-module-filter-wrap">
            Module
            <input
              className="mt-1 h-9 w-full rounded border px-2"
              value={moduleFilter}
              onChange={(event) => {
                setPage(1);
                setModuleFilter(event.target.value);
              }}
              placeholder="global"
              data-testid="admin-preset-runs-module-filter"
            />
          </label>

          <div className="flex items-end" data-testid="admin-preset-runs-filter-apply-wrap">
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
                  <React.Fragment key={row.id}>
                    <tr className="border-b" data-testid={`admin-preset-runs-row-${row.id}`}>
                      <td className="px-2 py-2 font-mono text-[11px]" data-testid={`admin-preset-runs-run-id-${row.id}`}>{row.id}</td>
                      <td className="px-2 py-2" data-testid={`admin-preset-runs-operator-${row.id}`}>{row.executed_by_email || row.executed_by || '-'}</td>
                      <td className="px-2 py-2" data-testid={`admin-preset-runs-executed-at-${row.id}`}>{formatDateTime(row.executed_at)}</td>
                      <td className="px-2 py-2" data-testid={`admin-preset-runs-countries-${row.id}`}>{(row.target_countries || []).join(', ') || '-'}</td>
                      <td className="px-2 py-2" data-testid={`admin-preset-runs-success-ratio-${row.id}`}>{successRatio}%</td>
                      <td className="px-2 py-2" data-testid={`admin-preset-runs-duration-${row.id}`}>{Number(row.duration_ms || 0)} ms</td>
                      <td className="px-2 py-2" data-testid={`admin-preset-runs-status-${row.id}`}>
                        <span className={`inline-flex rounded border px-2 py-1 ${row.status === 'success' ? 'border-emerald-300 bg-emerald-50 text-emerald-700' : row.status === 'partial_success' ? 'border-amber-300 bg-amber-50 text-amber-700' : 'border-rose-300 bg-rose-50 text-rose-700'}`}>
                          {row.status}
                        </span>
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
                      </td>
                    </tr>
                    {expanded ? (
                      <tr className="border-b bg-slate-50" data-testid={`admin-preset-runs-expanded-row-${row.id}`}>
                        <td className="px-2 py-2" colSpan={8} data-testid={`admin-preset-runs-expanded-cell-${row.id}`}>
                          {errors.length === 0 ? (
                            <p className="text-xs text-slate-600" data-testid={`admin-preset-runs-expanded-empty-${row.id}`}>Bu run için hata logu yok.</p>
                          ) : (
                            <div className="space-y-1" data-testid={`admin-preset-runs-error-list-${row.id}`}>
                              {errors.map((errorItem, index) => (
                                <p key={`run-error-${row.id}-${index}`} className="text-xs text-rose-700" data-testid={`admin-preset-runs-error-item-${row.id}-${index}`}>
                                  {String(errorItem?.country || '-').toUpperCase()} • {normalizeErrorText(errorItem?.error || errorItem?.detail, 'error')}
                                </p>
                              ))}
                            </div>
                          )}
                        </td>
                      </tr>
                    ) : null}
                  </React.Fragment>
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
