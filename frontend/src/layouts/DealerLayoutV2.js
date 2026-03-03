import React, { useEffect, useMemo, useState } from 'react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  BarChart3,
  Bell,
  BookOpen,
  Building2,
  ChevronDown,
  ChevronRight,
  CircleUserRound,
  FileText,
  Heart,
  LayoutDashboard,
  ListChecks,
  LogOut,
  MessageCircle,
  Pencil,
  Search,
  Shield,
  ShoppingCart,
  Sparkles,
  Star,
  StarOff,
  Store,
  UserRound,
  UserSquare2,
  Users,
} from 'lucide-react';

import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { useDealerPortalConfig } from '@/hooks/useDealerPortalConfig';
import { useUIHeaderConfig } from '@/hooks/useUIHeaderConfig';
import { trackDealerEvent } from '@/lib/dealerAnalytics';
import SiteFooter from '@/components/public/SiteFooter';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const QUICK_MENU_STORAGE_KEY = 'dealer-v2-quick-menu-usage';
const QUICK_MENU_FAVORITES_KEY = 'dealer-v2-quick-menu-favorites';
const QUICK_MENU_LIMIT = 6;
const QUICK_MENU_DEFAULT_KEYS = [
  'listings_active',
  'messages_inbox',
  'customer_list',
  'favorite_listings',
  'package_summary',
  'saved_cards',
];

const languageOptions = [
  { key: 'tr', label: 'TR' },
  { key: 'de', label: 'DE' },
  { key: 'fr', label: 'FR' },
];

const iconMap = {
  LayoutDashboard,
  ListChecks,
  Sparkles,
  MessageCircle,
  Users,
  Heart,
  BarChart3,
  ShoppingCart,
  CircleUserRound,
  UserRound,
  Shield,
  Building2,
  UserSquare2,
  Bell,
  FileText,
  BookOpen,
  Store,
};

