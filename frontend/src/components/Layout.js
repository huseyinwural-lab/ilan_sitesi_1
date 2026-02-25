import { NavLink, useNavigate, useLocation, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { useCountry } from '../contexts/CountryContext';
import { useTheme } from '../contexts/ThemeContext';
import { 
  LayoutDashboard, Users, Globe, Flag, Clock, Settings,
  LogOut, Menu, X, Sun, Moon, ChevronDown, FolderTree, Settings2, MenuSquare,
  Building, Star, ShieldCheck, FileText, Percent, Car, TrendingUp, Activity, Sparkles, Layers, Package
} from 'lucide-react';
import AdminBreadcrumbs from '@/components/admin/AdminBreadcrumbs';
import { Switch } from '@/components/ui/switch';
import { ADMIN_ROLE_GROUPS } from '@/shared/adminRbac';

import { useState, useEffect, useRef, useMemo } from 'react';


export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const { t, language, setLanguage } = useLanguage();
  const { selectedCountry, setSelectedCountry, getFlag, countryFlags } = useCountry();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();

  const urlCountry = (searchParams.get('country') || '').toUpperCase();
  const [adminPreferredMode, setAdminPreferredMode] = useState(() => {
    return localStorage.getItem('admin_mode') || (urlCountry ? 'country' : 'global');
  });
  const [sessionStatus, setSessionStatus] = useState('loading');
  const [sessionError, setSessionError] = useState('');
  const [systemHealth, setSystemHealth] = useState(null);
  const [systemHealthStatus, setSystemHealthStatus] = useState('idle');
  const [systemHealthDetail, setSystemHealthDetail] = useState(null);
  const [systemHealthDetailStatus, setSystemHealthDetailStatus] = useState('idle');
  const [showHealthPanel, setShowHealthPanel] = useState(false);
  const [cdnCountry, setCdnCountry] = useState('DE');
  const healthPanelRef = useRef(null);

  const checkSession = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setSessionStatus('error');
      setSessionError('Oturum bulunamadı. Lütfen tekrar giriş yapın.');
      return;
    }
    try {
      setSessionStatus('loading');
      setSessionError('');
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/session/health`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.status === 401 || res.status === 403) {
        setSessionStatus('error');
        setSessionError('Oturum süresi doldu. Lütfen tekrar giriş yapın.');
        logout();
        return;
      }
      if (!res.ok) {
        setSessionStatus('error');
        setSessionError('Oturum doğrulanamadı. Lütfen tekrar deneyin.');
        return;
      }
      setSessionStatus('ok');
    } catch (error) {
      setSessionStatus('error');
      setSessionError('Sunucuya ulaşılamadı. Lütfen tekrar deneyin.');
    }
  };

  const fetchSystemHealth = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) return;
    try {
      setSystemHealthStatus('loading');
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/system/health-summary`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        setSystemHealthStatus('error');
        return;
      }
      const data = await res.json();
      setSystemHealth(data);
      setSystemHealthStatus('ok');
    } catch (error) {
      setSystemHealthStatus('error');
    }
  };

  const fetchSystemHealthDetail = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) return;
    try {
      setSystemHealthDetailStatus('loading');
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/system/health-detail`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        setSystemHealthDetailStatus('error');
        return;
      }
      const data = await res.json();
      setSystemHealthDetail(data);
      setSystemHealthDetailStatus('ok');
    } catch (error) {
      setSystemHealthDetailStatus('error');
    }
  };

  useEffect(() => {
    checkSession();
  }, []);

  useEffect(() => {
    if (!user) return;
    fetchSystemHealth();
    const interval = setInterval(fetchSystemHealth, 60000);
    return () => clearInterval(interval);
  }, [user]);

  useEffect(() => {
    if (!user || !showHealthPanel) return;
    fetchSystemHealthDetail();
    const interval = setInterval(fetchSystemHealthDetail, 60000);
    return () => clearInterval(interval);
  }, [user, showHealthPanel]);

  useEffect(() => {
    if (!showHealthPanel) return;
    const handleClickOutside = (event) => {
      if (healthPanelRef.current && !healthPanelRef.current.contains(event.target)) {
        setShowHealthPanel(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showHealthPanel]);


  const prevUrlCountryRef = useRef(urlCountry);

  useEffect(() => {
    // Deep-link support: URL drives mode when a country param appears.
    // Important: do NOT tie this to adminPreferredMode changes (otherwise toggling to
    // global may get instantly overridden before URL updates propagate).
    if (urlCountry && prevUrlCountryRef.current !== urlCountry) {
      if (adminPreferredMode !== 'country') {
        setAdminPreferredMode('country');
      }
    }
    prevUrlCountryRef.current = urlCountry;
  }, [urlCountry]);


  useEffect(() => {
    // Persist preferred mode (UX only)
    localStorage.setItem('admin_mode', adminPreferredMode);
  }, [adminPreferredMode]);

  useEffect(() => {
    // Enforce: if user prefers country mode, URL must include ?country=XX
    if (location.pathname.startsWith('/admin') && adminPreferredMode === 'country' && !urlCountry) {
      const last = (localStorage.getItem('last_selected_country') || '').toUpperCase();
      const fallback = last || (selectedCountry || 'DE');
      const params = new URLSearchParams(searchParams);
      params.set('country', fallback);
      setSearchParams(params, { replace: true });
    }
  }, [adminPreferredMode, urlCountry, location.pathname]);

  const isCountryMode = adminPreferredMode === 'country';

  const formatSlaSeconds = (value) => {
    if (value === null || value === undefined) return '--';
    if (value < 60) return `${Math.round(value)}sn`;
    const minutes = Math.round(value / 60);
    if (minutes < 60) return `${minutes}dk`;
    const hours = Math.floor(minutes / 60);
    const remaining = minutes % 60;
    return remaining ? `${hours}sa ${remaining}dk` : `${hours}sa`;
  };

  const healthDisplay = useMemo(() => {
    if (systemHealthStatus === 'error') {
      return { status: 'error', label: 'DB Hata', timeLabel: '--:--', errorLabel: '--/5dk', title: 'Sağlık verisi alınamadı' };
    }
    if (!systemHealth) {
      return { status: 'idle', label: 'DB --', timeLabel: '--:--', errorLabel: '--/5dk', title: 'Sağlık kontrolü bekleniyor' };
    }
    const dbOk = systemHealth.db_status === 'ok';
    const timeLabel = systemHealth.last_check_at
      ? new Date(systemHealth.last_check_at).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })
      : '--:--';
    const errorCount = systemHealth.error_count_5m ?? 0;
    const errorRate = systemHealth.error_rate_per_min_5m ?? 0;
    const title = systemHealth.last_db_error
      ? `Son hata: ${systemHealth.last_db_error}`
      : 'Son 5dk hata oranı';
    return {
      status: dbOk ? 'ok' : 'error',
      label: dbOk ? 'DB OK' : 'DB Down',
      timeLabel,
      errorLabel: `${errorCount}/5dk (${errorRate}/dk)`,
      title,
    };
  }, [systemHealth, systemHealthStatus]);

  const healthDetailDisplay = useMemo(() => {
    if (systemHealthDetailStatus === 'error') {
      return {
        status: 'error',
        errorBuckets: [],
        latencyAvg: '--',
        latencyP95: '--',
        lastEtl: '--',
        errorLabel: 'Veri alınamadı',
        slowQueryCount: 0,
        slowQueryThreshold: 800,
        endpointStats: [],
        moderationSlaAvg: '--',
        moderationSlaPending: 0,
        cdnStatus: 'error',
        cdnHitRatio: '--',
        cdnOriginFetch: '--',
        cdnOriginRatio: '--',
        cdnWarmP95: '--',
        cdnColdP95: '--',
        cdnAlerts: {},
        cdnTargets: {},
        cdnCountryMetrics: {},
        cdnCountrySeries: {},
        cdnCanaryStatus: 'unknown',
        cfIdsPresent: false,
        cfIdsSource: 'unknown',
        cfMetricsEnabled: false,
      };
    }
    if (!systemHealthDetail) {
      return {
        status: 'idle',
        errorBuckets: [],
        latencyAvg: '--',
        latencyP95: '--',
        lastEtl: '--',
        errorLabel: 'Bekleniyor',
        slowQueryCount: 0,
        slowQueryThreshold: 800,
        endpointStats: [],
        moderationSlaAvg: '--',
        moderationSlaPending: 0,
        cdnStatus: 'disabled',
        cdnHitRatio: '--',
        cdnOriginFetch: '--',
        cdnOriginRatio: '--',
        cdnWarmP95: '--',
        cdnColdP95: '--',
        cdnAlerts: {},
        cdnTargets: {},
        cdnCountryMetrics: {},
        cdnCountrySeries: {},
        cdnCanaryStatus: 'unknown',
        cfIdsPresent: false,
        cfIdsSource: 'unknown',
        cfMetricsEnabled: false,
      };
    }
    const buckets = systemHealthDetail.error_buckets_24h || [];
    const maxBucket = buckets.reduce((max, b) => (b.count > max ? b.count : max), 0) || 1;
    const latencyAvg = systemHealthDetail.latency_avg_ms_24h ?? '--';
    const latencyP95 = systemHealthDetail.latency_p95_ms_24h ?? '--';
    const lastEtl = systemHealthDetail.last_etl_at
      ? new Date(systemHealthDetail.last_etl_at).toLocaleString('tr-TR', { hour: '2-digit', minute: '2-digit' })
      : '--';
    const slowQueryCount = systemHealthDetail.slow_query_count_24h ?? 0;
    const slowQueryThreshold = systemHealthDetail.slow_query_threshold_ms ?? 800;
    const endpointOrder = ['/api/search', '/api/listings', '/api/admin/*'];
    const endpointStatsRaw = systemHealthDetail.endpoint_stats || [];
    const endpointStats = endpointOrder.map((endpoint) => {
      const match = endpointStatsRaw.find((item) => item.endpoint === endpoint);
      return {
        endpoint,
        slowCount: match?.slow_query_count ?? 0,
        p95: match?.p95_latency_ms ?? '--',
      };
    });
    const moderationSlaAvg = formatSlaSeconds(systemHealthDetail.moderation_sla_avg_seconds);
    const moderationSlaPending = systemHealthDetail.moderation_sla_pending_count ?? 0;
    const cdnMetrics = systemHealthDetail.cdn_metrics || {};
    const cdnStatus = cdnMetrics.status || (cdnMetrics.enabled === false ? 'disabled' : 'ok');
    const cdnHitRatio = cdnMetrics.cache_hit_ratio ?? '--';
    const cdnOriginFetch = cdnMetrics.origin_fetch_count ?? '--';
    const cdnOriginRatio = cdnMetrics.origin_fetch_ratio ?? '--';
    const cdnWarmP95 = cdnMetrics.image_latency_p95_ms?.warm ?? '--';
    const cdnColdP95 = cdnMetrics.image_latency_p95_ms?.cold ?? '--';
    const cdnAlerts = cdnMetrics.alerts || {};
    const cdnTargets = cdnMetrics.targets || {};
    const cdnCountryMetrics = cdnMetrics.country_metrics || {};
    const cdnCountrySeries = cdnMetrics.country_timeseries || {};
    const cdnCanaryStatus = cdnMetrics.canary_status || 'unknown';
    const cfIdsPresent = systemHealthDetail.cf_ids_present ?? false;
    const cfIdsSource = systemHealthDetail.cf_ids_source ?? 'unknown';
    const cfMetricsEnabled = systemHealthDetail.cf_metrics_enabled ?? false;
    return {
      status: systemHealthDetail.db_status === 'ok' ? 'ok' : 'error',
      errorBuckets: buckets.map((bucket) => ({
        ...bucket,
        heightPct: Math.max(8, Math.round((bucket.count / maxBucket) * 100)),
      })),
      latencyAvg,
      latencyP95,
      lastEtl,
      errorLabel: `${systemHealthDetail.error_count_5m ?? 0}/5dk`,
      slowQueryCount,
      slowQueryThreshold,
      endpointStats,
      moderationSlaAvg,
      moderationSlaPending,
      cdnStatus,
      cdnHitRatio,
      cdnOriginFetch,
      cdnOriginRatio,
      cdnWarmP95,
      cdnColdP95,
      cdnAlerts,
      cdnTargets,
      cdnCountryMetrics,
      cdnCountrySeries,
      cdnCanaryStatus,
      cfIdsPresent,
      cfIdsSource,
      cfMetricsEnabled,
    };
  }, [systemHealthDetail, systemHealthDetailStatus]);

  const cdnCountries = ['DE', 'AT', 'CH', 'FR'];
  const cdnCountryMetrics = healthDetailDisplay.cdnCountryMetrics || {};
  const cdnCountrySeries = healthDetailDisplay.cdnCountrySeries || {};
  const selectedCountryMetrics = cdnCountryMetrics[cdnCountry] || {};
  const selectedCountrySeries = cdnCountrySeries[cdnCountry] || [];

  const getCdnMetricClass = (value, target, type = 'max') => {
    if (value === '--' || value === null || value === undefined) return 'text-slate-500';
    if (target === null || target === undefined) return 'text-slate-700';
    const numeric = Number(value);
    if (Number.isNaN(numeric)) return 'text-slate-500';
    if (type === 'min') {
      return numeric >= target ? 'text-emerald-600' : 'text-rose-600';
    }
    return numeric <= target ? 'text-emerald-600' : 'text-rose-600';
  };

  const sparkMax = selectedCountrySeries.reduce((max, item) => (item.hit_ratio > max ? item.hit_ratio : max), 0) || 100;

  const canaryLabels = {
    OK: 'OK',
    CONFIG_MISSING: 'Config Missing',
    SCOPE_ERROR: 'Scope Error',
    API_ERROR: 'API Error',
  };
  const canaryTooltips = {
    OK: 'Analytics okundu ve veri alındı.',
    CONFIG_MISSING: 'Account/Zone ID veya token eksik.',
    SCOPE_ERROR: 'Token scope yetersiz (403).',
    API_ERROR: 'API çağrısı başarısız veya veri yok.',
  };
  const canaryRaw = healthDetailDisplay.cdnCanaryStatus || 'UNKNOWN';
  const canaryLabel = canaryLabels[canaryRaw] || canaryRaw;
  const canaryTooltip = canaryTooltips[canaryRaw] || 'Canary sonucu bilinmiyor.';


  const canViewSystemHealth = Boolean(
    user && ['super_admin', 'country_admin'].includes(user.role) && location.pathname.startsWith('/admin')
  );

  const [sidebarOpen, setSidebarOpen] = useState(false);

  // NOTE: Side effects (localStorage / URL normalization) should live in effects,
  // but kept minimal here for MVP. If this causes re-render loops, we will migrate.

  const effectiveCountry = (urlCountry || selectedCountry || 'DE').toUpperCase();

  const withCountryParam = (path) => {
    if (!path || !path.startsWith('/admin')) return path;
    if (!isCountryMode) return path;
    const joiner = path.includes('?') ? '&' : '?';
    return `${path}${joiner}country=${encodeURIComponent(effectiveCountry)}`;
  };

  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [countryDropdownOpen, setCountryDropdownOpen] = useState(false);
  const [langDropdownOpen, setLangDropdownOpen] = useState(false);
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);

  // URL is source of truth (Admin Country Context v2)
  const setMode = (nextMode) => {
    const params = new URLSearchParams(searchParams);
    if (nextMode === 'global') {
      setAdminPreferredMode('global');
      params.delete('country');
      setSearchParams(params, { replace: true });
      return;
    }

    // country mode
    setAdminPreferredMode('country');
    const last = (localStorage.getItem('last_selected_country') || '').toUpperCase();
    const fallback = last || (selectedCountry || 'DE');
    params.set('country', fallback);
    setSearchParams(params, { replace: true });
  };

  const setCountryInUrl = (code) => {
    const c = (code || '').toUpperCase();
    const params = new URLSearchParams(searchParams);
    params.set('country', c);
    setSearchParams(params, { replace: true });
    localStorage.setItem('last_selected_country', c);
    setSelectedCountry(c);
  };

  useEffect(() => {
    // Keep CountryContext in sync for UX (flags etc.)
    if (isCountryMode && urlCountry && selectedCountry !== urlCountry) {
      setSelectedCountry(urlCountry);
    }
  }, [isCountryMode, urlCountry]);


  const handleLogout = () => {
    logout();
    navigate('/admin/login');
  };

  const roles = ADMIN_ROLE_GROUPS;

  const navItems = [
    { divider: true, label: 'Dashboard', roles: roles.dashboard },
    { path: '/admin', icon: LayoutDashboard, label: 'Kontrol Paneli', roles: roles.dashboard, testId: 'dashboard-control-panel' },
    { path: '/admin/dashboard', icon: TrendingUp, label: 'Genel Bakış', roles: roles.dashboard, testId: 'dashboard-overview' },
    { path: '/admin/country-compare', icon: Activity, label: 'Ülke Karşılaştırma', roles: roles.dashboard, testId: 'dashboard-country-compare' },

    { divider: true, label: 'Yönetim', roles: roles.userOps },
    { path: '/admin/admin-users', icon: Users, label: 'Admin Kullanıcıları', roles: roles.adminOnly, testId: 'management-admin-users' },
    { path: '/admin/roles', icon: ShieldCheck, label: 'Rol Tanımları', roles: roles.adminOnly, testId: 'management-roles' },
    { path: '/admin/rbac-matrix', icon: MenuSquare, label: 'Yetki Atama (RBAC Matrix)', roles: roles.adminOnly, testId: 'management-rbac-matrix' },

    { divider: true, label: 'Üyeler', roles: roles.userOps },
  { path: '/admin/individual-users', icon: Users, label: 'Bireysel Kullanıcılar', roles: roles.userOps, testId: 'members-individual-users' },
    { path: '/admin/dealers', icon: Building, label: 'Kurumsal Kullanıcılar', roles: roles.userOps, testId: 'members-corporate-users' },
  { path: '/admin/individual-applications', icon: Clock, label: 'Bireysel Üye Başvurular', roles: roles.userOps, testId: 'members-individual-applications' },
    { path: '/admin/dealer-applications', icon: Clock, label: 'Kurumsal Üye Başvurular', roles: roles.userOps, testId: 'members-corporate-applications' },

    { divider: true, label: 'İlan & Moderasyon', roles: roles.moderationWithSupport },
    { path: '/admin/moderation', icon: ShieldCheck, label: 'Moderation Queue', roles: roles.moderation, testId: 'listings-moderation-queue' },
  { path: '/admin/individual-listing-applications', icon: FileText, label: 'Bireysel İlan Başvuruları', roles: roles.moderation, testId: 'listings-individual-applications' },
  { path: '/admin/corporate-listing-applications', icon: FileText, label: 'Kurumsal İlan Başvuruları', roles: roles.moderation, testId: 'listings-corporate-applications' },

    { divider: true, label: 'Kampanyalar', roles: roles.moderation },
  { path: '/admin/individual-campaigns', icon: Flag, label: 'Bireysel Kampanyalar', roles: roles.moderation, testId: 'campaigns-individual' },
  { path: '/admin/corporate-campaigns', icon: Flag, label: 'Kurumsal Kampanyalar', roles: roles.moderation, testId: 'campaigns-corporate' },

    { divider: true, label: 'Reklamlar', roles: roles.adsManager },
  { path: '/admin/ads', icon: Activity, label: 'Reklam Yönetimi', roles: roles.adsManager, testId: 'ads-management' },
  { path: '/admin/ads/campaigns', icon: Flag, label: 'Kampanyalar', roles: roles.adsManager, testId: 'ads-campaigns' },

    { divider: true, label: 'Fiyatlandırma', roles: roles.pricingManager },
  { path: '/admin/pricing/campaign', icon: Sparkles, label: 'Kampanya Modu', roles: roles.pricingManager, testId: 'pricing-campaign-mode' },
  { path: '/admin/pricing/tiers', icon: Layers, label: 'Bireysel Kampanyalar', roles: roles.pricingManager, testId: 'pricing-individual-campaigns' },
  { path: '/admin/pricing/packages', icon: Package, label: 'Kurumsal Kampanyalar', roles: roles.pricingManager, testId: 'pricing-corporate-campaigns' },

    { divider: true, label: 'Katalog & İçerik', roles: roles.catalogView },
    { path: '/admin/categories', icon: FolderTree, label: 'Kategoriler', roles: roles.catalogView, testId: 'catalog-categories' },
    { path: '/admin/categories/import-export', icon: FileText, label: 'Kategori Import/Export', roles: roles.catalogAdmin, testId: 'catalog-categories-import-export' },
    { path: '/admin/attributes', icon: Settings2, label: 'Özellikler', roles: roles.catalogAdmin, testId: 'catalog-attributes' },
    { path: '/admin/menu-management', icon: MenuSquare, label: 'Menü Yönetimi', roles: roles.adminOnly, comingSoon: true, testId: 'catalog-menu-management' },

    { divider: true, label: 'Araç Verisi', roles: roles.vehicleAdmin },
    { path: '/admin/vehicle-makes', icon: Car, label: 'Araç Markaları', roles: roles.vehicleAdmin, testId: 'vehicle-makes' },
    { path: '/admin/vehicle-models', icon: Car, label: 'Araç Modelleri', roles: roles.vehicleAdmin, testId: 'vehicle-models' },

    { divider: true, label: 'Finans', roles: roles.finance },
    { path: '/admin/plans', icon: Star, label: 'Planlar', roles: roles.finance, testId: 'finance-plans' },
    { path: '/admin/invoices', icon: FileText, label: 'Faturalar', roles: roles.finance, testId: 'finance-invoices' },
    { path: '/admin/payments', icon: Activity, label: 'Ödemeler', roles: roles.finance, testId: 'finance-payments' },
    { path: '/admin/tax-rates', icon: Percent, label: 'Vergi Oranları', roles: roles.finance, testId: 'finance-tax-rates' },

    { divider: true, label: 'Sistem', roles: roles.system },
    { path: '/admin/countries', icon: Globe, label: 'Ülkeler', roles: roles.system, testId: 'system-countries' },
    { path: '/admin/audit', icon: Clock, label: 'Denetim Kayıtları', roles: roles.auditViewer, testId: 'system-audit-logs' },
    { path: '/admin/system-settings', icon: Settings, label: 'Sistem Ayarları', roles: roles.system, testId: 'system-settings' },
  ];

  const filteredNavItems = navItems.filter(item => 
    !item.roles || item.roles.includes(user?.role)
  );

  const isAdminPathDisabled = (path) => {
    if (!path) return false;
    // If route is not registered, treat as disabled (prevents 404 navigation)
    const known = new Set([
      '/admin',
      '/admin/users',
      '/admin/admin-users',
      '/admin/roles',
      '/admin/rbac-matrix',
      '/admin/individual-users',
      '/admin/individual-applications',
      '/admin/individual-listing-applications',
      '/admin/corporate-listing-applications',
      '/admin/individual-campaigns',
      '/admin/corporate-campaigns',
      '/admin/ads',
      '/admin/ads/campaigns',
      '/admin/pricing/campaign',
      '/admin/pricing/tiers',
      '/admin/pricing/packages',
      '/admin/dashboard',
      '/admin/country-compare',
      '/admin/countries',
      '/admin/system-settings',
      '/admin/categories',
      '/admin/menu-management',
      '/admin/attributes',
      '/admin/vehicle-makes',
      '/admin/vehicle-models',
      '/admin/audit',
      '/admin/plans',
      '/admin/payments',
      '/admin/moderation',
      '/admin/listings',
      '/admin/invoices',
      '/admin/tax-rates',
      '/admin/plans',
      '/admin/dealers',
      '/admin/dealer-applications',
      '/admin/system-settings',

    ]);
    return !known.has(path);
  };

  if (sessionStatus === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50" data-testid="admin-session-loading">
        <div className="text-sm text-slate-600">Admin oturumu doğrulanıyor...</div>
      </div>
    );
  }

  if (sessionStatus === 'error') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50" data-testid="admin-session-error">
        <div className="bg-white border rounded-lg p-6 w-full max-w-md text-center space-y-3">
          <h2 className="text-lg font-semibold">Oturum Hatası</h2>
          <p className="text-sm text-slate-600" data-testid="admin-session-error-message">{sessionError}</p>
          <div className="flex items-center justify-center gap-2">
            <button
              className="px-4 py-2 rounded bg-slate-900 text-white text-sm"
              onClick={checkSession}
              data-testid="admin-session-retry"
            >
              Tekrar Dene
            </button>
            <button
              className="px-4 py-2 rounded border text-sm"
              onClick={logout}
              data-testid="admin-session-logout"
            >
              Çıkış Yap
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Sidebar - Desktop */}
      <aside className={`fixed left-0 top-0 z-40 hidden lg:flex h-screen ${sidebarCollapsed ? 'w-16' : 'w-64'} flex-col border-r bg-card transition-all duration-200`}>
        {/* Logo */}
        <div className={`flex h-16 items-center gap-2 border-b ${sidebarCollapsed ? 'px-3' : 'px-6'}`}>
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center shrink-0">
            <span className="text-primary-foreground font-bold">A</span>
          </div>
          {!sidebarCollapsed && <span className="font-semibold text-lg tracking-tight">Admin Panel</span>}
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="ml-auto p-2 rounded-md hover:bg-muted transition-colors"
            title={sidebarCollapsed ? 'Expand' : 'Collapse'}
            data-testid="sidebar-collapse"
          >
            {sidebarCollapsed ? <ChevronDown size={16} /> : <ChevronDown size={16} className="rotate-90" />}
          </button>
        </div>

        {/* Navigation */}
        <nav className={`flex-1 overflow-y-auto ${sidebarCollapsed ? 'p-2' : 'p-4'}`}>
          <ul className="space-y-1">
            {filteredNavItems.map((item, index) => (
              item.divider ? (
                <li key={`divider-${index}`} className="pt-4 pb-2">
                  {!sidebarCollapsed && (
                    <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-3">
                      {item.label}
                    </span>
                  )}
                </li>
              ) : (
                <li key={item.path}>
                  {item.comingSoon || isAdminPathDisabled(item.path) ? (
                    <div
                      className="sidebar-item opacity-60 cursor-not-allowed"
                      title="Coming soon"
                    data-testid={`nav-${item.testId}`}
                    >
                      <item.icon size={18} />
                      {!sidebarCollapsed && (
                        <span className="flex-1">{typeof item.label === 'string' ? t(item.label) : item.label}</span>
                      )}
                      {!sidebarCollapsed && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted">Yakında</span>
                      )}
                    </div>
                  ) : (
                    <NavLink
                      to={withCountryParam(item.path)}
                      className={({ isActive }) =>
                        `sidebar-item ${isActive ? 'active' : ''}`
                      }
                    data-testid={`nav-${item.testId}`}
                    >
                      <item.icon size={18} />
                      {!sidebarCollapsed && (typeof item.label === 'string' ? t(item.label) : item.label)}
                    </NavLink>
                  )}
                </li>
              )
            ))}
          </ul>
        </nav>

        {/* User Section */}
        <div className="border-t p-4">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary font-semibold">
              {user?.full_name?.charAt(0)?.toUpperCase() || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-medium truncate">{user?.full_name}</p>
              <p className="text-xs text-muted-foreground capitalize">{t(user?.role)}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            data-testid="logout-btn"
          >
            <LogOut size={16} />
            {t('logout')}
          </button>
        </div>
      </aside>

      {/* Mobile Sidebar */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="fixed inset-0 bg-black/50" onClick={() => setSidebarOpen(false)} />
          <aside className="fixed left-0 top-0 h-screen w-64 bg-card border-r">
            <div className="flex h-16 items-center justify-between border-b px-6">
              <span className="font-semibold text-lg">Admin Panel</span>
              <button
                onClick={() => setSidebarOpen(false)}
                className="p-1 rounded hover:bg-muted"
                data-testid="mobile-sidebar-close-button"
              >
                <X size={20} />
              </button>
            </div>
            <nav className="p-4">
              <ul className="space-y-1">
                {filteredNavItems.map((item, index) => (
                  item.divider ? (
                    <li key={`divider-mobile-${index}`} className="pt-4 pb-2">
                      <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-3">
                        {item.label}
                      </span>
                    </li>
                  ) : (
                    <li key={item.path}>
                      {item.comingSoon || isAdminPathDisabled(item.path) ? (
                        <div
                          className="sidebar-item opacity-60 cursor-not-allowed"
                          title="Coming soon"
                    data-testid={`nav-mobile-${item.testId}`}
                        >
                          <item.icon size={18} />
                          <span className="flex-1">{typeof item.label === 'string' ? t(item.label) : item.label}</span>
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted">Yakında</span>
                        </div>
                      ) : (
                        <NavLink
                          to={withCountryParam(item.path)}
                          onClick={() => setSidebarOpen(false)}
                          className={({ isActive }) =>
                            `sidebar-item ${isActive ? 'active' : ''}`
                          }
                    data-testid={`nav-mobile-${item.testId}`}
                        >
                          <item.icon size={18} />
                          {typeof item.label === 'string' ? t(item.label) : item.label}
                        </NavLink>
                      )}
                    </li>
                  )
                ))}
              </ul>
            </nav>
          </aside>
        </div>
      )}

      {/* Main Content */}
      <div className={sidebarCollapsed ? 'lg:pl-16' : 'lg:pl-64'}>
        {/* Topbar */}
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b bg-card/95 backdrop-blur px-4 lg:px-8">
          {/* Left - Mobile menu + Country selector */}
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 rounded-md hover:bg-muted"
              data-testid="mobile-menu-btn"
            >
              <Menu size={20} />
            </button>

            {/* Admin Country Context v2 (URL-based) */}
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 border rounded-md px-2 py-1" data-testid="admin-mode-toggle">
                <span className={`text-xs ${!isCountryMode ? 'font-semibold' : 'text-muted-foreground'}`}>Global</span>
                <Switch
                  checked={isCountryMode}
                  onCheckedChange={(checked) => setMode(checked ? 'country' : 'global')}
                  data-testid="admin-mode-switch"
                />
                <span className={`text-xs ${isCountryMode ? 'font-semibold' : 'text-muted-foreground'}`}>Country</span>
              </div>

              <div className="relative">
                <button
                  onClick={() => {
                    setCountryDropdownOpen(!countryDropdownOpen);
                    setLangDropdownOpen(false);
                    setUserDropdownOpen(false);
                  }}
                  disabled={!isCountryMode}
                  className={`flex items-center gap-2 px-3 py-2 rounded-md hover:bg-muted transition-colors ${!isCountryMode ? 'opacity-50 cursor-not-allowed' : ''}`}
                  data-testid="country-selector"
                  title={!isCountryMode ? 'Country mode kapalı' : 'Country seç'}
                >
                  <span className="text-lg">{getFlag(isCountryMode ? (urlCountry || selectedCountry) : selectedCountry)}</span>
                  <span className="text-sm font-medium">{isCountryMode ? (urlCountry || selectedCountry) : selectedCountry}</span>
                  <ChevronDown size={16} className={`transition-transform ${countryDropdownOpen ? 'rotate-180' : ''}`} />
                </button>

                {countryDropdownOpen && isCountryMode && (
                  <div className="absolute right-0 mt-2 w-48 rounded-md border bg-card shadow-lg z-50">
                    {Object.entries(countryFlags).map(([code]) => (
                      <button
                        key={code}
                        onClick={() => {
                          setCountryInUrl(code);
                          setCountryDropdownOpen(false);
                        }}
                        className={`w-full flex items-center gap-2 px-4 py-2 text-sm hover:bg-muted transition-colors ${
                          (urlCountry || selectedCountry) === code ? 'bg-muted' : ''
                        }`}
                        data-testid={`country-select-${code}`}
                      >
                        <span className="text-lg">{getFlag(code)}</span>
                        <span className="font-medium">{code}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right - Theme, Language, User */}
          <div className="flex items-center gap-2">
            {canViewSystemHealth && (
              <div className="relative" ref={healthPanelRef}>
                <button
                  type="button"
                  onClick={() => setShowHealthPanel((prev) => !prev)}
                  className={`hidden md:flex items-center gap-2 px-3 py-1 rounded-full border text-xs ${
                    healthDisplay.status === 'ok'
                      ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
                      : healthDisplay.status === 'error'
                        ? 'border-rose-200 bg-rose-50 text-rose-700'
                        : 'border-slate-200 bg-slate-50 text-slate-600'
                  }`}
                  data-testid="admin-system-health-badge"
                  title={healthDisplay.title}
                >
                  <span
                    className={`h-2 w-2 rounded-full ${
                      healthDisplay.status === 'ok'
                        ? 'bg-emerald-500'
                        : healthDisplay.status === 'error'
                          ? 'bg-rose-500'
                          : 'bg-slate-400'
                    }`}
                    data-testid="admin-system-health-indicator"
                  />
                  <span data-testid="admin-system-health-status">{healthDisplay.label}</span>
                  <span className="text-muted-foreground" data-testid="admin-system-health-time">{healthDisplay.timeLabel}</span>
                  <span className="text-muted-foreground" data-testid="admin-system-health-error-rate">{healthDisplay.errorLabel}</span>
                </button>

                {showHealthPanel && (
                  <div
                    className="absolute right-0 mt-2 w-80 rounded-xl border bg-white p-4 shadow-lg z-50"
                    data-testid="admin-system-health-panel"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="text-sm font-semibold text-slate-900" data-testid="admin-system-health-panel-title">System Health</div>
                        <span
                          className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] text-slate-600"
                          data-testid="admin-system-health-slow-query-badge"
                          title={`Threshold > ${healthDetailDisplay.slowQueryThreshold}ms`}
                        >
                          Slow Queries (24s): {healthDetailDisplay.slowQueryCount}
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => setShowHealthPanel(false)}
                        className="text-xs text-slate-500 hover:text-slate-700"
                        data-testid="admin-system-health-panel-close"
                      >
                        Kapat
                      </button>
                    </div>
                    <div className="mt-3">
                      <div className="text-xs text-slate-500" data-testid="admin-system-health-panel-error-label">Son 24s Hata Oranı (5dk)</div>
                      <div className="mt-2 flex items-end gap-[2px] h-16" data-testid="admin-system-health-sparkline">
                        {healthDetailDisplay.errorBuckets.length ? (
                          healthDetailDisplay.errorBuckets.map((bucket, idx) => (
                            <div
                              key={`bucket-${idx}`}
                              className="flex-1 rounded-sm bg-slate-300"
                              style={{ height: `${bucket.heightPct}%` }}
                              data-testid={`admin-system-health-bar-${idx}`}
                              title={`${bucket.bucket_start} • ${bucket.count}`}
                            />
                          ))
                        ) : (
                          <div className="text-xs text-slate-400" data-testid="admin-system-health-sparkline-empty">
                            Veri yok
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="mt-3 grid grid-cols-2 gap-3 text-xs">
                      <div className="rounded-lg border border-slate-100 bg-slate-50 p-2" data-testid="admin-system-health-latency-avg">
                        <div className="text-slate-500">DB Ortalama</div>
                        <div className="font-semibold text-slate-900">{healthDetailDisplay.latencyAvg} ms</div>
                      </div>
                      <div className="rounded-lg border border-slate-100 bg-slate-50 p-2" data-testid="admin-system-health-latency-p95">
                        <div className="text-slate-500">DB p95</div>
                        <div className="font-semibold text-slate-900">{healthDetailDisplay.latencyP95} ms</div>
                      </div>
                      <div className="rounded-lg border border-slate-100 bg-slate-50 p-2" data-testid="admin-system-health-last-etl">
                        <div className="text-slate-500">Son ETL</div>
                        <div className="font-semibold text-slate-900">{healthDetailDisplay.lastEtl}</div>
                      </div>
                      <div className="rounded-lg border border-slate-100 bg-slate-50 p-2" data-testid="admin-system-health-error-5m">
                        <div className="text-slate-500">Hata (5dk)</div>
                        <div className="font-semibold text-slate-900">{healthDetailDisplay.errorLabel}</div>
                      </div>
                      <div className="rounded-lg border border-slate-100 bg-slate-50 p-2" data-testid="admin-system-health-moderation-sla">
                        <div className="text-slate-500">Moderation SLA Ort.</div>
                        <div className="font-semibold text-slate-900" data-testid="admin-system-health-moderation-sla-value">{healthDetailDisplay.moderationSlaAvg}</div>
                        <div className="text-[11px] text-slate-500" data-testid="admin-system-health-moderation-sla-pending">Pending: {healthDetailDisplay.moderationSlaPending}</div>
                      </div>
                      <div className="rounded-lg border border-slate-100 bg-slate-50 p-2" data-testid="admin-system-health-cdn-section">
                        <div className="flex items-center justify-between">
                          <div className="text-slate-500">CDN (Cloudflare)</div>
                          <div className="flex items-center gap-2">
                            {healthDetailDisplay.cdnStatus === 'disabled' ? (
                              <span className="text-[11px] font-semibold text-slate-500" data-testid="admin-system-health-cdn-disabled">Kapalı</span>
                            ) : healthDetailDisplay.cdnStatus === 'config_missing' ? (
                              <span className="text-[11px] font-semibold text-amber-600" data-testid="admin-system-health-cdn-config-missing">Configuration Missing</span>
                            ) : healthDetailDisplay.cdnAlerts.has_alert ? (
                              <span className="text-[11px] font-semibold text-rose-600" data-testid="admin-system-health-cdn-alert">Uyarı</span>
                            ) : (
                              <span className="text-[11px] font-semibold text-emerald-600" data-testid="admin-system-health-cdn-ok">OK</span>
                            )}
                            {!healthDetailDisplay.cfMetricsEnabled && (
                              <span className="text-[11px] font-semibold text-amber-600" data-testid="admin-system-health-cf-flag-warning">Flag Off</span>
                            )}
                          </div>
                        </div>
                        <div className="mt-2 space-y-1 text-[11px] text-slate-600" data-testid="admin-system-health-cdn-metrics">
                          <div data-testid="admin-system-health-cdn-hit">Hit Ratio: {healthDetailDisplay.cdnHitRatio}%</div>
                          <div data-testid="admin-system-health-cdn-origin">Origin Fetch: {healthDetailDisplay.cdnOriginFetch}</div>
                          <div data-testid="admin-system-health-cdn-origin-ratio">Origin Ratio: {healthDetailDisplay.cdnOriginRatio}%</div>
                          <div data-testid="admin-system-health-cdn-warm">Warm p95: {healthDetailDisplay.cdnWarmP95} ms</div>
                          <div data-testid="admin-system-health-cdn-cold">Cold p95: {healthDetailDisplay.cdnColdP95} ms</div>
                        </div>
                      </div>
                    </div>
                    <div className="mt-3 rounded-lg border border-slate-100 bg-slate-50 p-3" data-testid="admin-system-health-cdn-country-section">
                      <div className="flex items-center justify-between">
                        <div className="text-xs font-semibold text-slate-700" data-testid="admin-system-health-cdn-country-title">CDN Country Breakdown</div>
                        <div className="text-[11px] text-slate-500" data-testid="admin-system-health-cdn-active">
                          {healthDetailDisplay.cdnStatus === 'disabled'
                            ? 'Inactive'
                            : healthDetailDisplay.cdnStatus === 'config_missing'
                              ? 'Configuration Missing'
                              : 'CDN Metrics Active'}
                        </div>
                      </div>
                      <div className="mt-2 flex flex-wrap gap-2" data-testid="admin-system-health-cdn-country-toggle">
                        {cdnCountries.map((code) => (
                          <button
                            key={`cdn-country-${code}`}
                            type="button"
                            onClick={() => setCdnCountry(code)}
                            className={`rounded-full border px-2 py-1 text-[11px] font-semibold ${cdnCountry === code ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-slate-200 text-slate-600'}`}
                            data-testid={`admin-system-health-cdn-country-${code}`}
                          >
                            {code}
                          </button>
                        ))}
                      </div>
                      <div className="mt-2 space-y-1 text-[11px] text-slate-600" data-testid="admin-system-health-cdn-country-metrics">
                        {cdnCountries.map((code) => {
                          const metrics = cdnCountryMetrics[code] || {};
                          const hit = metrics.hit_ratio ?? '--';
                          const warm = metrics.warm_p95 ?? '--';
                          const cold = metrics.cold_p95 ?? '--';
                          const hitClass = getCdnMetricClass(hit, metrics.targets?.hit_ratio_min ?? healthDetailDisplay.cdnTargets.hit_ratio_min, 'min');
                          const warmClass = getCdnMetricClass(warm, metrics.targets?.warm_p95 ?? healthDetailDisplay.cdnTargets.warm_p95_ms?.[code], 'max');
                          const coldClass = getCdnMetricClass(cold, metrics.targets?.cold_p95 ?? healthDetailDisplay.cdnTargets.cold_p95_ms?.[code], 'max');
                          return (
                            <div
                              key={`cdn-row-${code}`}
                              className="flex items-center justify-between rounded-md border border-slate-200 bg-white px-2 py-1"
                              data-testid={`admin-system-health-cdn-row-${code}`}
                            >
                              <span className="text-slate-700" data-testid={`admin-system-health-cdn-row-country-${code}`}>{code}</span>
                              <span className={hitClass} data-testid={`admin-system-health-cdn-row-hit-${code}`}>Hit {hit}%</span>
                              <span className={warmClass} data-testid={`admin-system-health-cdn-row-warm-${code}`}>Warm {warm}ms</span>
                              <span className={coldClass} data-testid={`admin-system-health-cdn-row-cold-${code}`}>Cold {cold}ms</span>
                            </div>
                          );
                        })}
                      </div>
                      <div className="mt-3" data-testid="admin-system-health-cdn-sparkline">
                        <div className="text-[11px] text-slate-500">24s Hit Ratio Sparkline ({cdnCountry})</div>
                        <div className="mt-2 flex items-end gap-[2px] h-10" data-testid="admin-system-health-cdn-sparkline-bars">
                          {selectedCountrySeries.length ? (
                            selectedCountrySeries.map((point, idx) => (
                              <div
                                key={`cdn-spark-${idx}`}
                                className="flex-1 rounded-sm bg-blue-200"
                                style={{ height: `${Math.max(6, Math.round((point.hit_ratio / sparkMax) * 100))}%` }}
                                title={`${point.hour} • ${point.hit_ratio}%`}
                                data-testid={`admin-system-health-cdn-sparkline-bar-${idx}`}
                              />
                            ))
                          ) : (
                            <div className="text-[11px] text-slate-400" data-testid="admin-system-health-cdn-sparkline-empty">Veri yok</div>
                          )}
                        </div>
                      </div>
                      <div className="mt-2 text-[11px] text-slate-500" data-testid="admin-system-health-cdn-canary" title={canaryTooltip}>
                        Canary: {canaryLabel} · cf_ids_present: {healthDetailDisplay.cfIdsPresent ? 'true' : 'false'} · source: {healthDetailDisplay.cfIdsSource || '-'}
                      </div>
                    </div>
                    <div className="mt-2 text-[11px] text-slate-500" data-testid="admin-system-health-cdn-targets">
                      Hedefler: Hit ≥ {healthDetailDisplay.cdnTargets.hit_ratio_min ?? 85}% · Cold ≤ {healthDetailDisplay.cdnTargets.origin_fetch_ratio_max ?? 15}% · Warm/Cold p95 ADR-MEDIA-002
                    </div>
                    <div className="mt-3" data-testid="admin-system-health-endpoint-section">
                      <div className="text-xs text-slate-500" data-testid="admin-system-health-endpoint-title">Endpoint Slow Query</div>
                      <div className="mt-2 space-y-2" data-testid="admin-system-health-endpoint-table">
                        {healthDetailDisplay.endpointStats.map((row) => (
                          <div
                            key={row.endpoint}
                            className="flex items-center justify-between rounded-lg border border-slate-100 bg-slate-50 px-2 py-1 text-[11px]"
                            data-testid={`admin-system-health-endpoint-row-${row.endpoint.replace(/\W/g, '-')}`}
                          >
                            <span className="font-medium text-slate-700">{row.endpoint}</span>
                            <span className="text-slate-500">Slow: {row.slowCount}</span>
                            <span className="text-slate-500">p95: {row.p95} ms</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className="p-2 rounded-md hover:bg-muted transition-colors"
              data-testid="theme-toggle-topbar"
            >
              {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
            </button>

            {/* Language Selector */}
            <div className="relative">
              <button
                onClick={() => setLangDropdownOpen(!langDropdownOpen)}
                className="flex items-center gap-1 px-2 py-2 rounded-md hover:bg-muted transition-colors"
                data-testid="language-selector"
              >
                <Globe size={18} />
                <span className="uppercase text-xs font-medium">{language}</span>
              </button>
              {langDropdownOpen && (
                <div className="absolute top-full right-0 mt-1 w-32 rounded-md border bg-popover shadow-lg">
                  {['tr', 'de', 'fr'].map((lang) => (
                    <button
                      key={lang}
                      onClick={() => { setLanguage(lang); setLangDropdownOpen(false); }}
                      className={`w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-muted ${
                        language === lang ? 'bg-muted' : ''
                      }`}
                      data-testid={`language-option-${lang}`}
                    >
                      <span className="uppercase font-medium">{lang}</span>
                      <span className="text-muted-foreground">
                        {lang === 'tr' ? 'Türkçe' : lang === 'de' ? 'Deutsch' : 'Français'}
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* User Menu */}
            <div className="relative">
              <button
                onClick={() => setUserDropdownOpen(!userDropdownOpen)}
                className="flex items-center gap-2 px-2 py-1 rounded-md hover:bg-muted transition-colors"
                data-testid="user-menu"
              >
                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-semibold text-sm">
                  {user?.full_name?.charAt(0)?.toUpperCase() || 'U'}
                </div>
                <ChevronDown size={16} className="text-muted-foreground hidden sm:block" />
              </button>
              {userDropdownOpen && (
                <div className="absolute top-full right-0 mt-1 w-48 rounded-md border bg-popover shadow-lg">
                  <div className="p-3 border-b">
                    <p className="font-medium truncate">{user?.full_name}</p>
                    <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
                  </div>
                  <div className="p-1">
                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center gap-2 px-3 py-2 text-sm text-destructive hover:bg-muted rounded"
                      data-testid="user-menu-logout-button"
                    >
                      <LogOut size={14} />
                      {t('logout')}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="p-4 lg:p-8">
          <div className="mb-4">
            <AdminBreadcrumbs />
          </div>
          {children}
        </main>
      </div>
    </div>
  );
}
