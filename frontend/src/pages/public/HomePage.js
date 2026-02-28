import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import AdSlot from '@/components/public/AdSlot';
import './HomePage.css';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const DEFAULT_SHOWCASE_LAYOUT = {
  homepage: { enabled: true, rows: 3, columns: 4, listing_count: 12 },
};

const MODULE_CONFIG = [
  { key: 'real_estate', label: 'Emlak' },
  { key: 'vehicle', label: 'Vasıta' },
  { key: 'other', label: 'Diğer' },
];

const MODULE_ROOT_LIMIT = 8;
const ROOT_CHILD_LIMIT = 8;

const clamp = (value, min, max, fallback) => {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return fallback;
  return Math.min(max, Math.max(min, Math.floor(parsed)));
};

const normalizeShowcaseLayout = (raw) => {
  const source = raw || {};
  const homepage = source.homepage || {};
  return {
    homepage: {
      enabled: homepage.enabled !== false,
      rows: clamp(homepage.rows, 1, 12, 3),
      columns: clamp(homepage.columns, 1, 8, 4),
      listing_count: clamp(homepage.listing_count, 1, 120, 12),
    },
  };
};

const resolveEffectiveCount = (block) => Math.min(Number(block?.listing_count || 0), Number(block?.rows || 0) * Number(block?.columns || 0));
const normalizeGridColumns = (value, fallback = 4) => clamp(value, 1, 8, fallback);

const formatNumber = (value) => {
  const numeric = Number(value || 0);
  if (!Number.isFinite(numeric)) return '0';
  return numeric.toLocaleString('tr-TR');
};

const formatPrice = (value, currency = 'EUR') => {
  const numeric = Number(value || 0);
  if (!Number.isFinite(numeric)) return '-';
  return new Intl.NumberFormat('tr-TR', { style: 'currency', currency, maximumFractionDigits: 0 }).format(numeric);
};

const normalizeLabel = (category) => {
  if (!category) return '';
  const translated = Array.isArray(category.translations)
    ? category.translations.find((item) => item?.language === 'tr')?.name
      || category.translations[0]?.name
    : '';
  return translated || category.name || category.slug || '';
};

