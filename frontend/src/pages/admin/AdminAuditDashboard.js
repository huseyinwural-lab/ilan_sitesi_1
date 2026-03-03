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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({ action: '', resource_type: '', q: '' });

  const authHeader = useMemo(
    () => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` }),
    [],
  );

  const loadAuditData = async () => {
    setLoading(true);
    setError('');
    try {
      const params = {
        limit: 50,
        ...(filters.action ? { action: filters.action } : {}),
        ...(filters.resource_type ? { resource_type: filters.resource_type } : {}),
        ...(filters.q ? { q: filters.q } : {}),
      };

      const [schemaRes, eventsRes, statsRes, anomaliesRes] = await Promise.all([
        axios.get(`${API}/api/admin/audit/dashboard/schema`, { headers: authHeader }),
        axios.get(`${API}/api/admin/audit/dashboard/events`, { headers: authHeader, params }),
        axios.get(`${API}/api/admin/audit/dashboard/stats`, { headers: authHeader }),
        axios.get(`${API}/api/admin/audit/dashboard/anomalies`, { headers: authHeader }),
      ]);

      setSchemaInfo(schemaRes.data || null);
      setEvents(eventsRes.data?.items || []);
      setStats(statsRes.data || { windows: { '24h': null, '7d': null } });
      setAnomalies(anomaliesRes.data?.anomalies || []);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Audit dashboard verileri alınamadı.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAuditData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onFilterChange = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const applyFilters = () => {
    loadAuditData();
  };

  const clearFilters = () => {
    setFilters({ action: '', resource_type: '', q: '' });
    setTimeout(() => loadAuditData(), 0);
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
            value={filters.action}
            onChange={(e) => onFilterChange('action', e.target.value)}
            placeholder="action"
            className="h-9 rounded-md border px-3 text-sm"
            data-testid="admin-audit-filter-action"
          />
          <input
            value={filters.resource_type}
            onChange={(e) => onFilterChange('resource_type', e.target.value)}
            placeholder="resource_type"
            className="h-9 rounded-md border px-3 text-sm"
            data-testid="admin-audit-filter-resource"
          />
          <input
            value={filters.q}
            onChange={(e) => onFilterChange('q', e.target.value)}
            placeholder="search"
            className="h-9 rounded-md border px-3 text-sm"
            data-testid="admin-audit-filter-search"
          />
          <div className="flex gap-2">
            <button type="button" onClick={applyFilters} className="h-9 rounded-md border px-3 text-sm" data-testid="admin-audit-apply-filters">Uygula</button>
            <button type="button" onClick={clearFilters} className="h-9 rounded-md border px-3 text-sm" data-testid="admin-audit-clear-filters">Temizle</button>
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