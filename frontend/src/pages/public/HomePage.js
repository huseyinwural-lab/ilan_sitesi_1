import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import AdSlot from '@/components/public/AdSlot';
import './HomePage.css';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const DEFAULT_SHOWCASE_LAYOUT = {
  homepage: { enabled: true, rows: 9, columns: 7, listing_count: 63 },
  category_showcase: {
    enabled: true,
    default: { rows: 2, columns: 4, listing_count: 8 },
    categories: [],
  },
};

const clamp = (value, min, max, fallback) => {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return fallback;
  return Math.min(max, Math.max(min, Math.floor(parsed)));
};

const normalizeShowcaseLayout = (raw) => {
  const source = raw || {};
  const homepage = source.homepage || {};
  const categoryShowcase = source.category_showcase || {};
  const categoryDefault = categoryShowcase.default || {};

  return {
    homepage: {
      enabled: homepage.enabled !== false,
      rows: clamp(homepage.rows, 1, 12, 9),
      columns: clamp(homepage.columns, 1, 8, 7),
      listing_count: clamp(homepage.listing_count, 1, 120, 63),
    },
    category_showcase: {
      enabled: categoryShowcase.enabled !== false,
      default: {
        rows: clamp(categoryDefault.rows, 1, 12, 2),
        columns: clamp(categoryDefault.columns, 1, 8, 4),
        listing_count: clamp(categoryDefault.listing_count, 1, 120, 8),
      },
      categories: Array.isArray(categoryShowcase.categories)
        ? categoryShowcase.categories.map((item) => ({
          enabled: item?.enabled !== false,
          category_id: item?.category_id || '',
          category_slug: item?.category_slug || '',
          category_name: item?.category_name || '',
          rows: clamp(item?.rows, 1, 12, 2),
          columns: clamp(item?.columns, 1, 8, 4),
          listing_count: clamp(item?.listing_count, 1, 120, 8),
        }))
        : [],
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
  const [categories, setCategories] = useState([]);
  const [showcaseItems, setShowcaseItems] = useState([]);
  const [showcaseLayout, setShowcaseLayout] = useState(DEFAULT_SHOWCASE_LAYOUT);
  const [categoryShowcases, setCategoryShowcases] = useState([]);

  const countryCode = useMemo(() => (localStorage.getItem('selected_country') || 'DE').toUpperCase(), []);

  useEffect(() => {
    let active = true;

    const loadData = async () => {
      setLoading(true);
      try {
        const [categoryResult, layoutResult] = await Promise.allSettled([
          fetch(`${API}/categories?module=vehicle&country=${countryCode}`),
          fetch(`${API}/site/showcase-layout?_ts=${Date.now()}`, { cache: 'no-store' }),
        ]);

        let categoryList = [];
        if (categoryResult.status === 'fulfilled') {
          const categoryPayload = await categoryResult.value.json().catch(() => []);
          categoryList = Array.isArray(categoryPayload) ? categoryPayload : [];
        }

        let nextLayout = DEFAULT_SHOWCASE_LAYOUT;
        if (layoutResult.status === 'fulfilled') {
          const layoutPayload = await layoutResult.value.json().catch(() => ({}));
          nextLayout = normalizeShowcaseLayout(layoutPayload?.config);
        }

        const homeLimit = Math.max(1, resolveEffectiveCount(nextLayout.homepage));
        let showcaseItemsPayload = [];
        try {
          const showcaseRes = await fetch(`${API}/v2/search?country=${countryCode}&limit=${homeLimit}&page=1`);
          const showcasePayload = await showcaseRes.json().catch(() => ({}));
          showcaseItemsPayload = Array.isArray(showcasePayload?.items) ? showcasePayload.items : [];
        } catch (_err) {
          showcaseItemsPayload = [];
        }

        const rootCategoryById = new Map(categoryList.filter((item) => !item.parent_id).map((item) => [item.id, item]));
        const categoryConfigs = (nextLayout.category_showcase?.categories || [])
          .filter((item) => item.enabled !== false && (item.category_id || item.category_slug));

        const categoryResultPayloads = await Promise.all(
          categoryConfigs.map(async (item, index) => {
            const root = item.category_id ? rootCategoryById.get(item.category_id) : null;
            const categorySlug = item.category_slug || root?.slug || '';
            const categoryName = item.category_name || normalizeLabel(root) || categorySlug;
            if (!categorySlug) return null;
            const limit = Math.max(1, resolveEffectiveCount(item));
            try {
              const res = await fetch(`${API}/v2/search?country=${countryCode}&category=${encodeURIComponent(categorySlug)}&limit=${limit}&page=1`);
              const payload = await res.json().catch(() => ({}));
              return {
                key: `${item.category_id || categorySlug}-${index}`,
                category_slug: categorySlug,
                category_name: categoryName,
                rows: item.rows,
                columns: item.columns,
                listing_count: item.listing_count,
                effective_count: limit,
                items: Array.isArray(payload?.items) ? payload.items : [],
              };
            } catch (_err) {
              return {
                key: `${item.category_id || categorySlug}-${index}`,
                category_slug: categorySlug,
                category_name: categoryName,
                rows: item.rows,
                columns: item.columns,
                listing_count: item.listing_count,
                effective_count: limit,
                items: [],
              };
            }
          })
        );

        if (!active) return;
        setCategories(categoryList);
        setShowcaseItems(showcaseItemsPayload);
        setShowcaseLayout(nextLayout);
        setCategoryShowcases(categoryResultPayloads.filter(Boolean));
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

  const filteredCategoryRows = useMemo(() => {
    const byParent = new Map();
    categories.forEach((item) => {
      const key = item.parent_id || 'root';
      if (!byParent.has(key)) byParent.set(key, []);
      byParent.get(key).push(item);
    });

    const roots = byParent.get('root') || [];
    const query = searchInput.trim().toLowerCase();

    return roots
      .map((root) => {
        const children = (byParent.get(root.id) || []).sort((a, b) => Number(a.sort_order || 0) - Number(b.sort_order || 0));
        const firstChild = children[0] || null;
        return { root, firstChild };
      })
      .filter(({ root, firstChild }) => {
        if (!query) return true;
        const rootTitle = normalizeLabel(root).toLowerCase();
        const childTitle = normalizeLabel(firstChild).toLowerCase();
        return rootTitle.includes(query) || childTitle.includes(query);
      });
  }, [categories, searchInput]);

  const homeShowcaseBlock = useMemo(() => showcaseLayout.homepage || DEFAULT_SHOWCASE_LAYOUT.homepage, [showcaseLayout]);
  const homeShowcaseCount = useMemo(() => Math.max(1, resolveEffectiveCount(homeShowcaseBlock)), [homeShowcaseBlock]);
  const homeGridColumnClass = useMemo(
    () => `home-v2-showcase-grid-cols-${normalizeGridColumns(homeShowcaseBlock.columns, 7)}`,
    [homeShowcaseBlock.columns]
  );

  const showcaseWithPlaceholders = useMemo(() => {
    const base = Array.isArray(showcaseItems) ? showcaseItems.slice(0, homeShowcaseCount) : [];
    while (base.length < homeShowcaseCount) base.push(null);
    return base;
  }, [showcaseItems, homeShowcaseCount]);

  return (
    <div className="home-v2-page" data-testid="home-v2-page">
      <section className="home-v2-ad-top" data-testid="home-v2-top-ad-wrap">
        <AdSlot placement="AD_HOME_TOP" className="home-v2-ad-slot" />
      </section>

      <div className="home-v2-main-grid" data-testid="home-v2-main-grid">
        <aside className="home-v2-left-card" data-testid="home-v2-left-column">
          <div className="home-v2-urgent-row" data-testid="home-v2-urgent-row">
            <span className="home-v2-urgent-dot" aria-hidden="true" />
            <span className="home-v2-urgent-text" data-testid="home-v2-urgent-text">ACİL</span>
          </div>

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
            ) : filteredCategoryRows.length === 0 ? (
              <div className="home-v2-empty" data-testid="home-v2-category-empty">Kategori bulunamadı</div>
            ) : filteredCategoryRows.map(({ root, firstChild }) => {
              const rootLabel = normalizeLabel(root);
              const iconText = (rootLabel || '?').charAt(0).toUpperCase();
              return (
                <div key={root.id} className="home-v2-category-row" data-testid={`home-v2-category-row-${root.id}`}>
                  <Link
                    to={`/search?category=${encodeURIComponent(root.slug || root.id)}`}
                    className="home-v2-main-category"
                    data-testid={`home-v2-main-category-link-${root.id}`}
                  >
                    <span className="home-v2-main-category-icon" data-testid={`home-v2-main-category-icon-${root.id}`}>{iconText}</span>
                    <span className="home-v2-main-category-title" data-testid={`home-v2-main-category-title-${root.id}`}>{rootLabel}</span>
                  </Link>

                  {firstChild ? (
                    <Link
                      to={`/search?category=${encodeURIComponent(firstChild.slug || firstChild.id)}`}
                      className="home-v2-first-child"
                      data-testid={`home-v2-first-child-link-${firstChild.id}`}
                    >
                      <span className="home-v2-first-child-title" data-testid={`home-v2-first-child-title-${firstChild.id}`}>{normalizeLabel(firstChild)}</span>
                      <span className="home-v2-first-child-count" data-testid={`home-v2-first-child-count-${firstChild.id}`}>({formatNumber(firstChild.listing_count || 0)})</span>
                    </Link>
                  ) : null}
                </div>
              );
            })}
          </div>
        </aside>

        <section className="home-v2-right-content" data-testid="home-v2-right-content">
          <div className="home-v2-toolbar" data-testid="home-v2-toolbar">
            <Link to="/search" className="home-v2-showcase-link" data-testid="home-v2-showcase-all-link">Tüm vitrin ilanlarını göster</Link>
          </div>

          {homeShowcaseBlock.enabled !== false ? (
            <div
              className={`home-v2-showcase-grid ${homeGridColumnClass}`}
              data-testid="home-v2-showcase-grid"
            >
              {showcaseWithPlaceholders.map((item, index) => (
                item ? (
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
                ) : (
                  <div key={`ph-${index}`} className="home-v2-tile home-v2-tile-placeholder" data-testid={`home-v2-showcase-placeholder-${index}`}>
                    <div className="home-v2-tile-image" />
                    <div className="home-v2-tile-text"><span>&nbsp;</span><span>&nbsp;</span></div>
                  </div>
                )
              ))}
            </div>
          ) : (
            <div className="home-v2-empty" data-testid="home-v2-showcase-disabled">Ana sayfa vitrin alanı şu an pasif.</div>
          )}

          <div className="home-v2-mid-ad" data-testid="home-v2-mid-ad-wrap">
            <AdSlot placement="AD_LOGIN_1" className="home-v2-ad-slot home-v2-ad-slot-mid" />
          </div>

          {showcaseLayout.category_showcase?.enabled !== false && categoryShowcases.length > 0 ? (
            <div className="home-v2-category-showcase-list" data-testid="home-v2-category-showcase-list">
              {categoryShowcases.map((entry, index) => {
                const count = Math.max(1, resolveEffectiveCount(entry));
                const filled = Array.isArray(entry.items) ? entry.items.slice(0, count) : [];
                while (filled.length < count) filled.push(null);
                return (
                  <section className="home-v2-category-showcase-section" key={entry.key} data-testid={`home-v2-category-showcase-section-${index}`}>
                    <div className="home-v2-category-showcase-head" data-testid={`home-v2-category-showcase-head-${index}`}>
                      <h3 className="home-v2-category-showcase-title" data-testid={`home-v2-category-showcase-title-${index}`}>{entry.category_name || 'Kategori Vitrini'}</h3>
                      <Link to={`/search?category=${encodeURIComponent(entry.category_slug || '')}`} className="home-v2-showcase-link" data-testid={`home-v2-category-showcase-link-${index}`}>
                        Kategoriyi Gör
                      </Link>
                    </div>
                    <div
                      className={`home-v2-category-showcase-grid home-v2-category-showcase-grid-cols-${normalizeGridColumns(entry.columns, 4)}`}
                      data-testid={`home-v2-category-showcase-grid-${index}`}
                    >
                      {filled.map((item, tileIndex) => (
                        item ? (
                          <Link
                            key={`${entry.key}-${item.id}`}
                            to={`/ilan/${item.id}`}
                            className={`home-v2-tile ${item.is_featured ? 'home-v2-tile-featured' : ''} ${!item.is_featured && item.is_urgent ? 'home-v2-tile-urgent' : ''}`}
                            data-testid={`home-v2-category-showcase-tile-${index}-${item.id}`}
                          >
                            <div className="home-v2-tile-image">
                              {item.image ? <img src={item.image} alt={item.title || 'İlan'} /> : null}
                            </div>
                            <div className="home-v2-tile-text">
                              <span className="home-v2-tile-badges">
                                {item.is_featured ? <span className="home-v2-doping-badge home-v2-doping-badge-featured">Vitrin</span> : null}
                                {item.is_urgent ? <span className="home-v2-doping-badge home-v2-doping-badge-urgent">Acil</span> : null}
                              </span>
                              <span className="home-v2-tile-title">{item.title || '-'}</span>
                              <span className="home-v2-tile-price">{formatPrice(item.price_amount || item.price, item.currency || 'EUR')}</span>
                            </div>
                          </Link>
                        ) : (
                          <div key={`${entry.key}-ph-${tileIndex}`} className="home-v2-tile home-v2-tile-placeholder" data-testid={`home-v2-category-showcase-placeholder-${index}-${tileIndex}`}>
                            <div className="home-v2-tile-image" />
                            <div className="home-v2-tile-text"><span>&nbsp;</span><span>&nbsp;</span></div>
                          </div>
                        )
                      ))}
                    </div>
                  </section>
                );
              })}
            </div>
          ) : null}
        </section>
      </div>
    </div>
  );
}
