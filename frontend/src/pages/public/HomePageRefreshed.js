import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import AdSlot from '@/components/public/AdSlot';
import LayoutRenderer from '@/components/layout-builder/LayoutRenderer';
import { useLanguage } from '@/contexts/LanguageContext';
import { useContentLayoutResolve } from '@/hooks/useContentLayoutResolve';
import './HomePageRefreshed.css';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const MODULES = [
  { key: 'real_estate', label: 'Emlak', accent: '#f5a300' },
  { key: 'vehicle', label: 'Vasıta', accent: '#ff3355' },
  { key: 'other', label: 'Diğer', accent: '#a55df8' },
];

const LANGUAGE_LOCALE_MAP = {
  tr: 'tr-TR',
  de: 'de-DE',
  fr: 'fr-FR',
};

const SLIDES = [
  {
    image: '/homepage/slide-1.jpg',
    title: 'KKTC’nin ilan sitesi artık daha hızlı ve daha görünür.',
    ctaLabel: 'Ücretsiz İlan Ver',
    ctaUrl: '/ilan-ver',
  },
  {
    image: '/homepage/slide-2.jpg',
    title: 'WhatsApp destek hattı ile 7/24 ilan süreçlerinde yanınızdayız.',
    ctaLabel: 'Destek Merkezi',
    ctaUrl: '/bilgi/yardim-merkezi',
  },
  {
    image: '/homepage/slide-3.jpg',
    title: 'Vitrin ve Acil seçenekleriyle ilanlarınızı öne çıkarın.',
    ctaLabel: 'Vitrin İlanları',
    ctaUrl: '/search?doping=showcase',
  },
];

const DEFAULT_LAYOUT = {
  column_width: 304,
  l1_initial_limit: 6,
  module_order_mode: 'manual',
  module_order: MODULES.map((item) => item.key),
  module_l1_order_mode: {},
  module_l1_order: {},
  listing_module_grid_columns: 4,
  listing_lx_limit: 8,
};

const clamp = (value, min, max, fallback) => {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return fallback;
  return Math.max(min, Math.min(max, Math.floor(parsed)));
};

const formatCount = (value) => {
  const numeric = Number(value || 0);
  if (!Number.isFinite(numeric)) return '0';
  return numeric.toLocaleString('tr-TR');
};

const formatPrice = (value, currency = 'EUR') => {
  const numeric = Number(value || 0);
  if (!Number.isFinite(numeric)) return '-';
  return new Intl.NumberFormat('tr-TR', { style: 'currency', currency, maximumFractionDigits: 0 }).format(numeric);
};

const normalizeLayout = (raw) => {
  const source = raw || {};
  const rawModuleOrder = Array.isArray(source.module_order) ? source.module_order : [];
  const uniqueOrder = [];
  const seen = new Set();
  rawModuleOrder.forEach((item) => {
    const key = String(item || '').trim();
    if (!key || seen.has(key)) return;
    uniqueOrder.push(key);
    seen.add(key);
  });
  MODULES.forEach((item) => {
    if (!uniqueOrder.includes(item.key)) uniqueOrder.push(item.key);
  });

  return {
    column_width: clamp(source.column_width, 240, 420, DEFAULT_LAYOUT.column_width),
    l1_initial_limit: clamp(source.l1_initial_limit, 1, 20, DEFAULT_LAYOUT.l1_initial_limit),
    module_order_mode: source.module_order_mode === 'alphabetical' ? 'alphabetical' : 'manual',
    module_order: uniqueOrder,
    module_l1_order_mode: typeof source.module_l1_order_mode === 'object' && source.module_l1_order_mode ? source.module_l1_order_mode : {},
    module_l1_order: typeof source.module_l1_order === 'object' && source.module_l1_order ? source.module_l1_order : {},
    listing_module_grid_columns: clamp(source.listing_module_grid_columns, 2, 6, DEFAULT_LAYOUT.listing_module_grid_columns),
    listing_lx_limit: clamp(source.listing_lx_limit, 4, 20, DEFAULT_LAYOUT.listing_lx_limit),
  };
};

const normalizeLabel = (category, language = 'tr') => {
  if (!category) return '';
  const translated = Array.isArray(category.translations)
    ? category.translations.find((item) => item?.language === language)?.name
      || category.translations.find((item) => item?.language === 'tr')?.name
      || category.translations[0]?.name
    : '';
  return translated || category.name || category.slug || '';
};

