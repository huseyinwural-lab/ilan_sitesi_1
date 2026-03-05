import React, { useEffect, useMemo, useRef, useState } from 'react';
import AdSlot from '@/components/public/AdSlot';

const FALLBACK_IMAGES = ['/homepage/slide-1.jpg', '/homepage/slide-2.jpg', '/homepage/slide-3.jpg'];

const toNumber = (value, fallback) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

const normalizeItems = (items, fallbackPrefix = 'item') => {
  if (!Array.isArray(items)) return [];
  return items
    .map((item, index) => {
      if (typeof item === 'string') {
        return { id: `${fallbackPrefix}-${index}`, label: item, url: '#' };
      }
      if (!item || typeof item !== 'object') return null;
      return {
        id: item.id || `${fallbackPrefix}-${index}`,
        label: item.label || item.title || item.name || `Öğe ${index + 1}`,
        url: item.url || item.route || '#',
        count: item.count,
      };
    })
    .filter(Boolean);
};

export const BreadcrumbHeaderBlock = ({ props }) => {
  const fallbackCrumbs = useMemo(() => {
    if (typeof window === 'undefined') return ['Ana Sayfa'];
    const segments = window.location.pathname.split('/').filter(Boolean);
    if (!segments.length) return ['Ana Sayfa'];
    return ['Ana Sayfa', ...segments.map((segment) => decodeURIComponent(segment))];
  }, []);

  const rawItems = Array.isArray(props?.items) && props.items.length ? props.items : fallbackCrumbs;
  const items = rawItems.map((item, index) => (typeof item === 'string' ? { id: `crumb-${index}`, label: item } : item));
  const separator = props?.separator || ' > ';
  const maxDepth = Math.max(1, Math.min(10, toNumber(props?.max_depth, 8)));
  const visibleItems = items.slice(0, maxDepth);

  return (
    <nav className="rounded-lg border bg-white px-4 py-2 text-xs text-slate-600" data-testid="runtime-breadcrumb-header">
      {visibleItems.map((item, index) => (
        <span key={item.id || index} data-testid={`runtime-breadcrumb-item-${index}`}>
          <span className={index === visibleItems.length - 1 ? 'font-semibold text-slate-900' : ''}>{item.label || item.name || item.title}</span>
          {index < visibleItems.length - 1 ? <span className="mx-1">{separator}</span> : null}
        </span>
      ))}
    </nav>
  );
};

export const StickyActionBarBlock = ({ props }) => {
  const position = props?.position === 'right' ? 'right' : 'bottom';
  const primaryLabel = props?.primary_label || 'Hemen Ara';
  const secondaryLabel = props?.secondary_label || 'Mesaj Gönder';
  const phoneNumber = props?.phone_number || '';

  return (
    <div
      className={`z-30 ${position === 'bottom' ? 'fixed bottom-4 left-1/2 -translate-x-1/2' : 'fixed right-4 top-1/2 -translate-y-1/2'}`}
      data-testid="runtime-sticky-action-bar"
    >
      <div className="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-2 shadow-lg" data-testid="runtime-sticky-action-actions">
        <a
          href={phoneNumber ? `tel:${phoneNumber}` : '#'}
          className="rounded-full bg-emerald-600 px-3 py-1 text-xs font-semibold text-white"
          data-testid="runtime-sticky-action-primary"
        >
          {primaryLabel}
        </a>
        <button type="button" className="rounded-full border px-3 py-1 text-xs" data-testid="runtime-sticky-action-secondary">
          {secondaryLabel}
        </button>
      </div>
    </div>
  );
};

const CategoryNavigatorBase = ({ props, mode }) => {
  const title = props?.title || (mode === 'top' ? 'Kırılımlar' : 'Kategoriler');
  const showCounts = props?.show_counts !== false;
  const rawItems = props?.items || props?.menu_snapshot?.children || ['Emlak', 'Vasıta', 'Yedek Parça', 'İkinci El'];
  const items = normalizeItems(rawItems, `cat-${mode}`);

  return (
    <section className="rounded-xl border bg-white p-4" data-testid={`runtime-category-navigator-${mode}`}>
      <h3 className="text-sm font-semibold" data-testid={`runtime-category-navigator-${mode}-title`}>{title}</h3>
      <div className={mode === 'top' ? 'mt-3 flex flex-wrap gap-2' : 'mt-3 space-y-2'} data-testid={`runtime-category-navigator-${mode}-list`}>
        {items.map((item) => (
          <a
            key={item.id}
            href={item.url || '#'}
            className={mode === 'top' ? 'rounded-full border bg-slate-50 px-3 py-1 text-xs' : 'flex items-center justify-between rounded-md border px-3 py-2 text-xs'}
            data-testid={`runtime-category-navigator-${mode}-item-${item.id}`}
          >
            <span>{item.label}</span>
            {showCounts && mode !== 'top' ? <span className="text-slate-500">{item.count ?? '-'}</span> : null}
          </a>
        ))}
      </div>
    </section>
  );
};