const corporateTopMenu = [
  {
    key: 'overview',
    label: 'Özet Dashboard',
    icon: 'LayoutDashboard',
    route: '/dealer/overview',
    children: [
      { key: 'visit_count', label: 'Ziyaret Sayısı', icon: 'BarChart3', route: '/dealer/overview?widget=visit_count' },
      { key: 'store_performance', label: 'Mağaza Performansı', icon: 'BarChart3', route: '/dealer/overview?widget=store_performance' },
      { key: 'active_listing_count', label: 'Yayındaki İlan Sayısı', icon: 'ListChecks', route: '/dealer/overview?widget=active_listing_count' },
      { key: 'demanded_customer_count', label: 'Talep Olan Müşteri Sayısı', icon: 'Users', route: '/dealer/overview?widget=demanded_customer_count' },
      { key: 'matching_listings', label: 'Müşteriye Uygun İlanlar', icon: 'Sparkles', route: '/dealer/overview?widget=matching_listings' },
      { key: 'extra_widgets', label: 'Eklenebilir Widget Alanı', icon: 'LayoutDashboard', route: '/dealer/overview?widget=custom' },
    ],
  },
  {
    key: 'listings',
    label: 'İlanlar',
    icon: 'ListChecks',
    route: '/dealer/listings',
    children: [
      { key: 'listings_active', label: 'Yayında Olan İlanlar', icon: 'ListChecks', route: '/dealer/listings?status=active' },
      { key: 'listings_inactive', label: 'Yayında Olmayanlar', icon: 'ListChecks', route: '/dealer/listings?status=inactive' },
      { key: 'listings_draft', label: 'Taslak İlanlar', icon: 'ListChecks', route: '/dealer/listings?status=draft' },
      { key: 'listings_expired', label: 'Süresi Dolanlar', icon: 'ListChecks', route: '/dealer/listings?status=expired' },
      { key: 'listings_archive', label: 'Arşiv', icon: 'ListChecks', route: '/dealer/listings?status=archived' },
    ],
  },
  {
    key: 'messages',
    label: 'Mesajlar',
    icon: 'MessageCircle',
    route: '/dealer/messages',
    children: [
      { key: 'messages_inbox', label: 'Gelen Mesajlar', icon: 'MessageCircle', route: '/dealer/messages?folder=inbox' },
      { key: 'messages_sent', label: 'Gönderilen Mesajlar', icon: 'MessageCircle', route: '/dealer/messages?folder=sent' },
      { key: 'messages_archive', label: 'Arşiv', icon: 'MessageCircle', route: '/dealer/messages?folder=archive' },
      { key: 'messages_spam', label: 'Spam', icon: 'Shield', route: '/dealer/messages?folder=spam' },
    ],
  },
  {
    key: 'customers',
    label: 'Müşteri Yönetimi',
    icon: 'Users',
    route: '/dealer/customers',
    children: [
      { key: 'customer_list', label: 'Müşteri Listesi', icon: 'Users', route: '/dealer/customers?tab=list' },
      { key: 'customer_add', label: 'Müşteri Ekle', icon: 'Users', route: '/dealer/customers?tab=add' },
      { key: 'customer_potential', label: 'Potansiyel Müşteriler', icon: 'Users', route: '/dealer/customers?tab=potential' },
      {
        key: 'contracts',
        label: 'Sözleşmeler',
        icon: 'FileText',
        route: '/dealer/customers?tab=contracts',
        children: [
          { key: 'contracts_active', label: 'Aktif', icon: 'FileText', route: '/dealer/customers?tab=contracts&status=active' },
          { key: 'contracts_expired', label: 'Süresi Dolan', icon: 'FileText', route: '/dealer/customers?tab=contracts&status=expired' },
          { key: 'contracts_draft', label: 'Taslak', icon: 'FileText', route: '/dealer/customers?tab=contracts&status=draft' },
        ],
      },
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
    route: '/dealer/reports?section=listing_report',
    children: [
      { key: 'hourly_visit_report', label: 'Saatlik Ziyaret Sayısı', icon: 'BarChart3', route: '/dealer/reports?section=hourly_visit_report' },
      {
        key: 'performance_reports',
        label: 'Performans Raporları',
        icon: 'BarChart3',
        route: '/dealer/reports?section=views_report',
        children: [
          { key: 'view_report', label: 'Görüntülenme', icon: 'BarChart3', route: '/dealer/reports?section=views_report' },
          { key: 'favorite_report', label: 'Favori Alma', icon: 'Heart', route: '/dealer/reports?section=favorites_report' },
          { key: 'message_report', label: 'Gelen Mesaj', icon: 'MessageCircle', route: '/dealer/reports?section=messages_report' },
          { key: 'mobile_call_report', label: 'Gelen Arama (Mobil)', icon: 'BarChart3', route: '/dealer/reports?section=mobile_calls_report' },
          { key: 'total_show_report', label: 'Toplam Gösterim', icon: 'BarChart3', route: '/dealer/reports?section=listing_report' },
        ],
      },
    ],
  },
  {
    key: 'package_reports',
    label: 'Paket Raporları',
    icon: 'BarChart3',
    route: '/dealer/reports?section=package_reports',
    children: [
      { key: 'package_summary', label: 'Paket Özeti', icon: 'BarChart3', route: '/dealer/reports?section=package_reports' },
      { key: 'package_usage_counts', label: 'Kullanım Adetleri', icon: 'BarChart3', route: '/dealer/reports?section=package_reports' },
      { key: 'extra_listing_usage', label: 'Ek İlan Kullanımı', icon: 'BarChart3', route: '/dealer/reports?section=package_reports' },
    ],
  },
  {
    key: 'doping_usage',
    label: 'Doping Kullanım Raporu',
    icon: 'Sparkles',
    route: '/dealer/reports?section=doping_usage',
    children: [
      { key: 'active_doping', label: 'Aktif Dopingler', icon: 'Sparkles', route: '/dealer/reports?section=doping_usage' },
      { key: 'history_doping', label: 'Geçmiş Dopingler', icon: 'Sparkles', route: '/dealer/reports?section=doping_usage' },
      { key: 'user_based_doping', label: 'Kullanıcı Bazlı Liste', icon: 'Users', route: '/dealer/reports?section=doping_usage' },
      { key: 'date_filter_doping', label: 'Tarih Filtresi', icon: 'BarChart3', route: '/dealer/reports?section=doping_usage' },
    ],
  },
  {
    key: 'consultant_tracking',
    label: 'Danışman Takibi',
    icon: 'Users',
    route: '/dealer/consultant-tracking',
    children: [
      {
        key: 'consultant_service_reviews',
        label: 'Danışman Hizmet Değerlendirmeleri',
        icon: 'Users',
        route: '/dealer/consultant-tracking?tab=evaluations',
      },
    ],
  },
  {
    key: 'purchase',
    label: 'Satın Al',
    icon: 'ShoppingCart',
    route: '/dealer/purchase',
    children: [
      { key: 'bulk_doping_purchase', label: 'Toplu Doping Satın Al', icon: 'ShoppingCart', route: '/dealer/purchase?tab=bulk_doping' },
      { key: 'package_upgrade', label: 'Paket Yükseltme', icon: 'ShoppingCart', route: '/dealer/purchase?tab=package_upgrade' },
      { key: 'cart', label: 'Sepet', icon: 'ShoppingCart', route: '/dealer/purchase?tab=cart' },
      { key: 'payment_info', label: 'Ödeme Bilgileri', icon: 'FileText', route: '/dealer/purchase?tab=payment_info' },
    ],
  },
  {
    key: 'account',
    label: 'Hesabım',
    icon: 'CircleUserRound',
    route: '/dealer/settings?section=profile',
    children: [
      { key: 'personal_info', label: 'Kişisel Bilgilerim', icon: 'UserRound', route: '/dealer/settings?section=profile' },
      { key: 'account_email', label: 'E-Posta', icon: 'UserRound', route: '/dealer/settings?section=profile' },
      { key: 'account_phone', label: 'Cep Telefonu', icon: 'UserRound', route: '/dealer/settings?section=profile' },
      { key: 'password_change', label: 'Şifre Değişikliği', icon: 'Shield', route: '/dealer/settings?section=security' },
      { key: 'profile_photo', label: 'Profil Fotoğrafı', icon: 'UserRound', route: '/dealer/settings?section=profile' },
      { key: 'account_verification', label: 'Hesap Doğrulama', icon: 'Shield', route: '/dealer/settings?section=security' },
      { key: 'two_factor', label: '2 Aşamalı Doğrulama', icon: 'Shield', route: '/dealer/settings?section=security' },
      { key: 'recovery_email', label: 'Kurtarma E-Postası', icon: 'Shield', route: '/dealer/settings?section=security' },
      { key: 'sessions_devices', label: 'Oturumlar ve Cihazlar', icon: 'Shield', route: '/dealer/settings?section=security' },
      { key: 'store_content', label: 'Mağaza İçeriği', icon: 'Store', route: '/dealer/company' },
      { key: 'custom_categories', label: 'Özel Kategoriler', icon: 'Store', route: '/dealer/settings?section=address' },
      { key: 'business_info', label: 'İşletme Bilgileri', icon: 'Store', route: '/dealer/settings?section=address' },
      { key: 'store_users', label: 'Kullanıcılar', icon: 'UserSquare2', route: '/dealer/settings?section=store_users' },
      { key: 'packages_services', label: 'Paket ve Ek Hizmetler', icon: 'ShoppingCart', route: '/dealer/settings?section=packages_services' },
      { key: 'saved_cards', label: 'Kayıtlı Kartlarım', icon: 'FileText', route: '/dealer/settings?section=saved_cards' },
      { key: 'my_invoices', label: 'Faturalarım', icon: 'FileText', route: '/dealer/settings?section=invoices' },
      { key: 'account_movements', label: 'Hesap Hareketlerim', icon: 'FileText', route: '/dealer/settings?section=account_movements' },
      { key: 'my_permissions', label: 'İzinlerim', icon: 'Shield', route: '/dealer/settings?section=security' },
      { key: 'notif_listing', label: 'Bildirim: İlan', icon: 'Bell', route: '/dealer/settings?section=notifications' },
      { key: 'notif_store', label: 'Bildirim: Mağaza', icon: 'Bell', route: '/dealer/settings?section=notifications' },
      { key: 'notif_favorite', label: 'Bildirim: Favori', icon: 'Bell', route: '/dealer/settings?section=notifications' },
      { key: 'notif_native_ad', label: 'Bildirim: Doğal Reklam', icon: 'Bell', route: '/dealer/settings?section=notifications' },
      { key: 'notif_virtual_tour', label: 'Bildirim: Sanal Tur', icon: 'Bell', route: '/dealer/settings?section=notifications' },
      { key: 'electronic_sms', label: 'Ticari İleti: SMS', icon: 'Bell', route: '/dealer/settings?section=notifications' },
      { key: 'electronic_email', label: 'Ticari İleti: E-Posta', icon: 'Bell', route: '/dealer/settings?section=notifications' },
      { key: 'electronic_call', label: 'Ticari İleti: Arama', icon: 'Bell', route: '/dealer/settings?section=notifications' },
      { key: 'read_receipt', label: 'Mesaj Okundu Bilgisi', icon: 'Bell', route: '/dealer/settings?section=notifications' },
      { key: 'blocked_accounts', label: 'Engellediğim Hesap Sahipleri', icon: 'Shield', route: '/dealer/settings?section=blocked' },
    ],
  },
];

const mergeMenuRoutes = (nodes, overrides) => (
  nodes.map((node) => ({
    ...node,
    route: overrides[node.key] || node.route,
    children: Array.isArray(node.children) ? mergeMenuRoutes(node.children, overrides) : [],
  }))
);

const isRouteActive = (route, pathname, search) => {
  if (!route) return false;
  const routePath = route.split('?')[0];
  const routeQueryRaw = route.includes('?') ? route.split('?')[1] : '';
  if (routeQueryRaw) {
    const currentParams = new URLSearchParams(search || '');
    const expectedParams = new URLSearchParams(routeQueryRaw);
    const queryMatch = Array.from(expectedParams.entries()).every(([key, value]) => currentParams.get(key) === value);
    return pathname === routePath && queryMatch;
  }
  return pathname === routePath || pathname.startsWith(`${routePath}/`);
};

const isMenuNodeActive = (node, pathname, search) => {
  if (isRouteActive(node.route, pathname, search)) return true;
  return (node.children || []).some((child) => isMenuNodeActive(child, pathname, search));
};

const flattenMenuNodes = (nodes) => {
  const list = [];
  const walk = (items, rootKey = null) => {
    (items || []).forEach((item) => {
      const parentKey = rootKey || item.key;
      if (item.route) {
        list.push({
          key: item.key,
          label: item.label,
          route: item.route,
          icon: item.icon,
          parentKey,
        });
      }
      if (Array.isArray(item.children) && item.children.length) {
        walk(item.children, parentKey);
      }
    });
  };
  walk(nodes, null);
  return list;
};

const translateMenuNodes = (nodes, t) => (
  (nodes || []).map((node) => ({
    ...node,
    label: t(`dealer.menu.${node.key}`, node.label),
    children: translateMenuNodes(node.children || [], t),
  }))
);

export default function DealerLayoutV2() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const { language, setLanguage, t } = useLanguage();
  const {
    loading,
    error,
    headerItems,
    headerRow1Items,
    headerRow3Controls,
    sidebarItems,
  } = useDealerPortalConfig();

  const { configData: corporateHeaderConfig, logoUrl: corporateUiLogoUrl } = useUIHeaderConfig({
    segment: 'corporate',
    authRequired: true,
  });

  const [openMenuKey, setOpenMenuKey] = useState('favorites');
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [storeMenuOpen, setStoreMenuOpen] = useState(false);
  const [selectedStore, setSelectedStore] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [isPageEditMode, setIsPageEditMode] = useState(false);
  const [quickMenuUsage, setQuickMenuUsage] = useState({});
  const [quickMenuFavorites, setQuickMenuFavorites] = useState([]);
  const [quickMenuTab, setQuickMenuTab] = useState('recent');
  const [quickMenuEditOpen, setQuickMenuEditOpen] = useState(false);
  const [quickMenuSearch, setQuickMenuSearch] = useState('');
  const [navSummary, setNavSummary] = useState({
    badges: {
      active_listings: 0,
      total_listings: 0,
      favorites_total: 0,
      unread_messages: 0,
      customers_total: 0,
      cart_total: 0,
      announcements_total: 0,
    },
    left_menu: {},
  });
  const [corporateHeaderData, setCorporateHeaderData] = useState({ logo_url: null, items: [] });

  const corporateRowMap = useMemo(() => {
    const rows = Array.isArray(corporateHeaderConfig?.rows) ? corporateHeaderConfig.rows : [];
    const map = {};
    rows.forEach((row) => {
      const rowId = `${row?.id || ''}`.trim().toLowerCase();
      if (!rowId) return;
      map[rowId] = new Set((row?.blocks || []).map((block) => `${block?.type || ''}`.trim()).filter(Boolean));
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
  const showRow3StoreFilter = hasCorporateBlock('row3', 'store_filter', true);
  const showRow3UserMenu = hasCorporateBlock('row3', 'user_menu', true);

  const topMenuItems = useMemo(() => {
    const navRows = Array.isArray(sidebarItems) ? sidebarItems : [];
    const overrides = Object.fromEntries(
      navRows.map((item) => [item.key === 'settings' ? 'account' : item.key, item.route]),
    );
    const merged = mergeMenuRoutes(corporateTopMenu, overrides);

    if (!navRows.length) return translateMenuNodes(merged, t);

    const byKey = new Map(merged.map((item) => [item.key, item]));
    const orderedKeys = navRows
      .map((item) => (item.key === 'settings' ? 'account' : item.key))
      .filter((key) => byKey.has(key));

    const ordered = orderedKeys.map((key) => {
      const rawConfig = navRows.find((item) => (item.key === 'settings' ? 'account' : item.key) === key) || {};
      const baseItem = byKey.get(key);
      return {
        ...baseItem,
        route: rawConfig.route || baseItem.route,
        icon: rawConfig.icon || baseItem.icon,
      };
    });
    return translateMenuNodes(ordered, t);
  }, [sidebarItems, t]);

  const activeTopMenu = useMemo(
    () => topMenuItems.find((item) => isMenuNodeActive(item, location.pathname, location.search)) || null,
    [topMenuItems, location.pathname, location.search],
  );

  const row4MenuRoot = useMemo(() => {
    const selected = topMenuItems.find((item) => item.key === openMenuKey);
    return selected || activeTopMenu || topMenuItems[0] || null;
  }, [topMenuItems, openMenuKey, activeTopMenu]);

  const row1Actions = useMemo(
    () => (Array.isArray(headerRow1Items) && headerRow1Items.length ? headerRow1Items : headerItems || []),
    [headerItems, headerRow1Items],
  );

  const corporateLogoUrl = corporateHeaderData.logo_url || corporateUiLogoUrl || null;
  const corporateDynamicLinks = useMemo(() => {
    if (!Array.isArray(corporateHeaderData.items)) return [];
    return corporateHeaderData.items.filter((item) => item?.label && item?.url);
  }, [corporateHeaderData.items]);

  const row3Stores = useMemo(() => {
    const stores = headerRow3Controls?.stores;
    return Array.isArray(stores) && stores.length ? stores : [{ key: 'all', label: t('dealer.layout.all_stores', 'Tümü') }];
  }, [headerRow3Controls, t]);

  const userDisplayName = headerRow3Controls?.user_display_name || user?.full_name || user?.email || t('dealer.layout.user_fallback', 'Kurumsal Kullanıcı');
  const userInitials = userDisplayName
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('') || 'KU';

  const topMenuBadges = {
    listings: navSummary?.badges?.active_listings,
    messages: navSummary?.badges?.unread_messages,
    customers: navSummary?.badges?.customers_total,
    favorites: navSummary?.badges?.favorites_total,
    reports: navSummary?.badges?.total_listings,
    package_reports: navSummary?.badges?.total_listings,
    doping_usage: navSummary?.badges?.total_listings,
    consultant_tracking: navSummary?.badges?.customers_total,
    purchase: navSummary?.badges?.cart_total,
    account: navSummary?.badges?.announcements_total,
  };

  const quickMenuCandidates = useMemo(() => flattenMenuNodes(topMenuItems), [topMenuItems]);
  const quickMenuCandidateMap = useMemo(
    () => new Map(quickMenuCandidates.map((item) => [item.key, item])),
    [quickMenuCandidates],
  );

  const quickRecentItems = useMemo(() => {
    const byKey = quickMenuCandidateMap;
    const selected = [];
    const selectedSet = new Set();

    Object.entries(quickMenuUsage || {})
      .sort((a, b) => Number(b[1] || 0) - Number(a[1] || 0))
      .forEach(([key]) => {
        if (selected.length >= QUICK_MENU_LIMIT) return;
        const row = byKey.get(key);
        if (row && !selectedSet.has(row.key)) {
          selected.push(row);
          selectedSet.add(row.key);
        }
      });

    QUICK_MENU_DEFAULT_KEYS.forEach((key) => {
      if (selected.length >= QUICK_MENU_LIMIT) return;
      const row = byKey.get(key);
      if (row && !selectedSet.has(row.key)) {
        selected.push(row);
        selectedSet.add(row.key);
      }
    });

    quickMenuCandidates.forEach((row) => {
      if (selected.length >= QUICK_MENU_LIMIT) return;
      if (!selectedSet.has(row.key)) {
        selected.push(row);
        selectedSet.add(row.key);
      }
    });

    return selected.slice(0, QUICK_MENU_LIMIT);
  }, [quickMenuCandidates, quickMenuUsage, quickMenuCandidateMap]);

  const quickFavoriteItems = useMemo(() => {
    return (quickMenuFavorites || [])
      .map((key) => quickMenuCandidateMap.get(key))
      .filter(Boolean)
      .slice(0, QUICK_MENU_LIMIT);
  }, [quickMenuFavorites, quickMenuCandidateMap]);

  const quickMenuItems = quickMenuTab === 'favorites' ? quickFavoriteItems : quickRecentItems;

  const quickMenuManageItems = useMemo(() => {
    const normalizedQuery = quickMenuSearch.trim().toLowerCase();
    const rows = quickMenuCandidates.filter((item) => {
      if (!normalizedQuery) return true;
      const hay = `${item.label || ''} ${item.parentKey || ''}`.toLowerCase();
      return hay.includes(normalizedQuery);
    });
    return rows.slice(0, 30);
  }, [quickMenuCandidates, quickMenuSearch]);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(QUICK_MENU_STORAGE_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
        setQuickMenuUsage(parsed);
      }
    } catch (_) {
      setQuickMenuUsage({});
    }
  }, []);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(QUICK_MENU_FAVORITES_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        setQuickMenuFavorites(parsed.filter((item) => typeof item === 'string'));
      }
    } catch (_) {
      setQuickMenuFavorites([]);
    }
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem(QUICK_MENU_FAVORITES_KEY, JSON.stringify(quickMenuFavorites));
    } catch (_) {
      // ignore storage write errors
    }
  }, [quickMenuFavorites]);

  useEffect(() => {
    setSelectedStore(headerRow3Controls?.default_store_key || 'all');
  }, [headerRow3Controls?.default_store_key]);

  useEffect(() => {
    let active = true;
    fetch(`${API}/site/header?mode=corporate`)
      .then((res) => res.json())
      .then((data) => {
        if (!active) return;
        setCorporateHeaderData({
          logo_url: data?.logo_url || null,
          items: Array.isArray(data?.items) ? data.items : [],
        });
      })
      .catch(() => {
        if (!active) return;
        setCorporateHeaderData({ logo_url: null, items: [] });
      });

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (activeTopMenu?.key && activeTopMenu.key !== openMenuKey) {
      setOpenMenuKey(activeTopMenu.key);
    }
  }, [activeTopMenu?.key, openMenuKey]);

  useEffect(() => {
    const loadNavigationSummary = async () => {
      try {
        const token = localStorage.getItem('access_token');
        if (!token) return;
        const response = await fetch(`${API}/dealer/dashboard/navigation-summary`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) return;
        setNavSummary(payload);
      } catch (_) {
        setNavSummary((prev) => prev);
      }
    };
    loadNavigationSummary();
  }, [location.pathname]);

  useEffect(() => {
    setStoreMenuOpen(false);
    setUserMenuOpen(false);
  }, [location.pathname]);

  const handleNavClick = (item, zone) => {
    if (item?.key) {
      setQuickMenuUsage((prev) => {
        const next = {
          ...(prev || {}),
          [item.key]: Number((prev || {})[item.key] || 0) + 1,
        };
        try {
          localStorage.setItem(QUICK_MENU_STORAGE_KEY, JSON.stringify(next));
        } catch (_) {
          // ignore storage write errors
        }
        return next;
      });
    }
    trackDealerEvent('dealer_nav_click', {
      key: item.key,
      route: item.route,
      location: zone,
    });
  };

  const handleCorporateDynamicLink = (item) => {
    const href = (item?.url || '').trim();
    if (!href) return;
    const external = href.startsWith('http://') || href.startsWith('https://');
    if (item?.open_in_new_tab || external) {
      window.open(href, '_blank', 'noopener,noreferrer');
      return;
    }
    navigate(href);
  };

  const handleLogout = () => {
    trackDealerEvent('dealer_logout_click', { route: location.pathname });
    logout();
    navigate('/dealer/login');
  };

  const isFavoriteQuickMenuItem = (key) => (quickMenuFavorites || []).includes(key);

  const toggleQuickMenuFavorite = (key) => {
    if (!key) return;
    setQuickMenuFavorites((prev) => {
      if ((prev || []).includes(key)) {
        return (prev || []).filter((row) => row !== key);
      }
      return [key, ...(prev || [])].slice(0, 30);
    });
  };

  const renderContextSidebarNode = (item, depth = 0) => {
    const Icon = iconMap[item.icon] || ChevronRight;
    const isActive = isMenuNodeActive(item, location.pathname, location.search);
    const hasChildren = Array.isArray(item.children) && item.children.length > 0;
    const depthPadding = depth === 0 ? 'pl-0' : depth === 1 ? 'pl-3' : 'pl-6';
    return (
      <div key={item.key} className={depthPadding} data-testid={`dealer-layout-v2-row4-context-node-${item.key}`}>
        <button
          type="button"
          onClick={() => {
            if (item.route) {
              navigate(item.route);
              handleNavClick(item, 'row4-context-submenu');
            }
          }}
          className={`flex w-full items-center gap-2 rounded-md px-2.5 py-1.5 text-left text-sm transition ${isActive ? 'bg-slate-900 text-white' : 'text-slate-800 hover:bg-slate-100'}`}
          data-testid={`dealer-layout-v2-row4-context-link-${item.key}`}
        >
          <Icon size={14} />
          <span data-testid={`dealer-layout-v2-row4-context-label-${item.key}`}>{item.label}</span>
        </button>
        {hasChildren ? (
          <div className="mt-1 space-y-1" data-testid={`dealer-layout-v2-row4-context-children-${item.key}`}>
            {item.children.map((child) => renderContextSidebarNode(child, depth + 1))}
          </div>
        ) : null}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-white text-black" data-testid="dealer-layout-v2-root">
      <header className="border-b border-slate-200 bg-white" data-testid="dealer-layout-v2-header">
        <div className="mx-auto flex w-full max-w-[1440px] flex-col px-4 lg:px-6" data-testid="dealer-layout-v2-header-rows">
          <div className="flex flex-wrap items-center gap-3 py-3" data-testid="dealer-layout-v2-row1">
            {showRow1Logo ? (
              <button
                type="button"
                onClick={() => navigate('/')}
                className="inline-flex h-11 min-w-[132px] items-center justify-center rounded-md bg-yellow-400 px-3"
                data-testid="dealer-layout-v2-brand-button"
              >
                {corporateLogoUrl ? (
                  <img src={corporateLogoUrl} alt="Kurumsal Logo" className="h-8 w-28 object-contain" data-testid="dealer-layout-v2-brand-image" />
                ) : (
                  <span className="text-sm font-bold text-slate-900" data-testid="dealer-layout-v2-brand-fallback">{t('dealer.layout.brand_fallback', 'S Ofisim')}</span>
                )}
              </button>
            ) : null}

            <form
              className="min-w-[220px] flex-1"
              onSubmit={(event) => {
                event.preventDefault();
                const q = searchTerm.trim();
                navigate(q ? `/dealer/listings?q=${encodeURIComponent(q)}` : '/dealer/listings');
              }}
              data-testid="dealer-layout-v2-search-form"
            >
              <label className="relative block" data-testid="dealer-layout-v2-search-wrap">
                <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  value={searchTerm}
                  onChange={(event) => setSearchTerm(event.target.value)}
                  placeholder={t('dealer.layout.search_placeholder', 'İlan, müşteri veya rapor ara')}
                  className="h-11 w-full rounded-md border border-slate-200 pl-9 pr-3 text-sm text-slate-900"
                  data-testid="dealer-layout-v2-search-input"
                />
              </label>
            </form>

            <div className="ml-auto flex items-center gap-2" data-testid="dealer-layout-v2-row1-actions">
              {corporateDynamicLinks.length > 0 ? (
                <div className="hidden items-center gap-2 xl:flex" data-testid="dealer-layout-v2-row1-dynamic-links">
                  {corporateDynamicLinks.map((item, index) => (
                    <button
                      key={`${item.id || item.label}-${index}`}
                      type="button"
                      onClick={() => handleCorporateDynamicLink(item)}
                      className={`rounded-md border px-3 py-1.5 text-xs font-semibold ${item.style === 'solid' ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-100'}`}
                      data-testid={`dealer-layout-v2-row1-dynamic-link-${index}`}
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
              ) : null}

              {showRow1QuickActions ? row1Actions.slice(0, 2).map((item) => {
                const Icon = iconMap[item.icon] || LayoutDashboard;
                return (
                  <NavLink
                    key={item.id}
                    to={item.route}
                    className="inline-flex h-10 items-center gap-2 rounded-md border border-slate-200 px-3 text-sm font-semibold text-slate-700"
                    onClick={() => handleNavClick(item, 'row1-quick-action')}
                    data-testid={`dealer-layout-v2-row1-quick-action-${item.key}`}
                  >
                    <Icon size={15} />
                    <span>{item.label_i18n_key?.includes('message') ? t('dealer.layout.quick_action_messages', 'Mesajlar') : t('dealer.layout.quick_action_shortcut', 'Kısayol')}</span>
                  </NavLink>
                );
              }) : null}

              <button
                type="button"
                className="relative inline-flex h-10 w-10 items-center justify-center rounded-md border border-slate-200"
                onClick={() => navigate('/dealer/messages')}
                data-testid="dealer-layout-v2-row1-message-button"
              >
                <MessageCircle size={16} />
                {(navSummary?.badges?.unread_messages || 0) > 0 ? (
                  <span className="absolute -right-1 -top-1 inline-flex h-4 min-w-[16px] items-center justify-center rounded-full bg-rose-500 px-1 text-[10px] font-bold text-white" data-testid="dealer-layout-v2-row1-message-badge">
                    {navSummary.badges.unread_messages}
                  </span>
                ) : null}
              </button>

              <button
                type="button"
                className="relative inline-flex h-10 w-10 items-center justify-center rounded-md border border-slate-200"
                onClick={() => navigate('/dealer/messages')}
                data-testid="dealer-layout-v2-row1-announcement-icon-button"
              >
                <Bell size={16} />
                {(navSummary?.badges?.announcements_total || 0) > 0 ? (
                  <span className="absolute -right-1 -top-1 inline-flex h-4 min-w-[16px] items-center justify-center rounded-full bg-rose-500 px-1 text-[10px] font-bold text-white" data-testid="dealer-layout-v2-row1-announcement-icon-badge">
                    {navSummary.badges.announcements_total}
                  </span>
                ) : null}
              </button>

              <button
                type="button"
                onClick={() => navigate('/dealer/listings?create=1')}
                className="h-11 rounded-md bg-blue-600 px-4 text-sm font-semibold text-white"
                data-testid="dealer-layout-v2-row1-create-listing-button"
              >
                {t('dealer.layout.create_listing', 'İlan Ver')}
              </button>

              {showRow1Language ? (
                <div className="flex items-center gap-1 rounded-md bg-slate-100 p-1" data-testid="dealer-layout-v2-language-toggle">
                  {languageOptions.map((option) => (
                    <button
                      key={option.key}
                      type="button"
                      onClick={() => setLanguage(option.key)}
                      className={`rounded px-2 py-1 text-xs font-semibold ${language === option.key ? 'bg-white text-slate-900' : 'text-slate-500'}`}
                      data-testid={`dealer-layout-v2-language-${option.key}`}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              ) : null}
            </div>

          </div>

          <div className="relative border-t border-slate-200 py-2" data-testid="dealer-layout-v2-row2">
            <nav className="flex min-w-0 items-center gap-2 overflow-x-auto" data-testid="dealer-layout-v2-row2-top-menu">
              {topMenuItems.map((item) => {
                const Icon = iconMap[item.icon] || LayoutDashboard;
                const hasChildren = Array.isArray(item.children) && item.children.length > 0;
                const isActive = activeTopMenu?.key === item.key;
                const isOpen = openMenuKey === item.key;
                const badge = topMenuBadges[item.key];

                return (
                  <button
                    key={item.key}
                    type="button"
                    onClick={() => {
                      setOpenMenuKey(item.key);
                      if (item.route) {
                        navigate(item.route);
                        handleNavClick(item, 'row2-top-menu');
                      }
                    }}
                    className={`inline-flex shrink-0 items-center gap-2 rounded-md border px-3 py-2 text-sm font-semibold transition ${isActive || isOpen ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-200 text-slate-900 hover:bg-slate-100'}`}
                    data-testid={`dealer-layout-v2-row2-top-menu-item-${item.key}`}
                  >
                    <Icon size={15} />
                    <span data-testid={`dealer-layout-v2-row2-top-menu-label-${item.key}`}>{item.label}</span>
                    {typeof badge === 'number' && badge > 0 ? (
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${isActive || isOpen ? 'bg-white/20 text-white' : 'bg-slate-200 text-slate-700'}`} data-testid={`dealer-layout-v2-row2-top-menu-badge-${item.key}`}>
                        {badge}
                      </span>
                    ) : null}
                    {hasChildren ? (isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />) : null}
                  </button>
                );
              })}
            </nav>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 py-2" data-testid="dealer-layout-v2-row3">
            {showRow3UserMenu ? (
              <div className="relative flex min-w-[220px] items-center gap-2" data-testid="dealer-layout-v2-row3-user-block">
                <button
                  type="button"
                  onClick={() => setUserMenuOpen((prev) => !prev)}
                  className="inline-flex items-center gap-2 rounded-md border border-slate-200 bg-white px-2 py-1.5"
                  data-testid="dealer-layout-v2-row3-user-button"
                >
                  <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-slate-900 text-xs font-semibold text-white" data-testid="dealer-layout-v2-row3-user-avatar">{userInitials}</span>
                  <span className="text-left" data-testid="dealer-layout-v2-row3-user-content">
                    <span className="block text-sm font-semibold text-slate-900" data-testid="dealer-layout-v2-row3-user-name">{userDisplayName}</span>
                    <span className="block text-xs text-slate-500" data-testid="dealer-layout-v2-row3-user-rating">★★★★★ (0)</span>
                  </span>
                  {userMenuOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                </button>

                {userMenuOpen ? (
                  <div className="absolute left-0 top-11 z-30 min-w-[220px] rounded-xl border border-slate-200 bg-white p-2 shadow-lg" data-testid="dealer-layout-v2-row3-user-dropdown">
                    <button type="button" onClick={() => navigate('/dealer/settings?section=profile')} className="w-full rounded-md px-3 py-2 text-left text-sm text-slate-700 hover:bg-slate-100" data-testid="dealer-layout-v2-row3-user-dropdown-profile">{t('dealer.layout.profile_settings', 'Profil / Ayarlar')}</button>
                    <button type="button" onClick={handleLogout} className="mt-1 w-full rounded-md px-3 py-2 text-left text-sm text-rose-600 hover:bg-rose-50" data-testid="dealer-layout-v2-row3-user-dropdown-logout">{t('dealer.layout.logout', 'Çıkış Yap')}</button>
                  </div>
                ) : null}
              </div>
            ) : <div data-testid="dealer-layout-v2-row3-user-block-empty" />}

            <div className="ml-auto flex flex-wrap items-center gap-2" data-testid="dealer-layout-v2-row3-actions">
              {showRow3StoreFilter ? (
                <div className="relative flex items-center gap-2" data-testid="dealer-layout-v2-row3-store-filter-wrap">
                  <span className="text-xs font-semibold text-slate-600" data-testid="dealer-layout-v2-row3-store-filter-label">{t('dealer.layout.store_filter', 'Mağaza Filtresi')}</span>
                  <button
                    type="button"
                    onClick={() => setStoreMenuOpen((prev) => !prev)}
                    className="inline-flex h-9 min-w-[180px] items-center justify-between gap-2 rounded-md border border-slate-200 bg-white px-3 text-sm"
                    data-testid="dealer-layout-v2-row3-store-filter-button"
                  >
                    <span data-testid="dealer-layout-v2-row3-store-filter-selected">{row3Stores.find((store) => store.key === selectedStore)?.label || t('dealer.layout.all_stores', 'Tümü')}</span>
                    {storeMenuOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                  </button>

                  {storeMenuOpen ? (
                    <div className="absolute right-0 top-10 z-20 min-w-[220px] rounded-lg border border-slate-200 bg-white p-1 shadow-lg" data-testid="dealer-layout-v2-row3-store-filter-dropdown">
                      {row3Stores.map((store) => (
                        <button
                          key={store.key}
                          type="button"
                          onClick={() => {
                            setSelectedStore(store.key);
                            setStoreMenuOpen(false);
                            trackDealerEvent('dealer_header_store_filter_change', { store_key: store.key });
                          }}
                          className={`w-full rounded-md px-3 py-2 text-left text-sm ${selectedStore === store.key ? 'bg-slate-900 text-white' : 'text-slate-800 hover:bg-slate-100'}`}
                          data-testid={`dealer-layout-v2-row3-store-filter-option-${store.key}`}
                        >
                          {store.label}
                        </button>
                      ))}
                    </div>
                  ) : null}
                </div>
              ) : null}

              <button
                type="button"
                onClick={() => {
                  setIsPageEditMode((prev) => !prev);
                  navigate('/dealer/overview');
                }}
                className={`h-9 rounded-md border px-3 text-sm font-semibold ${isPageEditMode ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-300 bg-white text-slate-900'}`}
                data-testid="dealer-layout-v2-row3-page-edit-button"
              >
                {isPageEditMode ? t('dealer.layout.finish_edit', 'Düzenlemeyi Bitir') : t('dealer.layout.edit_page', 'Sayfayı Düzenle')}
              </button>

              <button
                type="button"
                onClick={() => navigate('/dealer/messages')}
                className="relative h-9 rounded-md border border-slate-300 bg-white px-3 text-sm font-semibold text-slate-900"
                data-testid="dealer-layout-v2-row3-announcements-button"
              >
                {t('dealer.layout.announcements', 'Duyurular')}
                {(navSummary?.badges?.announcements_total || 0) > 0 ? (
                  <span className="absolute -right-1 -top-1 inline-flex h-4 min-w-[16px] items-center justify-center rounded-full bg-rose-500 px-1 text-[10px] font-bold text-white" data-testid="dealer-layout-v2-row3-announcements-badge">
                    {navSummary.badges.announcements_total}
                  </span>
                ) : null}
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto grid w-full max-w-[1440px] grid-cols-1 gap-4 px-4 py-6 lg:grid-cols-[260px_minmax(0,1fr)] lg:px-6" data-testid="dealer-layout-v2-row4-main">
        <aside className="rounded-2xl border border-slate-200 bg-white p-3" data-testid="dealer-layout-v2-row4-sidebar">
          <div className="mb-3 rounded-xl border border-slate-200 bg-slate-50 p-2" data-testid="dealer-layout-v2-row4-quick-menu-wrap">
            <div className="mb-2 flex items-center justify-between gap-2" data-testid="dealer-layout-v2-row4-quick-menu-header">
              <div className="text-xs font-semibold text-slate-700" data-testid="dealer-layout-v2-row4-quick-menu-title">{t('dealer.layout.quick_menu_title', 'Kişisel Hızlı Menü')}</div>
              <button
                type="button"
                onClick={() => setQuickMenuEditOpen((prev) => !prev)}
                className={`inline-flex items-center gap-1 rounded border px-2 py-1 text-[11px] font-semibold ${quickMenuEditOpen ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-300 bg-white text-slate-700'}`}
                data-testid="dealer-layout-v2-row4-quick-menu-edit-toggle"
              >
                <Pencil size={11} />
                {quickMenuEditOpen ? t('dealer.layout.quick_menu_close', 'Kapat') : t('dealer.layout.quick_menu_edit', 'Düzenle')}
              </button>
            </div>

            <div className="mb-2 flex items-center gap-1" data-testid="dealer-layout-v2-row4-quick-menu-tabs">
              <button
                type="button"
                onClick={() => setQuickMenuTab('recent')}
                className={`rounded-full border px-2.5 py-1 text-[11px] font-semibold ${quickMenuTab === 'recent' ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-300 bg-white text-slate-700'}`}
                data-testid="dealer-layout-v2-row4-quick-menu-tab-recent"
              >
                {t('dealer.layout.quick_menu_recent', 'Son Kullanılanlar')}
              </button>
              <button
                type="button"
                onClick={() => setQuickMenuTab('favorites')}
                className={`rounded-full border px-2.5 py-1 text-[11px] font-semibold ${quickMenuTab === 'favorites' ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-300 bg-white text-slate-700'}`}
                data-testid="dealer-layout-v2-row4-quick-menu-tab-favorites"
              >
                {t('dealer.layout.quick_menu_favorites', 'Favorilerim')}
              </button>
            </div>

            <div className="space-y-1" data-testid="dealer-layout-v2-row4-quick-menu-list">
              {quickMenuItems.length === 0 ? (
                <div className="rounded border border-dashed border-slate-300 bg-white px-2.5 py-2 text-[11px] text-slate-600" data-testid="dealer-layout-v2-row4-quick-menu-empty">
                  {t('dealer.layout.quick_menu_empty', 'Bu sekmede öğe yok. Düzenle ile favori ekleyebilirsiniz.')}
                </div>
              ) : quickMenuItems.map((item) => {
                const Icon = iconMap[item.icon] || ChevronRight;
                const isActive = isRouteActive(item.route, location.pathname, location.search);
                const isFavorite = isFavoriteQuickMenuItem(item.key);
                return (
                  <div key={item.key} className="flex items-center gap-1" data-testid={`dealer-layout-v2-row4-quick-menu-row-${item.key}`}>
                    <button
                      type="button"
                      onClick={() => {
                        if (item.parentKey) setOpenMenuKey(item.parentKey);
                        navigate(item.route);
                        handleNavClick(item, 'row4-quick-menu');
                      }}
                      className={`flex min-w-0 flex-1 items-center gap-2 rounded-md border px-2.5 py-1.5 text-left text-xs font-semibold transition ${isActive ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-200 bg-white text-slate-800 hover:bg-slate-100'}`}
                      data-testid={`dealer-layout-v2-row4-quick-menu-item-${item.key}`}
                    >
                      <Icon size={13} />
                      <span className="truncate" data-testid={`dealer-layout-v2-row4-quick-menu-label-${item.key}`}>{item.label}</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => toggleQuickMenuFavorite(item.key)}
                      className={`inline-flex h-7 w-7 shrink-0 items-center justify-center rounded border ${isFavorite ? 'border-amber-300 bg-amber-50 text-amber-700' : 'border-slate-300 bg-white text-slate-600'}`}
                      data-testid={`dealer-layout-v2-row4-quick-menu-favorite-toggle-${item.key}`}
                    >
                      {isFavorite ? <Star size={12} /> : <StarOff size={12} />}
                    </button>
                  </div>
                );
              })}
            </div>

            {quickMenuEditOpen ? (
              <div className="mt-2 rounded border border-slate-200 bg-white p-2" data-testid="dealer-layout-v2-row4-quick-menu-edit-panel">
                <input
                  value={quickMenuSearch}
                  onChange={(event) => setQuickMenuSearch(event.target.value)}
                  placeholder={t('dealer.layout.quick_menu_search_placeholder', 'Menü ara...')}
                  className="h-8 w-full rounded border border-slate-300 px-2 text-xs"
                  data-testid="dealer-layout-v2-row4-quick-menu-edit-search"
                />
                <div className="mt-2 max-h-44 space-y-1 overflow-auto" data-testid="dealer-layout-v2-row4-quick-menu-edit-list">
                  {quickMenuManageItems.map((item) => {
                    const isFavorite = isFavoriteQuickMenuItem(item.key);
                    return (
                      <button
                        key={item.key}
                        type="button"
                        onClick={() => toggleQuickMenuFavorite(item.key)}
                        className={`flex w-full items-center justify-between rounded border px-2 py-1 text-left text-[11px] ${isFavorite ? 'border-amber-300 bg-amber-50 text-amber-800' : 'border-slate-200 bg-white text-slate-700'}`}
                        data-testid={`dealer-layout-v2-row4-quick-menu-edit-item-${item.key}`}
                      >
                        <span className="truncate">
                          {item.label}
                          <span className="ml-1 text-[10px] text-slate-500">({item.parentKey})</span>
                        </span>
                        {isFavorite ? <Star size={11} /> : <StarOff size={11} />}
                      </button>
                    );
                  })}
                </div>
              </div>
            ) : null}
            </div>

          <div className="mb-3 border-b border-slate-100 pb-2" data-testid="dealer-layout-v2-row4-sidebar-header">
            <div className="text-sm font-semibold text-slate-900" data-testid="dealer-layout-v2-row4-sidebar-title">
              {row4MenuRoot?.label || t('dealer.layout.menu_fallback_title', 'Menü')}
            </div>
            <div className="text-xs text-slate-500" data-testid="dealer-layout-v2-row4-sidebar-subtitle">{t('dealer.layout.menu_subtitle', '2. satırdan seçilen menünün alt kırılımları')}</div>
          </div>

          {loading ? <div className="mb-2 text-xs text-slate-500" data-testid="dealer-layout-v2-config-loading">{t('dealer.layout.menu_loading', 'Menü yükleniyor…')}</div> : null}
          {error ? <div className="mb-2 text-xs text-rose-700" data-testid="dealer-layout-v2-config-error">{error}</div> : null}

          <div className="space-y-1" data-testid="dealer-layout-v2-row4-sidebar-links">
            {row4MenuRoot ? (
              <button
                type="button"
                onClick={() => {
                  if (row4MenuRoot.route) {
                    navigate(row4MenuRoot.route);
                    handleNavClick(row4MenuRoot, 'row4-context-root');
                  }
                }}
                className={`flex w-full items-center justify-between rounded-md border px-2.5 py-2 text-sm font-semibold transition ${isRouteActive(row4MenuRoot.route, location.pathname, location.search) ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-200 text-slate-900 hover:bg-slate-100'}`}
                data-testid={`dealer-layout-v2-row4-sidebar-root-link-${row4MenuRoot.key}`}
              >
                <span className="inline-flex items-center gap-2">
                  {(iconMap[row4MenuRoot.icon] ? React.createElement(iconMap[row4MenuRoot.icon], { size: 14 }) : <ChevronRight size={14} />)}
                  <span data-testid={`dealer-layout-v2-row4-sidebar-root-label-${row4MenuRoot.key}`}>{row4MenuRoot.label}</span>
                </span>
                {typeof topMenuBadges[row4MenuRoot.key] === 'number' && topMenuBadges[row4MenuRoot.key] > 0 ? (
                  <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-bold text-slate-700" data-testid={`dealer-layout-v2-row4-sidebar-root-badge-${row4MenuRoot.key}`}>
                    {topMenuBadges[row4MenuRoot.key]}
                  </span>
                ) : null}
              </button>
            ) : null}

            {row4MenuRoot?.children?.length ? (
              <div className="space-y-1 pt-1" data-testid={`dealer-layout-v2-row4-sidebar-context-list-${row4MenuRoot.key}`}>
                {row4MenuRoot.children.map((child) => renderContextSidebarNode(child, 1))}
              </div>
            ) : null}

            <button
              type="button"
              onClick={handleLogout}
              className="mt-1 flex w-full items-center gap-2 rounded-md border border-rose-200 px-2.5 py-2 text-sm font-semibold text-rose-600 hover:bg-rose-50"
              data-testid="dealer-layout-v2-row4-sidebar-logout-button"
            >
              <LogOut size={14} />
              {t('dealer.layout.logout', 'Çıkış Yap')}
            </button>
          </div>
        </aside>

        <section className="min-w-0 rounded-2xl border border-slate-200 bg-white p-5" data-testid="dealer-layout-v2-row4-content">
          <Outlet />
        </section>
      </main>

      <div data-testid="dealer-layout-v2-row5-footer">
        <SiteFooter />
      </div>
    </div>
  );
}
