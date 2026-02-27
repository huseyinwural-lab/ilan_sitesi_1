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
      { key: 'virtual_tours', label: 'Sanal Turlar', icon: 'LayoutDashboard', route: '/dealer/overview' },
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
        route: '/dealer/overview',
        children: [
          { key: 'favorite_listings', label: 'Favori İlanlar', icon: 'Heart', route: '/dealer/listings' },
          { key: 'favorite_searches', label: 'Favori Aramalar', icon: 'Heart', route: '/dealer/overview' },
          { key: 'favorite_sellers', label: 'Favori Satıcılar', icon: 'Heart', route: '/dealer/customers' },
        ],
      },
      {
        key: 'reports',
        label: 'Raporlar',
        icon: 'BarChart3',
        route: '/dealer/reports',
        children: [
          { key: 'hourly_visit_report', label: 'Saatlik Ziyaret Sayısı', icon: 'BarChart3', route: '/dealer/reports' },
          {
            key: 'performance_reports',
            label: 'Performans Raporları',
            icon: 'BarChart3',
            route: '/dealer/reports',
            children: [
              { key: 'live_listing_report', label: 'Yayındaki İlan Raporu', icon: 'BarChart3', route: '/dealer/reports' },
              { key: 'view_report', label: 'Görüntüleme Raporu', icon: 'BarChart3', route: '/dealer/reports' },
              { key: 'favorite_report', label: 'Favoriye Alınma Raporu', icon: 'BarChart3', route: '/dealer/reports' },
              { key: 'message_report', label: 'Gelen Mesaj Raporu', icon: 'BarChart3', route: '/dealer/reports' },
              { key: 'mobile_call_report', label: 'Gelen Arama Raporu (Mobil)', icon: 'BarChart3', route: '/dealer/reports' },
            ],
          },
          { key: 'package_reports', label: 'Paket Raporları', icon: 'BarChart3', route: '/dealer/reports' },
          { key: 'doping_usage_report', label: 'Doping Kullanım Raporu', icon: 'BarChart3', route: '/dealer/reports' },
        ],
      },
      {
        key: 'consultant_tracking',
        label: 'Danışman Takibi',
        icon: 'Users',
        route: '/dealer/customers',
        children: [
          { key: 'consultant_service_reviews', label: 'Danışman Hizmet Değerlendirmeleri', icon: 'Users', route: '/dealer/reports' },
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
            route: '/dealer/settings',
            children: [
              { key: 'personal_info', label: 'Kişisel Bilgilerim', icon: 'UserRound', route: '/dealer/settings' },
              { key: 'account_email', label: 'E-Posta', icon: 'UserRound', route: '/dealer/settings' },
              { key: 'account_phone', label: 'Cep Telefonu', icon: 'UserRound', route: '/dealer/settings' },
              { key: 'password_change', label: 'Şifre Değişikliği', icon: 'Shield', route: '/dealer/settings' },
              { key: 'account_verification', label: 'Hesap Doğrulama', icon: 'Shield', route: '/dealer/settings' },
              { key: 'recovery_email', label: 'Kurtarma E-Postası', icon: 'Shield', route: '/dealer/settings' },
              { key: 'sessions_devices', label: 'Oturumlar ve Cihazlar', icon: 'Shield', route: '/dealer/settings' },
            ],
          },
          {
            key: 'security',
            label: 'Güvenlik',
            icon: 'Shield',
            route: '/dealer/settings',
            children: [
              { key: 'two_factor', label: '2 Aşamalı Doğrulama', icon: 'Shield', route: '/dealer/settings' },
            ],
          },
          {
            key: 'store',
            label: 'Mağazam',
            icon: 'Building2',
            route: '/dealer/company',
            children: [
              { key: 'store_content', label: 'Mağaza İçeriği', icon: 'Building2', route: '/dealer/company' },
              { key: 'custom_categories', label: 'Özel Kategoriler', icon: 'Building2', route: '/dealer/company' },
              { key: 'business_info', label: 'İşletme Bilgileri', icon: 'Building2', route: '/dealer/company' },
              { key: 'store_users', label: 'Kullanıcılar', icon: 'UserSquare2', route: '/dealer/company' },
              { key: 'packages_services', label: 'Paket ve Ek Hizmetler', icon: 'ShoppingCart', route: '/dealer/purchase' },
              { key: 'saved_cards', label: 'Kayıtlı Kartlarım', icon: 'FileText', route: '/dealer/settings' },
              { key: 'my_invoices', label: 'Faturalarım', icon: 'FileText', route: '/dealer/invoices' },
              { key: 'account_movements', label: 'Hesap Hareketlerim', icon: 'FileText', route: '/dealer/invoices' },
              { key: 'my_permissions', label: 'İzinlerim', icon: 'Shield', route: '/dealer/settings' },
            ],
          },
          {
            key: 'notification_preferences',
            label: 'Bildirim Tercihleri',
            icon: 'Bell',
            route: '/dealer/settings',
            children: [
              { key: 'electronic_messages', label: 'Elektronik İleti', icon: 'Bell', route: '/dealer/settings' },
              { key: 'read_receipt', label: 'Mesaj Okundu Bilgisi', icon: 'Bell', route: '/dealer/settings' },
            ],
          },
          {
            key: 'blocked_accounts',
            label: 'Engellediğim Hesap Sahipleri',
            icon: 'Ban',
            route: '/dealer/settings',
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
  const isCurrent = node.route && (pathname === node.route || pathname.startsWith(`${node.route}/`));
  if (isCurrent) return true;
  if (!Array.isArray(node.children) || node.children.length === 0) return false;
  return node.children.some((child) => isCorporateMenuActive(child, pathname));
};

const getCorporateMenuActiveTrail = (nodes, pathname, trail = []) => {
  for (const node of nodes) {
    const nextTrail = [...trail, node.key];
    const isCurrent = node.route && (pathname === node.route || pathname.startsWith(`${node.route}/`));
    if (isCurrent) return nextTrail;
    if (Array.isArray(node.children) && node.children.length) {
      const childTrail = getCorporateMenuActiveTrail(node.children, pathname, nextTrail);
      if (childTrail.length) return childTrail;
    }
  }
  return [];
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
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [expandedMenuMap, setExpandedMenuMap] = useState({ ofisim: true });

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

  const activeMenuTrail = useMemo(
    () => getCorporateMenuActiveTrail(structuredSidebarItems, activePath),
    [structuredSidebarItems, activePath],
  );

  useEffect(() => {
    setSelectedStore(headerRow3Controls?.default_store_key || 'all');
  }, [headerRow3Controls?.default_store_key]);

  useEffect(() => {
    setExpandedMenuMap((prev) => {
      const next = { ...prev };
      activeMenuTrail.forEach((key) => {
        next[key] = true;
      });
      if (typeof next.ofisim === 'undefined') {
        next.ofisim = true;
      }
      return next;
    });
  }, [activeMenuTrail]);

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

  const handleMenuToggle = (itemKey) => {
    setExpandedMenuMap((prev) => ({
      ...prev,
      [itemKey]: !prev[itemKey],
    }));
    trackDealerEvent('dealer_nav_expand_toggle', { key: itemKey, location: 'sidebar_tree' });
  };

  const renderCorporateMenuItem = (item, depth = 0) => {
    const Icon = iconMap[item.icon] || LayoutDashboard;
    const isActive = isCorporateMenuActive(item, activePath);
    const hasChildren = Array.isArray(item.children) && item.children.length > 0;
    const isExpanded = hasChildren && !!expandedMenuMap[item.key];
    const depthClass = depth === 0 ? 'pl-0' : depth === 1 ? 'pl-3' : depth === 2 ? 'pl-6' : 'pl-9';
    const labelClass = depth === 0 ? 'text-sm font-semibold' : 'text-sm font-medium';
    const itemClass = isActive
      ? 'bg-slate-800 text-white shadow-sm'
      : 'text-slate-900 hover:bg-slate-100';

    return (
      <div key={item.key} className={`${depthClass}`} data-testid={`dealer-sidebar-tree-item-${item.key}`}>
        {hasChildren ? (
          <button
            type="button"
            onClick={() => handleMenuToggle(item.key)}
            className={`flex w-full items-center gap-2 rounded-xl px-3 py-2 transition ${itemClass}`}
            data-testid={`dealer-sidebar-tree-toggle-${item.key}`}
          >
            <Icon size={15} />
            <span className={`${labelClass} flex-1 text-left`} data-testid={`dealer-sidebar-tree-label-${item.key}`}>{item.label}</span>
            {isExpanded ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
          </button>
        ) : item.route ? (
          <NavLink
            to={item.route}
            onClick={() => handleNavClick({ key: item.key, route: item.route }, 'sidebar_tree')}
            className={`flex items-center gap-2 rounded-xl px-3 py-2 transition ${itemClass}`}
            data-testid={`dealer-sidebar-tree-link-${item.key}`}
          >
            <Icon size={15} />
            <span className={labelClass} data-testid={`dealer-sidebar-tree-label-${item.key}`}>{item.label}</span>
          </NavLink>
        ) : (
          <div className="flex items-center gap-2 rounded-xl px-3 py-2 text-slate-800" data-testid={`dealer-sidebar-tree-link-${item.key}`}>
            <Icon size={15} />
            <span className={labelClass} data-testid={`dealer-sidebar-tree-label-${item.key}`}>{item.label}</span>
          </div>
        )}

        {hasChildren && isExpanded ? (
          <div className="mt-1 space-y-1" data-testid={`dealer-sidebar-tree-children-${item.key}`}>
            {item.children.map((child) => renderCorporateMenuItem(child, depth + 1))}
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

          {(showRow2FixedBlocks || showRow2Modules) ? (
            <div className="flex flex-wrap items-center gap-2 border-t border-slate-100 pt-2" data-testid="dealer-layout-header-row2">
              {showRow2FixedBlocks ? (headerRow1FixedBlocks || []).map((block) => (
                <span
                  key={block.key}
                  className="rounded-full bg-slate-100 px-2 py-1 text-[11px] font-semibold text-slate-600"
                  data-testid={`dealer-layout-header-row1-fixed-${block.key}`}
                >
                  {block.label}
                </span>
              )) : null}
              {showRow2Modules ? row2Modules.map((module) => {
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
              }) : null}
            </div>
          ) : null}

          {(showRow3StoreFilter || showRow3UserMenu) ? (
            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-2" data-testid="dealer-layout-header-row3">
              {showRow3StoreFilter ? (
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

      <main className="mx-auto grid max-w-7xl gap-6 px-4 py-6 lg:grid-cols-[260px_1fr] lg:px-6" data-testid="dealer-layout-main-grid">
        <aside className="rounded-2xl bg-white p-4 shadow-sm" data-testid="dealer-layout-sidebar">
          <div className="text-xs uppercase tracking-[0.2em] text-slate-600" data-testid="dealer-layout-sidebar-title">
            Navigasyon
          </div>

          {loading ? (
            <div className="mt-4 text-xs text-slate-500" data-testid="dealer-layout-sidebar-loading">Yükleniyor…</div>
          ) : (
            <div className="mt-4 max-h-[calc(100vh-14rem)] space-y-1 overflow-y-auto pr-1" data-testid="dealer-layout-sidebar-items">
              {structuredSidebarItems.map((item) => renderCorporateMenuItem(item, 0))}
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
