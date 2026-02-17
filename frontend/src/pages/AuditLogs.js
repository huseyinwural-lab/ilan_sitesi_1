import { useState, useEffect } from 'react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { 
  Clock, Filter, Search, ChevronLeft, ChevronRight
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

};

export default function AuditLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
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
  }, [actionFilter, eventTypeFilter, resourceFilter, countryFilter, adminUserFilter, dateStart, dateEnd, page]);

  const fetchLogs = async () => {
    try {
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
    const date = new Date(dateStr);
    return date.toLocaleString();
  };

  return (
    <div className="space-y-6" data-testid="audit-logs-page">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{t('audit_logs')}</h1>
        <p className="text-muted-foreground text-sm mt-1">
          System activity and change history
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <select
          value={actionFilter}
          onChange={(e) => { setActionFilter(e.target.value); setPage(0); }}
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
          onChange={(e) => { setResourceFilter(e.target.value); setPage(0); }}
          className="h-9 px-3 rounded-md border bg-background text-sm"
          data-testid="audit-resource-filter"
        >
          <option value="">All Resources</option>
          <option value="user">User</option>
          <option value="feature_flag">Feature Flag</option>
          <option value="country">Country</option>
          <option value="listing">Listing</option>
        </select>
      </div>

      {/* Logs Table */}
      <div className="rounded-md border bg-card overflow-hidden">
        <table className="data-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Action</th>
              <th>Resource</th>
              <th>User</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={5} className="text-center py-8">
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary" />
                  </div>
                </td>
              </tr>
            ) : logs.length === 0 ? (
              <tr>
                <td colSpan={5} className="text-center py-8 text-muted-foreground">
                  No audit logs found
                </td>
              </tr>
            ) : (
              logs.map((log) => (
                <tr 
                  key={log.id} 
                  className="cursor-pointer"
                  onClick={() => setExpandedLog(expandedLog === log.id ? null : log.id)}
                  data-testid={`audit-log-${log.id}`}
                >
                  <td className="whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <Clock size={14} className="text-muted-foreground" />
                      <span className="text-sm">{formatDate(log.created_at)}</span>
                    </div>
                  </td>
                  <td>
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${actionColors[log.action] || 'bg-muted'}`}>
                      {log.action}
                    </span>
                  </td>
                  <td>
                    <div>
                      <span className="font-medium capitalize">{log.resource_type?.replace('_', ' ')}</span>
                      {log.resource_id && (
                        <p className="text-xs text-muted-foreground font-mono truncate max-w-[120px]">
                          {log.resource_id}
                        </p>
                      )}
                    </div>
                  </td>
                  <td className="text-muted-foreground text-sm">
                    {log.user_email || 'System'}
                  </td>
                  <td>
                    {expandedLog === log.id ? (
                      <div className="text-xs space-y-1">
                        {log.old_values && (
                          <div>
                            <span className="text-muted-foreground">Old: </span>
                            <code className="text-rose-600">{JSON.stringify(log.old_values)}</code>
                          </div>
                        )}
                        {log.new_values && (
                          <div>
                            <span className="text-muted-foreground">New: </span>
                            <code className="text-emerald-600">{JSON.stringify(log.new_values)}</code>
                          </div>
                        )}
                        {log.ip_address && (
                          <div className="text-muted-foreground">
                            IP: {log.ip_address}
                          </div>
                        )}
                      </div>
                    ) : (
                      <span className="text-muted-foreground text-xs">Click to expand</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Showing {page * limit + 1} - {page * limit + logs.length}
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
            disabled={logs.length < limit}
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