export default function HomePage() {
  const [loading, setLoading] = useState(true);
  const [searchInput, setSearchInput] = useState('');
  const [categoriesByModule, setCategoriesByModule] = useState({});
  const [showcaseItems, setShowcaseItems] = useState([]);
  const [showcaseLayout, setShowcaseLayout] = useState(DEFAULT_SHOWCASE_LAYOUT);
  const [urgentTotal, setUrgentTotal] = useState(0);
  const [expandedModules, setExpandedModules] = useState({});
  const [expandedRoots, setExpandedRoots] = useState({});

  const countryCode = useMemo(() => (localStorage.getItem('selected_country') || 'DE').toUpperCase(), []);

  useEffect(() => {
    let active = true;

    const loadData = async () => {
      setLoading(true);
      try {
        const categoryRequests = MODULE_CONFIG.map((moduleItem) => fetch(`${API}/categories?module=${moduleItem.key}&country=${countryCode}`));
        const [layoutResult, ...categoryResults] = await Promise.allSettled([
          fetch(`${API}/site/showcase-layout?_ts=${Date.now()}`, { cache: 'no-store' }),
          ...categoryRequests,
        ]);

        const nextCategoriesByModule = {};
        for (let index = 0; index < MODULE_CONFIG.length; index += 1) {
          const moduleKey = MODULE_CONFIG[index].key;
          const result = categoryResults[index];
          if (result?.status === 'fulfilled') {
            const payload = await result.value.json().catch(() => []);
            nextCategoriesByModule[moduleKey] = Array.isArray(payload) ? payload : [];
          } else {
            nextCategoriesByModule[moduleKey] = [];
          }
        }

        let nextLayout = DEFAULT_SHOWCASE_LAYOUT;
        if (layoutResult.status === 'fulfilled') {
          const layoutPayload = await layoutResult.value.json().catch(() => ({}));
          nextLayout = normalizeShowcaseLayout(layoutPayload?.config);
        }

        const homeLimit = Math.max(1, resolveEffectiveCount(nextLayout.homepage));

        let showcaseItemsPayload = [];
        try {
          const showcaseRes = await fetch(`${API}/v2/search?country=${countryCode}&limit=${homeLimit}&page=1&doping_type=showcase`);
          const showcasePayload = await showcaseRes.json().catch(() => ({}));
          showcaseItemsPayload = Array.isArray(showcasePayload?.items) ? showcasePayload.items : [];
        } catch (_err) {
          showcaseItemsPayload = [];
        }

        let urgentPayloadTotal = 0;
        try {
          const urgentRes = await fetch(`${API}/v2/search?country=${countryCode}&limit=1&page=1&doping_type=urgent`);
          const urgentPayload = await urgentRes.json().catch(() => ({}));
          urgentPayloadTotal = Number(urgentPayload?.pagination?.total || 0);
        } catch (_err) {
          urgentPayloadTotal = 0;
        }

        if (!active) return;
        setCategoriesByModule(nextCategoriesByModule);
        setShowcaseItems(showcaseItemsPayload);
        setShowcaseLayout(nextLayout);
        setUrgentTotal(urgentPayloadTotal);
      } finally {
        if (active) setLoading(false);
      }
    };

    loadData();
    const interval = setInterval(loadData, 5 * 60 * 1000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [countryCode]);

  const moduleGroups = useMemo(() => {
    const query = searchInput.trim().toLowerCase();

    return MODULE_CONFIG.map((moduleItem) => {
      const categories = categoriesByModule[moduleItem.key] || [];
      const byParent = new Map();
      categories.forEach((item) => {
        const key = item.parent_id || 'root';
        if (!byParent.has(key)) byParent.set(key, []);
        byParent.get(key).push(item);
      });

      const roots = (byParent.get('root') || [])
        .sort((a, b) => Number(a.sort_order || 0) - Number(b.sort_order || 0))
        .map((root) => {
          const rootName = normalizeLabel(root);
          const rawChildren = (byParent.get(root.id) || []).sort((a, b) => Number(a.sort_order || 0) - Number(b.sort_order || 0));
          const rootMatches = rootName.toLowerCase().includes(query);

          const children = rawChildren.filter((child) => {
            if (!query) return true;
            return rootMatches || normalizeLabel(child).toLowerCase().includes(query);
          });

          if (query && !rootMatches && children.length === 0) return null;

          const rootTotalCount = Number(root.listing_count || 0) || children.reduce((sum, child) => sum + Number(child.listing_count || 0), 0);
          return {
            id: root.id,
            name: rootName,
            total_count: rootTotalCount,
            url: `/search?category=${encodeURIComponent(root.slug || root.id)}`,
            children_level1: children.map((child) => ({
              id: child.id,
              name: normalizeLabel(child),
              listing_count: Number(child.listing_count || 0),
              url: `/search?category=${encodeURIComponent(child.slug || child.id)}`,
            })),
          };
        })
        .filter(Boolean);

      return {
        module_key: moduleItem.key,
        module_label: moduleItem.label,
        roots,
      };
    });
  }, [categoriesByModule, searchInput]);

  const homeShowcaseBlock = useMemo(() => showcaseLayout.homepage || DEFAULT_SHOWCASE_LAYOUT.homepage, [showcaseLayout]);
  const homeShowcaseCount = useMemo(() => Math.max(1, resolveEffectiveCount(homeShowcaseBlock)), [homeShowcaseBlock]);
  const homeGridColumnClass = useMemo(() => `home-v2-showcase-grid-cols-${normalizeGridColumns(homeShowcaseBlock.columns, 4)}`, [homeShowcaseBlock.columns]);
  const showcaseVisibleItems = useMemo(() => (Array.isArray(showcaseItems) ? showcaseItems.slice(0, homeShowcaseCount) : []), [showcaseItems, homeShowcaseCount]);

  return (
    <div className="home-v2-page" data-testid="home-v2-page">
      <section className="home-v2-ad-top" data-testid="home-v2-top-ad-wrap">
        <AdSlot placement="AD_HOME_TOP" className="home-v2-ad-slot" />
      </section>

      <div className="home-v2-main-grid" data-testid="home-v2-main-grid">
        <aside className="home-v2-left-card" data-testid="home-v2-left-column">
          <Link to="/search?doping=urgent" className="home-v2-urgent-row home-v2-urgent-link" data-testid="home-v2-urgent-row">
            <span className="home-v2-urgent-dot" aria-hidden="true" />
            <span className="home-v2-urgent-text" data-testid="home-v2-urgent-text">ACİL ({formatNumber(urgentTotal)})</span>
          </Link>

          <div className="home-v2-category-search-wrap" data-testid="home-v2-category-search-wrap">
            <input
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
              placeholder="Kategori ara..."
              className="home-v2-category-search"
              data-testid="home-v2-category-search-input"
            />
          </div>

          <div className="home-v2-category-list" data-testid="home-v2-category-list">
            {loading ? (
              <div className="home-v2-empty" data-testid="home-v2-category-loading">Kategoriler yükleniyor...</div>
            ) : moduleGroups.every((moduleGroup) => moduleGroup.roots.length === 0) ? (
              <div className="home-v2-empty" data-testid="home-v2-category-empty">Kategori bulunamadı</div>
            ) : moduleGroups.map((moduleGroup) => {
              const moduleExpanded = !!expandedModules[moduleGroup.module_key];
              const visibleRoots = moduleExpanded ? moduleGroup.roots : moduleGroup.roots.slice(0, MODULE_ROOT_LIMIT);

              return (
                <section key={moduleGroup.module_key} className="home-v2-module-group" data-testid={`home-v2-module-group-${moduleGroup.module_key}`}>
                  <div className="home-v2-module-title" data-testid={`home-v2-module-title-${moduleGroup.module_key}`}>
                    {moduleGroup.module_label}
                  </div>

                  {visibleRoots.map((root) => {
                    const rootExpanded = !!expandedRoots[root.id];
                    const visibleChildren = rootExpanded ? root.children_level1 : root.children_level1.slice(0, ROOT_CHILD_LIMIT);

                    return (
                      <div key={root.id} className="home-v2-category-row" data-testid={`home-v2-category-row-${root.id}`}>
                        <Link to={root.url} className="home-v2-root-link" data-testid={`home-v2-root-link-${root.id}`}>
                          <span className="home-v2-root-title" data-testid={`home-v2-root-title-${root.id}`}>{root.name}</span>
                        </Link>

                        {visibleChildren.length > 0 ? (
                          <div className="home-v2-child-list" data-testid={`home-v2-child-list-${root.id}`}>
                            {visibleChildren.map((child) => (
                              <Link
                                key={child.id}
                                to={child.url}
                                className="home-v2-first-child"
                                data-testid={`home-v2-first-child-link-${child.id}`}
                              >
                                <span className="home-v2-first-child-title" data-testid={`home-v2-first-child-title-${child.id}`}>{child.name}</span>
                                <span className="home-v2-first-child-count" data-testid={`home-v2-first-child-count-${child.id}`}>
                                  ({formatNumber(child.listing_count)})
                                </span>
                              </Link>
                            ))}
                          </div>
                        ) : null}

                        {root.children_level1.length > ROOT_CHILD_LIMIT ? (
                          <button
                            type="button"
                            className="home-v2-toggle-btn"
                            onClick={() => setExpandedRoots((prev) => ({ ...prev, [root.id]: !rootExpanded }))}
                            data-testid={`home-v2-root-toggle-${root.id}`}
                          >
                            {rootExpanded ? 'Daha az göster' : 'Daha fazla göster'}
                          </button>
                        ) : null}
                      </div>
                    );
                  })}

                  {moduleGroup.roots.length > MODULE_ROOT_LIMIT ? (
                    <button
                      type="button"
                      className="home-v2-toggle-btn"
                      onClick={() => setExpandedModules((prev) => ({ ...prev, [moduleGroup.module_key]: !moduleExpanded }))}
                      data-testid={`home-v2-module-toggle-${moduleGroup.module_key}`}
                    >
                      {moduleExpanded ? 'Daha az göster' : 'Tümünü Göster'}
                    </button>
                  ) : null}
                </section>
              );
            })}
          </div>
        </aside>

        <section className="home-v2-right-content" data-testid="home-v2-right-content">
          <div className="home-v2-toolbar" data-testid="home-v2-toolbar">
            <Link to="/search?doping=showcase" className="home-v2-showcase-link" data-testid="home-v2-showcase-all-link">
              Tüm vitrin ilanlarını göster
            </Link>
          </div>

          {homeShowcaseBlock.enabled !== false ? (
            <div className={`home-v2-showcase-grid ${homeGridColumnClass}`} data-testid="home-v2-showcase-grid">
              {loading ? (
                <div className="home-v2-empty" data-testid="home-v2-showcase-loading">Vitrin ilanları yükleniyor...</div>
              ) : showcaseVisibleItems.length === 0 ? (
                <div className="home-v2-empty" data-testid="home-v2-showcase-empty">Vitrinde aktif ilan bulunmuyor.</div>
              ) : (
                showcaseVisibleItems.map((item) => (
                  <Link
                    key={item.id}
                    to={`/ilan/${item.id}`}
                    className={`home-v2-tile ${item.is_featured ? 'home-v2-tile-featured' : ''} ${!item.is_featured && item.is_urgent ? 'home-v2-tile-urgent' : ''}`}
                    data-testid={`home-v2-showcase-tile-${item.id}`}
                  >
                    <div className="home-v2-tile-image" data-testid={`home-v2-showcase-image-wrap-${item.id}`}>
                      {item.image ? <img src={item.image} alt={item.title || 'İlan'} data-testid={`home-v2-showcase-image-${item.id}`} /> : null}
                    </div>
                    <div className="home-v2-tile-text" data-testid={`home-v2-showcase-text-${item.id}`}>
                      <span className="home-v2-tile-badges" data-testid={`home-v2-showcase-badges-${item.id}`}>
                        {item.is_featured ? <span className="home-v2-doping-badge home-v2-doping-badge-featured" data-testid={`home-v2-featured-badge-${item.id}`}>Vitrin</span> : null}
                        {item.is_urgent ? <span className="home-v2-doping-badge home-v2-doping-badge-urgent" data-testid={`home-v2-urgent-badge-${item.id}`}>Acil</span> : null}
                      </span>
                      <span className="home-v2-tile-title" data-testid={`home-v2-showcase-title-${item.id}`}>{item.title || '-'}</span>
                      <span className="home-v2-tile-price" data-testid={`home-v2-showcase-price-${item.id}`}>{formatPrice(item.price_amount || item.price, item.currency || 'EUR')}</span>
                    </div>
                  </Link>
                ))
              )}
            </div>
          ) : (
            <div className="home-v2-empty" data-testid="home-v2-showcase-disabled">Ana sayfa vitrin alanı şu an pasif.</div>
          )}

          <div className="home-v2-mid-ad" data-testid="home-v2-mid-ad-wrap">
            <AdSlot placement="AD_LOGIN_1" className="home-v2-ad-slot home-v2-ad-slot-mid" />
          </div>
        </section>
      </div>
    </div>
  );
}