const fetchJsonWithTimeout = async (url, fallback = {}, timeoutMs = 7000) => {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, { cache: 'no-store', signal: controller.signal });
    const payload = await response.json().catch(() => fallback);
    return payload ?? fallback;
  } catch (_error) {
    return fallback;
  } finally {
    clearTimeout(timer);
  }
};

const ListingCard = ({ item, prefix }) => (
  <Link to={`/ilan/${item.id}`} className="home-kktc-card" data-testid={`${prefix}-card-${item.id}`}>
    <div className="home-kktc-card-image" data-testid={`${prefix}-image-wrap-${item.id}`}>
      {item.image ? <img src={item.image} alt={item.title || 'İlan'} data-testid={`${prefix}-image-${item.id}`} /> : null}
    </div>
    <div className="home-kktc-card-body" data-testid={`${prefix}-body-${item.id}`}>
      <div className="home-kktc-badges" data-testid={`${prefix}-badges-${item.id}`}>
        {item.is_featured ? <span className="home-kktc-badge home-kktc-badge-featured" data-testid={`${prefix}-featured-${item.id}`}>Vitrin</span> : null}
        {item.is_urgent ? <span className="home-kktc-badge home-kktc-badge-urgent" data-testid={`${prefix}-urgent-${item.id}`}>Acil</span> : null}
      </div>
      <div className="home-kktc-card-title" data-testid={`${prefix}-title-${item.id}`}>{item.title || '-'}</div>
      <div className="home-kktc-card-meta" data-testid={`${prefix}-meta-${item.id}`}>
        <span data-testid={`${prefix}-city-${item.id}`}>{item.city || '-'}</span>
        <span className="home-kktc-card-price" data-testid={`${prefix}-price-${item.id}`}>{formatPrice(item.price_amount || item.price, item.currency || 'EUR')}</span>
      </div>
    </div>
  </Link>
);

