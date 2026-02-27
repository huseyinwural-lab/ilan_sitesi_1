import React, { useEffect, useMemo, useState } from 'react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  Ban,
  BarChart3,
  Bell,
  Building2,
  ChevronDown,
  ChevronRight,
  FileText,
  Heart,
  LayoutDashboard,
  ListChecks,
  LogOut,
  MessageCircle,
  Shield,
  PlusSquare,
  Settings,
  ShoppingCart,
  UserRound,
  UserSquare2,
  Users,
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { useDealerPortalConfig } from '@/hooks/useDealerPortalConfig';
import { useUIHeaderConfig } from '@/hooks/useUIHeaderConfig';
import { trackDealerEvent } from '@/lib/dealerAnalytics';

const languageOptions = [
  { key: 'tr', label: 'TR' },
  { key: 'de', label: 'DE' },
  { key: 'fr', label: 'FR' },
];

const iconMap = {
  Ban,
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
  Bell,
  FileText,
  Building2,
  UserSquare2,
  Shield,
};

const corporateMenuStructure = [
  {
    key: 'ofisim',
    label: 'Ofisim',
    icon: 'LayoutDashboard',
    route: '/dealer/overview',
    children: [
      { key: 'overview', label: 'Özet', icon: 'LayoutDashboard', route: '/dealer/overview' },
      { key: 'listings', label: 'İlanlar', icon: 'ListChecks', route: '/dealer/listings' },
      { key: 'messages', label: 'Mesajlar', icon: 'MessageCircle', route: '/dealer/messages' },
      {
        key: 'customers',
        label: 'Müşteri Yönetimi',
        icon: 'Users',
        route: '/dealer/customers',
        children: [
          { key: 'contracts', label: 'Sözleşmeler', icon: 'FileText', route: '/dealer/customers' },
        ],
      },
      {
        key: 'favorites',
        label: 'Favoriler',
        icon: 'Heart',
        route: '/dealer/favorites',
        children: [
          { key: 'favorite_listings', label: 'Favori İlanlar', icon: 'Heart', route: '/dealer/favorites?tab=listings' },
          { key: 'favorite_searches', label: 'Favori Aramalar', icon: 'Heart', route: '/dealer/favorites?tab=searches' },
          { key: 'favorite_sellers', label: 'Favori Satıcılar', icon: 'Heart', route: '/dealer/favorites?tab=sellers' },
        ],
      },
      {
        key: 'reports',
        label: 'Raporlar',
        icon: 'BarChart3',
        route: '/dealer/reports',
        children: [
          { key: 'hourly_visit_report', label: 'Saatlik Ziyaret Sayısı', icon: 'BarChart3', route: '/dealer/reports?section=listing_report' },
          {
            key: 'performance_reports',
            label: 'Performans Raporları',
            icon: 'BarChart3',
            route: '/dealer/reports',
            children: [
              { key: 'live_listing_report', label: 'Yayındaki İlan Raporu', icon: 'BarChart3', route: '/dealer/reports?section=listing_report' },
              { key: 'view_report', label: 'Görüntüleme Raporu', icon: 'BarChart3', route: '/dealer/reports?section=views_report' },
              { key: 'favorite_report', label: 'Favoriye Alınma Raporu', icon: 'BarChart3', route: '/dealer/reports?section=favorites_report' },
              { key: 'message_report', label: 'Gelen Mesaj Raporu', icon: 'BarChart3', route: '/dealer/reports?section=messages_report' },
              { key: 'mobile_call_report', label: 'Gelen Arama Raporu (Mobil)', icon: 'BarChart3', route: '/dealer/reports?section=mobile_calls_report' },
            ],
          },
          { key: 'package_reports', label: 'Paket Raporları', icon: 'BarChart3', route: '/dealer/reports?section=package_reports' },
          { key: 'doping_usage_report', label: 'Doping Kullanım Raporu', icon: 'BarChart3', route: '/dealer/reports?section=doping_usage' },
        ],
      },
      {
        key: 'consultant_tracking',
        label: 'Danışman Takibi',
        icon: 'Users',
        route: '/dealer/consultant-tracking',
        children: [
          { key: 'consultant_service_reviews', label: 'Danışman Hizmet Değerlendirmeleri', icon: 'Users', route: '/dealer/consultant-tracking?tab=evaluations' },
        ],
      },
      {
        key: 'purchase',
        label: 'Satın Al',
        icon: 'ShoppingCart',
        route: '/dealer/purchase',
        children: [
          { key: 'bulk_doping_purchase', label: 'Toplu Doping Satın Al', icon: 'ShoppingCart', route: '/dealer/purchase' },
        ],
      },
      {
        key: 'account',
        label: 'Hesabım',
        icon: 'Settings',
        route: '/dealer/settings',
        children: [
          {
            key: 'account_information',
            label: 'Hesap Bilgilerim',
            icon: 'UserRound',
            route: '/dealer/settings?section=profile',
            children: [
              { key: 'personal_info', label: 'Kişisel Bilgilerim', icon: 'UserRound', route: '/dealer/settings?section=profile' },
              { key: 'account_email', label: 'E-Posta', icon: 'UserRound', route: '/dealer/settings?section=profile' },
              { key: 'account_phone', label: 'Cep Telefonu', icon: 'UserRound', route: '/dealer/settings?section=profile' },
              { key: 'password_change', label: 'Şifre Değişikliği', icon: 'Shield', route: '/dealer/settings?section=security' },
              { key: 'account_verification', label: 'Hesap Doğrulama', icon: 'Shield', route: '/dealer/settings?section=security' },
              { key: 'recovery_email', label: 'Kurtarma E-Postası', icon: 'Shield', route: '/dealer/settings?section=security' },
              { key: 'sessions_devices', label: 'Oturumlar ve Cihazlar', icon: 'Shield', route: '/dealer/settings?section=security' },
            ],
          },
          {
            key: 'security',
            label: 'Güvenlik',
            icon: 'Shield',
            route: '/dealer/settings?section=security',
            children: [
              { key: 'two_factor', label: '2 Aşamalı Doğrulama', icon: 'Shield', route: '/dealer/settings?section=security' },
            ],
          },
          {
            key: 'store',
            label: 'Mağazam',
            icon: 'Building2',
            route: '/dealer/settings?section=address',
            children: [
              { key: 'store_content', label: 'Mağaza İçeriği', icon: 'Building2', route: '/dealer/settings?section=address' },
              { key: 'custom_categories', label: 'Özel Kategoriler', icon: 'Building2', route: '/dealer/settings?section=address' },
              { key: 'business_info', label: 'İşletme Bilgileri', icon: 'Building2', route: '/dealer/settings?section=address' },
              { key: 'store_users', label: 'Kullanıcılar', icon: 'UserSquare2', route: '/dealer/settings?section=address' },
              { key: 'packages_services', label: 'Paket ve Ek Hizmetler', icon: 'ShoppingCart', route: '/dealer/purchase' },
              { key: 'saved_cards', label: 'Kayıtlı Kartlarım', icon: 'FileText', route: '/dealer/settings?section=address' },
              { key: 'my_invoices', label: 'Faturalarım', icon: 'FileText', route: '/dealer/invoices' },
              { key: 'account_movements', label: 'Hesap Hareketlerim', icon: 'FileText', route: '/dealer/invoices' },
              { key: 'my_permissions', label: 'İzinlerim', icon: 'Shield', route: '/dealer/settings?section=security' },
            ],
          },
          {
            key: 'notification_preferences',
            label: 'Bildirim Tercihleri',
            icon: 'Bell',
            route: '/dealer/settings?section=notifications',
            children: [
              { key: 'electronic_messages', label: 'Elektronik İleti', icon: 'Bell', route: '/dealer/settings?section=notifications' },
              { key: 'read_receipt', label: 'Mesaj Okundu Bilgisi', icon: 'Bell', route: '/dealer/settings?section=notifications' },
            ],
          },
          {
            key: 'blocked_accounts',
            label: 'Engellediğim Hesap Sahipleri',
            icon: 'Ban',
            route: '/dealer/settings?section=blocked',
          },
        ],
      },
    ],
  },
];

