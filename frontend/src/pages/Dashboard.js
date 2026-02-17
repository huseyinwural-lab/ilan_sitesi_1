import { useState, useEffect } from 'react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { useCountry } from '../contexts/CountryContext';
import { 
  Users, Globe, Flag, Activity, TrendingUp, 
  Shield, Clock, ArrowUpRight, ArrowDownRight 
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const StatCard = ({ icon: Icon, title, value, subtitle, trend, trendUp }) => (
  <div className="stat-card" data-testid={`stat-card-${title.toLowerCase().replace(/\s/g, '-')}`}>
    <div className="flex items-start justify-between">
      <div>
        <p className="text-sm font-medium text-muted-foreground">{title}</p>
        <p className="text-3xl font-bold mt-2 tracking-tight">{value}</p>
        {subtitle && <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>}
      </div>
      <div className="p-2 rounded-md bg-primary/10">
        <Icon className="text-primary" size={20} />
      </div>
    </div>
    {trend && (
      <div className={`flex items-center gap-1 mt-3 text-xs font-medium ${trendUp ? 'text-emerald-600' : 'text-rose-600'}`}>
        {trendUp ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
        {trend}
      </div>
    )}
  </div>
);

const RoleDistribution = ({ data, t }) => {
  const roles = [
    { key: 'super_admin', color: 'bg-blue-500' },
    { key: 'country_admin', color: 'bg-indigo-500' },
    { key: 'moderator', color: 'bg-purple-500' },
    { key: 'support', color: 'bg-amber-500' },
    { key: 'finance', color: 'bg-emerald-500' }
  ];
  
  const total = Object.values(data).reduce((a, b) => a + b, 0) || 1;

  return (
    <div className="bg-card rounded-md border p-6">
      <h3 className="font-semibold mb-4">{t('role')} Distribution</h3>
      <div className="space-y-3">
        {roles.map(({ key, color }) => (
          <div key={key} className="flex items-center gap-3">
            <div className={`w-3 h-3 rounded-full ${color}`} />
            <span className="text-sm flex-1">{t(key)}</span>
            <span className="text-sm font-medium">{data[key] || 0}</span>
            <div className="w-20 h-2 bg-muted rounded-full overflow-hidden">
              <div 
                className={`h-full ${color}`} 
                style={{ width: `${((data[key] || 0) / total) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const RecentActivity = ({ logs, t, getTranslated }) => {
  const actionColors = {
    CREATE: 'text-emerald-600 bg-emerald-100 dark:bg-emerald-900/30',
    UPDATE: 'text-blue-600 bg-blue-100 dark:bg-blue-900/30',
    DELETE: 'text-rose-600 bg-rose-100 dark:bg-rose-900/30',
    LOGIN: 'text-indigo-600 bg-indigo-100 dark:bg-indigo-900/30',
    TOGGLE: 'text-amber-600 bg-amber-100 dark:bg-amber-900/30',
    SUSPEND: 'text-orange-600 bg-orange-100 dark:bg-orange-900/30',
    ACTIVATE: 'text-teal-600 bg-teal-100 dark:bg-teal-900/30',
  };

  return (
    <div className="bg-card rounded-md border p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold">{t('recent_activity')}</h3>
        <Activity size={18} className="text-muted-foreground" />
      </div>
      <div className="space-y-3">
        {logs.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">No recent activity</p>
        ) : (
          logs.slice(0, 8).map((log, idx) => (
            <div key={log.id || idx} className="flex items-start gap-3 text-sm">
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${actionColors[log.action] || 'bg-muted'}`}>
                {log.action}
              </span>
              <div className="flex-1 min-w-0">
                <p className="truncate">
                  <span className="font-medium">{log.resource_type}</span>
                  {log.user_email && (
                    <span className="text-muted-foreground"> by {log.user_email}</span>
                  )}
                </p>
                <p className="text-xs text-muted-foreground">
                  {new Date(log.created_at).toLocaleString()}
                </p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const { t, getTranslated } = useLanguage();
  const { selectedCountry, getFlag } = useCountry();

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const country = new URLSearchParams(window.location.search).get('country');
      const qs = country ? `?country=${encodeURIComponent(country)}` : '';
      const response = await axios.get(`${API}/dashboard/stats${qs}`);
      setStats(response.data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="dashboard">
      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard 
          icon={Users} 
          title={t('total_users')} 
          value={stats?.users?.total || 0}
          subtitle={`${stats?.users?.active || 0} ${t('active').toLowerCase()}`}
        />
        <StatCard 
          icon={Globe} 
          title={t('enabled_countries')} 
          value={stats?.countries?.enabled || 0}
          subtitle="DE, CH, FR, AT"
        />
        <StatCard 
          icon={Flag} 
          title={t('enabled_features')} 
          value={stats?.feature_flags?.enabled || 0}
          subtitle={`of ${stats?.feature_flags?.total || 0} total`}
        />
        <StatCard 
          icon={Shield} 
          title="Active Modules" 
          value="2"
          subtitle="Emlak, Vasıta"
        />
      </div>

      {/* Role Distribution & Recent Activity */}
      <div className="grid gap-6 lg:grid-cols-2">
        <RoleDistribution data={stats?.users_by_role || {}} t={t} />
        <RecentActivity logs={stats?.recent_activity || []} t={t} getTranslated={getTranslated} />
      </div>

      {/* Quick Actions */}
      <div className="bg-card rounded-md border p-6">
        <h3 className="font-semibold mb-4">Quick Actions</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <a 
            href="/admin/users" 
            className="flex items-center gap-2 p-3 rounded-md border hover:bg-muted/50 transition-colors"
            data-testid="quick-action-users"
          >
            <Users size={18} className="text-primary" />
            <span className="text-sm font-medium">{t('users')}</span>
          </a>
          <a 
            href="/admin/feature-flags" 
            className="flex items-center gap-2 p-3 rounded-md border hover:bg-muted/50 transition-colors"
            data-testid="quick-action-flags"
          >
            <Flag size={18} className="text-primary" />
            <span className="text-sm font-medium">{t('feature_flags')}</span>
          </a>
          <a 
            href="/admin/countries" 
            className="flex items-center gap-2 p-3 rounded-md border hover:bg-muted/50 transition-colors"
            data-testid="quick-action-countries"
          >
            <Globe size={18} className="text-primary" />
            <span className="text-sm font-medium">{t('countries')}</span>
          </a>
          <a 
            href="/admin/audit-logs" 
            className="flex items-center gap-2 p-3 rounded-md border hover:bg-muted/50 transition-colors"
            data-testid="quick-action-audit"
          >
            <Clock size={18} className="text-primary" />
            <span className="text-sm font-medium">{t('audit_logs')}</span>
          </a>
        </div>
      </div>
    </div>
  );
}