export default function HomePageRefreshed() {
  const { language } = useLanguage();
  const [loading, setLoading] = useState(true);
  const [layout, setLayout] = useState(DEFAULT_LAYOUT);
  const [categoriesByModule, setCategoriesByModule] = useState({});
  const [showcaseItems, setShowcaseItems] = useState([]);
  const [recentItems, setRecentItems] = useState([]);
  const [expandedModules, setExpandedModules] = useState({});
  const [activeSlide, setActiveSlide] = useState(0);

  const countryCode = useMemo(() => (localStorage.getItem('selected_country') || 'DE').toUpperCase(), []);

  useEffect(() => {
    let active = true;

    const loadData = async () => {
      setLoading(true);
      const cacheBuster = `_ts=${Date.now()}`;
      const categoryPromises = MODULES.map((moduleItem) => (
        fetchJsonWithTimeout(`${API}/categories?module=${moduleItem.key}&country=${countryCode}&${cacheBuster}`, [])
      ));

      const [layoutPayload, ...categoryPayloads] = await Promise.all([
        fetchJsonWithTimeout(`${API}/site/home-category-layout?country=${countryCode}&${cacheBuster}`, {}),
        ...categoryPromises,
      ]);

      const nextLayout = normalizeLayout(layoutPayload?.config);
      const cardCount = Math.max(4, nextLayout.listing_lx_limit || 8);

      const [showcasePayload, recentPayload] = await Promise.all([
        fetchJsonWithTimeout(`${API}/v2/search?country=${countryCode}&size=${cardCount}&limit=${cardCount}&page=1&doping_type=showcase&sort=date_desc&${cacheBuster}`, {}),
        fetchJsonWithTimeout(`${API}/v2/search?country=${countryCode}&size=${cardCount}&limit=${cardCount}&page=1&sort=date_desc&${cacheBuster}`, {}),
      ]);

      if (!active) return;

      const categoryMap = {};
      MODULES.forEach((moduleItem, index) => {
        const payload = categoryPayloads[index];
        categoryMap[moduleItem.key] = Array.isArray(payload) ? payload : [];
      });

      setLayout(nextLayout);
      setCategoriesByModule(categoryMap);
      setShowcaseItems(Array.isArray(showcasePayload?.items) ? showcasePayload.items : []);
      setRecentItems(Array.isArray(recentPayload?.items) ? recentPayload.items : []);
      setLoading(false);
    };

    loadData();
    const interval = setInterval(loadData, 5 * 60 * 1000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [countryCode]);

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveSlide((prev) => (prev + 1) % SLIDES.length);
    }, 4500);
    return () => clearInterval(timer);
  }, []);

  const moduleOrder = useMemo(() => {
    const baseOrder = Array.isArray(layout.module_order) ? layout.module_order : MODULES.map((moduleItem) => moduleItem.key);
    if (layout.module_order_mode === 'alphabetical') {
      return [...MODULES]
        .sort((a, b) => a.label.localeCompare(b.label, LANGUAGE_LOCALE_MAP[language] || 'tr-TR'))
        .map((item) => item.key);
    }
    return baseOrder;
  }, [layout.module_order, layout.module_order_mode, language]);

  const moduleGroups = useMemo(() => {
    return moduleOrder.map((moduleKey) => {
      const moduleMeta = MODULES.find((item) => item.key === moduleKey) || { key: moduleKey, label: moduleKey, accent: '#64748b' };
      const categories = categoriesByModule[moduleKey] || [];
      const byId = new Map();
      const byParent = new Map();
      categories.forEach((item) => {
        byId.set(item.id, item);
        const parentKey = item.parent_id || 'root';
        if (!byParent.has(parentKey)) byParent.set(parentKey, []);
        byParent.get(parentKey).push(item);
      });

      const aggregateCache = new Map();
      const aggregateCount = (categoryId) => {
        if (!categoryId) return 0;
        if (aggregateCache.has(categoryId)) return aggregateCache.get(categoryId);
        const node = byId.get(categoryId);
        if (!node) return 0;
        const own = Number(node.listing_count || 0);
        const children = byParent.get(categoryId) || [];
        const total = own + children.reduce((sum, child) => sum + aggregateCount(child.id), 0);
        aggregateCache.set(categoryId, total);
        return total;
      };

      const orderList = Array.isArray(layout.module_l1_order?.[moduleKey]) ? layout.module_l1_order[moduleKey] : [];
      const orderIndex = new Map(orderList.map((item, index) => [item, index]));
      const rootMode = layout.module_l1_order_mode?.[moduleKey] || 'alphabetical';
      const roots = [...(byParent.get('root') || [])]
        .sort((a, b) => {
          if (rootMode === 'manual') {
            const ai = orderIndex.get(a.id) ?? orderIndex.get(a.slug) ?? Number(a.sort_order || 9999);
            const bi = orderIndex.get(b.id) ?? orderIndex.get(b.slug) ?? Number(b.sort_order || 9999);
            return ai - bi;
          }
          return normalizeLabel(a, language).localeCompare(normalizeLabel(b, language), LANGUAGE_LOCALE_MAP[language] || 'tr-TR');
        });

      const rootRows = roots.map((root) => {
        const children = [...(byParent.get(root.id) || [])]
          .sort((a, b) => Number(a.sort_order || 0) - Number(b.sort_order || 0))
          .map((child) => ({
            id: child.id,
            name: normalizeLabel(child, language),
            slug: child.slug || child.id,
            total_count: aggregateCount(child.id),
          }));

        return {
          id: root.id,
          name: normalizeLabel(root, language),
          slug: root.slug || root.id,
          icon_svg: root.icon_svg || null,
          total_count: aggregateCount(root.id),
          children,
        };
      });

      return {
        module_key: moduleKey,
        module_label: moduleMeta.label,
        module_accent: moduleMeta.accent,
        module_total_count: rootRows.reduce((sum, row) => sum + Number(row.total_count || 0), 0),
        roots: rootRows,
      };
    });
  }, [categoriesByModule, language, layout.module_l1_order, layout.module_l1_order_mode, moduleOrder]);

  const moduleRootLimit = clamp(layout.l1_initial_limit, 1, 20, 6);
  const cardColumnCount = clamp(layout.listing_module_grid_columns, 2, 6, 4);

  const {
    layout: resolvedHomeLayout,
    hasLayoutRows: hasRuntimeHomeLayout,
  } = useContentLayoutResolve({
    country: countryCode,
    module: 'global',
    pageType: 'home',
    enabled: Boolean(countryCode),
  });

  const renderHomeStaticSections = () => (
    <>
      <section data-testid="home-kktc-top-ad">
        <AdSlot placement="AD_HOME_TOP" className="mb-3" />
      </section>

      <div className="home-kktc-main" style={{ '--home-left-width': `${layout.column_width}px` }} data-testid="home-kktc-main">
        <aside className="home-kktc-categories" data-testid="home-kktc-category-column">
          <Link to="/search?doping=urgent" className="home-kktc-urgent-link" data-testid="home-kktc-urgent-link">
            ACİL İLANLAR
          </Link>

          <div className="home-kktc-modules" data-testid="home-kktc-module-list">
            {loading ? (
              <div className="home-kktc-empty" data-testid="home-kktc-categories-loading">Kategoriler yükleniyor...</div>
            ) : moduleGroups.map((moduleGroup) => {
              const expandedModule = Boolean(expandedModules[moduleGroup.module_key]);
              const visibleRoots = expandedModule ? moduleGroup.roots : moduleGroup.roots.slice(0, moduleRootLimit);

              return (
                <section key={moduleGroup.module_key} className="home-kktc-module" data-testid={`home-kktc-module-${moduleGroup.module_key}`}>
                  <div className="home-kktc-plain-list" data-testid={`home-kktc-plain-list-${moduleGroup.module_key}`}>
                    {visibleRoots.map((root) => (
                      <div key={root.id} className="home-kktc-root-group" data-testid={`home-kktc-root-group-${root.id}`}>
                        <Link
                          to={`/search?category=${encodeURIComponent(root.slug)}`}
                          className="home-kktc-root-line"
                          data-testid={`home-kktc-root-line-${root.id}`}
                        >
                          {root.icon_svg ? (
                            <span className="home-kktc-root-icon-svg" data-testid={`home-kktc-root-icon-svg-${root.id}`} dangerouslySetInnerHTML={{ __html: root.icon_svg }} />
                          ) : null}
                          <span className="home-kktc-root-line-text" data-testid={`home-kktc-root-line-text-${root.id}`}>
                            {root.name}
                            <span className="home-kktc-root-count" data-testid={`home-kktc-root-count-${root.id}`}> ({formatCount(root.total_count)})</span>
                          </span>
                        </Link>

                        {root.children.length > 0 ? (
                          <div className="home-kktc-child-lines" data-testid={`home-kktc-child-lines-${root.id}`}>
                            {root.children.map((child) => (
                              <Link
                                key={child.id}
                                to={`/search?category=${encodeURIComponent(child.slug)}`}
                                className="home-kktc-child-line"
                                data-testid={`home-kktc-child-line-${child.id}`}
                              >
                                {child.name}
                                <span className="home-kktc-child-count" data-testid={`home-kktc-child-count-${child.id}`}> ({formatCount(child.total_count)})</span>
                              </Link>
                            ))}
                          </div>
                        ) : null}
                      </div>
                    ))}
                  </div>

                  {moduleGroup.roots.length > moduleRootLimit ? (
                    <div className="home-kktc-module-toggle-wrap" data-testid={`home-kktc-module-toggle-wrap-${moduleGroup.module_key}`}>
                      <button
                        type="button"
                        className="home-kktc-module-toggle"
                        onClick={() => setExpandedModules((prev) => ({ ...prev, [moduleGroup.module_key]: !expandedModule }))}
                        data-testid={`home-kktc-module-toggle-${moduleGroup.module_key}`}
                      >
                        {expandedModule ? 'Daha Az Göster' : 'Tümünü Göster'}
                      </button>
                    </div>
                  ) : null}
                </section>
              );
            })}
          </div>
        </aside>

        <section className="home-kktc-content" data-testid="home-kktc-content-column">
          <div className="home-kktc-slider" data-testid="home-kktc-slider">
            <div className="home-kktc-slider-track" style={{ transform: `translateX(-${activeSlide * 100}%)` }} data-testid="home-kktc-slider-track">
              {SLIDES.map((slide, index) => (
                <article className="home-kktc-slide" key={slide.image} data-testid={`home-kktc-slide-${index}`}>
                  <img src={slide.image} alt={slide.title} data-testid={`home-kktc-slide-image-${index}`} />
                  <div className="home-kktc-slide-overlay" data-testid={`home-kktc-slide-overlay-${index}`}>
                    <h2 className="home-kktc-slide-title" data-testid={`home-kktc-slide-title-${index}`}>{slide.title}</h2>
                    <Link to={slide.ctaUrl} className="home-kktc-slide-cta" data-testid={`home-kktc-slide-cta-${index}`}>{slide.ctaLabel}</Link>
                  </div>
                </article>
              ))}
            </div>
            <div className="home-kktc-slider-dots" data-testid="home-kktc-slider-dots">
              {SLIDES.map((_slide, index) => (
                <button
                  key={`dot-${index}`}
                  type="button"
                  className={`home-kktc-slider-dot ${activeSlide === index ? 'active' : ''}`}
                  onClick={() => setActiveSlide(index)}
                  data-testid={`home-kktc-slider-dot-${index}`}
                />
              ))}
            </div>
          </div>

          <section className="home-kktc-section" data-testid="home-kktc-showcase-section">
            <div className="home-kktc-section-head" data-testid="home-kktc-showcase-head">
              <h3 className="home-kktc-section-title" data-testid="home-kktc-showcase-title">Vitrin İlanları</h3>
              <Link to="/search?doping=showcase" className="home-kktc-section-link" data-testid="home-kktc-showcase-all-link">Tümünü Gör</Link>
            </div>
            {loading ? (
              <div className="home-kktc-empty" data-testid="home-kktc-showcase-loading">Vitrin ilanları yükleniyor...</div>
            ) : showcaseItems.length === 0 ? (
              <div className="home-kktc-empty" data-testid="home-kktc-showcase-empty">Vitrin alanında aktif ilan bulunmuyor.</div>
            ) : (
              <div className="home-kktc-grid" style={{ gridTemplateColumns: `repeat(${cardColumnCount}, minmax(0, 1fr))` }} data-testid="home-kktc-showcase-grid">
                {showcaseItems.slice(0, layout.listing_lx_limit).map((item) => (
                  <ListingCard key={item.id} item={item} prefix="home-kktc-showcase" />
                ))}
              </div>
            )}
          </section>

          <section className="home-kktc-section" data-testid="home-kktc-recent-section">
            <div className="home-kktc-section-head" data-testid="home-kktc-recent-head">
              <h3 className="home-kktc-section-title" data-testid="home-kktc-recent-title">Son İlanlar</h3>
              <Link to="/search?sort=date_desc" className="home-kktc-section-link" data-testid="home-kktc-recent-all-link">Tümünü Gör</Link>
            </div>
            {loading ? (
              <div className="home-kktc-empty" data-testid="home-kktc-recent-loading">Son ilanlar yükleniyor...</div>
            ) : recentItems.length === 0 ? (
              <div className="home-kktc-empty" data-testid="home-kktc-recent-empty">Henüz ilan bulunmuyor.</div>
            ) : (
              <div className="home-kktc-grid" style={{ gridTemplateColumns: `repeat(${cardColumnCount}, minmax(0, 1fr))` }} data-testid="home-kktc-recent-grid">
                {recentItems.slice(0, layout.listing_lx_limit).map((item) => (
                  <ListingCard key={item.id} item={item} prefix="home-kktc-recent" />
                ))}
              </div>
            )}
          </section>

          <section data-testid="home-kktc-bottom-ad">
            <AdSlot placement="AD_LOGIN_1" className="rounded-xl border" />
          </section>
        </section>
      </div>
    </>
  );

  const runtimeRegistry = {
    'home.default-content': () => <>{renderHomeStaticSections()}</>,
    'shared.text-block': ({ props }) => (
      <section className="rounded-xl border bg-white p-4" data-testid="home-runtime-text-block">
        <h2 className="text-base font-semibold" data-testid="home-runtime-text-title">{props?.title || 'Başlık'}</h2>
        <p className="text-sm text-slate-600 mt-1" data-testid="home-runtime-text-body">{props?.body || ''}</p>
      </section>
    ),
    'shared.ad-slot': ({ props }) => (
      <section data-testid="home-runtime-ad-slot">
        <AdSlot placement={props?.placement || 'AD_HOME_TOP'} className="rounded-xl border" />
      </section>
    ),
  };

  return (
    <div className="home-kktc-page" data-testid="home-kktc-page">
      {hasRuntimeHomeLayout ? (
        <LayoutRenderer
          payload={resolvedHomeLayout?.revision?.payload_json}
          registry={runtimeRegistry}
          dataTestIdPrefix="home-runtime-layout"
        />
      ) : renderHomeStaticSections()}
    </div>
  );
}
