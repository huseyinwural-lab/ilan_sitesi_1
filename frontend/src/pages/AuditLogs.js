import { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import {
  Clock,
  Filter,
  Search,
  ChevronLeft,
  ChevronRight,
  FileDown,
  Eye,
  Copy,
  ArrowDownUp,
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const PAGE_SIZE = 20;

const COUNTRY_OPTIONS = ['DE', 'CH', 'FR', 'AT'];

const DEFAULT_EVENT_TYPES = [
  'FAILED_LOGIN',
  'RATE_LIMIT_BLOCK',
  'ADMIN_ROLE_CHANGE',
  'UNAUTHORIZED_ROLE_CHANGE_ATTEMPT',
  'MODERATION_APPROVE',
  'MODERATION_REJECT',
  'MODERATION_NEEDS_REVISION',
];

const DEFAULT_ACTIONS = [
  'CREATE',
  'UPDATE',
  'DELETE',
  'LOGIN',
  'LOGOUT',
  'TOGGLE',
  'SUSPEND',
  'ACTIVATE',
  'APPROVE',
  'REJECT',
  'NEEDS_REVISION',
  'ADMIN_ROLE_CHANGE',
  'UNAUTHORIZED_ROLE_CHANGE_ATTEMPT',
];

const DEFAULT_RESOURCES = ['auth', 'user', 'listing', 'country', 'feature_flag', 'invoice', 'payment', 'plan'];

const actionColors = {
  CREATE: 'bg-emerald-100 text-emerald-800',
  UPDATE: 'bg-blue-100 text-blue-800',
  DELETE: 'bg-rose-100 text-rose-800',
  LOGIN: 'bg-indigo-100 text-indigo-800',
  LOGOUT: 'bg-gray-100 text-gray-800',
  TOGGLE: 'bg-amber-100 text-amber-800',
  SUSPEND: 'bg-orange-100 text-orange-800',
  ACTIVATE: 'bg-teal-100 text-teal-800',
  APPROVE: 'bg-green-100 text-green-800',
  REJECT: 'bg-red-100 text-red-800',
  NEEDS_REVISION: 'bg-amber-100 text-amber-800',
  FAILED_LOGIN: 'bg-rose-100 text-rose-800',
  RATE_LIMIT_BLOCK: 'bg-rose-100 text-rose-800',
  ADMIN_ROLE_CHANGE: 'bg-blue-100 text-blue-800',
  UNAUTHORIZED_ROLE_CHANGE_ATTEMPT: 'bg-amber-100 text-amber-800',
};

const RESOURCE_ROUTE_MAP = {
  dealer: (id) => (id ? `/admin/dealers/${id}` : '/admin/dealers'),
  listing: () => '/admin/listings',
  plan: () => '/admin/plans',
  invoice: () => '/admin/invoices',
  payment: () => '/admin/payments',
  campaign: () => '/admin/individual-campaigns',
  country: () => '/admin/countries',
  user: () => '/admin/individual-users',
  admin_user: () => '/admin/admin-users',
};

const formatDateTime = (value) => {
  if (!value) return '-';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return '-';
  return parsed.toLocaleString('tr-TR');
};

const resolveActor = (log) => {
  return (
    log.admin_user_email ||
    log.user_email ||
    log.email ||
    log.admin_user_id ||
    log.user_id ||
    '-'
  );
};

const resolveResourceLabel = (log) => {
  if (!log.resource_type) return '-';
  if (!log.resource_id) return log.resource_type;
  return `${log.resource_type}:${log.resource_id}`;
};

const withCountryParam = (path) => {
  if (!path || !path.startsWith('/admin')) return path;
  const params = new URLSearchParams(window.location.search);
  const country = params.get('country');
  if (!country) return path;
  const joiner = path.includes('?') ? '&' : '?';
  return `${path}${joiner}country=${encodeURIComponent(country)}`;
};

export default function AuditLogs() {
  const { t } = useLanguage();
  const [dbReady, setDbReady] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [items, setItems] = useState([]);
  const [pagination, setPagination] = useState({ total: 0, page: 0, page_size: PAGE_SIZE });

  const [query, setQuery] = useState('');
  const [eventType, setEventType] = useState('');
  const [action, setAction] = useState('');
  const [resourceType, setResourceType] = useState('');
  const [countryCode, setCountryCode] = useState('');
  const [adminUserQuery, setAdminUserQuery] = useState('');
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const [sort, setSort] = useState('timestamp_desc');

  const [eventTypes, setEventTypes] = useState([]);
  const [actions, setActions] = useState([]);
  const [resources, setResources] = useState([]);

  const [detailLog, setDetailLog] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [copyStatus, setCopyStatus] = useState('');

  const authHeader = useMemo(
    () => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` }),
    []
  );

  const checkDb = async () => {
    try {
      const res = await axios.get(`${API}/health/db`);
      setDbReady(res.status === 200);
      if (res.status === 200) setError('');
    } catch (err) {
      setDbReady(false);
    }
  };

  const buildQueryParams = (includePaging = true) => {
    const params = new URLSearchParams();
    if (query.trim()) params.set('q', query.trim());
    if (eventType) params.set('event_type', eventType);
    if (action) params.set('action', action);
    if (resourceType) params.set('resource_type', resourceType);
    if (countryCode) params.set('country_code', countryCode);
    if (adminUserQuery.trim()) params.set('admin_user_id', adminUserQuery.trim());
    if (fromDate) params.set('from_date', fromDate);
    if (toDate) params.set('to_date', toDate);
    if (sort) params.set('sort', sort);
    if (includePaging) {
      params.set('page', pagination.page);
      params.set('page_size', pagination.page_size);
    }
    return params;
  };

  const fetchMeta = async () => {
    try {
      const [typesRes, actionsRes, resourcesRes] = await Promise.all([
        axios.get(`${API}/admin/audit-logs/event-types`, { headers: authHeader }),
        axios.get(`${API}/admin/audit-logs/actions`, { headers: authHeader }),
        axios.get(`${API}/admin/audit-logs/resources`, { headers: authHeader }),
      ]);
      setEventTypes(typesRes.data.event_types || []);
      setActions(actionsRes.data.actions || []);
      setResources(resourcesRes.data.resource_types || []);
    } catch (err) {
      setEventTypes([]);
      setActions([]);
      setResources([]);
    }
  };

  const fetchLogs = async () => {
    if (!dbReady) {
      setItems([]);
      setPagination((prev) => ({ ...prev, total: 0 }));
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const params = buildQueryParams(true);
      const res = await axios.get(`${API}/admin/audit-logs?${params.toString()}`, { headers: authHeader });
      setItems(res.data.items || []);
      setPagination(res.data.pagination || { total: 0, page: 0, page_size: PAGE_SIZE });
      setError('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Audit logları yüklenemedi');
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchDetail = async (logId) => {
    if (!dbReady || !logId) return;
    setDetailLoading(true);
    try {
      const res = await axios.get(`${API}/admin/audit-logs/${logId}`, { headers: authHeader });
      setDetailLog(res.data.log || null);
    } catch (err) {
      setDetailLog(null);
      setError(err.response?.data?.detail || 'Audit log detayı alınamadı');
    } finally {
      setDetailLoading(false);
    }
  };

  const handleExport = async () => {
    if (!dbReady || exporting) return;
    setExporting(true);
    try {
      const params = buildQueryParams(false);
      const res = await axios.get(`${API}/admin/audit-logs/export?${params.toString()}`, {
        headers: authHeader,
        responseType: 'blob',
      });
      const blobUrl = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = blobUrl;
      const contentDisposition = res.headers['content-disposition'] || '';
      const filenameMatch = contentDisposition.match(/filename=([^;]+)/i);
      link.download = filenameMatch ? filenameMatch[1].replace(/"/g, '') : 'audit-logs.csv';
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(blobUrl);
    } catch (err) {
      setError('CSV dışa aktarılamadı');
    } finally {
      setExporting(false);
    }
  };

  const handleCopy = async (value) => {
    if (!value) return;
    try {
      await navigator.clipboard.writeText(value);
      setCopyStatus('Kopyalandı');
      setTimeout(() => setCopyStatus(''), 1500);
    } catch (err) {
      setCopyStatus('Kopyalama başarısız');
      setTimeout(() => setCopyStatus(''), 1500);
    }
  };

  const resolveResourceRoute = (log) => {
    if (!log?.resource_type) return null;
    const resolver = RESOURCE_ROUTE_MAP[log.resource_type];
    if (!resolver) return null;
    return withCountryParam(resolver(log.resource_id));
  };

  useEffect(() => {
    checkDb();
  }, []);

  useEffect(() => {
    if (dbReady) {
      fetchMeta();
    }
  }, [dbReady]);

  useEffect(() => {
    fetchLogs();
  }, [
    dbReady,
    query,
    eventType,
    action,
    resourceType,
    countryCode,
    adminUserQuery,
    fromDate,
    toDate,
    sort,
    pagination.page,
    pagination.page_size,
  ]);

  const totalPages = Math.max(1, Math.ceil((pagination.total || 0) / pagination.page_size));
  const canPrev = pagination.page > 0;
  const canNext = pagination.page + 1 < totalPages;

  const effectiveEventTypes = eventTypes.length ? eventTypes : DEFAULT_EVENT_TYPES;
  const effectiveActions = actions.length ? actions : DEFAULT_ACTIONS;
  const effectiveResources = resources.length ? resources : DEFAULT_RESOURCES;

  return (
    <div className="space-y-6" data-testid="audit-logs-page">
      <div className="flex flex-wrap items-start justify-between gap-3" data-testid="audit-logs-header">
        <div>
          <h1 className="text-2xl font-bold tracking-tight" data-testid="audit-logs-title">
            {t('audit_logs')}
          </h1>
          <p className="text-sm text-muted-foreground" data-testid="audit-logs-subtitle">
            Sistem aktiviteleri ve denetim geçmişi
          </p>
        </div>
        <div className="flex items-center gap-2" data-testid="audit-logs-actions">
          <button
            type="button"
            onClick={fetchLogs}
            className="h-9 px-3 rounded-md border text-sm flex items-center gap-2"
            data-testid="audit-logs-refresh"
            disabled={loading}
          >
            <ArrowDownUp size={14} /> Yenile
          </button>
          <button
            type="button"
            onClick={handleExport}
            className="h-9 px-3 rounded-md bg-primary text-primary-foreground text-sm flex items-center gap-2 disabled:opacity-50"
            data-testid="audit-logs-export"
            disabled={!dbReady || exporting}
            title={!dbReady ? 'DB hazır değil' : 'CSV dışa aktar'}
          >
            <FileDown size={16} />
            {exporting ? 'Hazırlanıyor...' : 'CSV Dışa Aktar'}
          </button>
        </div>
      </div>

      {!dbReady && (
        <div className="border border-amber-200 bg-amber-50 text-amber-900 rounded-md p-4" data-testid="audit-logs-db-banner">
          DB hazır değil → işlemler devre dışı. Ops ekibine DATABASE_URL + migration kontrolü gerekiyor.
        </div>
      )}

      {error && (
        <div className="border border-red-200 bg-red-50 text-red-700 rounded-md p-3" data-testid="audit-logs-error">
          {error}
        </div>
      )}

      <div className="flex flex-wrap items-center gap-3" data-testid="audit-logs-filters">
        <div className="relative">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <input
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setPagination((prev) => ({ ...prev, page: 0 }));
            }}
            placeholder="Ara (event, kullanıcı, resource)"
            className="h-9 pl-8 pr-3 rounded-md border bg-background text-sm"
            data-testid="audit-logs-search"
          />
        </div>

        <Filter className="h-4 w-4 text-muted-foreground" data-testid="audit-logs-filter-icon" />

        <select
          value={eventType}
          onChange={(e) => {
            setEventType(e.target.value);
            setPagination((prev) => ({ ...prev, page: 0 }));
          }}
          className="h-9 px-3 rounded-md border bg-background text-sm"
          data-testid="audit-logs-event-type"
        >
          <option value="">Event Type (Tümü)</option>
          {effectiveEventTypes.map((type) => (
            <option key={type} value={type} data-testid={`audit-logs-event-type-${type}`}>
              {type}
            </option>
          ))}
        </select>

        <select
          value={action}
          onChange={(e) => {
            setAction(e.target.value);
            setPagination((prev) => ({ ...prev, page: 0 }));
          }}
          className="h-9 px-3 rounded-md border bg-background text-sm"
          data-testid="audit-logs-action"
        >
          <option value="">Action (Tümü)</option>
          {effectiveActions.map((value) => (
            <option key={value} value={value} data-testid={`audit-logs-action-${value}`}>
              {value}
            </option>
          ))}
        </select>

        <select
          value={resourceType}
          onChange={(e) => {
            setResourceType(e.target.value);
            setPagination((prev) => ({ ...prev, page: 0 }));
          }}
          className="h-9 px-3 rounded-md border bg-background text-sm"
          data-testid="audit-logs-resource"
        >
          <option value="">Resource (Tümü)</option>
          {effectiveResources.map((value) => (
            <option key={value} value={value} data-testid={`audit-logs-resource-${value}`}>
              {value}
            </option>
          ))}
        </select>

        <select
          value={countryCode}
          onChange={(e) => {
            setCountryCode(e.target.value);
            setPagination((prev) => ({ ...prev, page: 0 }));
          }}
          className="h-9 px-3 rounded-md border bg-background text-sm"
          data-testid="audit-logs-country"
        >
          <option value="">Country (Tümü)</option>
          {COUNTRY_OPTIONS.map((value) => (
            <option key={value} value={value} data-testid={`audit-logs-country-${value}`}>
              {value}
            </option>
          ))}
        </select>

        <input
          value={adminUserQuery}
          onChange={(e) => {
            setAdminUserQuery(e.target.value);
            setPagination((prev) => ({ ...prev, page: 0 }));
          }}
          placeholder="Admin kullanıcı (ID/E-posta)"
          className="h-9 px-3 rounded-md border bg-background text-sm"
          data-testid="audit-logs-admin-user"
        />

        <input
          type="date"
          value={fromDate}
          onChange={(e) => {
            setFromDate(e.target.value);
            setPagination((prev) => ({ ...prev, page: 0 }));
          }}
          className="h-9 px-3 rounded-md border bg-background text-sm"
          data-testid="audit-logs-date-from"
        />

        <input
          type="date"
          value={toDate}
          onChange={(e) => {
            setToDate(e.target.value);
            setPagination((prev) => ({ ...prev, page: 0 }));
          }}
          className="h-9 px-3 rounded-md border bg-background text-sm"
          data-testid="audit-logs-date-to"
        />

        <select
          value={sort}
          onChange={(e) => {
            setSort(e.target.value);
            setPagination((prev) => ({ ...prev, page: 0 }));
          }}
          className="h-9 px-3 rounded-md border bg-background text-sm"
          data-testid="audit-logs-sort"
        >
          <option value="timestamp_desc">Zaman (Yeni → Eski)</option>
          <option value="timestamp_asc">Zaman (Eski → Yeni)</option>
        </select>
      </div>

      <div className="border rounded-lg overflow-hidden" data-testid="audit-logs-table">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-muted">
              <tr data-testid="audit-logs-table-header">
                <th className="text-left p-3" data-testid="audit-logs-header-timestamp">Zaman</th>
                <th className="text-left p-3" data-testid="audit-logs-header-event">Event</th>
                <th className="text-left p-3" data-testid="audit-logs-header-action">Action</th>
                <th className="text-left p-3" data-testid="audit-logs-header-resource">Resource</th>
                <th className="text-left p-3" data-testid="audit-logs-header-actor">Aktör</th>
                <th className="text-left p-3" data-testid="audit-logs-header-country">Country</th>
                <th className="text-left p-3" data-testid="audit-logs-header-detail">Detay</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} className="p-6 text-center" data-testid="audit-logs-loading">
                    <div className="flex justify-center">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary" />
                    </div>
                  </td>
                </tr>
              ) : !dbReady ? (
                <tr>
                  <td colSpan={7} className="p-6 text-center text-muted-foreground" data-testid="audit-logs-disabled-empty">
                    DB hazır değil. Audit logları görüntülenemiyor.
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-6 text-center text-muted-foreground" data-testid="audit-logs-empty">
                    Kayıt bulunamadı
                  </td>
                </tr>
              ) : (
                items.map((log) => (
                  <tr key={log.id} className="border-t hover:bg-muted/40" data-testid={`audit-logs-row-${log.id}`}>
                    <td className="p-3 whitespace-nowrap" data-testid={`audit-logs-timestamp-${log.id}`}>
                      <div className="flex items-center gap-2">
                        <Clock size={14} className="text-muted-foreground" />
                        {formatDateTime(log.created_at || log.timestamp || log.ts)}
                      </div>
                    </td>
                    <td className="p-3" data-testid={`audit-logs-event-${log.id}`}>
                      <span className="font-mono text-xs">{log.event_type || '-'}</span>
                    </td>
                    <td className="p-3" data-testid={`audit-logs-action-${log.id}`}>
                      <span
                        className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${actionColors[log.action] || 'bg-gray-100 text-gray-800'}`}
                      >
                        {log.action || '-'}
                      </span>
                    </td>
                    <td className="p-3" data-testid={`audit-logs-resource-${log.id}`}>
                      <span className="text-muted-foreground break-all">
                        {resolveResourceLabel(log)}
                      </span>
                    </td>
                    <td className="p-3" data-testid={`audit-logs-actor-${log.id}`}>
                      <span className="text-muted-foreground break-all">{resolveActor(log)}</span>
                    </td>
                    <td className="p-3" data-testid={`audit-logs-country-${log.id}`}>
                      <span className="text-muted-foreground">{log.country_code || '-'}</span>
                    </td>
                    <td className="p-3" data-testid={`audit-logs-detail-${log.id}`}>
                      <button
                        type="button"
                        onClick={() => fetchDetail(log.id)}
                        className="text-primary hover:underline text-xs flex items-center gap-1 disabled:opacity-50"
                        data-testid={`audit-logs-view-${log.id}`}
                        disabled={!dbReady}
                        title={!dbReady ? 'DB hazır değil' : 'Detay'}
                      >
                        <Eye size={14} /> View
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3" data-testid="audit-logs-pagination">
        <p className="text-sm text-muted-foreground" data-testid="audit-logs-total">
          Toplam: {pagination.total || 0} kayıt
        </p>
        <div className="flex items-center gap-2" data-testid="audit-logs-pagination-controls">
          <button
            type="button"
            onClick={() => setPagination((prev) => ({ ...prev, page: Math.max(0, prev.page - 1) }))}
            disabled={!canPrev}
            className="flex items-center gap-1 px-3 py-1.5 rounded-md border text-sm disabled:opacity-50"
            data-testid="audit-logs-prev"
          >
            <ChevronLeft size={16} /> Önceki
          </button>
          <div className="text-sm text-muted-foreground" data-testid="audit-logs-page-indicator">
            Sayfa {pagination.page + 1} / {totalPages}
          </div>
          <button
            type="button"
            onClick={() => setPagination((prev) => ({ ...prev, page: Math.min(prev.page + 1, totalPages - 1) }))}
            disabled={!canNext}
            className="flex items-center gap-1 px-3 py-1.5 rounded-md border text-sm disabled:opacity-50"
            data-testid="audit-logs-next"
          >
            Sonraki <ChevronRight size={16} />
          </button>
        </div>
      </div>

      {detailLog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" data-testid="audit-logs-detail-modal">
          <div className="bg-card rounded-lg shadow-lg max-w-3xl w-full">
            <div className="p-4 border-b flex items-center justify-between" data-testid="audit-logs-detail-header">
              <div>
                <h3 className="text-lg font-semibold" data-testid="audit-logs-detail-title">Audit Log Detayı</h3>
                <p className="text-xs text-muted-foreground" data-testid="audit-logs-detail-id">ID: {detailLog.id}</p>
              </div>
              <button
                type="button"
                className="h-8 px-3 rounded-md border text-sm"
                onClick={() => setDetailLog(null)}
                data-testid="audit-logs-detail-close"
              >
                Kapat
              </button>
            </div>
            <div className="p-4 space-y-4" data-testid="audit-logs-detail-body">
              {detailLoading ? (
                <div className="text-sm text-muted-foreground" data-testid="audit-logs-detail-loading">
                  Yükleniyor...
                </div>
              ) : (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4" data-testid="audit-logs-detail-grid">
                    <div>
                      <div className="text-xs text-muted-foreground">Zaman</div>
                      <div className="text-sm" data-testid="audit-logs-detail-time">
                        {formatDateTime(detailLog.created_at || detailLog.timestamp || detailLog.ts)}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground">Event Type</div>
                      <div className="text-sm" data-testid="audit-logs-detail-event">{detailLog.event_type || '-'}</div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground">Action</div>
                      <div className="text-sm" data-testid="audit-logs-detail-action">{detailLog.action || '-'}</div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground">Resource</div>
                      <div className="text-sm" data-testid="audit-logs-detail-resource">{resolveResourceLabel(detailLog)}</div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground">Aktör</div>
                      <div className="text-sm" data-testid="audit-logs-detail-actor">{resolveActor(detailLog)}</div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground">Country</div>
                      <div className="text-sm" data-testid="audit-logs-detail-country">{detailLog.country_code || '-'}</div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground">IP</div>
                      <div className="text-sm" data-testid="audit-logs-detail-ip">{detailLog.ip_address || '-'}</div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground">User Agent</div>
                      <div className="text-sm break-all" data-testid="audit-logs-detail-user-agent">
                        {detailLog.user_agent || '-'}
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center gap-2" data-testid="audit-logs-detail-actions">
                    {detailLog.resource_id && (
                      <button
                        type="button"
                        onClick={() => handleCopy(detailLog.resource_id)}
                        className="h-9 px-3 rounded-md border text-sm flex items-center gap-2"
                        data-testid="audit-logs-copy-resource"
                      >
                        <Copy size={14} /> ID Kopyala
                      </button>
                    )}
                    {resolveResourceRoute(detailLog) && (
                      <button
                        type="button"
                        onClick={() => window.open(resolveResourceRoute(detailLog), '_blank')}
                        className="h-9 px-3 rounded-md bg-primary text-primary-foreground text-sm"
                        data-testid="audit-logs-open-resource"
                      >
                        Kaynağa Git
                      </button>
                    )}
                    {copyStatus && (
                      <span className="text-xs text-muted-foreground" data-testid="audit-logs-copy-status">
                        {copyStatus}
                      </span>
                    )}
                  </div>

                  <div className="border rounded-md p-3 bg-muted/40" data-testid="audit-logs-detail-json">
                    <div className="text-xs text-muted-foreground mb-2">Ham Veri</div>
                    <pre className="text-xs overflow-auto max-h-[300px]">
{JSON.stringify(detailLog, null, 2)}
                    </pre>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
