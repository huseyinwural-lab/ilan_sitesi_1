import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import AdSlot from '@/components/public/AdSlot';
import './HomePage.css';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const DEFAULT_SHOWCASE_LAYOUT = {
  homepage: { enabled: true, rows: 3, columns: 4, listing_count: 12 },
};

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
      rows: clamp(homepage.rows, 1, 12, 9),
      columns: clamp(homepage.columns, 1, 8, 7),
      listing_count: clamp(homepage.listing_count, 1, 120, 63),
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
  const [urgentTotal, setUrgentTotal] = useState(0);

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
        let urgentPayloadTotal = 0;
        try {
          const showcaseRes = await fetch(`${API}/v2/search?country=${countryCode}&limit=${homeLimit}&page=1&doping_type=showcase`);
          const showcasePayload = await showcaseRes.json().catch(() => ({}));
          showcaseItemsPayload = Array.isArray(showcasePayload?.items) ? showcasePayload.items : [];
        } catch (_err) {
          showcaseItemsPayload = [];
        }

        try {
          const urgentRes = await fetch(`${API}/v2/search?country=${countryCode}&limit=1&page=1&doping_type=urgent`);
          const urgentPayload = await urgentRes.json().catch(() => ({}));
          urgentPayloadTotal = Number(urgentPayload?.pagination?.total || 0);
        } catch (_err) {
          urgentPayloadTotal = 0;
        }

        if (!active) return;
        setCategories(categoryList);
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
        const countValue = firstChild ? Number(firstChild.listing_count || 0) : Number(root.listing_count || 0);
        return { root, firstChild, countValue };
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

  const showcaseVisibleItems = useMemo(() => {
    if (!Array.isArray(showcaseItems)) return [];
    return showcaseItems.slice(0, homeShowcaseCount);
  }, [showcaseItems, homeShowcaseCount]);

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
            ) : filteredCategoryRows.length === 0 ? (
              <div className="home-v2-empty" data-testid="home-v2-category-empty">Kategori bulunamadı</div>
            ) : filteredCategoryRows.map(({ root, firstChild, countValue }) => {
              const rootLabel = normalizeLabel(root);
              const firstChildLabel = normalizeLabel(firstChild);
              const categoryTarget = firstChild?.slug || firstChild?.id || root?.slug || root?.id;
              const pathText = firstChild ? `${rootLabel} > ${firstChildLabel}` : rootLabel;
              return (
                <div key={root.id} className="home-v2-category-row" data-testid={`home-v2-category-row-${root.id}`}>
                  <Link
                    to={`/search?category=${encodeURIComponent(categoryTarget)}`}
                    className="home-v2-category-path"
                    data-testid={`home-v2-category-path-link-${root.id}`}
                  >
                    <span className="home-v2-category-path-title" data-testid={`home-v2-category-path-title-${root.id}`}>{pathText}</span>
                    <span className="home-v2-category-path-count" data-testid={`home-v2-category-path-count-${root.id}`}>({formatNumber(countValue)})</span>
                  </Link>
                </div>
              );
            })}
          </div>
        </aside>

        <section className="home-v2-right-content" data-testid="home-v2-right-content">
          <div className="home-v2-toolbar" data-testid="home-v2-toolbar">
            <Link to="/search?doping=showcase" className="home-v2-showcase-link" data-testid="home-v2-showcase-all-link">Tüm vitrin ilanlarını göster</Link>
          </div>

          {homeShowcaseBlock.enabled !== false ? (
            <div
              className={`home-v2-showcase-grid ${homeGridColumnClass}`}
              data-testid="home-v2-showcase-grid"
            >
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
