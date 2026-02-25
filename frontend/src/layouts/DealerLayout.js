import React, { useMemo } from 'react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { LogOut } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';

const languageOptions = [
  { key: 'tr', label: 'TR' },
  { key: 'de', label: 'DE' },
  { key: 'fr', label: 'FR' },
];

const topNavItems = [
  {
    key: 'dashboard',
    path: '/dealer',
    labelKey: 'nav_dealer_dashboard',
    match: ['/dealer'],
    testId: 'dealer-top-nav-dashboard',
  },
  {
    key: 'listings',
    path: '/dealer/listings',
    labelKey: 'nav_listings',
    match: ['/dealer/listings'],
    testId: 'dealer-top-nav-listings',
  },
  {
    key: 'billing',
    path: '/dealer/invoices',
    labelKey: 'nav_invoices',
    match: ['/dealer/invoices'],
    testId: 'dealer-top-nav-invoices',
  },
  {
    key: 'company',
    path: '/dealer/company',
    labelKey: 'nav_company',
    match: ['/dealer/company'],
    testId: 'dealer-top-nav-company',
  },
  {
    key: 'privacy',
    path: '/dealer/privacy',
    labelKey: 'nav_privacy_center',
    match: ['/dealer/privacy'],
    testId: 'dealer-top-nav-privacy',
  },
];

export default function DealerLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { t, language, setLanguage } = useLanguage();

  const activeTopKey = useMemo(() => {
    const routeMap = [
      { key: 'listings', prefixes: ['/dealer/listings'] },
      { key: 'billing', prefixes: ['/dealer/invoices'] },
      { key: 'company', prefixes: ['/dealer/company'] },
      { key: 'privacy', prefixes: ['/dealer/privacy'] },
      { key: 'dashboard', prefixes: ['/dealer'] },
    ];
    const matched = routeMap.find((item) =>
      item.prefixes.some((prefix) => location.pathname === prefix || location.pathname.startsWith(`${prefix}/`))
    );
    return matched?.key || 'dashboard';
  }, [location.pathname]);

  const sideMenuGroups = useMemo(
    () => ({
      dashboard: [
        { path: '/dealer', labelKey: 'nav_dashboard', testId: 'dealer-side-overview' },
      ],
      listings: [
        { path: '/dealer/listings', labelKey: 'nav_my_listings', testId: 'dealer-side-listings' },
      ],
      billing: [
        { path: '/dealer/invoices', labelKey: 'nav_invoices', testId: 'dealer-side-invoices' },
      ],
      company: [
        { path: '/dealer/company', labelKey: 'nav_company_profile', testId: 'dealer-side-company-profile' },
      ],
      privacy: [
        { path: '/dealer/privacy', labelKey: 'nav_privacy_center', testId: 'dealer-side-privacy' },
      ],
    }),
    []
  );

  const handleLogout = () => {
    logout();
    navigate('/dealer/login');
  };

  return (
    <div className="min-h-screen bg-[var(--bg-warm)]" data-testid="dealer-layout">
      <header className="bg-[var(--brand-navy)] text-white" data-testid="dealer-topbar">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-4">
          <div className="flex items-center gap-4" data-testid="dealer-topbar-left">
            <div
              className="flex h-10 w-28 items-center justify-center rounded bg-yellow-400 text-sm font-bold text-slate-900"
              data-testid="dealer-logo"
            >
              ANNONCIA
            </div>
            <div className="text-xs uppercase tracking-[0.2em] text-white/70" data-testid="dealer-portal-label">
              {t('portal_dealer')}
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-3" data-testid="dealer-topbar-right">
            <div className="flex items-center gap-1 rounded-full bg-white/10 px-2 py-1" data-testid="dealer-language-toggle">
              {languageOptions.map((option) => (
                <button
                  key={option.key}
                  type="button"
                  onClick={() => setLanguage(option.key)}
                  className={`rounded-full px-2 py-1 text-xs font-semibold transition ${
                    language === option.key ? 'bg-white text-[var(--brand-navy)]' : 'text-white/70 hover:text-white'
                  }`}
                  data-testid={`dealer-language-${option.key}`}
                >
                  {option.label}
                </button>
              ))}
            </div>
            <div className="text-sm" data-testid="dealer-user-name">
              {user?.full_name || user?.email}
            </div>
            <button
              type="button"
              onClick={handleLogout}
              className="inline-flex items-center gap-2 rounded-full border border-white/40 px-3 py-1 text-xs uppercase tracking-wide"
              data-testid="dealer-logout"
            >
              <LogOut size={14} /> {t('logout')}
            </button>
          </div>
        </div>
      </header>

      <nav className="border-b bg-white/95" data-testid="dealer-top-nav">
        <div className="mx-auto max-w-6xl px-6">
          <div className="flex gap-6 overflow-x-auto py-3 text-sm font-semibold">
            {topNavItems.map((item) => (
              <NavLink
                key={item.key}
                to={item.path}
                className={({ isActive }) =>
                  `border-b-2 pb-2 transition ${
                    isActive
                      ? 'border-[#2f3854] text-[var(--brand-navy)]'
                      : 'border-transparent text-slate-500 hover:text-[var(--brand-navy)]'
                  }`
                }
                data-testid={item.testId}
              >
                {t(item.labelKey)}
              </NavLink>
            ))}
          </div>
        </div>
      </nav>

      <main className="mx-auto max-w-6xl px-6 py-8" data-testid="dealer-main">
        <div className="grid gap-6 lg:grid-cols-[240px_1fr]">
          <aside className="rounded-2xl bg-white p-4 shadow-sm" data-testid="dealer-side-nav">
            <div className="text-xs uppercase tracking-[0.2em] text-slate-400" data-testid="dealer-side-title">
              {t('nav_section')}
            </div>
            <div className="mt-4 space-y-1" data-testid="dealer-side-items">
              {sideMenuGroups[activeTopKey]?.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    `flex items-center gap-2 rounded-xl px-3 py-2 text-sm transition ${
                      isActive
                        ? 'bg-[var(--bg-warm)]/30 text-[var(--brand-navy)]'
                        : 'text-slate-500 hover:bg-slate-100'
                    }`
                  }
                  data-testid={item.testId}
                >
                  <span>{t(item.labelKey)}</span>
                </NavLink>
              ))}
            </div>
          </aside>
          <section className="rounded-2xl bg-white p-6 shadow-sm" data-testid="dealer-content">
            <Outlet />
          </section>
        </div>
      </main>
    </div>
  );
}
