import { NavLink, useNavigate, useLocation, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { useCountry } from '../contexts/CountryContext';
import { useTheme } from '../contexts/ThemeContext';
import { 
  LayoutDashboard, Users, Globe, Flag, Clock, Settings,
  LogOut, Menu, X, Sun, Moon, ChevronDown, FolderTree, Settings2, MenuSquare,
  Building, Star, ShieldCheck, FileText, Percent, Database, Car, TrendingUp, Activity
} from 'lucide-react';
import AdminBreadcrumbs from '@/components/admin/AdminBreadcrumbs';
import { Switch } from '@/components/ui/switch';

import { useState, useEffect, useRef } from 'react';


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

  const navItems = [
    // Dashboard
    { path: '/admin', icon: LayoutDashboard, label: 'dashboard' },

    // Genel Bakış
    { divider: true, label: 'Genel Bakış' },
    { path: '/admin/dashboard', icon: TrendingUp, label: 'Genel Bakış', roles: ['super_admin', 'country_admin', 'support'] },
    { path: '/admin/country-compare', icon: Activity, label: 'Ülke Karşılaştırma', roles: ['super_admin', 'country_admin', 'support'] },

    // Kullanıcı & Satıcı
    { divider: true, label: 'Kullanıcı & Satıcı' },
    { path: '/admin/users', icon: Users, label: 'users', roles: ['super_admin', 'country_admin'] },
    { path: '/admin/dealers', icon: Building, label: 'Bayiler', roles: ['super_admin', 'country_admin'] },
    { path: '/admin/dealer-applications', icon: Clock, label: 'Başvurular', roles: ['super_admin', 'country_admin'] },
    { path: '/admin/onboarding', icon: FileText, label: 'Başvurular', comingSoon: true, roles: ['super_admin', 'country_admin'] },

    // İlan & Moderasyon
    { divider: true, label: 'İlan & Moderasyon' },
    { path: '/admin/moderation', icon: ShieldCheck, label: 'Moderation Queue', roles: ['super_admin', 'country_admin', 'moderator'] },
    { path: '/admin/listings', icon: FolderTree, label: 'İlanlar', roles: ['super_admin', 'country_admin', 'moderator'] },
    { path: '/admin/reports', icon: Flag, label: 'Şikayetler', roles: ['super_admin', 'country_admin', 'moderator'] },

    // Katalog & Yapılandırma
    { divider: true, label: 'Katalog & Yapılandırma' },
    { path: '/admin/categories', icon: FolderTree, label: 'Kategoriler', roles: ['super_admin', 'country_admin'] },
    { path: '/admin/attributes', icon: Settings2, label: 'Özellikler', roles: ['super_admin'] },
    { path: '/admin/menu', icon: MenuSquare, label: 'Menü Yönetimi', roles: ['super_admin'] },
    { path: '/admin/feature-flags', icon: Flag, label: 'Özellik Bayrakları', roles: ['super_admin', 'country_admin'] },

    // Araç Verisi
    { divider: true, label: 'Araç Verisi', roles: ['super_admin', 'country_admin'] },
    { path: '/admin/vehicle-makes', icon: Car, label: 'Araç Markaları', roles: ['super_admin', 'country_admin'] },
    { path: '/admin/vehicle-models', icon: Car, label: 'Araç Modelleri', roles: ['super_admin', 'country_admin'] },

    // Finans
    { divider: true, label: 'Finans' },
    { path: '/admin/plans', icon: Star, label: 'Plans', roles: ['super_admin', 'country_admin', 'finance'] },
    { divider: true },

    { path: '/admin/invoices', icon: FileText, label: 'Invoices', roles: ['super_admin', 'country_admin', 'finance'] },
    { path: '/admin/billing', icon: FileText, label: 'Billing', roles: ['super_admin', 'country_admin', 'finance'] },
    { path: '/admin/tax-rates', icon: Percent, label: 'Tax Rates', roles: ['super_admin', 'country_admin', 'finance'] },

    // Sistem
    { divider: true, label: 'Sistem' },
    { path: '/admin/countries', icon: Globe, label: 'Ülkeler', roles: ['super_admin', 'country_admin'] },
    { path: '/admin/audit-logs', icon: Clock, label: 'Denetim Kayıtları', roles: ['super_admin', 'country_admin', 'finance'] },
    { path: '/admin/system-settings', icon: Settings, label: 'Sistem Ayarları', roles: ['super_admin', 'country_admin'] },
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
      '/admin/dashboard',
      '/admin/country-compare',
      '/admin/countries',
      '/admin/feature-flags',
      '/admin/categories',
      '/admin/attributes',
      '/admin/master-data/attributes',
      '/admin/master-data/vehicles',
      '/admin/audit-logs',
      '/admin/plans',
      '/admin/billing',
      '/admin/moderation',
      '/admin/listings',
      '/admin/reports',
      '/admin/invoices',
      '/admin/tax-rates',
      '/admin/plans',
      '/admin/dealers',
      '/admin/dealer-applications',
      '/admin/system-settings',

    ]);
    return !known.has(path);
  };

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
                      data-testid={`nav-${item.label}`}
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
                      data-testid={`nav-${item.label}`}
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
                          data-testid={`nav-mobile-${item.label}`}
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
                          data-testid={`nav-mobile-${item.label}`}
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
