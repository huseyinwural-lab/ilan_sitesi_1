import React, { useEffect, useMemo, useRef, useState } from 'react';
import AdSlot from '@/components/public/AdSlot';
import { ChevronDown, ChevronRight } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const FALLBACK_IMAGES = ['/homepage/slide-1.jpg', '/homepage/slide-2.jpg', '/homepage/slide-3.jpg'];
const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

const listingDetailCache = new Map();
const listingDetailPending = new Map();
const similarItemsCache = new Map();
const similarItemsPending = new Map();

const toNumber = (value, fallback) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

const parseCoordinate = (value) => {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return null;
  return parsed;
};

const resolveMediaUrl = (url) => {
  if (!url) return '';
  if (/^https?:\/\//i.test(url)) return url;
  return `${process.env.REACT_APP_BACKEND_URL}${url}`;
};

const resolveAdPlacementToken = (placement) => {
  const normalized = String(placement || '').trim().toLowerCase();
  if (['home_top', 'ad_home_top'].includes(normalized)) return 'AD_HOME_TOP';
  if (['home_bottom', 'ad_home_bottom'].includes(normalized)) return 'AD_HOME_BOTTOM';
  if (['category_top', 'ad_search_top', 'search_top'].includes(normalized)) return 'AD_SEARCH_TOP';
  if (['category_bottom', 'ad_category_bottom'].includes(normalized)) return 'AD_CATEGORY_BOTTOM';
  if (normalized.startsWith('ad_')) return String(placement);
  return 'AD_HOME_TOP';
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
        url: item.url || item.route || (item.id ? `/ilan/${item.id}` : '#'),
        count: item.count,
        price: item.price,
        currency: item.currency,
        image_url: item.image_url,
        score: item.score,
        score_explanation: Array.isArray(item.score_explanation) ? item.score_explanation : [],
      };
    })
    .filter(Boolean);
};

const normalizeToken = (value) => String(value || '').trim().toLowerCase();

const resolveLocalePrefix = () => {
  if (typeof window === 'undefined') return '';
  const first = String(window.location.pathname || '/').split('/').filter(Boolean)[0]?.toLowerCase();
  return ['tr', 'de', 'fr'].includes(first) ? `/${first}` : '';
};

const buildSearchCategoryUrl = (categoryToken) => {
  const localePrefix = resolveLocalePrefix();
  const base = `${localePrefix}/search`;
  if (!categoryToken) return base;
  return `${base}?category=${encodeURIComponent(categoryToken)}`;
};

const buildL0L1Categories = (items = []) => {
  const byParent = new Map();
  items.forEach((item) => {
    const parentKey = item?.parent_id || '__root__';
    if (!byParent.has(parentKey)) byParent.set(parentKey, []);
    byParent.get(parentKey).push(item);
  });

  const sortNodes = (nodes) => [...nodes].sort((a, b) => {
    const aOrder = Number(a?.sort_order || 0);
    const bOrder = Number(b?.sort_order || 0);
    if (aOrder !== bOrder) return aOrder - bOrder;
    return String(a?.name || '').localeCompare(String(b?.name || ''), 'tr');
  });

  return sortNodes(byParent.get('__root__') || []).map((root) => ({
    ...root,
    children: sortNodes(byParent.get(root.id) || []),
  }));
};

const normalizeListingFromCandidate = (candidate) => {
  if (!candidate || typeof candidate !== 'object') return null;
  const id = candidate.id || candidate.listing_id || null;
  return {
    id,
    title: candidate.title || candidate.name || 'İlan',
    description: candidate.description || '',
    price: candidate.price ?? candidate.price_amount ?? null,
    currency: candidate.currency || candidate.currency_primary || 'EUR',
    media: Array.isArray(candidate.media)
      ? candidate.media.map((item) => ({ ...item, url: resolveMediaUrl(item?.url || item?.image_url || item?.thumbnail_url) }))
      : (candidate.image_url ? [{ url: resolveMediaUrl(candidate.image_url), is_cover: true }] : []),
    location: {
      city: candidate.city || candidate?.location?.city || '',
      country: candidate.country || candidate?.location?.country || '',
      latitude: candidate.lat ?? candidate.latitude ?? candidate?.location?.latitude ?? null,
      longitude: candidate.lng ?? candidate.longitude ?? candidate?.location?.longitude ?? null,
    },
    seller: candidate.seller || null,
    attributes: candidate.attributes || {},
  };
};

