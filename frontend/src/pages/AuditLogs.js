import { useState, useEffect } from 'react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import {
  Clock,
  Filter,
  Search,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const actionColors = {
  CREATE: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400',
  UPDATE: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
  DELETE: 'bg-rose-100 text-rose-800 dark:bg-rose-900/30 dark:text-rose-400',
  LOGIN: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-400',
  LOGOUT: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400',
  TOGGLE: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
  SUSPEND: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
  ACTIVATE: 'bg-teal-100 text-teal-800 dark:bg-teal-900/30 dark:text-teal-400',
  APPROVE: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
  REJECT: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  NEEDS_REVISION: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
  FAILED_LOGIN: 'bg-rose-100 text-rose-800 dark:bg-rose-900/30 dark:text-rose-400',
  RATE_LIMIT_BLOCK: 'bg-rose-100 text-rose-800 dark:bg-rose-900/30 dark:text-rose-400',
  ADMIN_ROLE_CHANGE: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
  UNAUTHORIZED_ROLE_CHANGE_ATTEMPT: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
};

export default function AuditLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  const [actionFilter, setActionFilter] = useState('');
  const [eventTypeFilter, setEventTypeFilter] = useState('');
  const [resourceFilter, setResourceFilter] = useState('');
  const [countryFilter, setCountryFilter] = useState('');
  const [adminUserFilter, setAdminUserFilter] = useState('');
  const [dateStart, setDateStart] = useState('');
  const [dateEnd, setDateEnd] = useState('');

  const [page, setPage] = useState(0);
  const [expandedLog, setExpandedLog] = useState(null);
  const { t } = useLanguage();
  const limit = 20;

  useEffect(() => {
    fetchLogs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    actionFilter,
    eventTypeFilter,
    resourceFilter,
    countryFilter,
    adminUserFilter,
    dateStart,
    dateEnd,
    page,
  ]);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      params.append('skip', page * limit);
      params.append('limit', limit);
      if (actionFilter) params.append('action', actionFilter);
      if (eventTypeFilter) params.append('event_type', eventTypeFilter);
      if (resourceFilter) params.append('resource_type', resourceFilter);
      if (countryFilter) params.append('country', countryFilter);
      if (adminUserFilter) params.append('admin_user_id', adminUserFilter);
      if (dateStart) params.append('start', dateStart);
      if (dateEnd) params.append('end', dateEnd);

      const response = await axios.get(`${API}/audit-logs?${params}`);
      setLogs(response.data);
    } catch (error) {
      console.error('Failed to fetch audit logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleString();
  };

  const filtered = logs.filter((log) => {
    if (!search.trim()) return true;
    const s = search.toLowerCase();
    return JSON.stringify(log).toLowerCase().includes(s);
  });

  return (
    <div className="space-y-6" data-testid="audit-logs-page">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{t('audit_logs')}</h1>
        <p className="text-muted-foreground text-sm mt-1">System activity and change history</p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <div className="relative">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search logs…"
            className="h-9 pl-8 pr-3 rounded-md border bg-background text-sm"
          />
        </div>

        <Filter className="h-4 w-4 text-muted-foreground" />

        <select
          value={eventTypeFilter}
          onChange={(e) => {
            setEventTypeFilter(e.target.value);
            setPage(0);
          }}
          className="h-9 px-3 rounded-md border bg-background text-sm"
          data-testid="audit-event-type-filter"
        >
          <option value="">All Event Types</option>
          <option value="FAILED_LOGIN">FAILED_LOGIN</option>
          <option value="RATE_LIMIT_BLOCK">RATE_LIMIT_BLOCK</option>
          <option value="ADMIN_ROLE_CHANGE">ADMIN_ROLE_CHANGE</option>
          <option value="UNAUTHORIZED_ROLE_CHANGE_ATTEMPT">UNAUTHORIZED_ROLE_CHANGE_ATTEMPT</option>
          <option value="MODERATION_APPROVE">MODERATION_APPROVE</option>
          <option value="MODERATION_REJECT">MODERATION_REJECT</option>
          <option value="MODERATION_NEEDS_REVISION">MODERATION_NEEDS_REVISION</option>
        </select>

        <select
          value={countryFilter}
          onChange={(e) => {
            setCountryFilter(e.target.value);
            setPage(0);
          }}
          className="h-9 px-3 rounded-md border bg-background text-sm"
          data-testid="audit-country-filter"
        >
          <option value="">All Countries</option>
          <option value="DE">DE</option>
          <option value="CH">CH</option>
          <option value="FR">FR</option>
          <option value="AT">AT</option>
        </select>

        <input
          value={adminUserFilter}
          onChange={(e) => {
            setAdminUserFilter(e.target.value);
            setPage(0);
          }}
          placeholder="admin_user_id"
          className="h-9 px-3 rounded-md border bg-background text-sm"
          data-testid="audit-admin-user-filter"
        />

        <input
          type="date"
          value={dateStart}
          onChange={(e) => {
            setDateStart(e.target.value);
            setPage(0);
          }}
          className="h-9 px-3 rounded-md border bg-background text-sm"
          data-testid="audit-date-start"
        />

        <input
          type="date"
          value={dateEnd}
          onChange={(e) => {
            setDateEnd(e.target.value);
            setPage(0);
          }}
          className="h-9 px-3 rounded-md border bg-background text-sm"
          data-testid="audit-date-end"
        />

        <select
          value={actionFilter}
          onChange={(e) => {
            setActionFilter(e.target.value);
            setPage(0);
          }}
          className="h-9 px-3 rounded-md border bg-background text-sm"
          data-testid="audit-action-filter"
        >
          <option value="">All Actions</option>
          <option value="CREATE">CREATE</option>
          <option value="UPDATE">UPDATE</option>
          <option value="DELETE">DELETE</option>
          <option value="LOGIN">LOGIN</option>
          <option value="TOGGLE">TOGGLE</option>
          <option value="SUSPEND">SUSPEND</option>
          <option value="ACTIVATE">ACTIVATE</option>
          <option value="APPROVE">APPROVE</option>
          <option value="REJECT">REJECT</option>
          <option value="NEEDS_REVISION">NEEDS_REVISION</option>
        </select>

        <select
          value={resourceFilter}
          onChange={(e) => {
            setResourceFilter(e.target.value);
            setPage(0);
          }}
          className="h-9 px-3 rounded-md border bg-background text-sm"
          data-testid="audit-resource-filter"
        >
          <option value="">All Resources</option>
          <option value="auth">Auth</option>
          <option value="user">User</option>
          <option value="listing">Listing</option>
          <option value="country">Country</option>
          <option value="feature_flag">Feature Flag</option>
        </select>
      </div>

      <div className="border rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-muted">
            <tr>
              <th className="text-left p-3">Timestamp</th>
              <th className="text-left p-3">Event</th>
              <th className="text-left p-3">Action</th>
              <th className="text-left p-3">Resource</th>
              <th className="text-left p-3">User</th>
              <th className="text-left p-3">Details</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6} className="p-6 text-center">
                  <div className="flex justify-center">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary" />
                  </div>
                </td>
              </tr>
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={6} className="p-6 text-center text-muted-foreground">
                  No logs found
                </td>
              </tr>
            ) : (
              filtered.map((log) => (
                <tr key={log.id} className="border-t hover:bg-muted/50">
                  <td className="p-3 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <Clock size={14} className="text-muted-foreground" />
                      {formatDate(log.created_at || log.ts)}
                    </div>
                  </td>
                  <td className="p-3">
                    <span className="font-mono text-xs">{log.event_type || '-'}</span>
                  </td>
                  <td className="p-3">
                    <span
                      className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${actionColors[log.action] || 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400'}`}
                    >
                      {log.action || '-'}
                    </span>
                  </td>
                  <td className="p-3">
                    <span className="text-muted-foreground">
                      {log.resource_type || '-'}
                      {log.resource_id ? `:${log.resource_id}` : ''}
                    </span>
                  </td>
                  <td className="p-3">
                    <span className="text-muted-foreground">{log.user_email || log.email || log.user_id || '-'}</span>
                  </td>
                  <td className="p-3">
                    <button
                      onClick={() => setExpandedLog(expandedLog === log.id ? null : log.id)}
                      className="text-primary hover:underline text-xs"
                    >
                      {expandedLog === log.id ? 'Hide' : 'View'}
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>

        {expandedLog && (
          <div className="border-t bg-muted/30 p-4">
            <pre className="text-xs overflow-auto">{JSON.stringify(logs.find((l) => l.id === expandedLog), null, 2)}</pre>
          </div>
        )}
      </div>

      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Showing {page * limit + 1} - {page * limit + filtered.length}
        </p>
        <div className="flex gap-2">
          <button
            onClick={() => setPage(Math.max(0, page - 1))}
            disabled={page === 0}
            className="flex items-center gap-1 px-3 py-1.5 rounded-md border text-sm disabled:opacity-50"
          >
            <ChevronLeft size={16} />
            Previous
          </button>
          <button
            onClick={() => setPage(page + 1)}
            disabled={filtered.length < limit}
            className="flex items-center gap-1 px-3 py-1.5 rounded-md border text-sm disabled:opacity-50"
          >
            Next
            <ChevronRight size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
