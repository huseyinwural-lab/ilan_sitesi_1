import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import AdSlot from '@/components/public/AdSlot';
import './HomePage.css';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const SHOWCASE_TARGET_COUNT = 63;

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

  const countryCode = useMemo(() => (localStorage.getItem('selected_country') || 'DE').toUpperCase(), []);

  useEffect(() => {
    let active = true;

    const loadData = async () => {
      setLoading(true);
      try {
        const [categoryRes, showcaseRes] = await Promise.all([
          fetch(`${API}/categories?module=vehicle&country=${countryCode}`),
          fetch(`${API}/v2/search?country=${countryCode}&limit=${SHOWCASE_TARGET_COUNT}&page=1`),
        ]);

        const categoryPayload = await categoryRes.json().catch(() => []);
        const showcasePayload = await showcaseRes.json().catch(() => ({}));

        if (active) {
          setCategories(Array.isArray(categoryPayload) ? categoryPayload : []);
          setShowcaseItems(Array.isArray(showcasePayload?.items) ? showcasePayload.items : []);
        }
      } catch (_error) {
        if (active) {
          setCategories([]);
          setShowcaseItems([]);
        }
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

  const showcaseWithPlaceholders = useMemo(() => {
    const base = Array.isArray(showcaseItems) ? showcaseItems.slice(0, SHOWCASE_TARGET_COUNT) : [];
    while (base.length < SHOWCASE_TARGET_COUNT) base.push(null);
    return base;
  }, [showcaseItems]);

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

          <div className="home-v2-showcase-grid" data-testid="home-v2-showcase-grid">
            {showcaseWithPlaceholders.map((item, index) => (
              item ? (
                <Link
                  key={item.id}
                  to={`/ilan/${item.id}`}
                  className="home-v2-tile"
                  style={{
                    borderColor: item.is_featured ? '#4f46e5' : (item.is_urgent ? '#e11d48' : undefined),
                    borderWidth: item.is_featured || item.is_urgent ? 2 : 1,
                  }}
                  data-testid={`home-v2-showcase-tile-${item.id}`}
                >
                  <div className="home-v2-tile-image" data-testid={`home-v2-showcase-image-wrap-${item.id}`}>
                    {item.image ? <img src={item.image} alt={item.title || 'İlan'} data-testid={`home-v2-showcase-image-${item.id}`} /> : null}
                  </div>
                  <div className="home-v2-tile-text" data-testid={`home-v2-showcase-text-${item.id}`}>
                    <span className="home-v2-tile-title" data-testid={`home-v2-showcase-title-${item.id}`}>
                      {item.title || '-'}
                      {item.is_featured ? <span className="home-v2-doping-badge home-v2-doping-badge-featured" data-testid={`home-v2-featured-badge-${item.id}`}>Vitrin</span> : null}
                      {item.is_urgent ? <span className="home-v2-doping-badge home-v2-doping-badge-urgent" data-testid={`home-v2-urgent-badge-${item.id}`}>Acil</span> : null}
                    </span>
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

          <div className="home-v2-mid-ad" data-testid="home-v2-mid-ad-wrap">
            <AdSlot placement="AD_LOGIN_1" className="home-v2-ad-slot home-v2-ad-slot-mid" />
          </div>
        </section>
      </div>
    </div>
  );
}