export const CategoryNavigatorSideBlock = ({ props }) => <CategoryNavigatorBase props={props} mode="side" />;
export const CategoryNavigatorTopBlock = ({ props }) => <CategoryNavigatorBase props={props} mode="top" />;

export const AdvancedPhotoGalleryBlock = ({ props }) => {
  const images = Array.isArray(props?.images) && props.images.length ? props.images : FALLBACK_IMAGES;
  const [activeIndex, setActiveIndex] = useState(0);
  const enableZoom = props?.enable_zoom !== false;

  return (
    <section className="rounded-xl border bg-white p-4" data-testid="runtime-advanced-photo-gallery">
      <div className="aspect-[16/9] overflow-hidden rounded-lg border" data-testid="runtime-advanced-photo-main">
        <img
          src={images[activeIndex]}
          alt="listing"
          className={`h-full w-full object-cover transition ${enableZoom ? 'hover:scale-105' : ''}`}
          data-testid="runtime-advanced-photo-main-image"
        />
      </div>
      <div className="mt-2 flex flex-wrap gap-2" data-testid="runtime-advanced-photo-thumbs">
        {images.map((image, index) => (
          <button
            key={`${image}-${index}`}
            type="button"
            className={`h-14 w-20 overflow-hidden rounded border ${index === activeIndex ? 'border-sky-500' : 'border-slate-200'}`}
            onClick={() => setActiveIndex(index)}
            data-testid={`runtime-advanced-photo-thumb-${index}`}
          >
            <img src={image} alt={`thumb-${index}`} className="h-full w-full object-cover" />
          </button>
        ))}
      </div>
    </section>
  );
};

export const AutoPlayCarouselHeroBlock = ({ props }) => {
  const slides = normalizeItems(props?.slides || [
    { id: 's1', label: 'Vitrin İlanlarınız Daha Görünür', url: '/search?doping=showcase' },
    { id: 's2', label: 'Ücretsiz İlan Verin', url: '/ilan-ver' },
  ], 'hero').map((item, index) => ({ ...item, image: props?.images?.[index] || FALLBACK_IMAGES[index % FALLBACK_IMAGES.length] }));
  const [activeIndex, setActiveIndex] = useState(0);
  const autoPlaySeconds = Math.max(2, Math.min(15, toNumber(props?.auto_play_seconds, 5)));

  useEffect(() => {
    if (slides.length <= 1) return undefined;
    const timer = window.setInterval(() => {
      setActiveIndex((prev) => (prev + 1) % slides.length);
    }, autoPlaySeconds * 1000);
    return () => window.clearInterval(timer);
  }, [slides.length, autoPlaySeconds]);

  const activeSlide = slides[activeIndex];
  return (
    <section className="overflow-hidden rounded-2xl border" data-testid="runtime-auto-play-hero">
      <div className="relative aspect-[16/6] bg-slate-900">
        <img src={activeSlide.image} alt="hero" className="h-full w-full object-cover opacity-70" data-testid="runtime-auto-play-hero-image" />
        <div className="absolute inset-0 flex flex-col justify-end p-5 text-white" data-testid="runtime-auto-play-hero-overlay">
          <h3 className="text-lg font-semibold" data-testid="runtime-auto-play-hero-title">{activeSlide.label}</h3>
          <a href={activeSlide.url || '#'} className="mt-2 inline-flex w-fit rounded-full bg-white/90 px-3 py-1 text-xs font-semibold text-slate-900" data-testid="runtime-auto-play-hero-cta">
            {props?.cta_label || 'Detayları İncele'}
          </a>
        </div>
      </div>
    </section>
  );
};