const mergeCorporateMenuRoutes = (nodes, routeOverrides) =>
  nodes.map((node) => ({
    ...node,
    route: routeOverrides[node.key] || node.route || null,
    children: Array.isArray(node.children) && node.children.length
      ? mergeCorporateMenuRoutes(node.children, routeOverrides)
      : [],
  }));

const isCorporateMenuActive = (node, pathname) => {
  const routePath = node.route ? node.route.split('?')[0] : null;
  const isCurrent = routePath && (pathname === routePath || pathname.startsWith(`${routePath}/`));
  if (isCurrent) return true;
  if (!Array.isArray(node.children) || node.children.length === 0) return false;
  return node.children.some((child) => isCorporateMenuActive(child, pathname));
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
  const { configData: corporateHeaderConfig, logoUrl: corporateLogoUrl } = useUIHeaderConfig({
    segment: 'corporate',
    authRequired: true,
  });
  const [selectedStore, setSelectedStore] = useState('all');
  const [storeMenuOpen, setStoreMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [openMenuKey, setOpenMenuKey] = useState('favorites');

  const corporateRowMap = useMemo(() => {
    const rows = Array.isArray(corporateHeaderConfig?.rows) ? corporateHeaderConfig.rows : [];
    const map = {};
    rows.forEach((row) => {
      const rowId = `${row?.id || ''}`.trim().toLowerCase();
      if (!rowId) return;
      const set = new Set();
      const blocks = Array.isArray(row?.blocks) ? row.blocks : [];
      blocks.forEach((block) => {
        const type = `${block?.type || ''}`.trim();
        if (type) set.add(type);
      });
      map[rowId] = set;
    });
    return map;
  }, [corporateHeaderConfig]);

  const hasCorporateBlock = (rowId, type, fallback = true) => {
    const row = corporateRowMap[rowId];
    if (!row) return fallback;
    return row.has(type);
  };

  const showRow1Logo = hasCorporateBlock('row1', 'logo', true);
  const showRow1QuickActions = hasCorporateBlock('row1', 'quick_actions', true);
  const showRow1Language = hasCorporateBlock('row1', 'language_switcher', true);
  const showRow2FixedBlocks = hasCorporateBlock('row2', 'fixed_blocks', true);
  const showRow2Modules = hasCorporateBlock('row2', 'modules', true);
  const showRow3StoreFilter = hasCorporateBlock('row3', 'store_filter', true);
  const showRow3UserMenu = hasCorporateBlock('row3', 'user_menu', true);

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

  const sidebarRouteOverrides = useMemo(
    () => Object.fromEntries((sidebarItems || []).map((item) => [item.key, item.route])),
    [sidebarItems],
  );

  const structuredSidebarItems = useMemo(
    () => mergeCorporateMenuRoutes(corporateMenuStructure, sidebarRouteOverrides),
    [sidebarRouteOverrides],
  );

  const primaryMenuItems = useMemo(
    () => (structuredSidebarItems[0]?.children || []),
    [structuredSidebarItems],
  );

  const openPrimaryMenu = useMemo(
    () => primaryMenuItems.find((item) => item.key === openMenuKey) || null,
    [primaryMenuItems, openMenuKey],
  );

  const activePrimaryMenu = useMemo(
    () => primaryMenuItems.find((item) => isCorporateMenuActive(item, activePath)) || null,
    [primaryMenuItems, activePath],
  );

  useEffect(() => {
    setSelectedStore(headerRow3Controls?.default_store_key || 'all');
  }, [headerRow3Controls?.default_store_key]);

  useEffect(() => {
    setStoreMenuOpen(false);
    setUserMenuOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (!activePrimaryMenu?.key) return;
    if (activePrimaryMenu.key !== openMenuKey) {
      setOpenMenuKey(activePrimaryMenu.key);
    }
  }, [activePrimaryMenu?.key]);

  const handleLogout = () => {
    logout();
    navigate('/dealer/login');
  };

  const handleStoreChange = (nextStoreKey) => {
    setSelectedStore(nextStoreKey);
    setStoreMenuOpen(false);
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

  const getSecondaryDepthClass = (depth) => {
    if (depth <= 0) return 'pl-0';
    if (depth === 1) return 'pl-4';
    if (depth === 2) return 'pl-8';
    return 'pl-10';
  };

  const renderSecondaryMenuItem = (item, depth = 0) => {
    const Icon = iconMap[item.icon] || LayoutDashboard;
    const isActive = isCorporateMenuActive(item, activePath);
    const hasChildren = Array.isArray(item.children) && item.children.length > 0;
    const depthClass = getSecondaryDepthClass(depth);
    const itemClass = isActive ? 'bg-slate-800 text-white' : 'text-slate-900 hover:bg-slate-100';

    return (
      <div key={item.key} className={`${depthClass}`} data-testid={`dealer-row2-submenu-item-${item.key}`}>
        {item.route ? (
          <NavLink
            to={item.route}
            onClick={() => handleNavClick({ key: item.key, route: item.route }, 'row2_submenu')}
            className={`flex items-center gap-2 rounded-xl px-3 py-2 transition ${itemClass}`}
            data-testid={`dealer-row2-submenu-link-${item.key}`}
          >
            <Icon size={15} />
            <span className="text-sm font-medium" data-testid={`dealer-row2-submenu-label-${item.key}`}>{item.label}</span>
          </NavLink>
        ) : (
          <div className="flex items-center gap-2 rounded-xl px-3 py-2 text-slate-900" data-testid={`dealer-row2-submenu-link-${item.key}`}>
            <Icon size={15} />
            <span className="text-sm font-medium" data-testid={`dealer-row2-submenu-label-${item.key}`}>{item.label}</span>
          </div>
        )}

        {hasChildren ? (
          <div className="mt-1 space-y-1" data-testid={`dealer-row2-submenu-children-${item.key}`}>
            {item.children.map((child) => renderSecondaryMenuItem(child, depth + 1))}
          </div>
        ) : null}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-[var(--bg-warm)]" data-testid="dealer-layout-root">
      <header className="border-b bg-white" data-testid="dealer-layout-header">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-3 lg:px-6" data-testid="dealer-layout-header-rows">
          <div className="flex flex-wrap items-center justify-between gap-3" data-testid="dealer-layout-header-row1">
            <div className="flex items-center gap-3" data-testid="dealer-layout-brand-wrap">
              {showRow1Logo ? (
                <button
                  type="button"
                  onClick={() => navigate('/dealer/overview')}
                  className="flex h-10 min-w-28 items-center justify-center rounded bg-yellow-400 px-2 text-sm font-bold text-slate-900"
                  data-testid="dealer-layout-brand-button"
                >
                  {corporateLogoUrl ? (
                    <img
                      src={corporateLogoUrl}
                      alt="Kurumsal Logo"
                      className="h-8 w-28 object-contain"
                      data-testid="dealer-layout-brand-image"
                    />
                  ) : (
                    <span data-testid="dealer-layout-brand-fallback">ANNONCIA</span>
                  )}
                </button>
              ) : null}
              {showRow1QuickActions ? (
                <button
                  type="button"
                  onClick={() => navigate('/dealer/overview')}
                  className="rounded-full border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700"
                  data-testid="dealer-layout-main-menu-button"
                >
                  Ana Menü
                </button>
              ) : null}
              <span className="text-xs uppercase tracking-[0.2em] text-slate-500" data-testid="dealer-layout-portal-label">
                Kurumsal Portal
              </span>
            </div>

            {(showRow1QuickActions || showRow1Language) ? (
              <div className="flex flex-wrap items-center gap-2" data-testid="dealer-layout-quick-actions">
                {showRow1QuickActions ? row1Actions.map((item) => {
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
                }) : null}

                {showRow1Language ? (
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
                ) : null}
              </div>
            ) : null}
          </div>

          {showRow2Modules ? (
            <div className="border-t border-slate-200 pt-2" data-testid="dealer-layout-header-row2">
              <div className="flex items-center gap-1 overflow-x-auto pb-1" data-testid="dealer-layout-row2-primary-menu">
                {primaryMenuItems.map((item) => {
                  const Icon = iconMap[item.icon] || LayoutDashboard;
                  const hasChildren = Array.isArray(item.children) && item.children.length > 0;
                  const isActive = activePrimaryMenu?.key === item.key;
                  const isOpen = openMenuKey === item.key;

                  return (
                    <button
                      key={item.key}
                      type="button"
                      onClick={() => {
                        if (hasChildren) {
                          setOpenMenuKey((prev) => (prev === item.key ? null : item.key));
                          trackDealerEvent('dealer_nav_expand_toggle', { key: item.key, location: 'header_row2' });
                        } else if (item.route) {
                          navigate(item.route);
                          handleNavClick({ key: item.key, route: item.route }, 'header_row2');
                        }
                      }}
                      className={`inline-flex shrink-0 items-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium transition ${
                        isActive || isOpen ? 'border-slate-800 bg-slate-800 text-white' : 'border-slate-200 text-slate-900 hover:bg-slate-100'
                      }`}
                      data-testid={`dealer-row2-primary-menu-item-${item.key}`}
                    >
                      <Icon size={15} />
                      <span data-testid={`dealer-row2-primary-menu-label-${item.key}`}>{item.label}</span>
                      {hasChildren ? (
                        isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />
                      ) : null}
                    </button>
                  );
                })}
              </div>

              {openPrimaryMenu?.children?.length ? (
                <div className="mt-2 rounded-xl border border-slate-200 bg-white p-2" data-testid={`dealer-layout-row2-submenu-${openPrimaryMenu.key}`}>
                  <div className="space-y-1" data-testid="dealer-layout-row2-submenu-items">
                    {openPrimaryMenu.children.map((child) => renderSecondaryMenuItem(child, 0))}
                  </div>
                </div>
              ) : null}
            </div>
          ) : null}

          {(showRow3StoreFilter || showRow3UserMenu) ? (
            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-2" data-testid="dealer-layout-header-row3">
              {showRow3StoreFilter ? (
                <div className="relative flex items-center gap-2" data-testid="dealer-layout-row3-store-wrap">
                  <label className="text-xs font-semibold text-slate-600" data-testid="dealer-layout-row3-store-label">
                    Mağaza
                  </label>
                  <button
                    type="button"
                    onClick={() => setStoreMenuOpen((prev) => !prev)}
                    className="inline-flex h-9 min-w-[160px] items-center justify-between gap-2 rounded-md border border-slate-200 bg-white px-3 text-sm"
                    data-testid="dealer-layout-row3-store-filter"
                    disabled={!headerRow3Controls?.store_filter_enabled}
                  >
                    <span data-testid="dealer-layout-row3-store-selected-label">
                      {row3Stores.find((store) => store.key === selectedStore)?.label || 'Tüm Mağazalar'}
                    </span>
                    {storeMenuOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                  </button>

                  {storeMenuOpen && headerRow3Controls?.store_filter_enabled ? (
                    <div className="absolute left-[52px] top-10 z-20 min-w-[200px] rounded-lg border bg-white p-1 shadow-lg" data-testid="dealer-layout-row3-store-dropdown">
                      {row3Stores.map((store) => (
                        <button
                          key={store.key}
                          type="button"
                          onClick={() => handleStoreChange(store.key)}
                          className={`w-full rounded-md px-3 py-2 text-left text-sm ${selectedStore === store.key ? 'bg-slate-900 text-white' : 'text-slate-800 hover:bg-slate-100'}`}
                          data-testid={`dealer-layout-row3-store-option-${store.key}`}
                        >
                          {store.label}
                        </button>
                      ))}
                    </div>
                  ) : null}
                </div>
              ) : <div data-testid="dealer-layout-row3-store-wrap-empty" />}

              {showRow3UserMenu ? (
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
              ) : <div data-testid="dealer-layout-row3-user-menu-wrap-empty" />}
            </div>
          ) : null}
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6 lg:px-6" data-testid="dealer-layout-main-grid">
        {loading ? (
          <div className="mb-3 text-xs text-slate-600" data-testid="dealer-layout-content-loading">Menü yükleniyor…</div>
        ) : null}
        {error ? (
          <div className="mb-3 text-xs text-rose-700" data-testid="dealer-layout-content-error">{error}</div>
        ) : null}

        <section className="rounded-2xl bg-white p-6 shadow-sm" data-testid="dealer-layout-content">
          <Outlet />
        </section>
      </main>
    </div>
  );
}
