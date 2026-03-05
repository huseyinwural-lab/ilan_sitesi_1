import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const PAGE_TYPE_OPTIONS = [
  { value: 'home', label: 'Ana Sayfa (home)' },
  { value: 'search_l1', label: 'Kategori L1 (search_l1)' },
  { value: 'search_l2', label: 'Kategori L2 (search_l2)' },
  { value: 'listing_create_stepX', label: 'İlan Ver (listing_create_stepX)' },
];

const DEFAULT_COMPONENT_LIBRARY = [
  {
    key: 'home.default-content',
    name: 'Home Varsayılan İçerik',
    schema_json: { type: 'object', properties: {}, additionalProperties: false },
  },
  {
    key: 'search.l1.default-content',
    name: 'Search L1 Varsayılan İçerik',
    schema_json: { type: 'object', properties: {}, additionalProperties: false },
  },
  {
    key: 'search.l2.default-content',
    name: 'Search L2 Varsayılan İçerik',
    schema_json: { type: 'object', properties: {}, additionalProperties: false },
  },
  {
    key: 'listing.create.default-content',
    name: 'İlan Ver Varsayılan İçerik',
    schema_json: { type: 'object', properties: {}, additionalProperties: false },
  },
  {
    key: 'shared.text-block',
    name: 'Metin Bloğu',
    schema_json: {
      type: 'object',
      properties: {
        title: { type: 'string', title: 'Başlık' },
        body: { type: 'string', title: 'Metin' },
      },
      additionalProperties: false,
    },
  },
  {
    key: 'shared.ad-slot',
    name: 'Reklam Slotu',
    schema_json: {
      type: 'object',
      properties: {
        placement: {
          type: 'string',
          title: 'Placement',
          enum: ['AD_HOME_TOP', 'AD_SEARCH_TOP', 'AD_LOGIN_1'],
        },
      },
      additionalProperties: false,
    },
  },
  {
    key: 'layout.breadcrumb-header',
    name: 'Breadcrumb Header',
    schema_json: {
      type: 'object',
      properties: {
        separator: { type: 'string', title: 'Ayırıcı' },
        show_home: { type: 'boolean', title: 'Ana Sayfa Göster' },
        max_depth: { type: 'integer', title: 'Maksimum Derinlik' },
      },
      additionalProperties: false,
    },
    default_props: {
      separator: ' > ',
      show_home: true,
      max_depth: 8,
    },
  },
  {
    key: 'layout.sticky-action-bar',
    name: 'Sticky Action Bar',
    schema_json: {
      type: 'object',
      properties: {
        position: { type: 'string', title: 'Pozisyon', enum: ['bottom', 'right'] },
        primary_label: { type: 'string', title: 'Birincil Buton Metni' },
        secondary_label: { type: 'string', title: 'İkincil Buton Metni' },
        phone_number: { type: 'string', title: 'Telefon Numarası' },
      },
      additionalProperties: false,
    },
    default_props: {
      position: 'bottom',
      primary_label: 'Hemen Ara',
      secondary_label: 'Mesaj Gönder',
      phone_number: '',
    },
  },
  {
    key: 'layout.category-navigator-side',
    name: 'Category Navigator (Side)',
    schema_json: {
      type: 'object',
      properties: {
        title: { type: 'string', title: 'Başlık' },
        show_counts: { type: 'boolean', title: 'İlan Sayıları Göster' },
        max_levels: { type: 'integer', title: 'Maksimum Seviye' },
      },
      additionalProperties: false,
    },
    default_props: {
      title: 'Kategoriler',
      show_counts: true,
      max_levels: 6,
    },
  },
  {
    key: 'layout.category-navigator-top',
    name: 'Category Navigator (Top)',
    schema_json: {
      type: 'object',
      properties: {
        title: { type: 'string', title: 'Başlık' },
        show_counts: { type: 'boolean', title: 'İlan Sayıları Göster' },
        max_levels: { type: 'integer', title: 'Maksimum Seviye' },
      },
      additionalProperties: false,
    },
    default_props: {
      title: 'Kırılımlar',
      show_counts: true,
      max_levels: 6,
    },
  },
  {
    key: 'media.advanced-photo-gallery',
    name: 'Advanced Photo Gallery',
    schema_json: {
      type: 'object',
      properties: {
        enable_fullscreen: { type: 'boolean', title: 'Fullscreen' },
        enable_zoom: { type: 'boolean', title: 'Zoom' },
        show_thumbnails: { type: 'boolean', title: 'Küçük Görseller' },
      },
      additionalProperties: false,
    },
    default_props: {
      enable_fullscreen: true,
      enable_zoom: true,
      show_thumbnails: true,
    },
  },
  {
    key: 'media.auto-play-carousel-hero',
    name: 'Auto-Play Carousel (Hero Banner)',
    schema_json: {
      type: 'object',
      properties: {
        auto_play_seconds: { type: 'integer', title: 'Otomatik Dönüş (sn)' },
        show_overlay_text: { type: 'boolean', title: 'Üst Yazı Göster' },
        cta_label: { type: 'string', title: 'CTA Metni' },
      },
      additionalProperties: false,
    },
    default_props: {
      auto_play_seconds: 5,
      show_overlay_text: true,
      cta_label: 'Detayları İncele',
    },
  },
  {
    key: 'media.video-3d-tour-player',
    name: 'Video / 3D Tour Player',
    schema_json: {
      type: 'object',
      properties: {
        provider: { type: 'string', title: 'Sağlayıcı', enum: ['youtube', 'vimeo', 'tour360', 'custom_url'] },
        source_url: { type: 'string', title: 'Kaynak URL' },
        auto_play: { type: 'boolean', title: 'Otomatik Oynat' },
      },
      additionalProperties: false,
    },
    default_props: {
      provider: 'youtube',
      source_url: '',
      auto_play: false,
    },
  },
  {
    key: 'media.ad-promo-slot',
    name: 'Ad / Promo Slot',
    schema_json: {
      type: 'object',
      properties: {
        placement: { type: 'string', title: 'Placement', enum: ['AD_HOME_TOP', 'AD_SEARCH_TOP', 'AD_LOGIN_1'] },
        campaign_label: { type: 'string', title: 'Kampanya Etiketi' },
      },
      additionalProperties: false,
    },
    default_props: {
      placement: 'AD_HOME_TOP',
      campaign_label: 'Kampanya',
    },
  },
  {
    key: 'data.price-title-block',
    name: 'Price & Title Block',
    schema_json: {
      type: 'object',
      properties: {
        show_currency_switcher: { type: 'boolean', title: 'Kur Çevirici' },
        show_favorite_button: { type: 'boolean', title: 'Favori Butonu' },
        show_location: { type: 'boolean', title: 'Konum Göster' },
      },
      additionalProperties: false,
    },
    default_props: {
      show_currency_switcher: true,
      show_favorite_button: true,
      show_location: true,
    },
  },
  {
    key: 'data.attribute-grid-dynamic',
    name: 'Attribute Grid (Dynamic)',
    schema_json: {
      type: 'object',
      properties: {
        include_modules: {
          type: 'array',
          title: 'Modül Grupları',
          items: { type: 'string' },
        },
        compact_mode: { type: 'boolean', title: 'Kompakt Mod' },
      },
      additionalProperties: false,
    },
    default_props: {
      include_modules: ['core_fields', 'parameter_fields', 'detail_groups', 'address', 'photo', 'contact', 'payment', 'preview'],
      compact_mode: false,
    },
  },
  {
    key: 'data.description-text-area',
    name: 'Description Text Area',
    schema_json: {
      type: 'object',
      properties: {
        rich_text_enabled: { type: 'boolean', title: 'Zengin Metin' },
        max_length: { type: 'integer', title: 'Maksimum Uzunluk' },
      },
      additionalProperties: false,
    },
    default_props: {
      rich_text_enabled: true,
      max_length: 5000,
    },
  },
  {
    key: 'data.seller-card',
    name: 'Seller Card',
    schema_json: {
      type: 'object',
      properties: {
        show_rating: { type: 'boolean', title: 'Puan Göster' },
        show_membership: { type: 'boolean', title: 'Üyelik Bilgisi' },
        show_all_listings_link: { type: 'boolean', title: 'Tüm İlanları Linki' },
      },
      additionalProperties: false,
    },
    default_props: {
      show_rating: true,
      show_membership: true,
      show_all_listings_link: true,
    },
  },
  {
    key: 'interactive.interactive-map',
    name: 'Interactive Map',
    schema_json: {
      type: 'object',
      properties: {
        default_zoom: { type: 'integer', title: 'Varsayılan Zoom' },
        show_nearby_layers: { type: 'boolean', title: 'Yakındakiler Katmanı' },
        map_style: { type: 'string', title: 'Harita Stili', enum: ['standard', 'satellite'] },
      },
      additionalProperties: false,
    },
    default_props: {
      default_zoom: 14,
      show_nearby_layers: true,
      map_style: 'standard',
    },
  },
  {
    key: 'interactive.mortgage-loan-calculator',
    name: 'Mortgage / Loan Calculator',
    schema_json: {
      type: 'object',
      properties: {
        currency: { type: 'string', title: 'Para Birimi', enum: ['TRY', 'EUR', 'USD'] },
        default_months: { type: 'integer', title: 'Varsayılan Vade (Ay)' },
        show_interest_table: { type: 'boolean', title: 'Faiz Tablosu' },
      },
      additionalProperties: false,
    },
    default_props: {
      currency: 'TRY',
      default_months: 120,
      show_interest_table: true,
    },
  },
  {
    key: 'interactive.similar-listings-slider',
    name: 'Similar Listings Slider',
    schema_json: {
      type: 'object',
      properties: {
        source: { type: 'string', title: 'Kaynak', enum: ['similar', 'seller_other'] },
        max_items: { type: 'integer', title: 'Maksimum Kart' },
        auto_scroll: { type: 'boolean', title: 'Otomatik Kaydırma' },
      },
      additionalProperties: false,
    },
    default_props: {
      source: 'similar',
      max_items: 12,
      auto_scroll: false,
    },
  },
  {
    key: 'interactive.doping-selector',
    name: 'Doping Selector (İlan Ver)',
    schema_json: {
      type: 'object',
      properties: {
        available_dopings: { type: 'array', title: 'Doping Paketleri', items: { type: 'string' } },
        show_prices: { type: 'boolean', title: 'Fiyatları Göster' },
        default_selected: { type: 'string', title: 'Varsayılan Seçim' },
      },
      additionalProperties: false,
    },
    default_props: {
      available_dopings: ['Vitrin', 'Acil', 'Anasayfa'],
      show_prices: true,
      default_selected: 'Vitrin',
    },
  },
];

const LIBRARY_GROUP_DEFINITIONS = [
  { id: 'core', label: 'Temel Builder Bileşenleri' },
  { id: 'navigation', label: 'Navigasyon ve Yapı Bileşenleri' },
  { id: 'media', label: 'Medya ve Tanıtım Bileşenleri' },
  { id: 'data', label: 'Bilgi ve Veri Bileşenleri' },
  { id: 'interactive', label: 'Etkileşim ve Fonksiyonel Bileşenler' },
  { id: 'menu', label: 'Menü Snapshot Bileşenleri' },
  { id: 'other', label: 'Diğer' },
];