export const Video3DTourPlayerBlock = ({ props }) => {
  const sourceUrl = String(props?.source_url || '').trim();
  const provider = props?.provider || 'youtube';
  const iframeUrl = useMemo(() => {
    if (!sourceUrl) return '';
    if (provider === 'youtube' && sourceUrl.includes('watch?v=')) {
      return sourceUrl.replace('watch?v=', 'embed/');
    }
    if (provider === 'vimeo' && sourceUrl.includes('vimeo.com/')) {
      return sourceUrl.replace('vimeo.com/', 'player.vimeo.com/video/');
    }
    return sourceUrl;
  }, [provider, sourceUrl]);

  return (
    <section className="rounded-xl border bg-white p-4" data-testid="runtime-video-3d-player">
      <h3 className="text-sm font-semibold" data-testid="runtime-video-3d-title">Video / 3D Tur</h3>
      {iframeUrl ? (
        <iframe src={iframeUrl} title="video-player" className="mt-2 aspect-video w-full rounded border" allow="autoplay; fullscreen" data-testid="runtime-video-3d-iframe" />
      ) : (
        <p className="mt-2 text-xs text-slate-500" data-testid="runtime-video-3d-empty">Kaynak URL tanımlanmadı.</p>
      )}
    </section>
  );
};

export const AdPromoSlotBlock = ({ props }) => (
  <section className="rounded-xl border bg-white p-3" data-testid="runtime-ad-promo-slot">
    <div className="mb-2 text-xs text-slate-500" data-testid="runtime-ad-promo-label">{props?.campaign_label || 'Kampanya Alanı'}</div>
    <AdSlot placement={props?.placement || 'AD_HOME_TOP'} className="rounded-lg border" />
  </section>
);

export const PriceTitleBlock = ({ props }) => {
  const [currency, setCurrency] = useState('TRY');
  const [favorite, setFavorite] = useState(false);
  const basePrice = toNumber(props?.base_price, 1250000);
  const rates = { TRY: 1, EUR: 0.029, USD: 0.032 };
  const value = Math.round(basePrice * (rates[currency] || 1));

  return (
    <section className="rounded-xl border bg-white p-4" data-testid="runtime-price-title-block">
      <h2 className="text-base font-semibold" data-testid="runtime-price-title-heading">{props?.title || 'Modern 3+1 Daire'}</h2>
      <div className="mt-2 flex items-center gap-2" data-testid="runtime-price-title-row">
        <strong className="text-lg" data-testid="runtime-price-title-price">{new Intl.NumberFormat('tr-TR').format(value)} {currency}</strong>
        {props?.show_currency_switcher !== false ? (
          <select value={currency} onChange={(event) => setCurrency(event.target.value)} className="rounded border px-2 py-1 text-xs" data-testid="runtime-price-title-currency-select">
            <option value="TRY">TRY</option>
            <option value="EUR">EUR</option>
            <option value="USD">USD</option>
          </select>
        ) : null}
        {props?.show_favorite_button !== false ? (
          <button type="button" className="rounded border px-2 py-1 text-xs" onClick={() => setFavorite((prev) => !prev)} data-testid="runtime-price-title-favorite-button">
            {favorite ? 'Favorilerden Çıkar' : 'Favoriye Ekle'}
          </button>
        ) : null}
      </div>
    </section>
  );
};

export const AttributeGridDynamicBlock = ({ props }) => {
  const modules = Array.isArray(props?.include_modules) && props.include_modules.length
    ? props.include_modules
    : ['core_fields', 'parameter_fields', 'detail_groups', 'address', 'contact'];
  return (
    <section className="rounded-xl border bg-white p-4" data-testid="runtime-attribute-grid-dynamic">
      <h3 className="text-sm font-semibold" data-testid="runtime-attribute-grid-title">Özellik Tablosu</h3>
      <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2" data-testid="runtime-attribute-grid-items">
        {modules.map((moduleName) => (
          <div key={moduleName} className="rounded border bg-slate-50 px-3 py-2 text-xs" data-testid={`runtime-attribute-grid-item-${moduleName}`}>
            {moduleName}
          </div>
        ))}
      </div>
    </section>
  );
};

export const DescriptionTextAreaBlock = ({ props }) => (
  <section className="rounded-xl border bg-white p-4" data-testid="runtime-description-text-area">
    <h3 className="text-sm font-semibold" data-testid="runtime-description-title">Açıklama</h3>
    <p className="mt-2 whitespace-pre-wrap text-sm text-slate-700" data-testid="runtime-description-body">
      {props?.body || 'İlan açıklaması burada gösterilir. Zengin metin formatı desteklenir.'}
    </p>
  </section>
);

