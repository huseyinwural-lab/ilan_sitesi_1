import React, { useEffect, useMemo, useState } from 'react';
import { useLanguage } from '@/contexts/LanguageContext';
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

const MODULE_LABEL_MAP = new Map(MODULE_CONFIG.map((item) => [item.key, item.label]));

const DEFAULT_HOME_CATEGORY_LAYOUT = {
  column_width: 286,
  l1_initial_limit: 5,
  module_order_mode: 'manual',
  module_order: MODULE_CONFIG.map((item) => item.key),
  module_l1_order_mode: {},
  module_l1_order: {},
};

const REAL_ESTATE_DISPLAY_SCHEMA = {
  l1: ['Emlak'],
  l2: ['Konut', 'Ticari Alan', 'Arsa'],
};

const LANGUAGE_LOCALE_MAP = {
  tr: 'tr-TR',
  de: 'de-DE',
  fr: 'fr-FR',
};

const MODULE_ROOT_LIMIT = DEFAULT_HOME_CATEGORY_LAYOUT.l1_initial_limit;
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

const normalizeHomeCategoryLayout = (raw) => {
  const source = raw || {};
  const moduleOrderRaw = Array.isArray(source.module_order) ? source.module_order : [];
  const moduleOrder = [];
  const seen = new Set();
  moduleOrderRaw.forEach((item) => {
    const value = String(item || '').trim();
    if (!value || seen.has(value)) return;
    moduleOrder.push(value);
    seen.add(value);
  });
  MODULE_CONFIG.forEach((item) => {
    if (!moduleOrder.includes(item.key)) moduleOrder.push(item.key);
  });
  const moduleOrderMode = source.module_order_mode === 'alphabetical' ? 'alphabetical' : 'manual';
  const l1Modes = typeof source.module_l1_order_mode === 'object' && source.module_l1_order_mode ? source.module_l1_order_mode : {};
  const moduleL1OrderMode = {};
  Object.entries(l1Modes).forEach(([key, value]) => {
    if (value === 'alphabetical' || value === 'manual') {
      moduleL1OrderMode[key] = value;
    }
  });
  return {
    column_width: clamp(source.column_width, 220, 520, DEFAULT_HOME_CATEGORY_LAYOUT.column_width),
    l1_initial_limit: clamp(source.l1_initial_limit, 1, 20, DEFAULT_HOME_CATEGORY_LAYOUT.l1_initial_limit),
    module_order_mode: moduleOrderMode,
    module_order: moduleOrder,
    module_l1_order_mode: moduleL1OrderMode,
    module_l1_order: typeof source.module_l1_order === 'object' && source.module_l1_order ? source.module_l1_order : {},
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

const normalizeLabel = (category, language = 'tr') => {
  if (!category) return '';
  const translated = Array.isArray(category.translations)
    ? category.translations.find((item) => item?.language === language)?.name
      || category.translations.find((item) => item?.language === 'tr')?.name
      || category.translations[0]?.name
    : '';
  return translated || category.name || category.slug || '';
};

const normalizeNameKey = (value) => String(value || '').trim().toLowerCase();

export default function HomePage() {
  const { language } = useLanguage();
  const [loading, setLoading] = useState(true);
  const [searchInput, setSearchInput] = useState('');
  const [categoriesByModule, setCategoriesByModule] = useState({});
  const [showcaseItems, setShowcaseItems] = useState([]);
  const [showcaseLayout, setShowcaseLayout] = useState(DEFAULT_SHOWCASE_LAYOUT);
  const [homeCategoryLayout, setHomeCategoryLayout] = useState(DEFAULT_HOME_CATEGORY_LAYOUT);
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
        const [layoutResult, homeCategoryResult, ...categoryResults] = await Promise.allSettled([
          fetch(`${API}/site/showcase-layout?_ts=${Date.now()}`, { cache: 'no-store' }),
          fetch(`${API}/site/home-category-layout?country=${countryCode}&_ts=${Date.now()}`, { cache: 'no-store' }),
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

        let nextHomeCategoryLayout = DEFAULT_HOME_CATEGORY_LAYOUT;
        if (homeCategoryResult.status === 'fulfilled') {
          const categoryLayoutPayload = await homeCategoryResult.value.json().catch(() => ({}));
          nextHomeCategoryLayout = normalizeHomeCategoryLayout(categoryLayoutPayload?.config);
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
        setHomeCategoryLayout(nextHomeCategoryLayout);
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

  const moduleLabelMap = useMemo(() => new Map(MODULE_CONFIG.map((item) => [item.key, item.label])), []);

  const moduleOrder = useMemo(() => {
    const rawOrder = Array.isArray(homeCategoryLayout.module_order) ? homeCategoryLayout.module_order : [];
    if (homeCategoryLayout.module_order_mode === 'alphabetical') {
      return MODULE_CONFIG
        .map((item) => item.key)
        .sort((a, b) => {
          const labelA = MODULE_LABEL_MAP.get(a) || a;
          const labelB = MODULE_LABEL_MAP.get(b) || b;
          return labelA.localeCompare(labelB, LANGUAGE_LOCALE_MAP[language] || 'tr-TR');
        });
    }
    const unique = [];
    const seen = new Set();
    rawOrder.forEach((item) => {
      const value = String(item || '').trim();
      if (!value || seen.has(value)) return;
      unique.push(value);
      seen.add(value);
    });
    MODULE_CONFIG.forEach((item) => {
      if (!unique.includes(item.key)) unique.push(item.key);
    });
    return unique;
  }, [homeCategoryLayout.module_order, homeCategoryLayout.module_order_mode, language]);


  const moduleGroups = useMemo(() => {
    const query = searchInput.trim().toLowerCase();

    return moduleOrder.map((moduleKey) => {
      const moduleLabel = MODULE_LABEL_MAP.get(moduleKey) || moduleKey;
      const categories = categoriesByModule[moduleKey] || [];
      const byParent = new Map();
      categories.forEach((item) => {
        const key = item.parent_id || 'root';
        if (!byParent.has(key)) byParent.set(key, []);
        byParent.get(key).push(item);
      });

      const descendantCountMemo = new Map();
      const resolveDescendantCount = (node) => {
        if (!node) return 0;
        if (descendantCountMemo.has(node.id)) return descendantCountMemo.get(node.id);
        const children = byParent.get(node.id) || [];
        const ownCount = Number(node.listing_count || 0);
        const childrenSum = children.reduce((sum, child) => sum + resolveDescendantCount(child), 0);
        const total = children.length > 0 ? Math.max(ownCount, childrenSum) : ownCount;
        descendantCountMemo.set(node.id, total);
        return total;
      };

      const moduleOrderList = Array.isArray(homeCategoryLayout.module_l1_order?.[moduleKey])
        ? homeCategoryLayout.module_l1_order[moduleKey]
        : [];
      const moduleOrderIndex = new Map(moduleOrderList.map((item, index) => [item, index]));
      const resolveOrderIndex = (node) => {
        if (!node) return null;
        if (moduleOrderIndex.has(node.id)) return moduleOrderIndex.get(node.id);
        if (node.slug && moduleOrderIndex.has(node.slug)) return moduleOrderIndex.get(node.slug);
        return null;
      };

      const l1OrderMode = homeCategoryLayout.module_l1_order_mode?.[moduleKey] || 'manual';

      const level1Allowed = new Set(REAL_ESTATE_DISPLAY_SCHEMA.l1.map((name) => normalizeNameKey(name)));
      const level2Allowed = new Set(REAL_ESTATE_DISPLAY_SCHEMA.l2.map((name) => normalizeNameKey(name)));
      const level2SortIndex = new Map(REAL_ESTATE_DISPLAY_SCHEMA.l2.map((name, index) => [normalizeNameKey(name), index]));

      let rootCandidates = (byParent.get('root') || [])
        .sort((a, b) => {
          if (l1OrderMode === 'alphabetical') {
            const nameA = normalizeLabel(a, language);
            const nameB = normalizeLabel(b, language);
            return nameA.localeCompare(nameB, LANGUAGE_LOCALE_MAP[language] || 'tr-TR');
          }
          const ai = resolveOrderIndex(a);
          const bi = resolveOrderIndex(b);
          if (ai !== null || bi !== null) {
            return (ai ?? 9999) - (bi ?? 9999);
          }
          return Number(a.sort_order || 0) - Number(b.sort_order || 0);
        })
        .filter((root) => {
          if (moduleKey !== 'real_estate') return true;
          return level1Allowed.has(normalizeNameKey(normalizeLabel(root, language)));
        });

      const roots = rootCandidates
        .map((root) => {
          const rootName = normalizeLabel(root, language);
          let rawChildren = (byParent.get(root.id) || []).sort((a, b) => Number(a.sort_order || 0) - Number(b.sort_order || 0));

          if (moduleKey === 'real_estate') {
            rawChildren = rawChildren
              .filter((child) => level2Allowed.has(normalizeNameKey(normalizeLabel(child, language))))
              .sort((a, b) => {
                const aKey = normalizeNameKey(normalizeLabel(a, language));
                const bKey = normalizeNameKey(normalizeLabel(b, language));
                const ai = level2SortIndex.has(aKey) ? level2SortIndex.get(aKey) : 999;
                const bi = level2SortIndex.has(bKey) ? level2SortIndex.get(bKey) : 999;
                if (ai !== bi) return ai - bi;
                return Number(a.sort_order || 0) - Number(b.sort_order || 0);
              });
          }
          const rootMatches = rootName.toLowerCase().includes(query);

          const children = rawChildren.filter((child) => {
            if (!query) return true;
            return rootMatches || normalizeLabel(child, language).toLowerCase().includes(query);
          });

          if (query && !rootMatches && children.length === 0) return null;

          const rootTotalCount = resolveDescendantCount(root);
          return {
            id: root.id,
            name: rootName,
            total_count: rootTotalCount,
            url: `/search?category=${encodeURIComponent(root.slug || root.id)}`,
            children_level1: children.map((child) => ({
              id: child.id,
              name: normalizeLabel(child, language),
              listing_count: resolveDescendantCount(child),
              url: `/search?category=${encodeURIComponent(child.slug || child.id)}`,
            })),
          };
        })
        .filter(Boolean);

      return {
        module_key: moduleKey,
        module_label: moduleLabel,
        roots,
      };
    });
  }, [categoriesByModule, homeCategoryLayout.module_l1_order, homeCategoryLayout.module_l1_order_mode, language, moduleOrder, searchInput]);

  const moduleRootLimit = useMemo(
    () => clamp(homeCategoryLayout.l1_initial_limit, 1, 20, MODULE_ROOT_LIMIT),
    [homeCategoryLayout.l1_initial_limit]
  );
  const homeCategoryWidth = useMemo(
    () => clamp(homeCategoryLayout.column_width, 220, 520, DEFAULT_HOME_CATEGORY_LAYOUT.column_width),
    [homeCategoryLayout.column_width]
  );

  const homeShowcaseBlock = useMemo(() => showcaseLayout.homepage || DEFAULT_SHOWCASE_LAYOUT.homepage, [showcaseLayout]);
  const homeShowcaseCount = useMemo(() => Math.max(1, resolveEffectiveCount(homeShowcaseBlock)), [homeShowcaseBlock]);
  const homeGridColumnClass = useMemo(() => `home-v2-showcase-grid-cols-${normalizeGridColumns(homeShowcaseBlock.columns, 4)}`, [homeShowcaseBlock.columns]);
  const showcaseVisibleItems = useMemo(() => (Array.isArray(showcaseItems) ? showcaseItems.slice(0, homeShowcaseCount) : []), [showcaseItems, homeShowcaseCount]);

  return (
    <div className="home-v2-page" data-testid="home-v2-page">
      <section className="home-v2-ad-top" data-testid="home-v2-top-ad-wrap">
        <AdSlot placement="AD_HOME_TOP" className="home-v2-ad-slot" />
      </section>

      <div className="home-v2-main-grid" style={{ '--home-left-width': `${homeCategoryWidth}px` }} data-testid="home-v2-main-grid">
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
              const visibleRoots = moduleExpanded ? moduleGroup.roots : moduleGroup.roots.slice(0, moduleRootLimit);

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

                  {moduleGroup.roots.length > moduleRootLimit ? (
                    <button
                      type="button"
                      className="home-v2-toggle-btn"
                      onClick={() => setExpandedModules((prev) => ({ ...prev, [moduleGroup.module_key]: !moduleExpanded }))}
                      data-testid={`home-v2-module-toggle-${moduleGroup.module_key}`}
                    >
                      {moduleExpanded ? 'Daha az göster' : 'Devamını Gör'}
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
