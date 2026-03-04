import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import AdSlot from '@/components/public/AdSlot';
import { useLanguage } from '@/contexts/LanguageContext';
import './HomePageRefreshed.css';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const MODULES = [
  { key: 'real_estate', label: 'Emlak', accent: '#ffb119' },
  { key: 'vehicle', label: 'Vasıta', accent: '#ff385c' },
  { key: 'other', label: 'Diğer', accent: '#2da6ff' },
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

const CategoryIcon = ({ item, moduleKey }) => {
  const moduleAccent = MODULES.find((moduleItem) => moduleItem.key === moduleKey)?.accent || '#e2e8f0';
  if (item.icon_svg) {
    return (
      <span
        className="home-kktc-icon"
        style={{ background: `${moduleAccent}22` }}
        dangerouslySetInnerHTML={{ __html: item.icon_svg }}
        data-testid={`home-kktc-category-icon-svg-${item.id}`}
      />
    );
  }
  return (
    <span className="home-kktc-icon" style={{ background: `${moduleAccent}22` }} data-testid={`home-kktc-category-icon-fallback-${item.id}`}>
      {String(item.name || '?').slice(0, 1).toUpperCase()}
    </span>
  );
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
  const [searchInput, setSearchInput] = useState('');
  const [layout, setLayout] = useState(DEFAULT_LAYOUT);
  const [categoriesByModule, setCategoriesByModule] = useState({});
  const [showcaseItems, setShowcaseItems] = useState([]);
  const [recentItems, setRecentItems] = useState([]);
  const [urgentTotal, setUrgentTotal] = useState(0);
  const [expandedModules, setExpandedModules] = useState({});
  const [expandedRoots, setExpandedRoots] = useState({});
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

      const [showcasePayload, recentPayload, urgentPayload] = await Promise.all([
        fetchJsonWithTimeout(`${API}/v2/search?country=${countryCode}&size=${cardCount}&limit=${cardCount}&page=1&doping_type=showcase&sort=date_desc&${cacheBuster}`, {}),
        fetchJsonWithTimeout(`${API}/v2/search?country=${countryCode}&size=${cardCount}&limit=${cardCount}&page=1&sort=date_desc&${cacheBuster}`, {}),
        fetchJsonWithTimeout(`${API}/v2/search?country=${countryCode}&size=1&limit=1&page=1&doping_type=urgent&${cacheBuster}`, {}),
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
      setUrgentTotal(Number(urgentPayload?.pagination?.total ?? urgentPayload?.total ?? 0));
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
    const query = searchInput.trim().toLowerCase();

    return moduleOrder.map((moduleKey) => {
      const moduleLabel = MODULES.find((item) => item.key === moduleKey)?.label || moduleKey;
      const categories = categoriesByModule[moduleKey] || [];
      const byParent = new Map();
      categories.forEach((item) => {
        const parentKey = item.parent_id || 'root';
        if (!byParent.has(parentKey)) byParent.set(parentKey, []);
        byParent.get(parentKey).push(item);
      });

      const orderList = Array.isArray(layout.module_l1_order?.[moduleKey]) ? layout.module_l1_order[moduleKey] : [];
      const orderIndex = new Map(orderList.map((item, index) => [item, index]));
      const rootMode = layout.module_l1_order_mode?.[moduleKey] || 'alphabetical';
      const roots = (byParent.get('root') || [])
        .sort((a, b) => {
          if (rootMode === 'manual') {
            const ai = orderIndex.get(a.id) ?? orderIndex.get(a.slug) ?? Number(a.sort_order || 9999);
            const bi = orderIndex.get(b.id) ?? orderIndex.get(b.slug) ?? Number(b.sort_order || 9999);
            return ai - bi;
          }
          return normalizeLabel(a, language).localeCompare(normalizeLabel(b, language), LANGUAGE_LOCALE_MAP[language] || 'tr-TR');
        })
        .map((root) => {
          const rootName = normalizeLabel(root, language);
          const children = (byParent.get(root.id) || [])
            .sort((a, b) => Number(a.sort_order || 0) - Number(b.sort_order || 0))
            .map((child) => ({
              id: child.id,
              name: normalizeLabel(child, language),
              listing_count: Number(child.listing_count || 0),
              slug: child.slug || child.id,
            }))
            .filter((child) => !query || child.name.toLowerCase().includes(query) || rootName.toLowerCase().includes(query));

          if (query && !rootName.toLowerCase().includes(query) && children.length === 0) return null;

          return {
            id: root.id,
            name: rootName,
            slug: root.slug || root.id,
            icon_svg: root.icon_svg || null,
            listing_count: Number(root.listing_count || 0),
            children,
          };
        })
        .filter(Boolean);

      return {
        module_key: moduleKey,
        module_label: moduleLabel,
        roots,
      };
    });
  }, [categoriesByModule, language, layout.module_l1_order, layout.module_l1_order_mode, moduleOrder, searchInput]);

  const moduleRootLimit = clamp(layout.l1_initial_limit, 1, 20, 6);
  const childLimit = 7;
  const cardColumnCount = clamp(layout.listing_module_grid_columns, 2, 6, 4);

  return (
    <div className="home-kktc-page" data-testid="home-kktc-page">
      <section data-testid="home-kktc-top-ad">
        <AdSlot placement="AD_HOME_TOP" className="mb-3" />
      </section>

      <div className="home-kktc-main" style={{ '--home-left-width': `${layout.column_width}px` }} data-testid="home-kktc-main">
        <aside className="home-kktc-categories" data-testid="home-kktc-category-column">
          <div className="home-kktc-categories-header" data-testid="home-kktc-categories-title">Tüm Kategoriler</div>

          <Link to="/search?doping=urgent" className="home-kktc-urgent-link" data-testid="home-kktc-urgent-link">
            <div className="flex items-center gap-2">
              <span className="home-kktc-urgent-dot" aria-hidden="true" />
              <span className="text-xs font-extrabold text-red-700" data-testid="home-kktc-urgent-label">Acil İlanlar</span>
            </div>
            <span className="text-xs font-bold text-red-700" data-testid="home-kktc-urgent-count">{formatCount(urgentTotal)}</span>
          </Link>

          <div className="home-kktc-search-wrap" data-testid="home-kktc-category-search-wrap">
            <input
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
              className="home-kktc-search"
              placeholder="Kategori ara..."
              data-testid="home-kktc-category-search-input"
            />
          </div>

          <div className="home-kktc-modules" data-testid="home-kktc-module-list">
            {loading ? (
              <div className="home-kktc-empty" data-testid="home-kktc-categories-loading">Kategoriler yükleniyor...</div>
            ) : moduleGroups.map((moduleGroup) => {
              const expandedModule = Boolean(expandedModules[moduleGroup.module_key]);
              const visibleRoots = expandedModule ? moduleGroup.roots : moduleGroup.roots.slice(0, moduleRootLimit);
              const moduleAccent = MODULES.find((item) => item.key === moduleGroup.module_key)?.accent || '#cbd5e1';

              return (
                <section key={moduleGroup.module_key} className="home-kktc-module" data-testid={`home-kktc-module-${moduleGroup.module_key}`}>
                  <div className="home-kktc-module-title" style={{ background: `${moduleAccent}1f` }} data-testid={`home-kktc-module-title-${moduleGroup.module_key}`}>
                    <span>{moduleGroup.module_label}</span>
                    <span>{formatCount(moduleGroup.roots.length)}</span>
                  </div>

                  {visibleRoots.map((root) => {
                    const expandedRoot = Boolean(expandedRoots[root.id]);
                    const visibleChildren = expandedRoot ? root.children : root.children.slice(0, childLimit);
                    return (
                      <div className="home-kktc-root-row" key={root.id} data-testid={`home-kktc-root-row-${root.id}`}>
                        <Link to={`/search?category=${encodeURIComponent(root.slug)}`} className="home-kktc-root-link" data-testid={`home-kktc-root-link-${root.id}`}>
                          <CategoryIcon item={root} moduleKey={moduleGroup.module_key} />
                          <span className="home-kktc-root-name" data-testid={`home-kktc-root-name-${root.id}`}>{root.name}</span>
                          <span className="home-kktc-count" data-testid={`home-kktc-root-count-${root.id}`}>({formatCount(root.listing_count)})</span>
                        </Link>

                        {visibleChildren.length > 0 ? (
                          <div className="home-kktc-child-list" data-testid={`home-kktc-child-list-${root.id}`}>
                            {visibleChildren.map((child) => (
                              <Link
                                key={child.id}
                                to={`/search?category=${encodeURIComponent(child.slug)}`}
                                className="home-kktc-child-link"
                                data-testid={`home-kktc-child-link-${child.id}`}
                              >
                                <span className="home-kktc-child-name" data-testid={`home-kktc-child-name-${child.id}`}>{child.name}</span>
                                <span className="home-kktc-child-count" data-testid={`home-kktc-child-count-${child.id}`}>{formatCount(child.listing_count)}</span>
                              </Link>
                            ))}
                          </div>
                        ) : null}

                        {root.children.length > childLimit ? (
                          <button
                            type="button"
                            className="home-kktc-toggle-btn"
                            onClick={() => setExpandedRoots((prev) => ({ ...prev, [root.id]: !expandedRoot }))}
                            data-testid={`home-kktc-root-toggle-${root.id}`}
                          >
                            {expandedRoot ? 'Daha az göster' : 'Tümünü göster'}
                          </button>
                        ) : null}
                      </div>
                    );
                  })}

                  {moduleGroup.roots.length > moduleRootLimit ? (
                    <div className="px-2 pb-2">
                      <button
                        type="button"
                        className="home-kktc-toggle-btn"
                        onClick={() => setExpandedModules((prev) => ({ ...prev, [moduleGroup.module_key]: !expandedModule }))}
                        data-testid={`home-kktc-module-toggle-${moduleGroup.module_key}`}
                      >
                        {expandedModule ? 'Daha az göster' : 'Devamını Gör'}
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
    </div>
  );
}