export const SellerCardBlock = ({ props }) => (
  <section className="rounded-xl border bg-white p-4" data-testid="runtime-seller-card">
    <div className="flex items-center gap-3" data-testid="runtime-seller-card-header">
      <div className="h-12 w-12 rounded-full bg-slate-200" data-testid="runtime-seller-avatar" />
      <div>
        <h3 className="text-sm font-semibold" data-testid="runtime-seller-name">{props?.seller_name || 'Güvenilir Satıcı'}</h3>
        <p className="text-xs text-slate-500" data-testid="runtime-seller-meta">Puan: {props?.rating || '4.8'} • Üyelik: {props?.membership || 'Gold'}</p>
      </div>
    </div>
    <a href={props?.all_listings_url || '#'} className="mt-3 inline-flex rounded border px-3 py-1 text-xs" data-testid="runtime-seller-all-listings-link">Tüm İlanları</a>
  </section>
);

export const InteractiveMapBlock = ({ props }) => {
  const [showNearby, setShowNearby] = useState(props?.show_nearby_layers !== false);
  const lat = toNumber(props?.lat, 35.1856);
  const lng = toNumber(props?.lng, 33.3823);
  const zoom = Math.max(8, Math.min(18, toNumber(props?.default_zoom, 14)));
  const mapUrl = `https://www.openstreetmap.org/export/embed.html?bbox=${lng - 0.02}%2C${lat - 0.02}%2C${lng + 0.02}%2C${lat + 0.02}&layer=mapnik&marker=${lat}%2C${lng}`;

  return (
    <section className="rounded-xl border bg-white p-4" data-testid="runtime-interactive-map">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold" data-testid="runtime-interactive-map-title">Konum</h3>
        <button type="button" className="rounded border px-2 py-1 text-xs" onClick={() => setShowNearby((prev) => !prev)} data-testid="runtime-interactive-map-nearby-toggle">
          {showNearby ? 'Yakınları Gizle' : 'Yakınları Göster'}
        </button>
      </div>
      <iframe src={mapUrl} title="listing-map" className="h-64 w-full rounded border" data-testid="runtime-interactive-map-iframe" />
      <p className="mt-2 text-xs text-slate-500" data-testid="runtime-interactive-map-meta">Zoom: {zoom} • Yakındakiler: {String(showNearby)}</p>
    </section>
  );
};

export const MortgageLoanCalculatorBlock = ({ props }) => {
  const [amount, setAmount] = useState(toNumber(props?.amount, 1000000));
  const [months, setMonths] = useState(toNumber(props?.default_months, 120));
  const [rate, setRate] = useState(3.2);
  const monthlyRate = rate / 100;
  const monthly = monthlyRate > 0
    ? (amount * monthlyRate * (1 + monthlyRate) ** months) / (((1 + monthlyRate) ** months) - 1)
    : amount / Math.max(1, months);

  return (
    <section className="rounded-xl border bg-white p-4" data-testid="runtime-mortgage-calculator">
      <h3 className="text-sm font-semibold" data-testid="runtime-mortgage-title">Kredi / Mortgage Hesaplayıcı</h3>
      <div className="mt-3 grid gap-2 sm:grid-cols-3" data-testid="runtime-mortgage-input-grid">
        <input type="number" className="rounded border px-2 py-1 text-xs" value={amount} onChange={(e) => setAmount(Number(e.target.value || 0))} data-testid="runtime-mortgage-amount-input" />
        <input type="number" className="rounded border px-2 py-1 text-xs" value={months} onChange={(e) => setMonths(Number(e.target.value || 0))} data-testid="runtime-mortgage-months-input" />
        <input type="number" step="0.1" className="rounded border px-2 py-1 text-xs" value={rate} onChange={(e) => setRate(Number(e.target.value || 0))} data-testid="runtime-mortgage-rate-input" />
      </div>
      <p className="mt-3 text-sm font-semibold" data-testid="runtime-mortgage-result">Aylık Tahmini Taksit: {new Intl.NumberFormat('tr-TR', { maximumFractionDigits: 0 }).format(monthly || 0)} {props?.currency || 'TRY'}</p>
    </section>
  );
};