const inferListingIdFromRuntime = (props, runtimeContext) => {
  const directId = String(props?.listing_id || runtimeContext?.listingId || runtimeContext?.selectedListingId || runtimeContext?.listing?.id || '').trim();
  if (UUID_REGEX.test(directId)) return directId;

  const fromCandidates = [
    runtimeContext?.featuredListing,
    ...(Array.isArray(runtimeContext?.listingCandidates) ? runtimeContext.listingCandidates : []),
    ...(Array.isArray(runtimeContext?.searchItems) ? runtimeContext.searchItems : []),
    ...(Array.isArray(runtimeContext?.showcaseItems) ? runtimeContext.showcaseItems : []),
    ...(Array.isArray(runtimeContext?.recentItems) ? runtimeContext.recentItems : []),
  ]
    .map((item) => String(item?.id || item?.listing_id || '').trim())
    .find((id) => UUID_REGEX.test(id));
  if (fromCandidates) return fromCandidates;

  if (typeof window !== 'undefined') {
    const match = window.location.pathname.match(/\/ilan\/([0-9a-f-]{36})/i);
    if (match?.[1] && UUID_REGEX.test(match[1])) return match[1];
  }
  return null;
};

const fetchListingDetail = async (listingId) => {
  if (!listingId) return null;
  if (listingDetailCache.has(listingId)) return listingDetailCache.get(listingId);
  if (listingDetailPending.has(listingId)) return listingDetailPending.get(listingId);

  const request = fetch(`${API}/v1/listings/vehicle/${listingId}?preview=1`, { cache: 'no-store' })
    .then(async (response) => {
      if (!response.ok) return null;
      const payload = await response.json();
      const normalized = {
        ...payload,
        media: Array.isArray(payload?.media)
          ? payload.media.map((item) => ({ ...item, url: resolveMediaUrl(item?.url), thumbnail_url: resolveMediaUrl(item?.thumbnail_url) }))
          : [],
      };
      listingDetailCache.set(listingId, normalized);
      return normalized;
    })
    .catch(() => null)
    .finally(() => {
      listingDetailPending.delete(listingId);
    });

  listingDetailPending.set(listingId, request);
  return request;
};

const fetchSimilarListings = async (listingId) => {
  if (!listingId) return [];
  if (similarItemsCache.has(listingId)) return similarItemsCache.get(listingId);
  if (similarItemsPending.has(listingId)) return similarItemsPending.get(listingId);

  const request = fetch(`${API}/v1/listings/vehicle/${listingId}/similar?limit=8`, { cache: 'no-store' })
    .then(async (response) => {
      if (!response.ok) return [];
      const payload = await response.json();
      const items = normalizeItems(payload?.items || [], 'similar-live').map((item) => ({
        ...item,
        image_url: resolveMediaUrl(item.image_url),
        url: item.id ? `/ilan/${item.id}` : '#',
      }));
      similarItemsCache.set(listingId, items);
      return items;
    })
    .catch(() => [])
    .finally(() => {
      similarItemsPending.delete(listingId);
    });

  similarItemsPending.set(listingId, request);
  return request;
};

