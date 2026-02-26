import React, { useEffect, useMemo, useState } from 'react';
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

const moduleRouteMap = {
  active_listings: '/dealer/listings',
  today_messages: '/dealer/messages',
  views_7d: '/dealer/reports',
  lead_contact_click: '/dealer/customers',
  package_quota: '/dealer/purchase',
};

const moduleLabelMap = {
  'dealer.widget.active_listings': 'Aktif İlanlar',
  'dealer.widget.today_messages': 'Bugün Mesajlar',
  'dealer.widget.views_7d': '7 Gün Görüntülenme',
  'dealer.widget.lead_contact_click': 'Lead Tıklamaları',
  'dealer.widget.package_quota': 'Paket / Kota',
};

const resolveLabel = (key, t) => labelMap[key] || t(key) || key;
const resolveModuleLabel = (key, fallback, t) => moduleLabelMap[key] || t(key) || fallback || key;

export default function DealerLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { t, language, setLanguage } = useLanguage();
  const {
    loading,
    error,
    headerItems,
    headerRow1Items,
    headerRow1FixedBlocks,
    headerRow2Modules,
    headerRow3Controls,
    sidebarItems,
    modules,
  } = useDealerPortalConfig();
  const [selectedStore, setSelectedStore] = useState('all');
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  const activePath = useMemo(() => location.pathname, [location.pathname]);
  const row1Actions = useMemo(
    () => (headerRow1Items?.length ? headerRow1Items : headerItems),
    [headerRow1Items, headerItems],
  );
  const row2Modules = useMemo(
    () => (headerRow2Modules?.length ? headerRow2Modules : modules),
    [headerRow2Modules, modules],
  );
  const row3Stores = useMemo(() => {
    const stores = headerRow3Controls?.stores;
    return Array.isArray(stores) && stores.length ? stores : [{ key: 'all', label: 'Tüm Mağazalar' }];
  }, [headerRow3Controls]);

  useEffect(() => {
    setSelectedStore(headerRow3Controls?.default_store_key || 'all');
  }, [headerRow3Controls?.default_store_key]);

  const handleLogout = () => {
    logout();
    navigate('/dealer/login');
  };

  const handleStoreChange = (nextStoreKey) => {
    setSelectedStore(nextStoreKey);
    trackDealerEvent('dealer_header_store_filter_change', { store_key: nextStoreKey });
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
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-3 lg:px-6" data-testid="dealer-layout-header-rows">
          <div className="flex flex-wrap items-center justify-between gap-3" data-testid="dealer-layout-header-row1">
            <div className="flex items-center gap-3" data-testid="dealer-layout-brand-wrap">
              <button
                type="button"
                onClick={() => navigate('/dealer/overview')}
                className="flex h-10 w-28 items-center justify-center rounded bg-yellow-400 text-sm font-bold text-slate-900"
                data-testid="dealer-layout-brand-button"
              >
                ANNONCIA
              </button>
              <button
                type="button"
                onClick={() => navigate('/dealer/overview')}
                className="rounded-full border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700"
                data-testid="dealer-layout-main-menu-button"
              >
                Ana Menü
              </button>
              <span className="text-xs uppercase tracking-[0.2em] text-slate-500" data-testid="dealer-layout-portal-label">
                Kurumsal Portal
              </span>
            </div>

            <div className="flex flex-wrap items-center gap-2" data-testid="dealer-layout-quick-actions">
              {row1Actions.map((item) => {
                const Icon = iconMap[item.icon] || LayoutDashboard;
                return (
                  <NavLink
                    key={item.id}
                    to={item.route}
                    onClick={() => handleNavClick(item, 'header_row1')}
                    className={({ isActive }) =>
                      `inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-semibold transition ${
                        isActive ? 'border-[var(--brand-navy)] text-[var(--brand-navy)]' : 'border-slate-200 text-slate-600 hover:border-slate-300'
                      }`
                    }
                    data-testid={`dealer-header-row1-action-${item.key}`}
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
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2 border-t border-slate-100 pt-2" data-testid="dealer-layout-header-row2">
            {(headerRow1FixedBlocks || []).map((block) => (
              <span
                key={block.key}
                className="rounded-full bg-slate-100 px-2 py-1 text-[11px] font-semibold text-slate-600"
                data-testid={`dealer-layout-header-row1-fixed-${block.key}`}
              >
                {block.label}
              </span>
            ))}
            {row2Modules.map((module) => {
              const route = moduleRouteMap[module.data_source_key] || '/dealer/overview';
              const isActive = activePath === route || activePath.startsWith(`${route}/`);
              return (
                <button
                  type="button"
                  key={module.id}
                  onClick={() => {
                    trackDealerEvent('dealer_header_module_click', {
                      key: module.key,
                      route,
                      location: 'header_row2',
                    });
                    navigate(route);
                  }}
                  className={`rounded-full border px-3 py-1.5 text-xs font-semibold transition ${
                    isActive ? 'border-[var(--brand-navy)] text-[var(--brand-navy)] bg-[var(--bg-warm-soft)]' : 'border-slate-200 text-slate-600 hover:border-slate-300'
                  }`}
                  data-testid={`dealer-header-row2-module-${module.key}`}
                >
                  {resolveModuleLabel(module.title_i18n_key, module.key, t)}
                </button>
              );
            })}
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-2" data-testid="dealer-layout-header-row3">
            <div className="flex items-center gap-2" data-testid="dealer-layout-row3-store-wrap">
              <label className="text-xs font-semibold text-slate-600" data-testid="dealer-layout-row3-store-label">
                Mağaza
              </label>
              <select
                value={selectedStore}
                onChange={(event) => handleStoreChange(event.target.value)}
                className="h-9 rounded-md border border-slate-200 bg-white px-3 text-sm"
                data-testid="dealer-layout-row3-store-filter"
                disabled={!headerRow3Controls?.store_filter_enabled}
              >
                {row3Stores.map((store) => (
                  <option key={store.key} value={store.key} data-testid={`dealer-layout-row3-store-option-${store.key}`}>
                    {store.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="relative" data-testid="dealer-layout-row3-user-menu-wrap">
              <button
                type="button"
                onClick={() => setUserMenuOpen((prev) => !prev)}
                className="inline-flex items-center gap-2 rounded-full border border-slate-300 px-3 py-1.5 text-xs"
                data-testid="dealer-layout-row3-user-menu-button"
                disabled={!headerRow3Controls?.user_dropdown_enabled}
              >
                <UserRound size={14} />
                <span data-testid="dealer-layout-user-label">{user?.full_name || user?.email}</span>
              </button>

              {userMenuOpen && (
                <div className="absolute right-0 top-11 z-20 min-w-[180px] rounded-xl border bg-white p-2 shadow-lg" data-testid="dealer-layout-row3-user-menu-dropdown">
                  <button
                    type="button"
                    onClick={() => {
                      setUserMenuOpen(false);
                      navigate('/dealer/settings');
                    }}
                    className="w-full rounded-lg px-3 py-2 text-left text-sm text-slate-700 hover:bg-slate-100"
                    data-testid="dealer-layout-row3-user-menu-profile"
                  >
                    Profil / Ayarlar
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setUserMenuOpen(false);
                      handleLogout();
                    }}
                    className="mt-1 inline-flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-rose-600 hover:bg-rose-50"
                    data-testid="dealer-layout-row3-user-menu-logout"
                  >
                    <LogOut size={14} />
                    {t('logout')}
                  </button>
                </div>
              )}
            </div>
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
