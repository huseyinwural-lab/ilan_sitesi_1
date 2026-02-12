import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { useCountry } from '../contexts/CountryContext';
import { useTheme } from '../contexts/ThemeContext';
import { 
  LayoutDashboard, Users, Globe, Flag, Clock, Settings,
  LogOut, Menu, X, Sun, Moon, ChevronDown, FolderTree, Settings2, MenuSquare
} from 'lucide-react';
import { useState } from 'react';

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const { t, language, setLanguage } = useLanguage();
  const { selectedCountry, setSelectedCountry, getFlag, countryFlags } = useCountry();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [countryDropdownOpen, setCountryDropdownOpen] = useState(false);
  const [langDropdownOpen, setLangDropdownOpen] = useState(false);
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { path: '/', icon: LayoutDashboard, label: 'dashboard' },
    { path: '/users', icon: Users, label: 'users', roles: ['super_admin', 'country_admin'] },
    { path: '/countries', icon: Globe, label: 'countries' },
    { path: '/feature-flags', icon: Flag, label: 'feature_flags' },
    { path: '/audit-logs', icon: Clock, label: 'audit_logs', roles: ['super_admin', 'country_admin', 'finance'] },
  ];

  const filteredNavItems = navItems.filter(item => 
    !item.roles || item.roles.includes(user?.role)
  );

  return (
    <div className="min-h-screen bg-background">
      {/* Sidebar - Desktop */}
      <aside className="fixed left-0 top-0 z-40 hidden lg:flex h-screen w-64 flex-col border-r bg-card">
        {/* Logo */}
        <div className="flex h-16 items-center gap-2 border-b px-6">
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
            <span className="text-primary-foreground font-bold">A</span>
          </div>
          <span className="font-semibold text-lg tracking-tight">Admin Panel</span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto p-4">
          <ul className="space-y-1">
            {filteredNavItems.map((item) => (
              <li key={item.path}>
                <NavLink
                  to={item.path}
                  className={({ isActive }) =>
                    `sidebar-item ${isActive ? 'active' : ''}`
                  }
                  data-testid={`nav-${item.label}`}
                >
                  <item.icon size={18} />
                  {t(item.label)}
                </NavLink>
              </li>
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
              <button onClick={() => setSidebarOpen(false)} className="p-1 rounded hover:bg-muted">
                <X size={20} />
              </button>
            </div>
            <nav className="p-4">
              <ul className="space-y-1">
                {filteredNavItems.map((item) => (
                  <li key={item.path}>
                    <NavLink
                      to={item.path}
                      onClick={() => setSidebarOpen(false)}
                      className={({ isActive }) =>
                        `sidebar-item ${isActive ? 'active' : ''}`
                      }
                    >
                      <item.icon size={18} />
                      {t(item.label)}
                    </NavLink>
                  </li>
                ))}
              </ul>
            </nav>
          </aside>
        </div>
      )}

      {/* Main Content */}
      <div className="lg:pl-64">
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

            {/* Country Selector */}
            <div className="relative">
              <button
                onClick={() => setCountryDropdownOpen(!countryDropdownOpen)}
                className="flex items-center gap-2 px-3 py-2 rounded-md border hover:bg-muted transition-colors"
                data-testid="country-selector"
              >
                <span className="text-xl">{getFlag(selectedCountry)}</span>
                <span className="font-medium">{selectedCountry}</span>
                <ChevronDown size={16} className="text-muted-foreground" />
              </button>
              {countryDropdownOpen && (
                <div className="absolute top-full left-0 mt-1 w-40 rounded-md border bg-popover shadow-lg">
                  {Object.entries(countryFlags).map(([code, flag]) => (
                    <button
                      key={code}
                      onClick={() => { setSelectedCountry(code); setCountryDropdownOpen(false); }}
                      className={`w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-muted ${
                        selectedCountry === code ? 'bg-muted' : ''
                      }`}
                    >
                      <span>{flag}</span>
                      <span>{code}</span>
                    </button>
                  ))}
                </div>
              )}
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
          {children}
        </main>
      </div>
    </div>
  );
}
