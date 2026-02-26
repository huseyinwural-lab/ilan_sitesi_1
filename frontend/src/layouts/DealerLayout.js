import React, { useMemo } from 'react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  BarChart3,
  Heart,
  LayoutDashboard,
  ListChecks,
  LogOut,
  MessageCircle,
  PlusSquare,
  Settings,
  ShoppingCart,
  UserRound,
  Users,
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { useDealerPortalConfig } from '@/hooks/useDealerPortalConfig';
import { trackDealerEvent } from '@/lib/dealerAnalytics';

const languageOptions = [
  { key: 'tr', label: 'TR' },
  { key: 'de', label: 'DE' },
  { key: 'fr', label: 'FR' },
];

const iconMap = {
  LayoutDashboard,
  ListChecks,
  MessageCircle,
  Users,
  BarChart3,
  ShoppingCart,
  Settings,
  Heart,
  PlusSquare,
  UserRound,
};

const labelMap = {
  'dealer.nav.overview': 'Genel Bakış',
  'dealer.nav.listings': 'İlanlar',
  'dealer.nav.messages': 'Mesajlar',
  'dealer.nav.customers': 'Müşteriler',
  'dealer.nav.reports': 'Raporlar',
  'dealer.nav.purchase': 'Satın Al',
  'dealer.nav.settings': 'Ayarlar',
  'dealer.quick.favorites': 'Favoriler',
  'dealer.quick.messages': 'Mesajlar',
  'dealer.quick.create_listing': 'İlan Ver',
  'dealer.quick.profile': 'Profil',
};

const resolveLabel = (key, t) => labelMap[key] || t(key) || key;

export default function DealerLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { t, language, setLanguage } = useLanguage();
  const { loading, error, headerItems, sidebarItems } = useDealerPortalConfig();

  const activePath = useMemo(() => location.pathname, [location.pathname]);

  const handleLogout = () => {
    logout();
    navigate('/dealer/login');
  };

  const handleNavClick = (item, locationType) => {
    trackDealerEvent('dealer_nav_click', {
      key: item.key,
      route: item.route,
      location: locationType,
    });
    if (item.key === 'quick_create_listing') {
      trackDealerEvent('dealer_listing_create_start', { route: item.route });
    }
  };

  return (
    <div className="min-h-screen bg-[var(--bg-warm)]" data-testid="dealer-layout-root">
      <header className="border-b bg-white" data-testid="dealer-layout-header">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-3 lg:px-6">
          <div className="flex items-center gap-3" data-testid="dealer-layout-brand-wrap">
            <button
              type="button"
              onClick={() => navigate('/dealer/overview')}
              className="flex h-10 w-28 items-center justify-center rounded bg-yellow-400 text-sm font-bold text-slate-900"
              data-testid="dealer-layout-brand-button"
            >
              ANNONCIA
            </button>
            <span className="text-xs uppercase tracking-[0.2em] text-slate-500" data-testid="dealer-layout-portal-label">
              Kurumsal Portal
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-2" data-testid="dealer-layout-quick-actions">
            {headerItems.map((item) => {
              const Icon = iconMap[item.icon] || LayoutDashboard;
              return (
                <NavLink
                  key={item.id}
                  to={item.route}
                  onClick={() => handleNavClick(item, 'header')}
                  className={({ isActive }) =>
                    `inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-semibold transition ${
                      isActive ? 'border-[var(--brand-navy)] text-[var(--brand-navy)]' : 'border-slate-200 text-slate-600 hover:border-slate-300'
                    }`
                  }
                  data-testid={`dealer-header-action-${item.key}`}
                >
                  <Icon size={14} />
                  <span>{resolveLabel(item.label_i18n_key, t)}</span>
                </NavLink>
              );
            })}

            <div className="flex items-center gap-1 rounded-full bg-slate-100 px-2 py-1" data-testid="dealer-layout-language-toggle">
              {languageOptions.map((option) => (
                <button
                  key={option.key}
                  type="button"
                  onClick={() => setLanguage(option.key)}
                  className={`rounded-full px-2 py-1 text-xs font-semibold ${language === option.key ? 'bg-white text-slate-900' : 'text-slate-500'}`}
                  data-testid={`dealer-layout-language-${option.key}`}
                >
                  {option.label}
                </button>
              ))}
            </div>

            <span className="text-xs text-slate-600" data-testid="dealer-layout-user-label">
              {user?.full_name || user?.email}
            </span>
            <button
              type="button"
              onClick={handleLogout}
              className="inline-flex items-center gap-1 rounded-full border border-slate-300 px-3 py-1.5 text-xs"
              data-testid="dealer-layout-logout-button"
            >
              <LogOut size={14} />
              {t('logout')}
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto grid max-w-7xl gap-6 px-4 py-6 lg:grid-cols-[260px_1fr] lg:px-6" data-testid="dealer-layout-main-grid">
        <aside className="rounded-2xl bg-white p-4 shadow-sm" data-testid="dealer-layout-sidebar">
          <div className="text-xs uppercase tracking-[0.2em] text-slate-400" data-testid="dealer-layout-sidebar-title">
            Navigasyon
          </div>

          {loading ? (
            <div className="mt-4 text-xs text-slate-500" data-testid="dealer-layout-sidebar-loading">Yükleniyor…</div>
          ) : (
            <div className="mt-4 space-y-1" data-testid="dealer-layout-sidebar-items">
              {sidebarItems.map((item) => {
                const Icon = iconMap[item.icon] || LayoutDashboard;
                const isActive = activePath === item.route || activePath.startsWith(`${item.route}/`);
                return (
                  <NavLink
                    key={item.id}
                    to={item.route}
                    onClick={() => handleNavClick(item, 'sidebar')}
                    className={`flex items-center gap-2 rounded-xl px-3 py-2 text-sm transition ${
                      isActive ? 'bg-[var(--bg-warm-soft)] text-[var(--brand-navy)]' : 'text-slate-600 hover:bg-slate-100'
                    }`}
                    data-testid={`dealer-sidebar-item-${item.key}`}
                  >
                    <Icon size={16} />
                    <span>{resolveLabel(item.label_i18n_key, t)}</span>
                  </NavLink>
                );
              })}
            </div>
          )}

          {error && (
            <div className="mt-3 text-xs text-rose-600" data-testid="dealer-layout-sidebar-error">
              {error}
            </div>
          )}
        </aside>

        <section className="rounded-2xl bg-white p-6 shadow-sm" data-testid="dealer-layout-content">
          <Outlet />
        </section>
      </main>
    </div>
  );
}