const resolveLibraryGroupByKey = (componentKey) => {
  const key = String(componentKey || '');
  if (key.startsWith('menu.snapshot.')) return 'menu';
  if (key.startsWith('layout.')) return 'navigation';
  if (key.startsWith('media.')) return 'media';
  if (key.startsWith('data.')) return 'data';
  if (key.startsWith('interactive.')) return 'interactive';
  if (key.startsWith('home.') || key.startsWith('search.') || key.startsWith('listing.create.') || key.startsWith('shared.')) return 'core';
  return 'other';
};

const getDefaultComponentKey = (pageType) => {
  if (pageType === 'home') return 'home.default-content';
  if (pageType === 'search_l1') return 'search.l1.default-content';
  if (pageType === 'search_l2') return 'search.l2.default-content';
  if (pageType === 'listing_create_stepX') return 'listing.create.default-content';
  return 'shared.text-block';
};

const createEmptyPayload = (pageType) => ({
  rows: [
    {
      id: `row-${Date.now()}`,
      columns: [
        {
          id: `col-${Date.now()}`,
          width: { desktop: 12, tablet: 12, mobile: 12 },
          components: [
            {
              id: `cmp-${Date.now()}`,
              key: getDefaultComponentKey(pageType),
              props: pageType === 'home' || pageType === 'listing_create_stepX' ? {} : { note: 'Varsayılan içerik bloğu' },
              visibility: { desktop: true, tablet: true, mobile: true },
            },
          ],
        },
      ],
    },
  ],
});

const deepClone = (value) => JSON.parse(JSON.stringify(value));

const normalizePayload = (rawPayload, pageType) => {
  if (!rawPayload || typeof rawPayload !== 'object' || !Array.isArray(rawPayload.rows)) {
    return createEmptyPayload(pageType);
  }
  return rawPayload;
};

const buildMenuComponentLibraryItems = (menuItems) => {
  const activeItems = Array.isArray(menuItems)
    ? menuItems.filter((item) => item && item.active_flag !== false && item.id)
    : [];

  if (!activeItems.length) return [];

  const byParent = new Map();
  const byId = new Map(activeItems.map((item) => [item.id, item]));

  activeItems.forEach((item) => {
    const parentKey = item.parent_id || '__root__';
    if (!byParent.has(parentKey)) byParent.set(parentKey, []);
    byParent.get(parentKey).push(item);
  });

  const sortItems = (items) => [...items].sort((a, b) => {
    const aOrder = Number(a.sort_order || 0);
    const bOrder = Number(b.sort_order || 0);
    if (aOrder !== bOrder) return aOrder - bOrder;
    return String(a.label || '').localeCompare(String(b.label || ''), 'tr');
  });

  return sortItems(activeItems).map((item) => {
    const parentItem = item.parent_id ? byId.get(item.parent_id) : null;
    const submenuItems = sortItems(byParent.get(item.id) || []).map((child) => ({
      id: child.id,
      label: child.label,
      slug: child.slug || '',
      url: child.url || '',
    }));

    return {
      key: `menu.snapshot.${item.id}`,
      name: `${item.parent_id ? 'Alt Menü' : 'Menü'} • ${item.label}`,
      schema_json: {
        type: 'object',
        properties: {
          title: { type: 'string', title: 'Başlık' },
          show_children: { type: 'boolean', title: 'Alt menüleri göster' },
          style: { type: 'string', title: 'Görünüm', enum: ['list', 'chips'] },
          max_children: { type: 'integer', title: 'Maks. alt menü', minimum: 1, maximum: 20 },
        },
        additionalProperties: true,
      },
      default_props: {
        title: item.label,
        menu_label: item.label,
        menu_url: item.url || '',
        menu_slug: item.slug || '',
        menu_item_id: item.id,
        menu_parent_label: parentItem?.label || '',
        show_children: true,
        style: 'list',
        max_children: 8,
        menu_snapshot: {
          id: item.id,
          label: item.label,
          slug: item.slug || '',
          url: item.url || '',
          children: submenuItems,
        },
      },
    };
  });
};

const buildDealerPortalMenuLibraryItems = (configPayload) => {
  const navItems = Array.isArray(configPayload?.nav_items)
    ? configPayload.nav_items.filter((item) => item && item.visible !== false && item.id)
    : [];
  const moduleItems = Array.isArray(configPayload?.modules)
    ? configPayload.modules.filter((item) => item && item.visible !== false && item.id)
    : [];

  if (!navItems.length && !moduleItems.length) return [];

  const normalizeChild = (item, fallbackPrefix = 'item') => ({
    id: item.id || `${fallbackPrefix}-${item.key || item.label || 'x'}`,
    label: item.label || item.label_i18n_key || item.title_i18n_key || item.key || 'Menu',
    slug: item.slug || item.key || '',
    url: item.url || item.route || '',
  });

  const headerChildren = navItems.filter((item) => item.location === 'header').map((item) => normalizeChild(item, 'header'));
  const sidebarChildren = navItems.filter((item) => item.location === 'sidebar').map((item) => normalizeChild(item, 'sidebar'));
  const moduleChildren = moduleItems.map((item) => normalizeChild(item, 'module'));

  const rootBlocks = [
    {
      key: 'menu.snapshot.dealer.header',
      label: 'Dealer Header Menüsü',
      children: headerChildren,
    },
    {
      key: 'menu.snapshot.dealer.sidebar',
      label: 'Dealer Sidebar Menüsü',
      children: sidebarChildren,
    },
    {
      key: 'menu.snapshot.dealer.modules',
      label: 'Dealer Modül Menüsü',
      children: moduleChildren,
    },
  ].filter((item) => item.children.length > 0);

  const rootComponents = rootBlocks.map((block) => ({
    key: block.key,
    name: `Menü • ${block.label}`,
    schema_json: {
      type: 'object',
      properties: {
        title: { type: 'string', title: 'Başlık' },
        show_children: { type: 'boolean', title: 'Alt menüleri göster' },
        style: { type: 'string', title: 'Görünüm', enum: ['list', 'chips'] },
        max_children: { type: 'integer', title: 'Maks. alt menü', minimum: 1, maximum: 20 },
      },
      additionalProperties: true,
    },
    default_props: {
      title: block.label,
      menu_label: block.label,
      menu_url: '',
      menu_slug: block.key,
      menu_item_id: block.key,
      show_children: true,
      style: 'list',
      max_children: 10,
      menu_snapshot: {
        id: block.key,
        label: block.label,
        slug: block.key,
        url: '',
        children: block.children,
      },
    },
  }));

  const rowComponents = navItems.map((item) => {
    const label = item.label || item.label_i18n_key || item.key || 'Menu';
    return {
      key: `menu.snapshot.dealer.nav.${item.id}`,
      name: `Alt Menü • ${label}`,
      schema_json: {
        type: 'object',
        properties: {
          title: { type: 'string', title: 'Başlık' },
          show_children: { type: 'boolean', title: 'Alt menüleri göster' },
          style: { type: 'string', title: 'Görünüm', enum: ['list', 'chips'] },
          max_children: { type: 'integer', title: 'Maks. alt menü', minimum: 1, maximum: 20 },
        },
        additionalProperties: true,
      },
      default_props: {
        title: label,
        menu_label: label,
        menu_url: item.route || '',
        menu_slug: item.key || '',
        menu_item_id: item.id,
        menu_parent_label: item.location || '',
        show_children: true,
        style: 'list',
        max_children: 8,
        menu_snapshot: {
          id: item.id,
          label,
          slug: item.key || '',
          url: item.route || '',
          children: [],
        },
      },
    };
  });

  return [...rootComponents, ...rowComponents];
};

const buildTopMenuLibraryItems = (topItems) => {
  const items = Array.isArray(topItems) ? topItems.filter((item) => item && item.id) : [];
  if (!items.length) return [];

  return items.map((item) => ({
    key: `menu.snapshot.top.${item.id}`,
    name: `Üst Menü • ${item.name || item.key || 'Menu'}`,
    schema_json: {
      type: 'object',
      properties: {
        title: { type: 'string', title: 'Başlık' },
        show_children: { type: 'boolean', title: 'Alt menüleri göster' },
        style: { type: 'string', title: 'Görünüm', enum: ['list', 'chips'] },
        max_children: { type: 'integer', title: 'Maks. alt menü', minimum: 1, maximum: 20 },
      },
      additionalProperties: true,
    },
    default_props: {
      title: item.name || item.key || 'Menü',
      menu_label: item.name || item.key || 'Menü',
      menu_url: '',
      menu_slug: item.key || '',
      menu_item_id: item.id,
      show_children: false,
      style: 'chips',
      max_children: 6,
      menu_snapshot: {
        id: item.id,
        label: item.name || item.key || 'Menü',
        slug: item.key || '',
        url: '',
        children: [],
      },
    },
  }));
};

const buildCategoryTreeOptions = (items) => {
  const byParent = new Map();
  items.forEach((item) => {
    const parentKey = item.parent_id || '__root__';
    if (!byParent.has(parentKey)) byParent.set(parentKey, []);
    byParent.get(parentKey).push(item);
  });

  const sortNodes = (nodes) => {
    return [...nodes].sort((a, b) => {
      const aOrder = Number(a.sort_order || 0);
      const bOrder = Number(b.sort_order || 0);
      if (aOrder !== bOrder) return aOrder - bOrder;
      return String(a.name || '').localeCompare(String(b.name || ''), 'tr');
    });
  };

  const flattened = [];
  const walk = (parentId, depth) => {
    const children = sortNodes(byParent.get(parentId) || []);
    children.forEach((child) => {
      flattened.push({ ...child, depth });
      walk(child.id, depth + 1);
    });
  };

  walk('__root__', 0);
  return flattened;
};