export const SimilarListingsSliderBlock = ({ props }) => {
  const sliderRef = useRef(null);
  const items = normalizeItems(props?.items || ['Benzer İlan 1', 'Benzer İlan 2', 'Benzer İlan 3', 'Benzer İlan 4'], 'similar');

  const scrollByDirection = (direction) => {
    sliderRef.current?.scrollBy({ left: direction * 240, behavior: 'smooth' });
  };

  return (
    <section className="rounded-xl border bg-white p-4" data-testid="runtime-similar-listings-slider">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold" data-testid="runtime-similar-listings-title">Benzer İlanlar</h3>
        <div className="flex gap-1">
          <button type="button" className="rounded border px-2 py-1 text-xs" onClick={() => scrollByDirection(-1)} data-testid="runtime-similar-slider-left">←</button>
          <button type="button" className="rounded border px-2 py-1 text-xs" onClick={() => scrollByDirection(1)} data-testid="runtime-similar-slider-right">→</button>
        </div>
      </div>
      <div ref={sliderRef} className="flex gap-3 overflow-x-auto pb-2" data-testid="runtime-similar-slider-track">
        {items.map((item) => (
          <a key={item.id} href={item.url || '#'} className="min-w-[220px] rounded-lg border bg-slate-50 p-3 text-xs" data-testid={`runtime-similar-slider-item-${item.id}`}>
            {item.label}
          </a>
        ))}
      </div>
    </section>
  );
};

export const DopingSelectorBlock = ({ props }) => {
  const options = Array.isArray(props?.available_dopings) && props.available_dopings.length
    ? props.available_dopings
    : ['Vitrin', 'Acil', 'Anasayfa'];
  const [selected, setSelected] = useState(props?.default_selected || options[0]);

  return (
    <section className="rounded-xl border bg-white p-4" data-testid="runtime-doping-selector">
      <h3 className="text-sm font-semibold" data-testid="runtime-doping-selector-title">Doping Seçimi</h3>
      <div className="mt-3 grid gap-2 sm:grid-cols-3" data-testid="runtime-doping-selector-grid">
        {options.map((option) => (
          <button
            key={option}
            type="button"
            onClick={() => setSelected(option)}
            className={`rounded-lg border px-3 py-2 text-xs ${selected === option ? 'border-sky-500 bg-sky-50' : 'border-slate-200 bg-white'}`}
            data-testid={`runtime-doping-selector-option-${option}`}
          >
            <div className="font-semibold">{option}</div>
            {props?.show_prices !== false ? <div className="text-slate-500">{option === 'Vitrin' ? '₺299' : option === 'Acil' ? '₺149' : '₺99'}</div> : null}
          </button>
        ))}
      </div>
      <p className="mt-2 text-xs text-slate-600" data-testid="runtime-doping-selector-selected">Seçili Paket: {selected}</p>
    </section>
  );
};

export const EXTENDED_RUNTIME_REGISTRY = {
  'layout.breadcrumb-header': ({ props }) => <BreadcrumbHeaderBlock props={props} />,
  'layout.sticky-action-bar': ({ props }) => <StickyActionBarBlock props={props} />,
  'layout.category-navigator-side': ({ props }) => <CategoryNavigatorSideBlock props={props} />,
  'layout.category-navigator-top': ({ props }) => <CategoryNavigatorTopBlock props={props} />,
  'media.advanced-photo-gallery': ({ props }) => <AdvancedPhotoGalleryBlock props={props} />,
  'media.auto-play-carousel-hero': ({ props }) => <AutoPlayCarouselHeroBlock props={props} />,
  'media.video-3d-tour-player': ({ props }) => <Video3DTourPlayerBlock props={props} />,
  'media.ad-promo-slot': ({ props }) => <AdPromoSlotBlock props={props} />,
  'data.price-title-block': ({ props }) => <PriceTitleBlock props={props} />,
  'data.attribute-grid-dynamic': ({ props }) => <AttributeGridDynamicBlock props={props} />,
  'data.description-text-area': ({ props }) => <DescriptionTextAreaBlock props={props} />,
  'data.seller-card': ({ props }) => <SellerCardBlock props={props} />,
  'interactive.interactive-map': ({ props }) => <InteractiveMapBlock props={props} />,
  'interactive.mortgage-loan-calculator': ({ props }) => <MortgageLoanCalculatorBlock props={props} />,
  'interactive.similar-listings-slider': ({ props }) => <SimilarListingsSliderBlock props={props} />,
  'interactive.doping-selector': ({ props }) => <DopingSelectorBlock props={props} />,
};