const useRuntimeListingData = (props, runtimeContext) => {
  const initialListing = useMemo(() => {
    return normalizeListingFromCandidate(props?.listing_payload)
      || normalizeListingFromCandidate(runtimeContext?.listing)
      || normalizeListingFromCandidate(runtimeContext?.featuredListing)
      || normalizeListingFromCandidate((runtimeContext?.listingCandidates || [])[0])
      || normalizeListingFromCandidate((runtimeContext?.searchItems || [])[0])
      || null;
  }, [props?.listing_payload, runtimeContext]);

  const [listing, setListing] = useState(initialListing);
  const [similarItems, setSimilarItems] = useState(() => normalizeItems(props?.items || runtimeContext?.similarItems || [], 'similar-runtime'));

  const inferredListingId = useMemo(() => inferListingIdFromRuntime(props, runtimeContext), [props, runtimeContext]);

  useEffect(() => {
    setListing(initialListing);
  }, [initialListing]);

  useEffect(() => {
    let alive = true;
    if (!inferredListingId) return () => {
      alive = false;
    };

    fetchListingDetail(inferredListingId).then((payload) => {
      if (!alive || !payload) return;
      const normalized = normalizeListingFromCandidate(payload);
      if (normalized) setListing(normalized);
    });

    return () => {
      alive = false;
    };
  }, [inferredListingId]);

  useEffect(() => {
    let alive = true;
    if (!inferredListingId) return () => {
      alive = false;
    };

    fetchSimilarListings(inferredListingId).then((items) => {
      if (!alive) return;
      if (Array.isArray(items) && items.length > 0) setSimilarItems(items);
    });

    return () => {
      alive = false;
    };
  }, [inferredListingId]);

  return {
    listing,
    similarItems,
    listingId: inferredListingId,
  };
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

const CategoryNavigatorBase = ({ props, mode, runtimeContext }) => {
  const title = props?.title || (mode === 'top' ? 'Kırılımlar' : 'Kategoriler');
  const showCounts = props?.show_counts !== false;
  const treeBehavior = props?.tree_behavior === 'accordion' ? 'accordion' : 'expanded';
  const maxLevels = Math.max(1, Math.min(3, toNumber(props?.max_levels, 2)));
  const selectedToken = normalizeToken(runtimeContext?.activeCategorySlug);
  const triggerCategoryChange = (categoryToken) => {
    if (typeof runtimeContext?.onCategoryChange === 'function') {
      runtimeContext.onCategoryChange(categoryToken || null);
      return;
    }
    if (typeof window !== 'undefined') {
      window.location.href = buildSearchCategoryUrl(categoryToken);
    }
  };

  const runtimeItems = Array.isArray(runtimeContext?.categories) ? runtimeContext.categories : [];
  const l0l1Tree = useMemo(() => {
    if (runtimeItems.length > 0) return buildL0L1Categories(runtimeItems);

    const fallbackItems = normalizeItems(props?.items || props?.menu_snapshot?.children || ['Emlak', 'Vasıta', 'Yedek Parça', 'İkinci El'], `cat-${mode}`);
    return fallbackItems.map((item, index) => ({
      id: item.id || `fallback-root-${index}`,
      name: item.label,
      slug: item.id || `fallback-root-${index}`,
      listing_count: item.count,
      children: [],
    }));
  }, [runtimeItems, props?.items, props?.menu_snapshot?.children, mode]);
  const [openRootId, setOpenRootId] = useState('');

  useEffect(() => {
    if (!selectedToken || !l0l1Tree.length) return;
    const matchedRoot = l0l1Tree.find((root) => {
      const rootMatch = [root.id, root.slug].some((token) => normalizeToken(token) === selectedToken);
      const childMatch = (root.children || []).some((child) => [child.id, child.slug].some((token) => normalizeToken(token) === selectedToken));
      return rootMatch || childMatch;
    });
    if (matchedRoot?.id) setOpenRootId(matchedRoot.id);
  }, [selectedToken, l0l1Tree]);

  if (mode === 'top') {
    const chips = l0l1Tree.slice(0, Math.max(1, toNumber(props?.max_levels, 8))).map((root) => ({
      id: root.id,
      label: root.name,
      count: root.listing_count,
      href: buildSearchCategoryUrl(root.id || root.slug),
    }));

    return (
      <section className="rounded-xl border bg-white p-4" data-testid="runtime-category-navigator-top">
        <h3 className="text-sm font-semibold" data-testid="runtime-category-navigator-top-title">{title}</h3>
        <div className="mt-3 flex flex-wrap gap-2" data-testid="runtime-category-navigator-top-list">
          {chips.map((chip) => (
            <button
              key={chip.id}
              type="button"
              onClick={() => triggerCategoryChange(chip.id)}
              className="rounded-full border bg-slate-50 px-3 py-1 text-xs hover:bg-slate-100"
              data-testid={`runtime-category-navigator-top-item-${chip.id}`}
            >
              {chip.label}{showCounts ? ` (${Number(chip.count || 0)})` : ''}
            </button>
          ))}
        </div>
      </section>
    );
  }

  return (
    <section className="rounded-xl border bg-white p-4" data-testid="runtime-category-navigator-side">
      <h3 className="text-sm font-semibold" data-testid="runtime-category-navigator-side-title">{title}</h3>
      <div className="mt-3 rounded-lg border bg-white p-2" data-testid="runtime-category-navigator-side-tree">
        {l0l1Tree.map((root) => {
          const rootToken = root.id || root.slug;
          const rootSelected = [root.id, root.slug].some((token) => normalizeToken(token) === selectedToken);
          const isOpen = treeBehavior === 'expanded' || openRootId === root.id;
          const hasChildren = Array.isArray(root.children) && root.children.length > 0;

          return (
            <div key={root.id} className="border-b last:border-b-0" data-testid={`runtime-category-navigator-side-root-${root.id}`}>
              <div className="flex items-center gap-1 py-1">
                {hasChildren ? (
                  <button
                    type="button"
                    onClick={() => setOpenRootId((prev) => (prev === root.id ? '' : root.id))}
                    className="rounded p-1 text-slate-500 hover:bg-slate-100"
                    data-testid={`runtime-category-navigator-side-toggle-${root.id}`}
                  >
                    {isOpen ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
                  </button>
                ) : <span className="inline-block h-6 w-6" aria-hidden="true" />}

                <button
                  type="button"
                  onClick={() => triggerCategoryChange(rootToken)}
                  className={`flex w-full items-center justify-between rounded-md px-2 py-1.5 text-left text-sm transition ${rootSelected ? 'bg-slate-900 font-semibold text-white' : 'font-semibold text-slate-800 hover:bg-slate-100'}`}
                  data-testid={`runtime-category-navigator-side-root-link-${root.id}`}
                >
                  <span>{root.name}</span>
                  {showCounts ? <span className={`text-xs ${rootSelected ? 'text-white/90' : 'text-slate-500'}`}>({Number(root.listing_count || 0)})</span> : null}
                </button>
              </div>

              {hasChildren && isOpen && maxLevels > 1 ? (
                <div className="mb-2 ml-7 space-y-1" data-testid={`runtime-category-navigator-side-children-${root.id}`}>
                  {root.children.map((child) => {
                    const childToken = child.id || child.slug;
                    const childSelected = [child.id, child.slug].some((token) => normalizeToken(token) === selectedToken);
                    return (
                      <button
                        key={child.id}
                        type="button"
                        onClick={() => triggerCategoryChange(childToken)}
                        className={`flex items-center justify-between rounded-md px-2 py-1 text-sm transition ${childSelected ? 'bg-blue-50 font-medium text-blue-700' : 'text-slate-600 hover:bg-slate-50'}`}
                        data-testid={`runtime-category-navigator-side-child-link-${child.id}`}
                      >
                        <span>{child.name}</span>
                        {showCounts ? <span className="text-xs text-slate-500">({Number(child.listing_count || 0)})</span> : null}
                      </button>
                    );
                  })}
                </div>
              ) : null}
            </div>
          );
        })}
      </div>
    </section>
  );
};

export const CategoryNavigatorSideBlock = ({ props, runtimeContext }) => <CategoryNavigatorBase props={props} mode="side" runtimeContext={runtimeContext} />;
export const CategoryNavigatorTopBlock = ({ props, runtimeContext }) => <CategoryNavigatorBase props={props} mode="top" runtimeContext={runtimeContext} />;

export const AdvancedPhotoGalleryBlock = ({ props, runtimeContext }) => {
  const { listing } = useRuntimeListingData(props, runtimeContext);
  const listingImages = Array.isArray(listing?.media)
    ? listing.media.map((item) => item?.url).filter(Boolean)
    : [];
  const images = Array.isArray(props?.images) && props.images.length
    ? props.images.map((item) => resolveMediaUrl(item))
    : (listingImages.length ? listingImages : FALLBACK_IMAGES);
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

export const AutoPlayCarouselHeroBlock = ({ props, runtimeContext }) => {
  const fallbackSlides = normalizeItems(runtimeContext?.showcaseItems || runtimeContext?.searchItems || [], 'hero-live').slice(0, 5);
  const slides = normalizeItems(props?.slides || fallbackSlides || [
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
    <AdSlot placement={resolveAdPlacementToken(props?.placement || 'AD_HOME_TOP')} className="rounded-lg border" />
  </section>
);

const SimpleListingCard = ({ item, dataTestId }) => (
  <a href={item?.url || '#'} className="rounded-lg border bg-white p-3 text-xs" data-testid={dataTestId}>
    <div className="font-semibold">{item?.label || 'İlan'}</div>
    <div className="mt-1 text-slate-600">{item?.price ? `${new Intl.NumberFormat('tr-TR').format(item.price)} ${item?.currency || 'EUR'}` : 'Detay'}</div>
  </a>
);

export const CTABlock = ({ props }) => {
  const title = props?.title || 'ACİL';
  const href = props?.link || '/acil';
  const fontSize = Math.max(10, Math.min(24, Number(props?.font_size || 14)));
  const fontWeight = String(props?.font_weight || '700');
  const fontColor = props?.font_color || '#ffffff';
  const backgroundColor = props?.background_color || '#dc2626';

  return (
    <section className="rounded-xl border bg-white p-4" data-testid="runtime-cta-block">
      <a
        href={href}
        className="inline-flex items-center rounded-full px-4 py-2"
        style={{ fontSize, fontWeight, color: fontColor, backgroundColor }}
        data-testid="runtime-cta-block-button"
      >
        {props?.icon ? <span className="mr-2">{props.icon}</span> : null}
        {title}
      </a>
    </section>
  );
};

export const ListingGridBlock = ({ props, runtimeContext }) => {
  const maxItems = Math.max(1, Math.min(48, Number(props?.columns || 4) * Number(props?.rows || 2)));
  const items = normalizeItems(
    props?.items
      || runtimeContext?.showcaseItems
      || runtimeContext?.searchItems
      || runtimeContext?.recentItems
      || ['Vitrin İlan 1', 'Vitrin İlan 2', 'Vitrin İlan 3', 'Vitrin İlan 4'],
    'listing-grid',
  ).slice(0, maxItems);

  const columns = Math.max(1, Math.min(6, Number(props?.columns || 4)));

  return (
    <section className="rounded-xl border bg-white p-4" data-testid="runtime-listing-grid">
      <h3 className="text-sm font-semibold" data-testid="runtime-listing-grid-title">Listing Grid</h3>
      <div className="mt-3 grid gap-2" style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }} data-testid="runtime-listing-grid-items">
        {items.map((item, index) => <SimpleListingCard key={`${item.id}-${index}`} item={item} dataTestId={`runtime-listing-grid-item-${index}`} />)}
      </div>
    </section>
  );
};

export const ListingListBlock = ({ props, runtimeContext }) => {
  const perPage = Math.max(5, Math.min(100, Number(props?.per_page || 20)));
  const items = normalizeItems(
    props?.items
      || runtimeContext?.searchItems
      || runtimeContext?.urgentItems
      || runtimeContext?.recentItems
      || ['Acil İlan 1', 'Acil İlan 2', 'Acil İlan 3'],
    'listing-list',
  ).slice(0, perPage);

  return (
    <section className="rounded-xl border bg-white p-4" data-testid="runtime-listing-list">
      <h3 className="text-sm font-semibold" data-testid="runtime-listing-list-title">Listing List</h3>
      <div className="mt-3 space-y-2" data-testid="runtime-listing-list-items">
        {items.map((item, index) => <SimpleListingCard key={`${item.id}-${index}`} item={item} dataTestId={`runtime-listing-list-item-${index}`} />)}
      </div>
    </section>
  );
};

export const ListingCardBlock = ({ props, runtimeContext }) => {
  const first = normalizeItems(
    props?.items || runtimeContext?.searchItems || runtimeContext?.recentItems || ['İlan Kartı'],
    'listing-card',
  )[0] || { id: 'listing-card-1', label: 'İlan Kartı' };

  return (
    <section className="rounded-xl border bg-white p-4" data-testid="runtime-listing-card-block">
      <h3 className="text-sm font-semibold" data-testid="runtime-listing-card-title">Listing Card</h3>
      <div className="mt-3" data-testid="runtime-listing-card-content">
        <SimpleListingCard item={first} dataTestId="runtime-listing-card-item" />
      </div>
    </section>
  );
};

export const SubCategoryBlock = ({ props, runtimeContext }) => {
  const depth = Math.max(1, Math.min(4, Number(props?.depth || 2)));
  const columns = Math.max(1, Math.min(6, Number(props?.columns || 3)));
  const tree = buildL0L1Categories(Array.isArray(runtimeContext?.categories) ? runtimeContext.categories : []);
  const items = tree.flatMap((root) => {
    const base = [{ id: root.id, label: root.name, count: root.listing_count }];
    if (depth > 1) {
      base.push(...(root.children || []).map((child) => ({ id: child.id, label: child.name, count: child.listing_count })));
    }
    return base;
  });

  const normalizedItems = (items.length ? items : normalizeItems(['Alt Kategori 1', 'Alt Kategori 2', 'Alt Kategori 3'], 'sub-category'));

  return (
    <section className="rounded-xl border bg-white p-4" data-testid="runtime-sub-category-block">
      <h3 className="text-sm font-semibold" data-testid="runtime-sub-category-title">Sub Category Block</h3>
      <div className="mt-3 grid gap-2" style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }} data-testid="runtime-sub-category-items">
        {normalizedItems.map((item, index) => (
          <a key={`${item.id || index}`} href={item?.url || '#'} className="rounded border bg-slate-50 px-2 py-2 text-xs" data-testid={`runtime-sub-category-item-${index}`}>
            {item.label}
            {props?.show_count !== false ? <span className="ml-1 text-slate-500">({Number(item.count || 0)})</span> : null}
          </a>
        ))}
      </div>
    </section>
  );
};

export const ImageBlock = ({ props }) => (
  <section className="rounded-xl border bg-white p-4" data-testid="runtime-image-block">
    {props?.image_url ? (
      <img src={resolveMediaUrl(props.image_url)} alt={props?.alt || 'image'} className="w-full rounded border" data-testid="runtime-image-block-image" />
    ) : (
      <div className="rounded border border-dashed px-3 py-8 text-xs text-slate-500" data-testid="runtime-image-block-empty">Image URL tanımlanmadı.</div>
    )}
  </section>
);

export const PriceTitleBlock = ({ props, runtimeContext }) => {
  const { listing } = useRuntimeListingData(props, runtimeContext);
  const [currency, setCurrency] = useState('TRY');
  const [favorite, setFavorite] = useState(false);
  const basePrice = toNumber(listing?.price ?? props?.base_price, 1250000);
  const rates = { TRY: 1, EUR: 0.029, USD: 0.032 };
  const value = Math.round(basePrice * (rates[currency] || 1));
  const resolvedCurrency = listing?.currency || props?.currency || currency;

  return (
    <section className="rounded-xl border bg-white p-4" data-testid="runtime-price-title-block">
      <h2 className="text-base font-semibold" data-testid="runtime-price-title-heading">{listing?.title || props?.title || 'Modern 3+1 Daire'}</h2>
      <div className="mt-2 flex items-center gap-2" data-testid="runtime-price-title-row">
        <strong className="text-lg" data-testid="runtime-price-title-price">{new Intl.NumberFormat('tr-TR').format(value)} {resolvedCurrency}</strong>
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

export const AttributeGridDynamicBlock = ({ props, runtimeContext }) => {
  const { listing } = useRuntimeListingData(props, runtimeContext);
  const modules = Array.isArray(props?.include_modules) && props.include_modules.length
    ? props.include_modules
    : ['core_fields', 'parameter_fields', 'detail_groups', 'address', 'contact'];
  const liveAttributes = listing?.attributes && typeof listing.attributes === 'object'
    ? Object.entries(listing.attributes).slice(0, 8)
    : [];

  return (
    <section className="rounded-xl border bg-white p-4" data-testid="runtime-attribute-grid-dynamic">
      <h3 className="text-sm font-semibold" data-testid="runtime-attribute-grid-title">Özellik Tablosu</h3>
      <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2" data-testid="runtime-attribute-grid-items">
        {liveAttributes.length > 0 ? liveAttributes.map(([key, value]) => (
          <div key={key} className="rounded border bg-slate-50 px-3 py-2 text-xs" data-testid={`runtime-attribute-grid-item-${key}`}>
            <strong>{key}</strong>: {String(value)}
          </div>
        )) : modules.map((moduleName) => (
          <div key={moduleName} className="rounded border bg-slate-50 px-3 py-2 text-xs" data-testid={`runtime-attribute-grid-item-${moduleName}`}>
            {moduleName}
          </div>
        ))}
      </div>
    </section>
  );
};

export const DescriptionTextAreaBlock = ({ props, runtimeContext }) => {
  const { listing } = useRuntimeListingData(props, runtimeContext);
  return (
  <section className="rounded-xl border bg-white p-4" data-testid="runtime-description-text-area">
    <h3 className="text-sm font-semibold" data-testid="runtime-description-title">Açıklama</h3>
    <p className="mt-2 whitespace-pre-wrap text-sm text-slate-700" data-testid="runtime-description-body">
      {listing?.description || props?.body || 'İlan açıklaması burada gösterilir. Zengin metin formatı desteklenir.'}
    </p>
  </section>
  );
};

export const SellerCardBlock = ({ props, runtimeContext }) => {
  const { listing } = useRuntimeListingData(props, runtimeContext);
  const seller = listing?.seller || {};
  return (
  <section className="rounded-xl border bg-white p-4" data-testid="runtime-seller-card">
    <div className="flex items-center gap-3" data-testid="runtime-seller-card-header">
      <div className="h-12 w-12 rounded-full bg-slate-200" data-testid="runtime-seller-avatar" />
      <div>
        <h3 className="text-sm font-semibold" data-testid="runtime-seller-name">{seller?.name || props?.seller_name || 'Güvenilir Satıcı'}</h3>
        <p className="text-xs text-slate-500" data-testid="runtime-seller-meta">
          Profil: {seller?.profile_type || props?.membership || 'kurumsal'} • Aktif İlan: {seller?.total_listings ?? '-'}
        </p>
        <p className="text-xs text-slate-500" data-testid="runtime-seller-reputation">
          Puan: {seller?.rating ?? '4.7'} • Yorum: {seller?.reviews_count ?? 0} • Yanıt: %{seller?.response_rate ?? 0}
        </p>
      </div>
    </div>
    <a href={props?.all_listings_url || '#'} className="mt-3 inline-flex rounded border px-3 py-1 text-xs" data-testid="runtime-seller-all-listings-link">Tüm İlanları</a>
  </section>
  );
};

export const InteractiveMapBlock = ({ props, runtimeContext }) => {
  const { listing } = useRuntimeListingData(props, runtimeContext);
  const [showNearby, setShowNearby] = useState(props?.show_nearby_layers !== false);
  const [poiItems, setPoiItems] = useState([]);
  const [poiLoading, setPoiLoading] = useState(false);
  const lat = parseCoordinate(props?.lat ?? listing?.location?.latitude) ?? 35.1856;
  const lng = parseCoordinate(props?.lng ?? listing?.location?.longitude) ?? 33.3823;
  const zoom = Math.max(8, Math.min(18, toNumber(props?.default_zoom, 14)));
  const mapUrl = `https://www.openstreetmap.org/export/embed.html?bbox=${lng - 0.02}%2C${lat - 0.02}%2C${lng + 0.02}%2C${lat + 0.02}&layer=mapnik&marker=${lat}%2C${lng}`;

  useEffect(() => {
    let alive = true;
    if (!showNearby) return () => {
      alive = false;
    };

    setPoiLoading(true);
    const endpoint = `${API}/public/geo/nearby-pois?lat=${lat}&lng=${lng}&radius_km=1.6&limit=6`;
    fetch(endpoint, { cache: 'no-store' })
      .then((response) => (response.ok ? response.json() : null))
      .then((payload) => {
        if (!alive) return;
        const items = Array.isArray(payload?.items) ? payload.items : [];
        setPoiItems(items);
      })
      .catch(() => {
        if (alive) setPoiItems([]);
      })
      .finally(() => {
        if (alive) setPoiLoading(false);
      });

    return () => {
      alive = false;
    };
  }, [lat, lng, showNearby]);

  return (
    <section className="rounded-xl border bg-white p-4" data-testid="runtime-interactive-map">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold" data-testid="runtime-interactive-map-title">Konum</h3>
        <button type="button" className="rounded border px-2 py-1 text-xs" onClick={() => setShowNearby((prev) => !prev)} data-testid="runtime-interactive-map-nearby-toggle">
          {showNearby ? 'Yakınları Gizle' : 'Yakınları Göster'}
        </button>
      </div>
      <iframe src={mapUrl} title="listing-map" className="h-64 w-full rounded border" data-testid="runtime-interactive-map-iframe" />
      <p className="mt-2 text-xs text-slate-500" data-testid="runtime-interactive-map-meta">Zoom: {zoom} • Şehir: {listing?.location?.city || '-'}</p>
      {showNearby ? (
        <div className="mt-2 flex flex-wrap gap-2" data-testid="runtime-interactive-map-nearby-layers">
          {poiLoading ? <span className="text-[11px] text-slate-500" data-testid="runtime-interactive-map-poi-loading">POI yükleniyor...</span> : null}
          {!poiLoading && poiItems.length === 0 ? <span className="text-[11px] text-slate-500" data-testid="runtime-interactive-map-poi-empty">Yakın POI bulunamadı.</span> : null}
          {poiItems.map((poi, index) => (
            <span
              key={`${poi.id || index}`}
              className="rounded-full border bg-slate-50 px-2 py-1 text-[11px]"
              data-testid={`runtime-interactive-map-nearby-${index}`}
            >
              {poi.name} • {poi.distance_km} km
            </span>
          ))}
        </div>
      ) : null}
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

export const SimilarListingsSliderBlock = ({ props, runtimeContext }) => {
  const { similarItems: liveSimilarItems } = useRuntimeListingData(props, runtimeContext);
  const sliderRef = useRef(null);
  const items = normalizeItems(
    props?.items
      || (liveSimilarItems.length ? liveSimilarItems : null)
      || runtimeContext?.searchItems
      || ['Benzer İlan 1', 'Benzer İlan 2', 'Benzer İlan 3', 'Benzer İlan 4'],
    'similar',
  );

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
            <div className="font-semibold">{item.label}</div>
            <div className="mt-1 text-slate-500">{item.price ? `${new Intl.NumberFormat('tr-TR').format(item.price)} ${item.currency || 'EUR'}` : 'Detay'}</div>
            {typeof item.score === 'number' ? (
              <div className="mt-1 text-[11px] text-slate-600" data-testid={`runtime-similar-slider-score-${item.id}`}>
                Skor: {item.score}/100
              </div>
            ) : null}
            {Array.isArray(item.score_explanation) && item.score_explanation.length > 0 ? (
              <div className="mt-1 text-[11px] text-slate-500" data-testid={`runtime-similar-slider-explain-${item.id}`}>
                {item.score_explanation[0]}
              </div>
            ) : null}
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
  'category.navigator': ({ props, runtimeContext }) => <CategoryNavigatorSideBlock props={props} runtimeContext={runtimeContext} />,
  'cta.block': ({ props, runtimeContext }) => <CTABlock props={props} runtimeContext={runtimeContext} />,
  'listing.grid': ({ props, runtimeContext }) => <ListingGridBlock props={props} runtimeContext={runtimeContext} />,
  'listing.list': ({ props, runtimeContext }) => <ListingListBlock props={props} runtimeContext={runtimeContext} />,
  'listing.card': ({ props, runtimeContext }) => <ListingCardBlock props={props} runtimeContext={runtimeContext} />,
  'category.sub-category-block': ({ props, runtimeContext }) => <SubCategoryBlock props={props} runtimeContext={runtimeContext} />,
  'ad.slot': ({ props, runtimeContext }) => <AdPromoSlotBlock props={{ ...props, placement: resolveAdPlacementToken(props?.placement) }} runtimeContext={runtimeContext} />,
  'media.hero-banner': ({ props, runtimeContext }) => <AutoPlayCarouselHeroBlock props={props} runtimeContext={runtimeContext} />,
  'media.carousel': ({ props, runtimeContext }) => <AutoPlayCarouselHeroBlock props={props} runtimeContext={runtimeContext} />,
  'media.image': ({ props, runtimeContext }) => <ImageBlock props={props} runtimeContext={runtimeContext} />,
  'media.video': ({ props, runtimeContext }) => <Video3DTourPlayerBlock props={props} runtimeContext={runtimeContext} />,
  'map.block': ({ props, runtimeContext }) => <InteractiveMapBlock props={props} runtimeContext={runtimeContext} />,
  'layout.breadcrumb-header': ({ props, runtimeContext }) => <BreadcrumbHeaderBlock props={props} runtimeContext={runtimeContext} />,
  'layout.sticky-action-bar': ({ props, runtimeContext }) => <StickyActionBarBlock props={props} runtimeContext={runtimeContext} />,
  'layout.category-navigator-side': ({ props, runtimeContext }) => <CategoryNavigatorSideBlock props={props} runtimeContext={runtimeContext} />,
  'layout.category-navigator-top': ({ props, runtimeContext }) => <CategoryNavigatorTopBlock props={props} runtimeContext={runtimeContext} />,
  'media.advanced-photo-gallery': ({ props, runtimeContext }) => <AdvancedPhotoGalleryBlock props={props} runtimeContext={runtimeContext} />,
  'media.auto-play-carousel-hero': ({ props, runtimeContext }) => <AutoPlayCarouselHeroBlock props={props} runtimeContext={runtimeContext} />,
  'media.video-3d-tour-player': ({ props, runtimeContext }) => <Video3DTourPlayerBlock props={props} runtimeContext={runtimeContext} />,
  'media.ad-promo-slot': ({ props, runtimeContext }) => <AdPromoSlotBlock props={props} runtimeContext={runtimeContext} />,
  'data.price-title-block': ({ props, runtimeContext }) => <PriceTitleBlock props={props} runtimeContext={runtimeContext} />,
  'data.attribute-grid-dynamic': ({ props, runtimeContext }) => <AttributeGridDynamicBlock props={props} runtimeContext={runtimeContext} />,
  'data.description-text-area': ({ props, runtimeContext }) => <DescriptionTextAreaBlock props={props} runtimeContext={runtimeContext} />,
  'data.seller-card': ({ props, runtimeContext }) => <SellerCardBlock props={props} runtimeContext={runtimeContext} />,
  'interactive.interactive-map': ({ props, runtimeContext }) => <InteractiveMapBlock props={props} runtimeContext={runtimeContext} />,
  'interactive.mortgage-loan-calculator': ({ props, runtimeContext }) => <MortgageLoanCalculatorBlock props={props} runtimeContext={runtimeContext} />,
  'interactive.similar-listings-slider': ({ props, runtimeContext }) => <SimilarListingsSliderBlock props={props} runtimeContext={runtimeContext} />,
  'interactive.doping-selector': ({ props, runtimeContext }) => <DopingSelectorBlock props={props} runtimeContext={runtimeContext} />,
};