const computeLayoutDiff = (publishedPayload, draftPayload) => {
  const publishedRows = Array.isArray(publishedPayload?.rows) ? publishedPayload.rows : [];
  const draftRows = Array.isArray(draftPayload?.rows) ? draftPayload.rows : [];

  const publishedRowMap = new Map(publishedRows.map((row) => [row.id, row]));
  const draftRowMap = new Map(draftRows.map((row) => [row.id, row]));

  const changedRowIds = new Set();
  const changedColumnIds = new Set();
  const changedComponentIds = new Set();

  const allRowIds = new Set([...publishedRowMap.keys(), ...draftRowMap.keys()]);
  allRowIds.forEach((rowId) => {
    const beforeRow = publishedRowMap.get(rowId);
    const afterRow = draftRowMap.get(rowId);
    if (!beforeRow || !afterRow) {
      changedRowIds.add(rowId);
      return;
    }

    const beforeColumns = Array.isArray(beforeRow.columns) ? beforeRow.columns : [];
    const afterColumns = Array.isArray(afterRow.columns) ? afterRow.columns : [];
    const beforeColumnMap = new Map(beforeColumns.map((column) => [column.id, column]));
    const afterColumnMap = new Map(afterColumns.map((column) => [column.id, column]));
    const allColumnIds = new Set([...beforeColumnMap.keys(), ...afterColumnMap.keys()]);

    allColumnIds.forEach((columnId) => {
      const beforeColumn = beforeColumnMap.get(columnId);
      const afterColumn = afterColumnMap.get(columnId);
      if (!beforeColumn || !afterColumn) {
        changedRowIds.add(rowId);
        changedColumnIds.add(columnId);
        return;
      }

      const beforeWidth = JSON.stringify(beforeColumn.width || {});
      const afterWidth = JSON.stringify(afterColumn.width || {});
      if (beforeWidth !== afterWidth) {
        changedRowIds.add(rowId);
        changedColumnIds.add(columnId);
      }

      const beforeComponents = Array.isArray(beforeColumn.components) ? beforeColumn.components : [];
      const afterComponents = Array.isArray(afterColumn.components) ? afterColumn.components : [];
      const beforeComponentMap = new Map(beforeComponents.map((component) => [component.id, component]));
      const afterComponentMap = new Map(afterComponents.map((component) => [component.id, component]));
      const allComponentIds = new Set([...beforeComponentMap.keys(), ...afterComponentMap.keys()]);

      allComponentIds.forEach((componentId) => {
        const beforeComponent = beforeComponentMap.get(componentId);
        const afterComponent = afterComponentMap.get(componentId);
        if (!beforeComponent || !afterComponent) {
          changedRowIds.add(rowId);
          changedColumnIds.add(columnId);
          changedComponentIds.add(componentId);
          return;
        }
        const beforeSnapshot = JSON.stringify({ key: beforeComponent.key, props: beforeComponent.props || {} });
        const afterSnapshot = JSON.stringify({ key: afterComponent.key, props: afterComponent.props || {} });
        if (beforeSnapshot !== afterSnapshot) {
          changedRowIds.add(rowId);
          changedColumnIds.add(columnId);
          changedComponentIds.add(componentId);
        }
      });
    });
  });

  return {
    changedRowIds,
    changedColumnIds,
    changedComponentIds,
    summary: {
      rows: changedRowIds.size,
      columns: changedColumnIds.size,
      components: changedComponentIds.size,
    },
  };
};

