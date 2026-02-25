import React, { useEffect, useMemo, useState } from 'react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { LogOut } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const languageOptions = [
  { key: 'tr', label: 'TR' },
  { key: 'de', label: 'DE' },
  { key: 'fr', label: 'FR' },
];

const topNavItems = [
  {
    key: 'listings',
    path: '/account',
    labelKey: 'nav_listings',
    match: ['/account', '/account/listings'],
    testId: 'account-top-nav-listings',
  },
  {
    key: 'messages',
    path: '/account/messages',
    labelKey: 'nav_messages',
    match: ['/account/messages'],
    testId: 'account-top-nav-messages',
  },
  {
    key: 'favorites',
    path: '/account/favorites',
    labelKey: 'nav_favorites',
    match: ['/account/favorites'],
    testId: 'account-top-nav-favorites',
  },
  {
    key: 'services',
    path: '/account/support',
    labelKey: 'nav_services',
    match: ['/account/support'],
    testId: 'account-top-nav-services',
  },
  {
    key: 'account',
    path: '/account/security',
    labelKey: 'nav_account',
    match: ['/account/security', '/account/privacy'],
    testId: 'account-top-nav-account',
  },
];

const UserPanelLayout = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { t, language, setLanguage } = useLanguage();
  const [counts, setCounts] = useState({ favorites: 0, messages: 0 });

  const sideMenuGroups = useMemo(
    () => [
      {
        key: 'listings',
        title: 'İlan Yönetimi',
        testId: 'account-side-group-listings',
        items: [
          { path: '/account', labelKey: 'nav_dashboard', testId: 'account-side-dashboard' },
          { path: '/account/listings', labelKey: 'nav_my_listings', testId: 'account-side-listings' },
        ],
      },
      {
        key: 'messages',
        title: 'Mesajlar',
        testId: 'account-side-group-messages',
        items: [
          { path: '/account/messages', labelKey: 'nav_messages', testId: 'account-side-messages' },
        ],
      },
      {
        key: 'favorites',
        title: 'Favoriler',
        testId: 'account-side-group-favorites',
        items: [
          { path: '/account/favorites', labelKey: 'nav_favorite_listings', testId: 'account-side-favorites' },
        ],
      },
      {
        key: 'services',
        title: 'Servisler',
        testId: 'account-side-group-services',
        items: [
          { path: '/account/support', labelKey: 'nav_support', testId: 'account-side-support' },
        ],
      },
      {
        key: 'account',
        title: 'Hesap & Güvenlik',
        testId: 'account-side-group-account',
        items: [
          { path: '/account/security', label: 'Güvenlik', testId: 'account-side-security' },
          { path: '/account/privacy', labelKey: 'nav_privacy_center', testId: 'account-side-privacy' },
        ],
      },
    ],
    []
  );

  useEffect(() => {
    let active = true;
    const fetchCounts = async () => {
      try {
        const headers = { Authorization: `Bearer ${localStorage.getItem('access_token')}` };
        const [favRes, msgRes] = await Promise.all([
          fetch(`${API}/v1/favorites/count`, { headers }),
          fetch(`${API}/v1/messages/unread-count`, { headers }),
        ]);
        const favData = favRes.ok ? await favRes.json() : { count: 0 };
        const msgData = msgRes.ok ? await msgRes.json() : { count: 0 };
        if (active) {
          setCounts({ favorites: favData.count || 0, messages: msgData.count || 0 });
        }
      } catch (err) {
        if (active) {
          setCounts({ favorites: 0, messages: 0 });
        }
      }
    };
    fetchCounts();
    return () => {
      active = false;
    };
  }, [location.pathname]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const renderBadge = (value, testId) => {
    if (!value) return null;
    return (
      <span
        className="ml-auto inline-flex min-w-[22px] items-center justify-center rounded-full bg-[var(--brand-navy)] px-2 py-0.5 text-[11px] text-white"
        data-testid={testId}
      >
        {value}
      </span>
    );
  };

  const resolveLabel = (item) => {
    if (item.label) return item.label;
    return t(item.labelKey);
  };

  return (
    <div className="min-h-screen bg-[#F8F9FA] account-theme" data-testid="account-layout">
      <header className="bg-[var(--brand-navy)] text-white" data-testid="account-topbar">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-4">
          <div className="flex items-center gap-4" data-testid="account-topbar-left">
            <div
              className="flex h-10 w-28 items-center justify-center rounded bg-[#F57C00] text-sm font-bold text-white"
              data-testid="account-logo"
            >
              ANNONCIA
            </div>
            <div className="text-xs uppercase tracking-[0.2em] text-white/70" data-testid="account-portal-label">
              {t('portal_consumer')}
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-3" data-testid="account-topbar-right">
            <div className="flex items-center gap-1 rounded-full bg-[var(--bg-surface-soft)] px-2 py-1" data-testid="account-language-toggle">
              {languageOptions.map((option) => (
                <button
                  key={option.key}
                  type="button"
                  onClick={() => setLanguage(option.key)}
                  className={`rounded-full px-2 py-1 text-xs font-semibold transition ${
                    language === option.key ? 'bg-white text-[var(--text-primary)]' : 'text-white/70 hover:text-white'
                  }`}
                  data-testid={`account-language-${option.key}`}
                >
                  {option.label}
                </button>
              ))}
            </div>
            <div className="text-sm" data-testid="account-user-name">
              {user?.full_name || user?.email}
            </div>
            <button
              type="button"
              onClick={handleLogout}
              className="inline-flex items-center gap-2 rounded-full border border-white/40 px-3 py-1 text-xs uppercase tracking-wide"
              data-testid="account-logout"
            >
              <LogOut size={14} /> {t('logout')}
            </button>
          </div>
        </div>
      </header>

      <nav className="border-b bg-white" data-testid="account-top-nav">
        <div className="mx-auto max-w-6xl px-6">
          <div className="flex gap-6 overflow-x-auto py-3 text-sm font-semibold">
            {topNavItems.map((item) => (
              <NavLink
                key={item.key}
                to={item.path}
                className={({ isActive }) =>
                  `border-b-2 pb-2 transition ${
                    isActive
                      ? 'border-[var(--color-primary)] text-[var(--text-primary)]'
                      : 'border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
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

      <main className="mx-auto max-w-6xl px-6 py-8" data-testid="account-main">
        <div className="grid gap-6 lg:grid-cols-[260px_1fr]">
          <aside className="rounded-2xl bg-white p-4 shadow-sm" data-testid="account-side-nav">
            <div className="text-xs uppercase tracking-[0.2em] text-[var(--text-secondary)]" data-testid="account-side-title">
              {t('nav_section')}
            </div>
            <div className="mt-4 space-y-4" data-testid="account-side-items">
              {sideMenuGroups.map((group) => (
                <div key={group.key} data-testid={group.testId}>
                  <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-400">
                    {group.title}
                  </div>
                  <div className="mt-2 space-y-1">
                    {group.items.map((item) => (
                      <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) =>
                          `flex items-center gap-2 rounded-xl px-3 py-2 text-sm transition ${
                            isActive
                              ? 'bg-[var(--color-primary-soft)] text-[var(--text-primary)]'
                              : 'text-[var(--text-secondary)] hover:bg-slate-100'
                          }`
                        }
                        data-testid={item.testId}
                      >
                        <span>{resolveLabel(item)}</span>
                        {item.path === '/account/favorites' &&
                          renderBadge(counts.favorites, 'account-side-favorites-badge')}
                        {item.path === '/account/messages' &&
                          renderBadge(counts.messages, 'account-side-messages-badge')}
                      </NavLink>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </aside>
          <section className="rounded-2xl bg-white p-6 shadow-sm" data-testid="account-content">
            <Outlet />
          </section>
        </div>
      </main>
    </div>
  );
};

export default UserPanelLayout;
