import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { AdminEmptyState, AdminErrorState, AdminLoadingState } from '@/components/admin/standard/AdminStateBlocks';
import { AdminStatusBadge } from '@/components/admin/standard/AdminStatusBadge';
import { AdminMoneyText } from '@/components/admin/standard/AdminMoneyText';

const API = process.env.REACT_APP_BACKEND_URL;

export default function AdminAuditDashboard() {
  const [events, setEvents] = useState([]);
  const [stats, setStats] = useState({ windows: { '24h': null, '7d': null } });
  const [anomalies, setAnomalies] = useState([]);
  const [schemaInfo, setSchemaInfo] = useState(null);
  const [eventTypes, setEventTypes] = useState([]);
  const [countries, setCountries] = useState([]);
  const [pagination, setPagination] = useState({ page: 1, size: 20, total: 0, total_pages: 0, sort: 'created_at:desc' });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({
    q: '',
    actor: '',
    role: 'all',
    country: 'all',
    event_type: '',
    date_from: '',
    date_to: '',
    sort: 'created_at:desc',
  });

  const authHeader = useMemo(
    () => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` }),
    [],
  );

  const queryParams = useMemo(() => {
    const params = {
      page: pagination.page,
      size: pagination.size,
      sort: filters.sort,
    };
    if (filters.q.trim()) params.q = filters.q.trim();
    if (filters.actor.trim()) params.actor = filters.actor.trim();
    if (filters.role !== 'all') params.role = filters.role;
    if (filters.country !== 'all') params.country = filters.country;
    if (filters.event_type.trim()) params.event_type = filters.event_type.trim();
    if (filters.date_from) params.date_from = filters.date_from;
    if (filters.date_to) params.date_to = filters.date_to;
    return params;
  }, [filters, pagination.page, pagination.size]);

  const loadAuditData = async ({ withStaticData = false } = {}) => {
    setLoading(true);
    setError('');
    try {
      const dynamicCalls = [
        axios.get(`${API}/api/admin/audit-logs`, { headers: authHeader, params: queryParams }),
      ];

      if (withStaticData) {
        dynamicCalls.push(
          axios.get(`${API}/api/admin/audit/dashboard/schema`, { headers: authHeader }),
          axios.get(`${API}/api/admin/audit/dashboard/stats`, { headers: authHeader }),
          axios.get(`${API}/api/admin/audit/dashboard/anomalies`, { headers: authHeader }),
          axios.get(`${API}/api/admin/audit-logs/event-types`, { headers: authHeader }),
          axios.get(`${API}/api/countries`, { headers: authHeader }),
        );
      }

      const responses = await Promise.all(dynamicCalls);
      const logsRes = responses[0];
      setEvents(logsRes.data?.items || []);

      const incomingPagination = logsRes.data?.pagination || {};
      setPagination((prev) => ({
        ...prev,
        total: Number(incomingPagination.total || 0),
        total_pages: Number(incomingPagination.total_pages || 0),
        sort: incomingPagination.sort || prev.sort,
      }));

      if (withStaticData) {
        const schemaRes = responses[1];
        const statsRes = responses[2];
        const anomaliesRes = responses[3];
        const eventTypesRes = responses[4];
        const countriesRes = responses[5];

        setSchemaInfo(schemaRes.data || null);
        setStats(statsRes.data || { windows: { '24h': null, '7d': null } });
        setAnomalies(anomaliesRes.data?.anomalies || []);
        setEventTypes(eventTypesRes.data?.event_types || []);
        setCountries(countriesRes.data || []);
      }
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Audit dashboard verileri alınamadı.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAuditData({ withStaticData: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    loadAuditData({ withStaticData: false });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [queryParams]);

  const onFilterChange = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const applyFilters = () => {
    setPagination((prev) => ({ ...prev, page: 1 }));
  };

  const clearFilters = () => {
    setFilters({
      q: '',
      actor: '',
      role: 'all',
      country: 'all',
      event_type: '',
      date_from: '',
      date_to: '',
      sort: 'created_at:desc',
    });
    setPagination((prev) => ({ ...prev, page: 1 }));
  };

  const onPageMove = (nextPage) => {
    setPagination((prev) => ({ ...prev, page: nextPage }));
  };

  const stats24h = stats?.windows?.['24h'] || {};
  const stats7d = stats?.windows?.['7d'] || {};
  const risk24hMinor = Number(stats24h.financial_risk_minor ?? (stats24h.denied_403_events || 0) * 100);
  const risk7dMinor = Number(stats7d.financial_risk_minor ?? (stats7d.denied_403_events || 0) * 100);

  const resolveSeverityVariant = (value) => {
    const key = String(value || '').toLowerCase();
    if (['critical', 'high', 'danger'].includes(key)) return 'danger';
    if (['warning', 'warn', 'medium'].includes(key)) return 'warning';
    if (['info', 'low'].includes(key)) return 'info';
    return 'neutral';
  };

  return (
    <div className="space-y-6" data-testid="admin-audit-dashboard-page">
      <div className="flex flex-wrap items-center justify-between gap-3" data-testid="admin-audit-dashboard-header">
        <div>
          <h1 className="text-2xl font-semibold" data-testid="admin-audit-dashboard-title">Audit Dashboard</h1>
          <p className="text-sm text-muted-foreground" data-testid="admin-audit-dashboard-subtitle">
            Son olaylar, 24s/7g özetler ve anomali sinyalleri.
          </p>
        </div>
        <button
          type="button"
          className="h-9 rounded-md border px-3 text-sm"
          onClick={loadAuditData}
          data-testid="admin-audit-refresh-button"
        >
          Yenile
        </button>
      </div>

      {schemaInfo ? (
        <div className="rounded-md border bg-slate-50 p-3 text-xs" data-testid="admin-audit-schema-lock-card">
          <div className="font-medium" data-testid="admin-audit-schema-version">Schema: {schemaInfo.schema_version}</div>
          <div className="text-muted-foreground" data-testid="admin-audit-schema-start-at">
            Collection start: {schemaInfo.collection_start_at || '-'}
          </div>
        </div>
      ) : null}

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2" data-testid="admin-audit-stats-grid">
        <div className="rounded-md border p-4" data-testid="admin-audit-stats-24h-card">
          <div className="text-sm font-semibold">24 Saat</div>
          <div className="mt-2 grid grid-cols-2 gap-2 text-sm">
            <div data-testid="admin-audit-stats-24h-total">Toplam: {stats24h.total_events || 0}</div>
            <div data-testid="admin-audit-stats-24h-actors">Aktör: {stats24h.unique_actors || 0}</div>
            <div data-testid="admin-audit-stats-24h-403">403: {stats24h.denied_403_events || 0}</div>
            <div data-testid="admin-audit-stats-24h-publish-fail">Publish fail: {stats24h.publish_failure_events || 0}</div>
            <div data-testid="admin-audit-stats-24h-export">Export attempt: {stats24h.export_attempt_events || 0}</div>
            <div className="col-span-2" data-testid="admin-audit-stats-24h-risk">
              Tahmini risk: <AdminMoneyText amountMinor={risk24hMinor} testId="admin-audit-stats-24h-risk-money" />
            </div>
          </div>
        </div>

        <div className="rounded-md border p-4" data-testid="admin-audit-stats-7d-card">
          <div className="text-sm font-semibold">7 Gün</div>
          <div className="mt-2 grid grid-cols-2 gap-2 text-sm">
            <div data-testid="admin-audit-stats-7d-total">Toplam: {stats7d.total_events || 0}</div>
            <div data-testid="admin-audit-stats-7d-actors">Aktör: {stats7d.unique_actors || 0}</div>
            <div data-testid="admin-audit-stats-7d-403">403: {stats7d.denied_403_events || 0}</div>
            <div data-testid="admin-audit-stats-7d-publish-fail">Publish fail: {stats7d.publish_failure_events || 0}</div>
            <div data-testid="admin-audit-stats-7d-export">Export attempt: {stats7d.export_attempt_events || 0}</div>
            <div className="col-span-2" data-testid="admin-audit-stats-7d-risk">
              Tahmini risk: <AdminMoneyText amountMinor={risk7dMinor} testId="admin-audit-stats-7d-risk-money" />
            </div>
          </div>
        </div>
      </div>

      <div className="rounded-md border p-4" data-testid="admin-audit-anomalies-card">
        <div className="text-sm font-semibold" data-testid="admin-audit-anomalies-title">Anomalies</div>
        {anomalies.length === 0 ? (
          <div className="mt-2" data-testid="admin-audit-anomalies-empty-wrap">
            <AdminEmptyState message="Anomali yok." testId="admin-audit-anomalies-empty" />
          </div>
        ) : (
          <div className="mt-3 space-y-2" data-testid="admin-audit-anomalies-list">
            {anomalies.map((item) => (
              <div key={item.type} className="rounded-md border p-3 text-sm" data-testid={`admin-audit-anomaly-${item.type}`}>
                <div className="flex items-center justify-between gap-2">
                  <div className="font-medium" data-testid={`admin-audit-anomaly-title-${item.type}`}>{item.type}</div>
                  <AdminStatusBadge
                    label={String(item.severity || 'info')}
                    variant={resolveSeverityVariant(item.severity)}
                    testId={`admin-audit-anomaly-severity-${item.type}`}
                  />
                </div>
                <div className="text-muted-foreground">{item.description}</div>
                <div className="text-xs text-muted-foreground">count: {item.count} / threshold: {item.threshold}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="rounded-md border p-4" data-testid="admin-audit-events-card">
        <div className="mb-3 text-sm font-semibold" data-testid="admin-audit-events-title">Recent events</div>
        <div className="mb-3 grid grid-cols-1 gap-2 md:grid-cols-4" data-testid="admin-audit-filters">
          <input
            value={filters.q}
            onChange={(e) => onFilterChange('q', e.target.value)}
            placeholder="q"
            className="h-9 rounded-md border px-3 text-sm"
            data-testid="admin-audit-filter-q"
          />
          <input
            value={filters.actor}
            onChange={(e) => onFilterChange('actor', e.target.value)}
            placeholder="actor"
            className="h-9 rounded-md border px-3 text-sm"
            data-testid="admin-audit-filter-actor"
          />
          <select
            value={filters.role}
            onChange={(e) => onFilterChange('role', e.target.value)}
            className="h-9 rounded-md border px-3 text-sm"
            data-testid="admin-audit-filter-role"
          >
            <option value="all" data-testid="admin-audit-filter-role-option-all">all</option>
            {['super_admin', 'country_admin', 'admin', 'finance', 'dealer', 'user', 'support', 'moderator'].map((role) => (
              <option key={role} value={role} data-testid={`admin-audit-filter-role-option-${role}`}>{role}</option>
            ))}
          </select>
          <select
            value={filters.country}
            onChange={(e) => onFilterChange('country', e.target.value)}
            className="h-9 rounded-md border px-3 text-sm"
            data-testid="admin-audit-filter-country"
          >
            <option value="all" data-testid="admin-audit-filter-country-option-all">all</option>
            {countries.map((item) => (
              <option key={item.code} value={item.code} data-testid={`admin-audit-filter-country-option-${item.code}`}>{item.code}</option>
            ))}
          </select>
        </div>

        <div className="mb-3 grid grid-cols-1 gap-2 md:grid-cols-4" data-testid="admin-audit-filters-2">
          <select
            value={filters.event_type}
            onChange={(e) => onFilterChange('event_type', e.target.value)}
            className="h-9 rounded-md border px-3 text-sm"
            data-testid="admin-audit-filter-event-type"
          >
            <option value="" data-testid="admin-audit-filter-event-type-option-all">all event_type</option>
            {eventTypes.map((item) => (
              <option key={item} value={item} data-testid={`admin-audit-filter-event-type-option-${item}`}>{item}</option>
            ))}
          </select>
          <input
            type="date"
            value={filters.date_from}
            onChange={(e) => onFilterChange('date_from', e.target.value)}
            className="h-9 rounded-md border px-3 text-sm"
            data-testid="admin-audit-filter-date-from"
          />
          <input
            type="date"
            value={filters.date_to}
            onChange={(e) => onFilterChange('date_to', e.target.value)}
            className="h-9 rounded-md border px-3 text-sm"
            data-testid="admin-audit-filter-date-to"
          />
          <select
            value={filters.sort}
            onChange={(e) => onFilterChange('sort', e.target.value)}
            className="h-9 rounded-md border px-3 text-sm"
            data-testid="admin-audit-filter-sort"
          >
            <option value="created_at:desc" data-testid="admin-audit-filter-sort-desc">created_at:desc</option>
            <option value="created_at:asc" data-testid="admin-audit-filter-sort-asc">created_at:asc</option>
          </select>
        </div>

        <div className="mb-3 grid grid-cols-1 gap-2 md:grid-cols-3" data-testid="admin-audit-pagination-controls">
          <select
            value={pagination.size}
            onChange={(e) => setPagination((prev) => ({ ...prev, page: 1, size: Number(e.target.value) }))}
            className="h-9 rounded-md border px-3 text-sm"
            data-testid="admin-audit-page-size"
          >
            {[10, 20, 50, 100].map((value) => (
              <option key={value} value={value} data-testid={`admin-audit-page-size-option-${value}`}>{value}</option>
            ))}
          </select>
          <div className="flex gap-2">
            <button type="button" onClick={applyFilters} className="h-9 rounded-md border px-3 text-sm" data-testid="admin-audit-apply-filters">Uygula</button>
            <button type="button" onClick={clearFilters} className="h-9 rounded-md border px-3 text-sm" data-testid="admin-audit-clear-filters">Temizle</button>
          </div>
          <div className="flex items-center justify-end gap-2" data-testid="admin-audit-pagination-summary">
            <span className="text-xs text-slate-500" data-testid="admin-audit-pagination-meta">
              page {pagination.page}/{Math.max(1, pagination.total_pages || 1)} · total {pagination.total}
            </span>
            <button
              type="button"
              className="h-8 rounded-md border px-2 text-xs disabled:opacity-50"
              disabled={pagination.page <= 1}
              onClick={() => onPageMove(pagination.page - 1)}
              data-testid="admin-audit-pagination-prev"
            >
              Prev
            </button>
            <button
              type="button"
              className="h-8 rounded-md border px-2 text-xs disabled:opacity-50"
              disabled={pagination.page >= Math.max(1, pagination.total_pages || 1)}
              onClick={() => onPageMove(pagination.page + 1)}
              data-testid="admin-audit-pagination-next"
            >
              Next
            </button>
          </div>
        </div>

        {loading ? <AdminLoadingState message="Audit kayıtları yükleniyor..." testId="admin-audit-events-loading" /> : null}
        {error ? <AdminErrorState message={error} testId="admin-audit-events-error" /> : null}

        {!loading && !error ? (
          events.length === 0 ? (
            <AdminEmptyState message="Kayıt yok." testId="admin-audit-events-empty" />
          ) : (
            <div className="overflow-auto" data-testid="admin-audit-events-table-wrap">
              <table className="w-full text-sm" data-testid="admin-audit-events-table">
                <thead>
                  <tr className="border-b text-left text-xs text-muted-foreground">
                    <th className="py-2 pr-2">Time</th>
                    <th className="py-2 pr-2">Action</th>
                    <th className="py-2 pr-2">Resource</th>
                    <th className="py-2 pr-2">Actor</th>
                    <th className="py-2 pr-2">Severity</th>
                  </tr>
                </thead>
                <tbody>
                  {events.map((evt) => (
                    <tr key={evt.id} className="border-b" data-testid={`admin-audit-event-row-${evt.id}`}>
                      <td className="py-2 pr-2" data-testid={`admin-audit-event-time-${evt.id}`}>{evt.occurred_at || '-'}</td>
                      <td className="py-2 pr-2" data-testid={`admin-audit-event-action-${evt.id}`}>{evt.action}</td>
                      <td className="py-2 pr-2" data-testid={`admin-audit-event-resource-${evt.id}`}>{evt.resource_type}</td>
                      <td className="py-2 pr-2" data-testid={`admin-audit-event-actor-${evt.id}`}>{evt.actor_email_masked || '-'}</td>
                      <td className="py-2 pr-2" data-testid={`admin-audit-event-severity-${evt.id}`}>
                        <AdminStatusBadge
                          label={String(evt.severity || 'info')}
                          variant={resolveSeverityVariant(evt.severity)}
                          testId={`admin-audit-event-severity-badge-${evt.id}`}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        ) : null}
      </div>
    </div>
  );
}