export default function AdminContentBuilder() {
  const authHeaders = useMemo(
    () => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` }),
    [],
  );

  const [pageType, setPageType] = useState('home');
  const [country, setCountry] = useState('DE');
  const [moduleName, setModuleName] = useState('global');
  const [categoryId, setCategoryId] = useState('');

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');

  const [pageId, setPageId] = useState('');
  const [activeDraftId, setActiveDraftId] = useState('');
  const [revisionList, setRevisionList] = useState([]);
  const [payloadJson, setPayloadJson] = useState(createEmptyPayload('home'));

  const [bindingCategoryId, setBindingCategoryId] = useState('');
  const [bindingActiveItem, setBindingActiveItem] = useState(null);
  const [bindingLoading, setBindingLoading] = useState(false);
  const [showPreviewComparison, setShowPreviewComparison] = useState(false);
  const [previewRefreshToken, setPreviewRefreshToken] = useState(0);
  const [diffFilter, setDiffFilter] = useState('all');
  const [diffJumpCursor, setDiffJumpCursor] = useState({ row: -1, component: -1 });

  const [selectedRowId, setSelectedRowId] = useState('');
  const [selectedColumnId, setSelectedColumnId] = useState('');
  const [selectedComponentId, setSelectedComponentId] = useState('');
  const [draggingRowId, setDraggingRowId] = useState('');
  const [draggingComponentId, setDraggingComponentId] = useState('');
  const [draggingLibraryComponentKey, setDraggingLibraryComponentKey] = useState('');
  const [dragOverRowId, setDragOverRowId] = useState('');
  const [dragOverColumnId, setDragOverColumnId] = useState('');
  const [isSetupDrawerOpen, setIsSetupDrawerOpen] = useState(false);
  const [pendingFocusComponentId, setPendingFocusComponentId] = useState('');

  const [componentLibrary, setComponentLibrary] = useState(DEFAULT_COMPONENT_LIBRARY);
  const [categoryOptions, setCategoryOptions] = useState([]);
  const [categorySearch, setCategorySearch] = useState('');
  const [categoriesLoading, setCategoriesLoading] = useState(false);
  const [librarySearchQuery, setLibrarySearchQuery] = useState('');
  const [libraryGroupFilter, setLibraryGroupFilter] = useState('all');
  const [libraryMenuCategoryFilterId, setLibraryMenuCategoryFilterId] = useState('');
  const [collapsedLibraryGroups, setCollapsedLibraryGroups] = useState({});

  const [policyReport, setPolicyReport] = useState(null);
  const [policyReportLoading, setPolicyReportLoading] = useState(false);

  const previewComparisonRef = useRef(null);

  const getLibrary = useCallback(async () => {
    try {
      const [componentDefsResponse, menuItemsResponse, dealerConfigResponse, topMenuResponse] = await Promise.allSettled([
        axios.get(`${API}/admin/site/content-layout/components`, {
          headers: authHeaders,
          params: { page: 1, limit: 100, is_active: true },
        }),
        axios.get(`${API}/admin/menu-items`, {
          headers: authHeaders,
          params: { country: country.toUpperCase() },
        }),
        axios.get(`${API}/admin/dealer-portal/config`, {
          headers: authHeaders,
          params: { mode: 'draft' },
        }),
        axios.get(`${API}/menu/top-items`),
      ]);

      const fetchedItems = componentDefsResponse.status === 'fulfilled' && Array.isArray(componentDefsResponse.value.data?.items)
        ? componentDefsResponse.value.data.items
        : [];

      const menuItems = menuItemsResponse.status === 'fulfilled' && Array.isArray(menuItemsResponse.value.data?.items)
        ? menuItemsResponse.value.data.items
        : [];

      const dealerConfigPayload = dealerConfigResponse.status === 'fulfilled' && dealerConfigResponse.value?.data
        ? dealerConfigResponse.value.data
        : null;

      const topMenuItems = topMenuResponse.status === 'fulfilled' && Array.isArray(topMenuResponse.value?.data)
        ? topMenuResponse.value.data
        : [];

      const menuLibraryItems = [
        ...buildMenuComponentLibraryItems(menuItems),
        ...buildDealerPortalMenuLibraryItems(dealerConfigPayload),
        ...buildTopMenuLibraryItems(topMenuItems),
      ];

      const normalized = fetchedItems.map((item) => ({
        key: item.key,
        name: item.name || item.key,
        schema_json: item.schema_json && typeof item.schema_json === 'object'
          ? item.schema_json
          : { type: 'object', properties: {}, additionalProperties: true },
      }));

      const merged = [...DEFAULT_COMPONENT_LIBRARY];
      [...normalized, ...menuLibraryItems].forEach((item) => {
        const index = merged.findIndex((existing) => existing.key === item.key);
        if (index >= 0) {
          merged[index] = { ...merged[index], ...item };
        } else {
          merged.push(item);
        }
      });
      setComponentLibrary(merged);
    } catch (_err) {
      setComponentLibrary(DEFAULT_COMPONENT_LIBRARY);
    }
  }, [authHeaders, country]);

  useEffect(() => {
    getLibrary();
  }, [getLibrary]);

  useEffect(() => {
    let active = true;
    const fetchCategories = async () => {
      setCategoriesLoading(true);
      try {
        const res = await axios.get(`${API}/categories`, {
          params: {
            module: moduleName.trim(),
            country: country.toUpperCase(),
          },
        });
        if (!active) return;
        const list = Array.isArray(res.data) ? res.data : [];
        setCategoryOptions(buildCategoryTreeOptions(list));
      } catch (_err) {
        if (active) setCategoryOptions([]);
      } finally {
        if (active) setCategoriesLoading(false);
      }
    };

    if (moduleName.trim()) {
      fetchCategories();
    } else {
      setCategoryOptions([]);
    }

    return () => {
      active = false;
    };
  }, [moduleName, country]);

  const filteredCategoryOptions = useMemo(() => {
    const query = categorySearch.trim().toLowerCase();
    if (!query) return categoryOptions;
    return categoryOptions.filter((item) => {
      const name = String(item.name || '').toLowerCase();
      const slug = String(item.slug || '').toLowerCase();
      return name.includes(query) || slug.includes(query);
    });
  }, [categoryOptions, categorySearch]);

  const menuComponentCount = useMemo(
    () => componentLibrary.filter((item) => String(item?.key || '').startsWith('menu.snapshot.')).length,
    [componentLibrary],
  );

  const libraryCategoryNameById = useMemo(() => {
    const next = new Map();
    categoryOptions.forEach((item) => {
      next.set(item.id, item.name || item.slug || item.id);
    });
    return next;
  }, [categoryOptions]);

  const selectedLibraryCategoryLabel = useMemo(
    () => (libraryMenuCategoryFilterId ? String(libraryCategoryNameById.get(libraryMenuCategoryFilterId) || '').toLowerCase() : ''),
    [libraryCategoryNameById, libraryMenuCategoryFilterId],
  );

  const filteredLibraryItems = useMemo(() => {
    const query = librarySearchQuery.trim().toLowerCase();
    return componentLibrary.filter((item) => {
      const groupId = resolveLibraryGroupByKey(item.key);
      if (libraryGroupFilter !== 'all' && groupId !== libraryGroupFilter) return false;

      const haystack = [
        item.name,
        item.key,
        item?.default_props?.menu_label,
        item?.default_props?.menu_parent_label,
        item?.default_props?.menu_slug,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();

      if (query && !haystack.includes(query)) return false;

      if (selectedLibraryCategoryLabel) {
        if (!String(item.key || '').startsWith('menu.snapshot.')) return false;
        if (!haystack.includes(selectedLibraryCategoryLabel)) return false;
      }

      return true;
    });
  }, [componentLibrary, librarySearchQuery, libraryGroupFilter, selectedLibraryCategoryLabel]);

  const groupedLibraryItems = useMemo(() => {
    const grouped = LIBRARY_GROUP_DEFINITIONS.map((group) => ({
      ...group,
      items: filteredLibraryItems.filter((item) => resolveLibraryGroupByKey(item.key) === group.id),
    })).filter((group) => group.items.length > 0);
    return grouped;
  }, [filteredLibraryItems]);

  const draggingLibraryComponentName = useMemo(() => {
    if (!draggingLibraryComponentKey) return '';
    return componentLibrary.find((item) => item.key === draggingLibraryComponentKey)?.name || '';
  }, [componentLibrary, draggingLibraryComponentKey]);

  const selectedCanvasContext = useMemo(() => {
    const rows = Array.isArray(payloadJson?.rows) ? payloadJson.rows : [];
    const row = rows.find((item) => item.id === selectedRowId);
    if (!row) return 'Henüz seçim yok';

    const rowIndex = rows.findIndex((item) => item.id === selectedRowId) + 1;
    const columns = Array.isArray(row.columns) ? row.columns : [];
    const column = columns.find((item) => item.id === selectedColumnId);
    const columnIndex = column ? (columns.findIndex((item) => item.id === selectedColumnId) + 1) : null;

    let componentLabel = '';
    if (column && selectedComponentId) {
      const components = Array.isArray(column.components) ? column.components : [];
      const component = components.find((item) => item.id === selectedComponentId);
      if (component) componentLabel = component.key;
    }

    if (componentLabel) return `Seçili: Row ${rowIndex} • Column ${columnIndex} • ${componentLabel}`;
    if (columnIndex) return `Seçili: Row ${rowIndex} • Column ${columnIndex}`;
    return `Seçili: Row ${rowIndex}`;
  }, [payloadJson, selectedRowId, selectedColumnId, selectedComponentId]);

  const previewBasePath = useMemo(() => {
    const selectedCategory = (bindingCategoryId || categoryId).trim();
    if (pageType === 'home') return '/';
    if (pageType === 'search_l1' || pageType === 'search_l2') {
      return `/search${selectedCategory ? `?category=${encodeURIComponent(selectedCategory)}` : ''}`;
    }
    return '/ilan-ver/detaylar';
  }, [pageType, bindingCategoryId, categoryId]);

  const publishedPreviewUrl = useMemo(() => {
    if (typeof window === 'undefined') return previewBasePath;
    const separator = previewBasePath.includes('?') ? '&' : '?';
    return `${window.location.origin}${previewBasePath}${separator}cb_preview_ts=${previewRefreshToken}`;
  }, [previewBasePath, previewRefreshToken]);

  const draftPreviewUrl = useMemo(() => {
    if (typeof window === 'undefined') return previewBasePath;
    const separator = previewBasePath.includes('?') ? '&' : '?';
    return `${window.location.origin}${previewBasePath}${separator}layout_preview=draft&cb_preview_ts=${previewRefreshToken}`;
  }, [previewBasePath, previewRefreshToken]);

  const publishedRevisionPayload = useMemo(() => {
    const published = revisionList.find((revision) => revision.status === 'published');
    return published?.payload_json || { rows: [] };
  }, [revisionList]);

  const layoutDiff = useMemo(
    () => computeLayoutDiff(publishedRevisionPayload, payloadJson),
    [publishedRevisionPayload, payloadJson],
  );

  const getComponentSchema = (componentKey) => {
    const componentDef = componentLibrary.find((item) => item.key === componentKey);
    return componentDef?.schema_json && typeof componentDef.schema_json === 'object'
      ? componentDef.schema_json
      : { type: 'object', properties: {}, additionalProperties: true };
  };

  const getComponentDefaultProps = (componentKey) => {
    const componentDef = componentLibrary.find((item) => item.key === componentKey);
    if (componentDef?.default_props && typeof componentDef.default_props === 'object') {
      return deepClone(componentDef.default_props);
    }
    if (componentKey === 'shared.text-block') {
      return { title: 'Başlık', body: 'Metin içeriği' };
    }
    return {};
  };

  const toggleLibraryGroupCollapsed = (groupId) => {
    setCollapsedLibraryGroups((prev) => ({
      ...prev,
      [groupId]: !prev[groupId],
    }));
  };

  const refreshPreviewAfterInteraction = () => {
    setPreviewRefreshToken(Date.now());
  };

  const autoFocusPreviewIfVisible = () => {
    if (!showPreviewComparison) return;
    const target = previewComparisonRef.current;
    if (!target) return;
    window.requestAnimationFrame(() => {
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  };

  useEffect(() => {
    if (!pendingFocusComponentId) return;
    const timer = window.setTimeout(() => {
      const target = document.querySelector(`[data-testid="admin-content-builder-component-${pendingFocusComponentId}"]`);
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
        target.focus?.();
      }
      setPendingFocusComponentId('');
    }, 120);
    return () => window.clearTimeout(timer);
  }, [pendingFocusComponentId]);

  const updateComponentPropValue = (rowId, columnId, componentId, propKey, propValue) => {
    const next = deepClone(payloadJson);
    const row = (next.rows || []).find((item) => item.id === rowId);
    const column = (row?.columns || []).find((item) => item.id === columnId);
    const component = (column?.components || []).find((item) => item.id === componentId);
    if (!component) return;
    if (!component.props || typeof component.props !== 'object') component.props = {};
    component.props[propKey] = propValue;
    updatePayload(next);
  };

  const getRevisionsForPage = async (targetPageId, targetPageType) => {
    const res = await axios.get(`${API}/admin/site/content-layout/pages/${targetPageId}/revisions`, {
      headers: authHeaders,
    });
    const revisions = Array.isArray(res.data?.items) ? res.data.items : [];
    setRevisionList(revisions);

    const draft = revisions.find((item) => item.status === 'draft');
    if (draft) {
      setActiveDraftId(draft.id);
      setPayloadJson(normalizePayload(draft.payload_json, targetPageType));
      return;
    }

    const published = revisions.find((item) => item.status === 'published');
    const draftCreateRes = await axios.post(
      `${API}/admin/site/content-layout/pages/${targetPageId}/revisions/draft`,
      { payload_json: normalizePayload(published?.payload_json, targetPageType) },
      { headers: authHeaders },
    );
    const newDraft = draftCreateRes.data?.item;
    setActiveDraftId(newDraft?.id || '');
    setPayloadJson(normalizePayload(newDraft?.payload_json, targetPageType));
  };

  const loadOrCreatePage = async () => {
    setLoading(true);
    setError('');
    setStatus('');
    try {
      await getLibrary();
      const normalizedCategoryId = categoryId.trim();
      const listRes = await axios.get(`${API}/admin/site/content-layout/pages`, {
        headers: authHeaders,
        params: {
          page_type: pageType,
          country: country.toUpperCase(),
          module: moduleName.trim(),
          page: 1,
          limit: 50,
        },
      });

      const listItems = Array.isArray(listRes.data?.items) ? listRes.data.items : [];
      let page = listItems.find((item) => {
        if (normalizedCategoryId) return item.category_id === normalizedCategoryId;
        return item.category_id === null;
      });

      if (!page) {
        const createRes = await axios.post(
          `${API}/admin/site/content-layout/pages`,
          {
            page_type: pageType,
            country: country.toUpperCase(),
            module: moduleName.trim(),
            category_id: normalizedCategoryId || null,
          },
          { headers: authHeaders },
        );
        page = createRes.data?.item;
      }

      if (!page?.id) throw new Error('layout_page_not_created');
      setPageId(page.id);
      setBindingCategoryId(normalizedCategoryId);
      await getRevisionsForPage(page.id, pageType);
      setPolicyReport(null);
      setStatus('Sayfa yüklendi. Draft düzenleyebilirsiniz.');
      toast.success('Layout page başarıyla yüklendi.');
      setIsSetupDrawerOpen(false);
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || 'Sayfa yüklenemedi');
      toast.error('Sayfa yüklenemedi veya oluşturulamadı.');
    } finally {
      setLoading(false);
    }
  };

  const saveDraft = async () => {
    if (!activeDraftId) {
      setError('Aktif draft bulunamadı. Önce “Sayfayı Yükle/Oluştur” yapın.');
      return false;
    }
    setSaving(true);
    setError('');
    setStatus('');
    try {
      await axios.patch(
        `${API}/admin/site/content-layout/revisions/${activeDraftId}/draft`,
        { payload_json: payloadJson },
        { headers: authHeaders },
      );
      setStatus('Draft kaydedildi.');
      toast.success('Draft kaydedildi.');
      refreshPreviewAfterInteraction();
      return true;
    } catch (err) {
      setError(err?.response?.data?.detail || 'Draft kaydedilemedi');
      toast.error('Draft kaydedilemedi.');
      return false;
    } finally {
      setSaving(false);
    }
  };

  const fetchPolicyReport = async ({ silent = false } = {}) => {
    if (!activeDraftId) return null;
    setPolicyReportLoading(true);
    try {
      const response = await axios.get(
        `${API}/admin/site/content-layout/revisions/${activeDraftId}/policy-report`,
        { headers: authHeaders },
      );
      const report = response.data?.report || null;
      setPolicyReport(report);
      if (!silent && report?.policy === 'listing_create') {
        if (report?.passed) {
          toast.success('Policy report başarılı.');
        } else {
          toast.error('Policy report bazı kurallardan geçemedi.');
        }
      }
      return report;
    } catch (err) {
      setError(err?.response?.data?.detail || 'Policy report alınamadı');
      if (!silent) toast.error('Policy report alınamadı.');
      return null;
    } finally {
      setPolicyReportLoading(false);
    }
  };

  useEffect(() => {
    if (pageType !== 'listing_create_stepX' || !activeDraftId) {
      setPolicyReport(null);
      return;
    }
    fetchPolicyReport({ silent: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pageType, activeDraftId]);

  const publishDraft = async () => {
    if (!activeDraftId) {
      setError('Yayınlanacak draft bulunamadı.');
      return;
    }
    setSaving(true);
    setError('');
    setStatus('');
    try {
      const saveOk = await saveDraft();
      if (!saveOk) {
        setStatus('Publish durduruldu: Draft kaydedilemedi.');
        return;
      }

      if (pageType === 'listing_create_stepX') {
        const report = await fetchPolicyReport({ silent: true });
        if (report?.policy === 'listing_create' && report.passed === false) {
          setError('Policy report başarısız. Publish öncesi kuralları düzeltin.');
          setStatus('Publish durduruldu: Policy report başarısız.');
          toast.error('Publish engellendi: listing_create policy kuralları sağlanmadı.');
          return;
        }
      }

      await axios.post(`${API}/admin/site/content-layout/revisions/${activeDraftId}/publish`, {}, { headers: authHeaders });
      setStatus('Draft publish edildi. Yeni draft oluşturuluyor...');
      await getRevisionsForPage(pageId, pageType);
      setStatus('Publish tamamlandı. Yeni draft hazır.');
      toast.success('Publish tamamlandı.');
    } catch (err) {
      setError(err?.response?.data?.detail || 'Publish başarısız');
      toast.error('Publish başarısız.');
    } finally {
      setSaving(false);
    }
  };

  const updatePayload = (nextPayload) => {
    setPayloadJson(nextPayload);
  };

  const addRow = () => {
    const next = deepClone(payloadJson);
    if (!Array.isArray(next.rows)) next.rows = [];
    next.rows.push({
      id: `row-${Date.now()}`,
      columns: [{
        id: `col-${Date.now()}`,
        width: { desktop: 12, tablet: 12, mobile: 12 },
        components: [],
      }],
    });
    updatePayload(next);
    refreshPreviewAfterInteraction();
  };

  const moveRow = (rowId, direction) => {
    const next = deepClone(payloadJson);
    const rows = Array.isArray(next.rows) ? next.rows : [];
    const index = rows.findIndex((row) => row.id === rowId);
    if (index < 0) return;
    const target = direction === 'up' ? index - 1 : index + 1;
    if (target < 0 || target >= rows.length) return;
    [rows[index], rows[target]] = [rows[target], rows[index]];
    updatePayload(next);
    refreshPreviewAfterInteraction();
  };

  const removeRow = (rowId) => {
    const next = deepClone(payloadJson);
    next.rows = (next.rows || []).filter((row) => row.id !== rowId);
    updatePayload(next);
    refreshPreviewAfterInteraction();
    if (selectedRowId === rowId) {
      setSelectedRowId('');
      setSelectedColumnId('');
      setSelectedComponentId('');
    }
  };

  const addColumn = (rowId) => {
    const next = deepClone(payloadJson);
    const row = (next.rows || []).find((item) => item.id === rowId);
    if (!row) return;
    if (!Array.isArray(row.columns)) row.columns = [];
    row.columns.push({
      id: `col-${Date.now()}`,
      width: { desktop: 6, tablet: 12, mobile: 12 },
      components: [],
    });
    updatePayload(next);
    refreshPreviewAfterInteraction();
  };

  const moveColumn = (rowId, columnId, direction) => {
    const next = deepClone(payloadJson);
    const row = (next.rows || []).find((item) => item.id === rowId);
    const columns = row?.columns || [];
    const index = columns.findIndex((item) => item.id === columnId);
    if (index < 0) return;
    const target = direction === 'left' ? index - 1 : index + 1;
    if (target < 0 || target >= columns.length) return;
    [columns[index], columns[target]] = [columns[target], columns[index]];
    updatePayload(next);
    refreshPreviewAfterInteraction();
  };

  const updateColumnWidth = (rowId, columnId, key, value) => {
    const next = deepClone(payloadJson);
    const row = (next.rows || []).find((item) => item.id === rowId);
    const column = (row?.columns || []).find((item) => item.id === columnId);
    if (!column) return;
    if (!column.width || typeof column.width !== 'object') column.width = {};
    column.width[key] = Math.max(1, Math.min(12, Number(value) || 12));
    updatePayload(next);
  };

  const removeColumn = (rowId, columnId) => {
    const next = deepClone(payloadJson);
    const row = (next.rows || []).find((item) => item.id === rowId);
    if (!row) return;
    row.columns = (row.columns || []).filter((column) => column.id !== columnId);
    updatePayload(next);
    refreshPreviewAfterInteraction();
    if (selectedColumnId === columnId) {
      setSelectedColumnId('');
      setSelectedComponentId('');
    }
  };

  const addComponent = (rowId, columnId, key) => {
    if (!key) return;
    const next = deepClone(payloadJson);
    const row = (next.rows || []).find((item) => item.id === rowId);
    const column = (row?.columns || []).find((item) => item.id === columnId);
    if (!column) return;

    if (pageType === 'listing_create_stepX' && key === 'listing.create.default-content') {
      const rows = Array.isArray(next.rows) ? next.rows : [];
      const existingDefaultCount = rows.reduce((sum, currentRow) => {
        const columns = Array.isArray(currentRow?.columns) ? currentRow.columns : [];
        return sum + columns.reduce((innerSum, currentColumn) => {
          const components = Array.isArray(currentColumn?.components) ? currentColumn.components : [];
          return innerSum + components.filter((component) => component?.key === 'listing.create.default-content').length;
        }, 0);
      }, 0);
      if (existingDefaultCount >= 1) {
        setError('İlan Ver akışında yalnızca bir adet varsayılan içerik bileşeni kullanılabilir.');
        toast.error('İlan Ver için ikinci varsayılan bileşen eklenemez.');
        return;
      }
    }

    if (!Array.isArray(column.components)) column.components = [];
    const nextComponentId = `cmp-${Date.now()}-${Math.round(Math.random() * 100)}`;
    column.components.push({
      id: nextComponentId,
      key,
      props: getComponentDefaultProps(key),
      visibility: { desktop: true, tablet: true, mobile: true },
    });
    updatePayload(next);
    setSelectedRowId(rowId);
    setSelectedColumnId(columnId);
    setSelectedComponentId(nextComponentId);
    setPendingFocusComponentId(nextComponentId);
    refreshPreviewAfterInteraction();
    autoFocusPreviewIfVisible();
  };

  const updateComponentField = (rowId, columnId, componentId, field, value) => {
    const next = deepClone(payloadJson);
    const row = (next.rows || []).find((item) => item.id === rowId);
    const column = (row?.columns || []).find((item) => item.id === columnId);
    const component = (column?.components || []).find((item) => item.id === componentId);
    if (!component) return;
    if (field === 'key') {
      if (pageType === 'listing_create_stepX' && value === 'listing.create.default-content') {
        const existingDefaultCount = (next.rows || []).reduce((sum, currentRow) => {
          const columns = Array.isArray(currentRow?.columns) ? currentRow.columns : [];
          return sum + columns.reduce((innerSum, currentColumn) => {
            const components = Array.isArray(currentColumn?.components) ? currentColumn.components : [];
            return innerSum + components.filter((item) => item?.key === 'listing.create.default-content' && item?.id !== componentId).length;
          }, 0);
        }, 0);
        if (existingDefaultCount >= 1) {
          setError('İlan Ver akışında yalnızca bir adet varsayılan içerik bileşeni kullanılabilir.');
          toast.error('İkinci varsayılan bileşen seçilemez.');
          return;
        }
      }
      component.key = value;
      component.props = getComponentDefaultProps(value);
    } else {
      component[field] = value;
    }
    updatePayload(next);
    refreshPreviewAfterInteraction();
  };

  const removeComponent = (rowId, columnId, componentId) => {
    const next = deepClone(payloadJson);
    const row = (next.rows || []).find((item) => item.id === rowId);
    const column = (row?.columns || []).find((item) => item.id === columnId);
    if (!column) return;
    column.components = (column.components || []).filter((component) => component.id !== componentId);
    updatePayload(next);
    refreshPreviewAfterInteraction();
    if (selectedComponentId === componentId) {
      setSelectedComponentId('');
    }
  };

  const moveComponent = (rowId, columnId, componentId, direction) => {
    const next = deepClone(payloadJson);
    const row = (next.rows || []).find((item) => item.id === rowId);
    const column = (row?.columns || []).find((item) => item.id === columnId);
    const list = column?.components || [];
    const index = list.findIndex((item) => item.id === componentId);
    if (index < 0) return;
    const target = direction === 'up' ? index - 1 : index + 1;
    if (target < 0 || target >= list.length) return;
    [list[index], list[target]] = [list[target], list[index]];
    updatePayload(next);
    refreshPreviewAfterInteraction();
  };

  const handleRowDrop = (targetRowId) => {
    if (!draggingRowId || draggingRowId === targetRowId) {
      setDragOverRowId('');
      return;
    }
    const next = deepClone(payloadJson);
    const rows = next.rows || [];
    const fromIndex = rows.findIndex((row) => row.id === draggingRowId);
    const toIndex = rows.findIndex((row) => row.id === targetRowId);
    if (fromIndex < 0 || toIndex < 0) return;
    const [moved] = rows.splice(fromIndex, 1);
    rows.splice(toIndex, 0, moved);
    updatePayload(next);
    refreshPreviewAfterInteraction();
    setDraggingRowId('');
    setDragOverRowId('');
  };

  const handleComponentDrop = (targetRowId, targetColumnId) => {
    if (draggingLibraryComponentKey) {
      addComponent(targetRowId, targetColumnId, draggingLibraryComponentKey);
      setDraggingLibraryComponentKey('');
      setDragOverColumnId('');
      return;
    }

    if (!draggingComponentId) {
      setDragOverColumnId('');
      return;
    }
    const next = deepClone(payloadJson);
    let movedComponent = null;

    (next.rows || []).forEach((row) => {
      (row.columns || []).forEach((column) => {
        const index = (column.components || []).findIndex((component) => component.id === draggingComponentId);
        if (index >= 0) {
          movedComponent = column.components[index];
          column.components.splice(index, 1);
        }
      });
    });

    if (!movedComponent) return;
    const targetRow = (next.rows || []).find((row) => row.id === targetRowId);
    const targetColumn = (targetRow?.columns || []).find((column) => column.id === targetColumnId);
    if (!targetColumn) return;
    if (!Array.isArray(targetColumn.components)) targetColumn.components = [];
    targetColumn.components.push(movedComponent);
    updatePayload(next);
    setSelectedRowId(targetRowId);
    setSelectedColumnId(targetColumnId);
    setSelectedComponentId(movedComponent.id || '');
    setPendingFocusComponentId(movedComponent.id || '');
    refreshPreviewAfterInteraction();
    autoFocusPreviewIfVisible();
    setDraggingComponentId('');
    setDragOverColumnId('');
  };

  const fetchActiveBinding = async () => {
    const categoryToCheck = (bindingCategoryId || categoryId).trim();
    if (!categoryToCheck) {
      setError('Binding için kategori ID zorunlu.');
      return;
    }
    setBindingLoading(true);
    try {
      const res = await axios.get(`${API}/admin/site/content-layout/bindings/active`, {
        headers: authHeaders,
        params: {
          country: country.toUpperCase(),
          module: moduleName.trim(),
          category_id: categoryToCheck,
        },
      });
      setBindingActiveItem(res.data?.item || null);
      setStatus('Aktif binding sorgulandı.');
      toast.success('Aktif binding bilgisi güncellendi.');
    } catch (err) {
      setError(err?.response?.data?.detail || 'Aktif binding getirilemedi');
      toast.error('Aktif binding getirilemedi.');
    } finally {
      setBindingLoading(false);
    }
  };

  const bindCurrentPage = async () => {
    const categoryToBind = (bindingCategoryId || categoryId).trim();
    if (!pageId) {
      setError('Önce bir page oluşturun/yükleyin.');
      return;
    }
    if (!categoryToBind) {
      setError('Binding için kategori ID zorunlu.');
      return;
    }
    setBindingLoading(true);
    try {
      await axios.post(
        `${API}/admin/site/content-layout/bindings`,
        {
          country: country.toUpperCase(),
          module: moduleName.trim(),
          category_id: categoryToBind,
          layout_page_id: pageId,
        },
        { headers: authHeaders },
      );
      setStatus('Kategori binding kaydedildi.');
      toast.success('Kategori binding kaydedildi.');
      await fetchActiveBinding();
    } catch (err) {
      setError(err?.response?.data?.detail || 'Binding kaydedilemedi');
      toast.error('Binding kaydedilemedi.');
    } finally {
      setBindingLoading(false);
    }
  };

  const unbindCurrentCategory = async () => {
    const categoryToUnbind = (bindingCategoryId || categoryId).trim();
    if (!categoryToUnbind) {
      setError('Unbind için kategori ID zorunlu.');
      return;
    }
    setBindingLoading(true);
    try {
      await axios.post(
        `${API}/admin/site/content-layout/bindings/unbind`,
        {
          country: country.toUpperCase(),
          module: moduleName.trim(),
          category_id: categoryToUnbind,
        },
        { headers: authHeaders },
      );
      setBindingActiveItem(null);
      setStatus('Kategori binding kaldırıldı.');
      toast.success('Binding kaldırıldı.');
    } catch (err) {
      setError(err?.response?.data?.detail || 'Unbind başarısız');
      toast.error('Binding kaldırma başarısız.');
    } finally {
      setBindingLoading(false);
    }
  };

  return (
    <div className="space-y-5" data-testid="admin-content-builder-page">
      <header className="rounded-xl border bg-white p-4" data-testid="admin-content-builder-header">
        <div className="flex flex-wrap items-center gap-2" data-testid="admin-content-builder-top-actions">
          <Sheet open={isSetupDrawerOpen} onOpenChange={setIsSetupDrawerOpen}>
            <SheetTrigger asChild>
              <button
                type="button"
                className="h-10 rounded bg-slate-900 px-4 text-sm text-white"
                data-testid="admin-content-builder-open-setup-drawer-button"
              >
                Formları Aç
              </button>
            </SheetTrigger>
            <SheetContent
              side="right"
              className="w-[min(96vw,560px)] overflow-y-auto"
              data-testid="admin-content-builder-setup-drawer"
            >
              <SheetHeader data-testid="admin-content-builder-setup-drawer-header">
                <SheetTitle data-testid="admin-content-builder-setup-drawer-title">Content Builder Formları</SheetTitle>
                <SheetDescription data-testid="admin-content-builder-setup-drawer-description">
                  Sayfa tanımı ve kategori binding işlemlerini sağ panelden yönetin.
                </SheetDescription>
              </SheetHeader>

              <div className="mt-4 space-y-5" data-testid="admin-content-builder-setup-drawer-body">
                <section className="rounded-lg border p-3" data-testid="admin-content-builder-layout-form-section">
                  <h3 className="text-xs font-semibold" data-testid="admin-content-builder-layout-form-title">Layout Page Formu</h3>
                  <div className="mt-2 space-y-2" data-testid="admin-content-builder-filters">
                    <label className="text-xs block" data-testid="admin-content-builder-page-type-wrap">
                      Sayfa Tipi
                      <select className="mt-1 h-10 w-full rounded border px-2" value={pageType} onChange={(e) => setPageType(e.target.value)} data-testid="admin-content-builder-page-type-select">
                        {PAGE_TYPE_OPTIONS.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                      </select>
                    </label>

                    <label className="text-xs block" data-testid="admin-content-builder-country-wrap">
                      Ülke
                      <input className="mt-1 h-10 w-full rounded border px-2" value={country} onChange={(e) => setCountry(e.target.value.toUpperCase())} data-testid="admin-content-builder-country-input" />
                    </label>

                    <label className="text-xs block" data-testid="admin-content-builder-module-wrap">
                      Module
                      <input className="mt-1 h-10 w-full rounded border px-2" value={moduleName} onChange={(e) => setModuleName(e.target.value)} data-testid="admin-content-builder-module-input" />
                    </label>

                    <label className="text-xs block" data-testid="admin-content-builder-category-wrap">
                      Category ID (opsiyonel)
                      <input className="mt-1 h-10 w-full rounded border px-2" value={categoryId} onChange={(e) => setCategoryId(e.target.value)} data-testid="admin-content-builder-category-input" />
                    </label>

                    <button type="button" className="h-10 w-full rounded bg-slate-900 px-4 text-sm text-white" onClick={loadOrCreatePage} disabled={loading} data-testid="admin-content-builder-load-page-button">
                      {loading ? 'Yükleniyor...' : 'Sayfayı Yükle/Oluştur'}
                    </button>
                  </div>
                </section>

                <section className="rounded-lg border bg-slate-50 p-3" data-testid="admin-content-builder-binding-panel">
                  <h3 className="text-xs font-semibold" data-testid="admin-content-builder-binding-panel-title">Kategori Binding Formu</h3>
                  <div className="mt-2 space-y-2" data-testid="admin-content-builder-binding-controls">
                    <label className="text-xs block" data-testid="admin-content-builder-binding-category-search-wrap">
                      Kategori Ara
                      <input
                        className="mt-1 h-9 w-full rounded border px-2"
                        value={categorySearch}
                        onChange={(e) => setCategorySearch(e.target.value)}
                        placeholder="Kategori adı / slug"
                        data-testid="admin-content-builder-binding-category-search-input"
                      />
                    </label>

                    <label className="text-xs block" data-testid="admin-content-builder-binding-category-wrap">
                      Kategori Ağacı Seçimi
                      <select
                        className="mt-1 h-9 w-full rounded border px-2"
                        value={bindingCategoryId}
                        onChange={(e) => setBindingCategoryId(e.target.value)}
                        data-testid="admin-content-builder-binding-category-input"
                      >
                        <option value="">{categoriesLoading ? 'Kategoriler yükleniyor...' : 'Kategori seçin'}</option>
                        {filteredCategoryOptions.map((item) => (
                          <option key={item.id} value={item.id}>
                            {`${'— '.repeat(item.depth)}${item.name}`}
                          </option>
                        ))}
                      </select>
                    </label>

                    <div className="grid grid-cols-1 gap-2 sm:grid-cols-3" data-testid="admin-content-builder-binding-action-grid">
                      <button type="button" className="h-9 rounded border px-3 text-xs" onClick={fetchActiveBinding} disabled={bindingLoading} data-testid="admin-content-builder-binding-fetch-button">Aktifi Getir</button>
                      <button type="button" className="h-9 rounded bg-blue-600 px-3 text-xs text-white" onClick={bindCurrentPage} disabled={bindingLoading} data-testid="admin-content-builder-binding-bind-button">Bu Page'i Bağla</button>
                      <button type="button" className="h-9 rounded border border-rose-300 px-3 text-xs text-rose-700" onClick={unbindCurrentCategory} disabled={bindingLoading} data-testid="admin-content-builder-binding-unbind-button">Binding Kaldır</button>
                    </div>
                  </div>
                </section>
              </div>
            </SheetContent>
          </Sheet>

          <button type="button" className="h-10 rounded border px-4 text-sm" onClick={saveDraft} disabled={saving || !activeDraftId} data-testid="admin-content-builder-save-draft-button">
            Draft Kaydet
          </button>

          <button type="button" className="h-10 rounded bg-emerald-600 px-4 text-sm text-white" onClick={publishDraft} disabled={saving || !activeDraftId} data-testid="admin-content-builder-publish-button">
            Publish
          </button>

          <button
            type="button"
            className="h-10 rounded border px-4 text-xs"
            onClick={() => fetchPolicyReport()}
            disabled={!activeDraftId || policyReportLoading}
            data-testid="admin-content-builder-policy-report-button"
          >
            {policyReportLoading ? 'Policy Raporu...' : 'Policy Report'}
          </button>

          <button
            type="button"
            className="h-10 rounded border px-4 text-xs"
            onClick={() => setShowPreviewComparison((prev) => !prev)}
            data-testid="admin-content-builder-preview-toggle-button"
          >
            {showPreviewComparison ? 'Preview Gizle' : 'Preview Karşılaştır'}
          </button>

          <a href={publishedPreviewUrl} target="_blank" rel="noreferrer" className="text-xs font-medium underline" data-testid="admin-content-builder-preview-published-link">
            Published Aç
          </a>
          <a href={draftPreviewUrl} target="_blank" rel="noreferrer" className="text-xs font-medium underline" data-testid="admin-content-builder-preview-draft-link">
            Draft Preview Aç (layout_preview=draft)
          </a>
        </div>

        <div className="mt-3 flex flex-wrap gap-3 text-xs text-slate-600" data-testid="admin-content-builder-meta-row">
          <span data-testid="admin-content-builder-page-id">page_id: {pageId || '-'}</span>
          <span data-testid="admin-content-builder-draft-id">draft_id: {activeDraftId || '-'}</span>
          <span data-testid="admin-content-builder-revision-count">revision_count: {revisionList.length}</span>
          <span data-testid="admin-content-builder-binding-active-summary">
            {bindingActiveItem ? (
              <>
                Aktif binding page_id: <strong data-testid="admin-content-builder-binding-active-page-id">{bindingActiveItem.layout_page_id}</strong>
              </>
            ) : (
              <span data-testid="admin-content-builder-binding-active-empty">Aktif binding bulunamadı.</span>
            )}
          </span>
        </div>

        {policyReport?.policy === 'listing_create' ? (
          <div className={`mt-3 rounded-lg border p-3 text-xs ${policyReport.passed ? 'border-emerald-200 bg-emerald-50' : 'border-rose-200 bg-rose-50'}`} data-testid="admin-content-builder-policy-report-panel">
            <div className="flex items-center justify-between gap-3" data-testid="admin-content-builder-policy-report-header">
              <strong data-testid="admin-content-builder-policy-report-title">Listing Create Policy Report</strong>
              <span data-testid="admin-content-builder-policy-report-status">Durum: {policyReport.passed ? 'PASS' : 'FAIL'}</span>
            </div>
            <div className="mt-2 space-y-1" data-testid="admin-content-builder-policy-report-list">
              {(policyReport.checks || []).map((check) => (
                <div key={check.id} className="flex flex-wrap items-center gap-2" data-testid={`admin-content-builder-policy-check-${check.id}`}>
                  <span className={`inline-flex rounded px-2 py-0.5 ${check.status === 'pass' ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}`} data-testid={`admin-content-builder-policy-check-status-${check.id}`}>
                    {String(check.status || '').toUpperCase()}
                  </span>
                  <span data-testid={`admin-content-builder-policy-check-label-${check.id}`}>{check.label}</span>
                  <span className="text-slate-500" data-testid={`admin-content-builder-policy-check-detail-${check.id}`}>{check.detail}</span>
                </div>
              ))}
            </div>
          </div>
        ) : null}

        {showPreviewComparison ? (
          <div ref={previewComparisonRef} className="mt-3 grid grid-cols-1 gap-3 xl:grid-cols-2" data-testid="admin-content-builder-preview-iframes">
            <div className="rounded border bg-white p-2" data-testid="admin-content-builder-preview-published-wrap">
              <div className="mb-1 text-[11px] text-slate-600" data-testid="admin-content-builder-preview-published-label">Published</div>
              <iframe title="published-preview" src={publishedPreviewUrl} className="h-[380px] w-full rounded border" data-testid="admin-content-builder-preview-published-iframe" />
            </div>
            <div className="rounded border bg-white p-2" data-testid="admin-content-builder-preview-draft-wrap">
              <div className="mb-1 text-[11px] text-slate-600" data-testid="admin-content-builder-preview-draft-label">Draft Preview</div>
              <iframe title="draft-preview" src={draftPreviewUrl} className="h-[380px] w-full rounded border" data-testid="admin-content-builder-preview-draft-iframe" />
            </div>
          </div>
        ) : null}

        {status ? <p className="mt-2 text-xs text-emerald-700" data-testid="admin-content-builder-status-message">{status}</p> : null}
        {error ? <p className="mt-2 text-xs text-rose-700" data-testid="admin-content-builder-error-message">{error}</p> : null}
      </header>

      <div className="grid gap-5 xl:grid-cols-[280px_minmax(0,1fr)]" data-testid="admin-content-builder-main-grid">
        <aside className="rounded-xl border bg-white p-4" data-testid="admin-content-builder-library">
          <h2 className="text-sm font-semibold" data-testid="admin-content-builder-library-title">Component Library</h2>
          <p className="mt-1 text-xs text-slate-500" data-testid="admin-content-builder-library-note">
            Bir sütunu seçip bileşen ekleyin. Menü bileşenleri: <strong data-testid="admin-content-builder-library-menu-count">{menuComponentCount}</strong>
          </p>

          <div className="mt-3 space-y-2" data-testid="admin-content-builder-library-filters">
            <input
              type="text"
              className="h-9 w-full rounded border px-2 text-xs"
              placeholder="Bileşen ara (hızlı arama)"
              value={librarySearchQuery}
              onChange={(event) => setLibrarySearchQuery(event.target.value)}
              data-testid="admin-content-builder-library-search-input"
            />

            <select
              className="h-9 w-full rounded border px-2 text-xs"
              value={libraryGroupFilter}
              onChange={(event) => setLibraryGroupFilter(event.target.value)}
              data-testid="admin-content-builder-library-group-filter"
            >
              <option value="all">Tüm Gruplar</option>
              {LIBRARY_GROUP_DEFINITIONS.map((group) => (
                <option key={group.id} value={group.id}>{group.label}</option>
              ))}
            </select>

            <select
              className="h-9 w-full rounded border px-2 text-xs"
              value={libraryMenuCategoryFilterId}
              onChange={(event) => setLibraryMenuCategoryFilterId(event.target.value)}
              data-testid="admin-content-builder-library-menu-category-filter"
            >
              <option value="">Menü için kategori ağacı filtresi (opsiyonel)</option>
              {categoryOptions.map((item) => (
                <option key={item.id} value={item.id}>{`${'— '.repeat(item.depth)}${item.name}`}</option>
              ))}
            </select>
          </div>

          <div className="mt-3 space-y-2" data-testid="admin-content-builder-library-list">
            {groupedLibraryItems.map((group) => {
              const isCollapsed = Boolean(collapsedLibraryGroups[group.id]);
              return (
                <section key={group.id} className="rounded border bg-slate-50/60 p-2" data-testid={`admin-content-builder-library-group-${group.id}`}>
                  <button
                    type="button"
                    className="flex w-full items-center justify-between rounded px-2 py-1 text-left text-xs font-semibold"
                    onClick={() => toggleLibraryGroupCollapsed(group.id)}
                    data-testid={`admin-content-builder-library-group-toggle-${group.id}`}
                  >
                    <span>{group.label}</span>
                    <span data-testid={`admin-content-builder-library-group-count-${group.id}`}>{group.items.length}</span>
                  </button>

                  {!isCollapsed ? (
                    <div className="mt-2 space-y-2" data-testid={`admin-content-builder-library-group-list-${group.id}`}>
                      {group.items.map((component) => (
                        <div
                          key={component.key}
                          className="rounded border bg-white p-2"
                          draggable
                          onDragStart={() => {
                            setDraggingLibraryComponentKey(component.key);
                            setDraggingComponentId('');
                          }}
                          onDragEnd={() => setDraggingLibraryComponentKey('')}
                          data-testid={`admin-content-builder-library-item-${component.key}`}
                        >
                          <div className="text-xs font-medium" data-testid={`admin-content-builder-library-item-name-${component.key}`}>{component.name}</div>
                          <div className="text-[11px] text-slate-500" data-testid={`admin-content-builder-library-item-key-${component.key}`}>{component.key}</div>
                          <div className="mt-1 text-[11px] text-slate-500" data-testid={`admin-content-builder-library-drag-hint-${component.key}`}>
                            Bu kartı doğrudan canvas sütununa sürükleyebilirsiniz.
                          </div>
                          <button
                            type="button"
                            className="mt-2 h-8 rounded border px-2 text-xs"
                            onClick={() => {
                              if (!selectedRowId || !selectedColumnId) {
                                setError('Önce canvas üzerinde bir sütun seçin.');
                                return;
                              }
                              addComponent(selectedRowId, selectedColumnId, component.key);
                            }}
                            data-testid={`admin-content-builder-library-add-${component.key}`}
                          >
                            Seçili Sütuna Ekle
                          </button>
                        </div>
                      ))}
                    </div>
                  ) : null}
                </section>
              );
            })}

            {!groupedLibraryItems.length ? (
              <div className="rounded border border-dashed p-3 text-xs text-slate-500" data-testid="admin-content-builder-library-empty-state">
                Filtreye uygun bileşen bulunamadı.
              </div>
            ) : null}
          </div>
        </aside>

        <section className="rounded-xl border bg-white p-4" data-testid="admin-content-builder-canvas">
          <div className="mb-3 flex items-center justify-between" data-testid="admin-content-builder-canvas-header">
            <h2 className="text-sm font-semibold" data-testid="admin-content-builder-canvas-title">Sortable Canvas</h2>
            <button type="button" className="h-9 rounded border px-3 text-xs" onClick={addRow} data-testid="admin-content-builder-add-row-button">Satır Ekle</button>
          </div>

          <div className="mb-2 rounded-md border border-sky-200 bg-sky-50 px-3 py-2 text-xs text-sky-800" data-testid="admin-content-builder-selection-summary">
            {selectedCanvasContext}
          </div>

          <div className="mb-3 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs" data-testid="admin-content-builder-diff-summary">
            <span data-testid="admin-content-builder-diff-rows">Row değişimi: <strong>{layoutDiff.summary.rows}</strong></span>
            <span className="mx-2">•</span>
            <span data-testid="admin-content-builder-diff-columns">Column değişimi: <strong>{layoutDiff.summary.columns}</strong></span>
            <span className="mx-2">•</span>
            <span data-testid="admin-content-builder-diff-components">Component değişimi: <strong>{layoutDiff.summary.components}</strong></span>
          </div>

          <div className="space-y-4" data-testid="admin-content-builder-rows">
            {(payloadJson.rows || []).map((row, rowIndex) => (
              <article
                key={row.id}
                className={`rounded-lg border p-3 transition ${dragOverRowId === row.id ? 'border-slate-900 bg-slate-50' : 'border-slate-200'} ${layoutDiff.changedRowIds.has(row.id) ? 'ring-1 ring-amber-500' : ''} ${selectedRowId === row.id ? 'ring-2 ring-sky-400 bg-sky-50/40' : ''}`}
                draggable
                onDragStart={() => setDraggingRowId(row.id)}
                onDragEnd={() => {
                  setDraggingRowId('');
                  setDragOverRowId('');
                }}
                onClick={() => {
                  setSelectedRowId(row.id);
                }}
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragOverRowId(row.id);
                }}
                onDragLeave={() => {
                  if (dragOverRowId === row.id) setDragOverRowId('');
                }}
                onDrop={() => handleRowDrop(row.id)}
                data-testid={`admin-content-builder-row-${row.id}`}
              >
                <div className="mb-3 flex flex-wrap items-center gap-2" data-testid={`admin-content-builder-row-actions-${row.id}`}>
                  <span className="text-xs font-semibold" data-testid={`admin-content-builder-row-label-${row.id}`}>Row {rowIndex + 1}</span>
                  <button type="button" className="h-8 rounded border px-2 text-xs" onClick={() => moveRow(row.id, 'up')} data-testid={`admin-content-builder-row-move-up-${row.id}`}>Yukarı</button>
                  <button type="button" className="h-8 rounded border px-2 text-xs" onClick={() => moveRow(row.id, 'down')} data-testid={`admin-content-builder-row-move-down-${row.id}`}>Aşağı</button>
                  <button type="button" className="h-8 rounded border px-2 text-xs" onClick={() => addColumn(row.id)} data-testid={`admin-content-builder-row-add-column-${row.id}`}>Sütun Ekle</button>
                  <button type="button" className="h-8 rounded border border-rose-300 px-2 text-xs text-rose-700" onClick={() => removeRow(row.id)} data-testid={`admin-content-builder-row-remove-${row.id}`}>Satırı Sil</button>
                </div>

                {dragOverRowId === row.id ? (
                  <div className="mb-3 rounded border border-dashed border-slate-500 bg-white px-2 py-1 text-[11px] text-slate-600" data-testid={`admin-content-builder-row-drop-indicator-${row.id}`}>
                    Satırı buraya bırak
                  </div>
                ) : null}

                <div className="grid grid-cols-1 gap-3 lg:grid-cols-2" data-testid={`admin-content-builder-row-columns-${row.id}`}>
                  {(row.columns || []).map((column) => (
                    <div
                      key={column.id}
                      className={`rounded-md border p-3 transition ${selectedColumnId === column.id ? 'border-sky-600 ring-2 ring-sky-300 bg-sky-50/40' : 'border-slate-200'} ${dragOverColumnId === column.id ? 'bg-amber-50 border-amber-400' : ''} ${layoutDiff.changedColumnIds.has(column.id) ? 'ring-1 ring-amber-500' : ''}`}
                      onClick={() => {
                        setSelectedRowId(row.id);
                        setSelectedColumnId(column.id);
                        setSelectedComponentId('');
                      }}
                      onDragOver={(e) => {
                        e.preventDefault();
                        setDragOverColumnId(column.id);
                      }}
                      onDragLeave={() => {
                        if (dragOverColumnId === column.id) setDragOverColumnId('');
                      }}
                      onDrop={() => handleComponentDrop(row.id, column.id)}
                      data-testid={`admin-content-builder-column-${column.id}`}
                    >
                      <div className="mb-2 flex flex-wrap items-center gap-2" data-testid={`admin-content-builder-column-header-${column.id}`}>
                        <span className="text-xs font-medium" data-testid={`admin-content-builder-column-label-${column.id}`}>Column</span>
                        <label className="text-[11px]" data-testid={`admin-content-builder-width-desktop-wrap-${column.id}`}>D
                          <select className="ml-1 rounded border px-1" value={column.width?.desktop || 12} onChange={(e) => updateColumnWidth(row.id, column.id, 'desktop', e.target.value)} data-testid={`admin-content-builder-width-desktop-${column.id}`}>
                            {Array.from({ length: 12 }).map((_, index) => <option key={index + 1} value={index + 1}>{index + 1}/12</option>)}
                          </select>
                        </label>
                        <label className="text-[11px]" data-testid={`admin-content-builder-width-tablet-wrap-${column.id}`}>T
                          <select className="ml-1 rounded border px-1" value={column.width?.tablet || 12} onChange={(e) => updateColumnWidth(row.id, column.id, 'tablet', e.target.value)} data-testid={`admin-content-builder-width-tablet-${column.id}`}>
                            {Array.from({ length: 12 }).map((_, index) => <option key={index + 1} value={index + 1}>{index + 1}/12</option>)}
                          </select>
                        </label>
                        <label className="text-[11px]" data-testid={`admin-content-builder-width-mobile-wrap-${column.id}`}>M
                          <select className="ml-1 rounded border px-1" value={column.width?.mobile || 12} onChange={(e) => updateColumnWidth(row.id, column.id, 'mobile', e.target.value)} data-testid={`admin-content-builder-width-mobile-${column.id}`}>
                            {Array.from({ length: 12 }).map((_, index) => <option key={index + 1} value={index + 1}>{index + 1}/12</option>)}
                          </select>
                        </label>
                        <button type="button" className="ml-auto rounded border border-rose-300 px-2 py-1 text-[11px] text-rose-700" onClick={() => removeColumn(row.id, column.id)} data-testid={`admin-content-builder-remove-column-${column.id}`}>
                          Sil
                        </button>
                        <button type="button" className="rounded border px-2 py-1 text-[11px]" onClick={() => moveColumn(row.id, column.id, 'left')} data-testid={`admin-content-builder-move-column-left-${column.id}`}>
                          ←
                        </button>
                        <button type="button" className="rounded border px-2 py-1 text-[11px]" onClick={() => moveColumn(row.id, column.id, 'right')} data-testid={`admin-content-builder-move-column-right-${column.id}`}>
                          →
                        </button>
                      </div>

                      {dragOverColumnId === column.id ? (
                        <div className="mb-2 rounded border border-dashed border-amber-500 bg-amber-100 px-2 py-1 text-[11px] text-amber-700" data-testid={`admin-content-builder-column-drop-indicator-${column.id}`}>
                          {draggingLibraryComponentKey
                            ? `${draggingLibraryComponentName || 'Seçili bileşen'} bu sütuna eklenecek`
                            : 'Bileşeni bu sütuna bırak'}
                        </div>
                      ) : null}

                      <div className="space-y-2" data-testid={`admin-content-builder-components-${column.id}`}>
                        {(column.components || []).map((component, componentIndex) => (
                          <div
                            key={component.id}
                            className={`rounded border bg-slate-50 p-2 ${layoutDiff.changedComponentIds.has(component.id) ? 'border-amber-500 bg-amber-50' : ''} ${selectedComponentId === component.id ? 'border-sky-500 ring-2 ring-sky-300 bg-sky-50' : ''}`}
                            tabIndex={0}
                            draggable
                            onDragStart={() => setDraggingComponentId(component.id)}
                            onDragEnd={() => {
                              setDraggingComponentId('');
                              setDragOverColumnId('');
                            }}
                            onClick={(event) => {
                              event.stopPropagation();
                              setSelectedRowId(row.id);
                              setSelectedColumnId(column.id);
                              setSelectedComponentId(component.id);
                            }}
                            data-testid={`admin-content-builder-component-${component.id}`}
                          >
                            <div className="flex flex-wrap items-center gap-2" data-testid={`admin-content-builder-component-header-${component.id}`}>
                              <select
                                className="h-8 min-w-[220px] rounded border px-2 text-xs"
                                value={component.key}
                                onChange={(e) => updateComponentField(row.id, column.id, component.id, 'key', e.target.value)}
                                data-testid={`admin-content-builder-component-key-${component.id}`}
                              >
                                {componentLibrary.map((item) => <option key={item.key} value={item.key}>{item.name}</option>)}
                              </select>
                              <button type="button" className="h-8 rounded border px-2 text-xs" onClick={() => moveComponent(row.id, column.id, component.id, 'up')} data-testid={`admin-content-builder-component-up-${component.id}`}>↑</button>
                              <button type="button" className="h-8 rounded border px-2 text-xs" onClick={() => moveComponent(row.id, column.id, component.id, 'down')} data-testid={`admin-content-builder-component-down-${component.id}`}>↓</button>
                              <button type="button" className="h-8 rounded border border-rose-300 px-2 text-xs text-rose-700" onClick={() => removeComponent(row.id, column.id, component.id)} data-testid={`admin-content-builder-component-remove-${component.id}`}>Sil</button>
                            </div>
                            <div className="mt-2 rounded border bg-white p-2" data-testid={`admin-content-builder-component-props-${component.id}`}>
                              <div className="mb-1 text-[11px] font-semibold text-slate-700" data-testid={`admin-content-builder-component-props-title-${component.id}`}>
                                Schema Form Editor
                              </div>
                              {Object.entries(getComponentSchema(component.key)?.properties || {}).length === 0 ? (
                                <div className="text-[11px] text-slate-500" data-testid={`admin-content-builder-component-props-empty-${component.id}`}>
                                  Bu bileşenin düzenlenebilir prop alanı yok.
                                </div>
                              ) : (
                                <div className="space-y-2" data-testid={`admin-content-builder-component-props-fields-${component.id}`}>
                                  {Object.entries(getComponentSchema(component.key)?.properties || {}).map(([propKey, propSchema]) => {
                                    const fieldType = propSchema?.type || 'string';
                                    const fieldTitle = propSchema?.title || propKey;
                                    const value = component.props?.[propKey];

                                    if (Array.isArray(propSchema?.enum)) {
                                      return (
                                        <label key={propKey} className="block text-[11px]" data-testid={`admin-content-builder-prop-wrap-${component.id}-${propKey}`}>
                                          {fieldTitle}
                                          <select
                                            className="mt-1 h-8 w-full rounded border px-2 text-[11px]"
                                            value={value ?? propSchema.enum[0]}
                                            onChange={(e) => updateComponentPropValue(row.id, column.id, component.id, propKey, e.target.value)}
                                            data-testid={`admin-content-builder-prop-input-${component.id}-${propKey}`}
                                          >
                                            {propSchema.enum.map((option) => (
                                              <option key={`${propKey}-${option}`} value={option}>{option}</option>
                                            ))}
                                          </select>
                                        </label>
                                      );
                                    }

                                    if (fieldType === 'boolean') {
                                      return (
                                        <label key={propKey} className="inline-flex items-center gap-2 text-[11px]" data-testid={`admin-content-builder-prop-wrap-${component.id}-${propKey}`}>
                                          <input
                                            type="checkbox"
                                            checked={Boolean(value)}
                                            onChange={(e) => updateComponentPropValue(row.id, column.id, component.id, propKey, e.target.checked)}
                                            data-testid={`admin-content-builder-prop-input-${component.id}-${propKey}`}
                                          />
                                          {fieldTitle}
                                        </label>
                                      );
                                    }

                                    if (fieldType === 'object' && propSchema?.properties) {
                                      const objectValue = component.props?.[propKey] && typeof component.props?.[propKey] === 'object'
                                        ? component.props[propKey]
                                        : {};
                                      return (
                                        <div key={propKey} className="rounded border p-2" data-testid={`admin-content-builder-prop-wrap-${component.id}-${propKey}`}>
                                          <div className="text-[11px] font-medium mb-1">{fieldTitle}</div>
                                          <div className="space-y-2">
                                            {Object.entries(propSchema.properties || {}).map(([nestedKey, nestedSchema]) => {
                                              const nestedType = nestedSchema?.type || 'string';
                                              const nestedTitle = nestedSchema?.title || nestedKey;
                                              const nestedValue = objectValue?.[nestedKey];

                                              if (nestedType === 'boolean') {
                                                return (
                                                  <label key={nestedKey} className="inline-flex items-center gap-2 text-[11px]" data-testid={`admin-content-builder-prop-input-${component.id}-${propKey}-${nestedKey}`}>
                                                    <input
                                                      type="checkbox"
                                                      checked={Boolean(nestedValue)}
                                                      onChange={(e) => updateComponentPropValue(row.id, column.id, component.id, propKey, {
                                                        ...objectValue,
                                                        [nestedKey]: e.target.checked,
                                                      })}
                                                    />
                                                    {nestedTitle}
                                                  </label>
                                                );
                                              }

                                              if (nestedType === 'number' || nestedType === 'integer') {
                                                return (
                                                  <label key={nestedKey} className="block text-[11px]">
                                                    {nestedTitle}
                                                    <input
                                                      type="number"
                                                      className="mt-1 h-8 w-full rounded border px-2 text-[11px]"
                                                      value={Number.isFinite(Number(nestedValue)) ? Number(nestedValue) : ''}
                                                      onChange={(e) => updateComponentPropValue(row.id, column.id, component.id, propKey, {
                                                        ...objectValue,
                                                        [nestedKey]: Number(e.target.value || 0),
                                                      })}
                                                    />
                                                  </label>
                                                );
                                              }

                                              return (
                                                <label key={nestedKey} className="block text-[11px]">
                                                  {nestedTitle}
                                                  <input
                                                    type="text"
                                                    className="mt-1 h-8 w-full rounded border px-2 text-[11px]"
                                                    value={nestedValue ?? ''}
                                                    onChange={(e) => updateComponentPropValue(row.id, column.id, component.id, propKey, {
                                                      ...objectValue,
                                                      [nestedKey]: e.target.value,
                                                    })}
                                                  />
                                                </label>
                                              );
                                            })}
                                          </div>
                                        </div>
                                      );
                                    }

                                    if (fieldType === 'array') {
                                      const arrayValue = Array.isArray(value) ? value : [];
                                      const itemType = propSchema?.items?.type || 'string';
                                      return (
                                        <label key={propKey} className="block text-[11px]" data-testid={`admin-content-builder-prop-wrap-${component.id}-${propKey}`}>
                                          {fieldTitle}
                                          <input
                                            type="text"
                                            className="mt-1 h-8 w-full rounded border px-2 text-[11px]"
                                            value={arrayValue.join(', ')}
                                            onChange={(e) => {
                                              const parts = e.target.value
                                                .split(',')
                                                .map((item) => item.trim())
                                                .filter(Boolean);
                                              const parsed = itemType === 'number' || itemType === 'integer'
                                                ? parts.map((item) => Number(item)).filter((item) => Number.isFinite(item))
                                                : parts;
                                              updateComponentPropValue(row.id, column.id, component.id, propKey, parsed);
                                            }}
                                            placeholder="virgülle ayırın"
                                            data-testid={`admin-content-builder-prop-input-${component.id}-${propKey}`}
                                          />
                                        </label>
                                      );
                                    }

                                    if (fieldType === 'number' || fieldType === 'integer') {
                                      return (
                                        <label key={propKey} className="block text-[11px]" data-testid={`admin-content-builder-prop-wrap-${component.id}-${propKey}`}>
                                          {fieldTitle}
                                          <input
                                            type="number"
                                            className="mt-1 h-8 w-full rounded border px-2 text-[11px]"
                                            value={Number.isFinite(Number(value)) ? Number(value) : ''}
                                            onChange={(e) => updateComponentPropValue(row.id, column.id, component.id, propKey, Number(e.target.value || 0))}
                                            data-testid={`admin-content-builder-prop-input-${component.id}-${propKey}`}
                                          />
                                        </label>
                                      );
                                    }

                                    return (
                                      <label key={propKey} className="block text-[11px]" data-testid={`admin-content-builder-prop-wrap-${component.id}-${propKey}`}>
                                        {fieldTitle}
                                        <input
                                          type="text"
                                          className="mt-1 h-8 w-full rounded border px-2 text-[11px]"
                                          value={value ?? ''}
                                          onChange={(e) => updateComponentPropValue(row.id, column.id, component.id, propKey, e.target.value)}
                                          data-testid={`admin-content-builder-prop-input-${component.id}-${propKey}`}
                                        />
                                      </label>
                                    );
                                  })}
                                </div>
                              )}

                              <details className="mt-2" data-testid={`admin-content-builder-component-raw-json-${component.id}`}>
                                <summary className="cursor-pointer text-[11px] text-slate-500">Gelişmiş JSON</summary>
                                <textarea
                                  className="mt-1 min-h-[70px] w-full rounded border p-2 font-mono text-[11px]"
                                  value={JSON.stringify(component.props || {}, null, 2)}
                                  onChange={(e) => {
                                    try {
                                      const parsed = JSON.parse(e.target.value || '{}');
                                      updateComponentField(row.id, column.id, component.id, 'props', parsed);
                                      setError('');
                                    } catch (_err) {
                                      setError('Props JSON geçersiz');
                                    }
                                  }}
                                  data-testid={`admin-content-builder-component-props-input-${component.id}`}
                                />
                              </details>
                            </div>
                            <div className="mt-1 text-[11px] text-slate-500" data-testid={`admin-content-builder-component-order-${component.id}`}>
                              Sıra: {componentIndex + 1}
                            </div>
                          </div>
                        ))}

                        <button
                          type="button"
                          className="h-8 rounded border px-2 text-xs"
                          onClick={() => addComponent(row.id, column.id, getDefaultComponentKey(pageType))}
                          data-testid={`admin-content-builder-column-add-default-component-${column.id}`}
                        >
                          Varsayılan Bileşen Ekle
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </article>
            ))}
          </div>

          <div className="mt-4" data-testid="admin-content-builder-payload-preview-wrap">
            <h3 className="text-xs font-semibold" data-testid="admin-content-builder-payload-preview-title">Payload Preview</h3>
            <textarea
              className="mt-2 min-h-[220px] w-full rounded border p-2 font-mono text-[11px]"
              value={JSON.stringify(payloadJson, null, 2)}
              onChange={(e) => {
                try {
                  const parsed = JSON.parse(e.target.value || '{}');
                  setPayloadJson(parsed);
                  setError('');
                } catch (_err) {
                  setError('Payload JSON geçersiz');
                }
              }}
              data-testid="admin-content-builder-payload-preview-input"
            />
          </div>
        </section>
      </div>
    </div>
  );
}
