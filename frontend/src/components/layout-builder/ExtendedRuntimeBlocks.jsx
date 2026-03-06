import React, { useEffect, useMemo, useRef, useState } from 'react';
import AdSlot from '@/components/public/AdSlot';

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

const resolveRuntimeCountry = (runtimeContext, props) => {
  const raw = String(runtimeContext?.country || props?.country || '').trim();
  if (!raw) return 'TR';
  return raw.toUpperCase();
};

const resolveQueryParam = (key) => {
  if (typeof window === 'undefined') return '';
  const params = new URLSearchParams(window.location.search || '');
  return String(params.get(key) || '').trim();
};

const buildCategoryRoute = (category) => {
  const localePrefix = resolveLocalePrefix();
  const slug = String(category?.slug || '').trim();
  const id = String(category?.id || '').trim();
  const base = `${localePrefix}/kategori`;
  if (!id && !slug) return base;
  const params = new URLSearchParams();
  if (id) params.set('category_id', id);
  if (slug) params.set('slug', slug);
  if (category?.parent_id) params.set('parent_id', String(category.parent_id));
  return `${base}?${params.toString()}`;
};

const normalizePublicListingItem = (item, index = 0) => {
  const badges = Array.isArray(item?.badges)
    ? item.badges
    : (item?.badge ? [item.badge] : []);
  const city = item?.location?.city || item?.city || '';
  return {
    id: item?.id || `listing-${index}`,
    title: item?.title || item?.name || `İlan ${index + 1}`,
    price: Number(item?.price ?? item?.price_amount ?? 0) || 0,
    currency: item?.currency || 'EUR',
    city,
    badges,
    image_url: resolveMediaUrl(item?.thumbnail_url || item?.image_url || item?.cover_image_url || ''),
    url: item?.detail_url || (item?.id ? `/ilan/${item.id}` : '#'),
  };
};

const usePublicListings = ({ props, runtimeContext, defaultSource = 'latest', defaultLimit = 8, includePagination = false }) => {
  const [items, setItems] = useState([]);
  const [pagination, setPagination] = useState({ total: 0, page: 1, pages: 0 });
  const [loading, setLoading] = useState(false);

  const country = resolveRuntimeCountry(runtimeContext, props);
  const source = String(props?.source || defaultSource || 'latest').trim().toLowerCase();
  const rows = Math.max(1, Math.min(12, Number(props?.rows || 1)));
  const columns = Math.max(1, Math.min(6, Number(props?.columns || defaultLimit)));
  const autoRefresh = String(props?.auto_refresh || 'off').toLowerCase();
  const order = String(props?.order || 'newest').toLowerCase();
  const perPage = Math.max(1, Math.min(100, Number(props?.per_page || (rows * columns) || defaultLimit)));
  const requestedLimit = Math.max(1, Math.min(100, rows * columns || perPage || defaultLimit));
  const pageFromUrl = Math.max(1, Number(resolveQueryParam('page') || 1));
  const currentPage = includePagination ? pageFromUrl : 1;
  const searchCategoryId = resolveQueryParam('category_id') || resolveQueryParam('category');
  const searchBadge = resolveQueryParam('badge');
  const searchQuery = resolveQueryParam('q');
  const categoryId = String(props?.category_id || searchCategoryId || '').trim();
  const badge = String(props?.badge || searchBadge || '').trim();
  const query = String(props?.q || searchQuery || '').trim();

  const queryString = useMemo(() => {
    const params = new URLSearchParams();
    params.set('country', country);
    if (source) params.set('source', source);
    if (badge) params.set('badge', badge);
    if (categoryId) params.set('category_id', categoryId);
    if (query) params.set('q', query);
    params.set('order', order || 'newest');
    params.set('page', String(currentPage));
    params.set('limit', String(includePagination ? perPage : requestedLimit));
    return params.toString();
  }, [country, source, badge, categoryId, query, order, currentPage, includePagination, perPage, requestedLimit]);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    fetch(`${API}/public/listings?${queryString}`, { cache: 'no-store' })
      .then((response) => (response.ok ? response.json() : null))
      .then((payload) => {
        if (!alive) return;
        const normalizedItems = Array.isArray(payload?.items)
          ? payload.items.map((item, index) => normalizePublicListingItem(item, index))
          : [];
        setItems(normalizedItems);
        setPagination(payload?.pagination || { total: 0, page: currentPage, pages: 0 });
      })
      .catch(() => {
        if (!alive) return;
        setItems([]);
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, [queryString, currentPage]);

  useEffect(() => {
    const msMap = { '15s': 15000, '30s': 30000, '60s': 60000 };
    const ttl = msMap[autoRefresh] || 0;
    if (!ttl) return undefined;
    const timer = window.setInterval(() => {
      fetch(`${API}/public/listings?${queryString}`, { cache: 'no-store' })
        .then((response) => (response.ok ? response.json() : null))
        .then((payload) => {
          const normalizedItems = Array.isArray(payload?.items)
            ? payload.items.map((item, index) => normalizePublicListingItem(item, index))
            : [];
          setItems(normalizedItems);
          setPagination(payload?.pagination || { total: 0, page: currentPage, pages: 0 });
        })
        .catch(() => {});
    }, ttl);
    return () => window.clearInterval(timer);
  }, [autoRefresh, queryString, currentPage]);

  return {
    items,
    loading,
    pagination,
    currentPage,
    country,
    requestedLimit: includePagination ? perPage : requestedLimit,
  };
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

const resolveCategoryNodeCount = (node) => {
  const own = Number(node?.listing_count || 0);
  if (Number.isFinite(own) && own > 0) return own;
  const children = Array.isArray(node?.children) ? node.children : [];
  if (!children.length) return 0;
  return children.reduce((sum, child) => sum + resolveCategoryNodeCount(child), 0);
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

const useAdminCategoryTree = ({ country, moduleName, depthToken }) => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let alive = true;
    const normalizedModule = String(moduleName || '').trim();
    const moduleParam = ['global', 'all', '*', ''].includes(normalizedModule.toLowerCase()) ? '' : normalizedModule;
    setLoading(true);
    const params = new URLSearchParams();
    params.set('country', country);
    params.set('depth', depthToken);
    if (moduleParam) params.set('module', moduleParam);

    fetch(`${API}/categories/tree?${params.toString()}`, { cache: 'no-store' })
      .then((response) => (response.ok ? response.json() : null))
      .then((payload) => {
        if (!alive) return;
        setItems(Array.isArray(payload?.items) ? payload.items : []);
      })
      .catch(() => {
        if (alive) setItems([]);
      })
      .finally(() => {
        if (alive) setLoading(false);
      });

    return () => {
      alive = false;
    };
  }, [country, moduleName, depthToken]);

  return { items, loading };
};

const resolveCategoryNodeToken = (node) => String(node?.id || node?.slug || '').trim();

const findCategoryPathInTree = (tree, selectedToken) => {
  const walk = (nodes, trail) => {
    for (const node of nodes) {
      const nextTrail = [...trail, node];
      const isMatch = [node?.id, node?.slug].some((token) => normalizeToken(token) === selectedToken);
      if (isMatch) return nextTrail;
      const childPath = walk(Array.isArray(node?.children) ? node.children : [], nextTrail);
      if (childPath.length) return childPath;
    }
    return [];
  };
  return walk(Array.isArray(tree) ? tree : [], []);
};

const triggerCategoryNavigation = (runtimeContext, node) => {
  const token = resolveCategoryNodeToken(node);
  if (typeof runtimeContext?.onCategoryChange === 'function') {
    runtimeContext.onCategoryChange(token || null);
  }
  if (typeof window !== 'undefined') {
    window.location.href = buildCategoryRoute(node || {});
  }
};

export const CategoryNavigatorMainSideBlock = ({ props, runtimeContext }) => {
  const title = props?.title || 'Kategoriler';
  const showCounts = props?.show_counts !== false;
  const country = resolveRuntimeCountry(runtimeContext, props);
  const moduleName = String(props?.module || runtimeContext?.module || 'global').trim();
  const { items: apiTree, loading } = useAdminCategoryTree({ country, moduleName, depthToken: 'L1' });
  const runtimeItems = Array.isArray(runtimeContext?.categories) ? runtimeContext.categories : [];

  const tree = useMemo(() => {
    if (apiTree.length > 0) return apiTree;
    if (runtimeItems.length > 0) return buildL0L1Categories(runtimeItems);
    return [];
  }, [apiTree, runtimeItems]);

  return (
    <section className="rounded border border-slate-200 bg-white p-3" data-testid="runtime-category-navigator-main-side">
      <h3 className="border-b pb-2 text-[13px] font-bold text-slate-700" data-testid="runtime-category-navigator-main-side-title">{title}</h3>
      <div className="mt-2" data-testid="runtime-category-navigator-main-side-tree">
        {loading ? <div className="text-xs text-slate-500" data-testid="runtime-category-navigator-main-side-loading">Yükleniyor...</div> : null}
        {tree.map((root) => {
          const rootCount = resolveCategoryNodeCount(root);
          const rootChildren = Array.isArray(root.children) ? root.children : [];
          return (
            <div key={root.id || root.slug} className="border-b border-slate-200 py-2 last:border-b-0" data-testid={`runtime-category-navigator-main-side-root-${root.id || root.slug}`}>
              <button
                type="button"
                className="text-left text-[18px] font-bold leading-6 text-blue-700"
                onClick={() => triggerCategoryNavigation(runtimeContext, root)}
                data-testid={`runtime-category-navigator-main-side-root-link-${root.id || root.slug}`}
              >
                {root.name}{showCounts ? ` (${rootCount})` : ''}
              </button>
              <div className="mt-1 space-y-0.5 pl-8" data-testid={`runtime-category-navigator-main-side-children-${root.id || root.slug}`}>
                {rootChildren.map((child) => {
                  const childCount = resolveCategoryNodeCount(child);
                  return (
                    <button
                      key={child.id || child.slug}
                      type="button"
                      className="block w-full text-left text-[17px] font-semibold leading-6 text-blue-700"
                      onClick={() => triggerCategoryNavigation(runtimeContext, child)}
                      data-testid={`runtime-category-navigator-main-side-child-link-${child.id || child.slug}`}
                    >
                      {child.name}{showCounts ? ` (${childCount})` : ''}
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
};

export const CategoryNavigatorCategorySideBlock = ({ props, runtimeContext }) => {
  const title = props?.title || 'Kategori Side';
  const country = resolveRuntimeCountry(runtimeContext, props);
  const moduleName = String(props?.module || runtimeContext?.module || 'global').trim();
  const maxVisibleItems = Math.max(4, Math.min(40, toNumber(props?.max_visible_items, 12)));
  const { items: apiTree, loading } = useAdminCategoryTree({ country, moduleName, depthToken: 'Lall' });
  const runtimeItems = Array.isArray(runtimeContext?.categories) ? runtimeContext.categories : [];
  const selectedToken = normalizeToken(runtimeContext?.activeCategorySlug || resolveQueryParam('category_id') || resolveQueryParam('slug'));

  const tree = useMemo(() => {
    if (apiTree.length > 0) return apiTree;
    if (runtimeItems.length > 0) return buildL0L1Categories(runtimeItems);
    return [];
  }, [apiTree, runtimeItems]);

  const pathNodes = useMemo(() => {
    if (!tree.length) return [];
    const matched = selectedToken ? findCategoryPathInTree(tree, selectedToken) : [];
    return matched.length ? matched : [tree[0]];
  }, [tree, selectedToken]);

  const contentParentNode = useMemo(() => {
    if (!pathNodes.length) return null;
    const last = pathNodes[pathNodes.length - 1];
    const lastChildren = Array.isArray(last?.children) ? last.children : [];
    if (lastChildren.length > 0) return last;
    if (pathNodes.length >= 2) return pathNodes[pathNodes.length - 2];
    return last;
  }, [pathNodes]);

  const contentItems = useMemo(() => {
    const children = Array.isArray(contentParentNode?.children) ? contentParentNode.children : [];
    return children.slice(0, maxVisibleItems);
  }, [contentParentNode, maxVisibleItems]);

  const breadcrumbNodes = pathNodes.length ? ['Anasayfa', ...pathNodes.map((node) => node.name)] : ['Anasayfa'];
  const listHeight = Math.max(220, Math.min(560, maxVisibleItems * 34));

  return (
    <section className="space-y-2" data-testid="runtime-category-navigator-category-side">
      <div className="flex flex-wrap items-center gap-2 text-[18px] font-semibold text-blue-700" data-testid="runtime-category-navigator-category-side-breadcrumb">
        {breadcrumbNodes.map((label, index) => (
          <React.Fragment key={`${label}-${index}`}>
            {index > 0 ? <span className="text-slate-400">›</span> : null}
            <span>{label}</span>
          </React.Fragment>
        ))}
      </div>

      <div className="rounded border border-slate-300 bg-white p-4" data-testid="runtime-category-navigator-category-side-card">
        <h3 className="mb-2 text-[18px] font-bold text-blue-700" data-testid="runtime-category-navigator-category-side-title">{title}</h3>
        <div className="space-y-0.5" data-testid="runtime-category-navigator-category-side-path-lines">
          {pathNodes.map((node, index) => (
            <button
              key={node.id || node.slug || `path-${index}`}
              type="button"
              className="block text-left text-[17px] font-semibold leading-6 text-blue-700"
              style={{ paddingLeft: `${index * 22}px` }}
              onClick={() => triggerCategoryNavigation(runtimeContext, node)}
              data-testid={`runtime-category-navigator-category-side-path-link-${node.id || node.slug || index}`}
            >
              {node.name}
            </button>
          ))}
        </div>

        <div className="mt-2 overflow-y-auto pr-2" style={{ maxHeight: `${listHeight}px` }} data-testid="runtime-category-navigator-category-side-scroll-list">
          {loading ? <div className="text-xs text-slate-500" data-testid="runtime-category-navigator-category-side-loading">Yükleniyor...</div> : null}
          {contentItems.map((item) => (
            <button
              key={item.id || item.slug}
              type="button"
              className="block w-full text-left text-[17px] font-semibold leading-7 text-blue-700"
              onClick={() => triggerCategoryNavigation(runtimeContext, item)}
              data-testid={`runtime-category-navigator-category-side-item-${item.id || item.slug}`}
            >
              {item.name} <span className="text-slate-500">({resolveCategoryNodeCount(item)})</span>
            </button>
          ))}
        </div>
      </div>
    </section>
  );
};

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

const useDynamicBanners = (props, runtimeContext) => {
  const [items, setItems] = useState([]);
  const mode = String(props?.mode || 'static').toLowerCase();
  const placement = String(props?.placement || 'home_top').toLowerCase();
  const country = resolveRuntimeCountry(runtimeContext, props);

  useEffect(() => {
    let alive = true;
    if (mode !== 'dynamic') {
      setItems([]);
      return () => {
        alive = false;
      };
    }
    const params = new URLSearchParams();
    params.set('placement', placement);
    params.set('country', country);
    fetch(`${API}/banners?${params.toString()}`, { cache: 'no-store' })
      .then((response) => (response.ok ? response.json() : null))
      .then((payload) => {
        if (!alive) return;
        const nextItems = Array.isArray(payload?.items) ? payload.items : [];
        setItems(nextItems.map((item) => ({
          id: item.id,
          image_url: resolveMediaUrl(item.image_url || ''),
          target_url: item.target_url || '#',
        })));
      })
      .catch(() => {
        if (alive) setItems([]);
      });
    return () => {
      alive = false;
    };
  }, [mode, placement, country]);

  return items;
};

export const AutoPlayCarouselHeroBlock = ({ props, runtimeContext }) => {
  const dynamicSlides = useDynamicBanners(props, runtimeContext);
  const fallbackSlides = normalizeItems(runtimeContext?.showcaseItems || runtimeContext?.searchItems || [], 'hero-live').slice(0, 5);
  const staticSlides = normalizeItems(props?.slides || fallbackSlides || [
    { id: 's1', label: 'Vitrin İlanlarınız Daha Görünür', url: '/search?doping=showcase' },
    { id: 's2', label: 'Ücretsiz İlan Verin', url: '/ilan-ver' },
  ], 'hero').map((item, index) => ({ ...item, image: props?.images?.[index] || FALLBACK_IMAGES[index % FALLBACK_IMAGES.length] }));
  const slides = dynamicSlides.length
    ? dynamicSlides.map((item, index) => ({ id: item.id || `dynamic-${index}`, label: props?.title || 'Banner', url: item.target_url || '#', image: item.image_url || FALLBACK_IMAGES[index % FALLBACK_IMAGES.length] }))
    : staticSlides;
  const safeSlides = slides.length > 0
    ? slides
    : [{ id: 'fallback-hero', label: props?.title || 'Vitrin', url: '#', image: FALLBACK_IMAGES[0] }];
  const [activeIndex, setActiveIndex] = useState(0);
  const autoPlaySeconds = Math.max(2, Math.min(15, toNumber(props?.auto_play_seconds, 5)));

  useEffect(() => {
    if (safeSlides.length <= 1) return undefined;
    const timer = window.setInterval(() => {
      setActiveIndex((prev) => (prev + 1) % safeSlides.length);
    }, autoPlaySeconds * 1000);
    return () => window.clearInterval(timer);
  }, [safeSlides.length, autoPlaySeconds]);

  const activeSlide = safeSlides[activeIndex] || safeSlides[0];
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

export const Video3DTourPlayerBlock = ({ props, runtimeContext }) => {
  const dynamicItems = useDynamicBanners(props, runtimeContext);
  const mode = String(props?.mode || 'static').toLowerCase();
  const sourceUrl = String(props?.source_url || '').trim();
  const provider = props?.provider || 'youtube';
  const iframeUrl = useMemo(() => {
    if (mode === 'dynamic') return '';
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
      {mode === 'dynamic' && dynamicItems.length > 0 ? (
        <a href={dynamicItems[0].target_url || '#'} className="mt-2 block" data-testid="runtime-video-3d-dynamic-link">
          <img src={dynamicItems[0].image_url} alt="dynamic-banner" className="aspect-video w-full rounded border object-cover" data-testid="runtime-video-3d-dynamic-image" />
        </a>
      ) : iframeUrl ? (
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
    <AdSlot
      placement={resolveAdPlacementToken(props?.placement || 'AD_HOME_TOP')}
      className="rounded-lg border"
      rotation={String(props?.rotation || 'off').toLowerCase() === 'on'}
      country={props?.country}
      size={props?.size || 'auto'}
    />
  </section>
);

const SimpleListingCard = ({ item, dataTestId }) => (
  <a href={item?.url || '#'} className="overflow-hidden rounded-lg border bg-white text-xs" data-testid={dataTestId}>
    <div className="aspect-[4/3] bg-slate-100" data-testid={`${dataTestId}-photo-wrap`}>
      {item?.image_url ? (
        <img src={item.image_url} alt={item?.title || 'listing'} className="h-full w-full object-cover" data-testid={`${dataTestId}-photo`} />
      ) : (
        <div className="flex h-full items-center justify-center text-[11px] text-slate-500" data-testid={`${dataTestId}-photo-empty`}>Foto yok</div>
      )}
    </div>
    <div className="space-y-1 p-3">
      <div className="line-clamp-2 font-semibold" data-testid={`${dataTestId}-title`}>{item?.title || item?.label || 'İlan'}</div>
      <div className="font-medium text-slate-800" data-testid={`${dataTestId}-price`}>
        {item?.price ? `${new Intl.NumberFormat('tr-TR').format(item.price)} ${item?.currency || 'EUR'}` : 'Fiyat bilgisi yok'}
      </div>
      <div className="text-slate-500" data-testid={`${dataTestId}-location`}>{item?.city || 'Lokasyon'}</div>
      {Array.isArray(item?.badges) && item.badges.length > 0 ? (
        <div className="flex flex-wrap gap-1" data-testid={`${dataTestId}-badges`}>
          {item.badges.map((badge) => (
            <span key={`${item.id}-${badge}`} className="rounded-full border px-2 py-0.5 text-[10px] uppercase" data-testid={`${dataTestId}-badge-${badge}`}>
              {badge}
            </span>
          ))}
        </div>
      ) : null}
    </div>
  </a>
);

const resolveQuickFilterRoute = (quickFilter) => {
  const localePrefix = resolveLocalePrefix();
  const normalized = String(quickFilter || '').trim().toLowerCase();
  if (normalized === 'urgent') return `${localePrefix}/acil?badge=urgent`;
  if (normalized === 'showcase') return `${localePrefix}/vitrin?badge=showcase`;
  if (normalized === 'campaign') return `${localePrefix}/kampanya?badge=campaign`;
  return `${localePrefix}/acil?badge=urgent`;
};

export const HeadingBlock = ({ props }) => {
  const text = props?.text || 'Başlık';
  const fontSize = Math.max(16, Math.min(72, Number(props?.font_size || 32)));
  const fontWeight = String(props?.font_weight || '800');
  const textAlign = String(props?.alignment || 'left');
  return (
    <section className="rounded-xl border bg-white p-4" data-testid="runtime-heading-block">
      <h2 style={{ fontSize, fontWeight, textAlign }} className="leading-tight" data-testid="runtime-heading-block-text">{text}</h2>
    </section>
  );
};

export const TextContentBlock = ({ props }) => {
  const text = props?.text || props?.body || 'Metin içeriği';
  const fontSize = Math.max(12, Math.min(28, Number(props?.font_size || 15)));
  const fontWeight = String(props?.font_weight || '400');
  const textAlign = String(props?.alignment || 'left');
  return (
    <section className="rounded-xl border bg-white p-4" data-testid="runtime-text-content-block">
      <p style={{ fontSize, fontWeight, textAlign }} className="whitespace-pre-wrap text-slate-700" data-testid="runtime-text-content-block-text">{text}</p>
    </section>
  );
};

export const CTABlock = ({ props }) => {
  const mode = String(props?.mode || 'quick_filter').toLowerCase();
  const title = props?.title || (mode === 'quick_filter' ? 'ACİL' : 'Detay');
  const href = mode === 'quick_filter'
    ? resolveQuickFilterRoute(props?.quick_filter)
    : (props?.link || '/acil');
  const stylePreset = String(props?.style || 'primary').toLowerCase();
  const target = String(props?.target || 'same').toLowerCase();
  const fontSize = Math.max(10, Math.min(24, Number(props?.font_size || 14)));
  const fontWeight = String(props?.font_weight || '700');
  const fontStyle = String(props?.font_style || 'normal');
  const textColor = props?.text_color || '#ffffff';
  const bgColor = props?.bg_color || '#dc2626';

  const presetStyles = {
    primary: { backgroundColor: '#1d4ed8', color: '#ffffff', border: '1px solid #1d4ed8' },
    danger: { backgroundColor: '#dc2626', color: '#ffffff', border: '1px solid #dc2626' },
    outline: { backgroundColor: 'transparent', color: '#0f172a', border: '1px solid #94a3b8' },
    ghost: { backgroundColor: '#f8fafc', color: '#0f172a', border: '1px solid transparent' },
  };
  const selectedPreset = presetStyles[stylePreset] || presetStyles.primary;

  return (
    <section className="rounded-xl border bg-white p-4" data-testid="runtime-cta-block">
      <button
        type="button"
        className="inline-flex w-full max-w-full items-center justify-center rounded-full px-4 py-2 text-center"
        style={{
          fontSize,
          fontWeight,
          fontStyle,
          color: textColor || selectedPreset.color,
          backgroundColor: bgColor || selectedPreset.backgroundColor,
          border: selectedPreset.border,
          whiteSpace: 'normal',
          wordBreak: 'break-word',
        }}
        onClick={() => {
          if (typeof window === 'undefined') return;
          if (target === 'new_tab') {
            window.open(href, '_blank', 'noopener,noreferrer');
          } else {
            window.location.href = href;
          }
        }}
        data-testid="runtime-cta-block-button"
      >
        {props?.icon ? <span className="mr-2">{props.icon}</span> : null}
        {title}
      </button>
    </section>
  );
};

export const ListingGridBlock = ({ props, runtimeContext }) => {
  const columns = Math.max(1, Math.min(6, Number(props?.columns || 4)));
  const rows = Math.max(1, Math.min(12, Number(props?.rows || 2)));
  const maxItems = columns * rows;

  const { items: apiItems, loading } = usePublicListings({
    props,
    runtimeContext,
    defaultSource: 'showcase',
    defaultLimit: maxItems,
    includePagination: false,
  });

  const fallbackItems = normalizeItems(
    runtimeContext?.showcaseItems || runtimeContext?.searchItems || runtimeContext?.recentItems || ['Vitrin İlan 1', 'Vitrin İlan 2', 'Vitrin İlan 3', 'Vitrin İlan 4'],
    'listing-grid',
  ).map((item, index) => normalizePublicListingItem(item, index));

  const items = (apiItems.length ? apiItems : fallbackItems).slice(0, maxItems);


  return (
    <section className="rounded-xl border bg-white p-4" data-testid="runtime-listing-grid">
      <h3 className="text-sm font-semibold" data-testid="runtime-listing-grid-title">Listing Grid</h3>
      {loading ? <div className="mt-2 text-[11px] text-slate-500" data-testid="runtime-listing-grid-loading">İlanlar yükleniyor...</div> : null}
      <div className="mt-3 grid gap-2" style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }} data-testid="runtime-listing-grid-items">
        {items.map((item, index) => <SimpleListingCard key={`${item.id}-${index}`} item={item} dataTestId={`runtime-listing-grid-item-${index}`} />)}
      </div>
      {!loading && items.length === 0 ? <div className="mt-2 rounded border border-dashed px-2 py-2 text-[11px] text-slate-500" data-testid="runtime-listing-grid-empty">İlan bulunamadı.</div> : null}
    </section>
  );
};

export const ListingListBlock = ({ props, runtimeContext }) => {
  const [tick, setTick] = useState(0);
  const paginationEnabled = props?.pagination !== false;
  const { items: apiItems, loading, pagination, currentPage } = usePublicListings({
    props,
    runtimeContext,
    defaultSource: 'urgent',
    defaultLimit: Math.max(5, Math.min(100, Number(props?.per_page || 20))),
    includePagination: paginationEnabled,
  });

  const fallbackItems = normalizeItems(
    runtimeContext?.searchItems || runtimeContext?.urgentItems || runtimeContext?.recentItems || ['Acil İlan 1', 'Acil İlan 2', 'Acil İlan 3'],
    'listing-list',
  ).map((item, index) => normalizePublicListingItem(item, index));

  const items = apiItems.length ? apiItems : fallbackItems;

  const updatePage = (nextPage) => {
    if (typeof window === 'undefined') return;
    const params = new URLSearchParams(window.location.search || '');
    params.set('page', String(Math.max(1, nextPage)));
    const nextUrl = `${window.location.pathname}?${params.toString()}`;
    window.history.pushState({}, '', nextUrl);
    setTick((prev) => prev + 1);
    window.dispatchEvent(new PopStateEvent('popstate'));
  };

  return (
    <section className="rounded-xl border bg-white p-4" data-testid="runtime-listing-list" data-refresh-key={tick}>
      <h3 className="text-sm font-semibold" data-testid="runtime-listing-list-title">Listing List</h3>
      {loading ? <div className="mt-2 text-[11px] text-slate-500" data-testid="runtime-listing-list-loading">İlanlar yükleniyor...</div> : null}
      <div className="mt-3 space-y-2" data-testid="runtime-listing-list-items">
        {items.map((item, index) => <SimpleListingCard key={`${item.id}-${index}`} item={item} dataTestId={`runtime-listing-list-item-${index}`} />)}
      </div>
      {!loading && items.length === 0 ? <div className="mt-2 rounded border border-dashed px-2 py-2 text-[11px] text-slate-500" data-testid="runtime-listing-list-empty">İlan bulunamadı.</div> : null}
      {paginationEnabled ? (
        <div className="mt-3 flex items-center justify-between text-xs" data-testid="runtime-listing-list-pagination">
          <button
            type="button"
            className="rounded border px-2 py-1 disabled:opacity-50"
            disabled={currentPage <= 1}
            onClick={() => updatePage(currentPage - 1)}
            data-testid="runtime-listing-list-pagination-prev"
          >
            Önceki
          </button>
          <span data-testid="runtime-listing-list-pagination-meta">Sayfa {pagination?.page || currentPage} / {Math.max(1, pagination?.pages || 1)}</span>
          <button
            type="button"
            className="rounded border px-2 py-1 disabled:opacity-50"
            disabled={currentPage >= Number(pagination?.pages || 1)}
            onClick={() => updatePage(currentPage + 1)}
            data-testid="runtime-listing-list-pagination-next"
          >
            Sonraki
          </button>
        </div>
      ) : null}
    </section>
  );
};

export const ListingCardBlock = ({ props, runtimeContext }) => {
  const { items: apiItems } = usePublicListings({
    props,
    runtimeContext,
    defaultSource: 'latest',
    defaultLimit: 1,
    includePagination: false,
  });

  const first = apiItems[0]
    || normalizePublicListingItem((normalizeItems(props?.items || runtimeContext?.searchItems || runtimeContext?.recentItems || ['İlan Kartı'], 'listing-card')[0] || {}), 0)
    || { id: 'listing-card-1', title: 'İlan Kartı', badges: [] };

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
  const depth = Math.max(1, Math.min(6, Number(props?.depth || 2)));
  const columns = Math.max(1, Math.min(6, Number(props?.columns || 3)));
  const showCount = props?.show_count !== false;
  const country = resolveRuntimeCountry(runtimeContext, props);
  const fallbackParent = resolveQueryParam('category_id') || resolveQueryParam('category');
  const parentId = String(props?.parent_id || runtimeContext?.activeCategoryId || fallbackParent || '').trim();
  const [apiItems, setApiItems] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    const params = new URLSearchParams();
    params.set('country', country);
    if (parentId) params.set('parent_id', parentId);
    params.set('depth', String(depth));

    fetch(`${API}/categories/children?${params.toString()}`, { cache: 'no-store' })
      .then((response) => (response.ok ? response.json() : null))
      .then(async (payload) => {
        if (!alive) return;
        const baseItems = Array.isArray(payload)
          ? payload
          : (Array.isArray(payload?.items) ? payload.items : []);

        let countMap = new Map();
        if (showCount) {
          const countParams = new URLSearchParams();
          countParams.set('country', country);
          if (parentId) countParams.set('parent_id', parentId);
          const countsResponse = await fetch(`${API}/categories/listing-counts?${countParams.toString()}`, { cache: 'no-store' }).catch(() => null);
          if (countsResponse?.ok) {
            const countPayload = await countsResponse.json();
            const items = Array.isArray(countPayload?.items) ? countPayload.items : [];
            countMap = new Map(items.map((entry) => [String(entry.id), Number(entry.listing_count || 0)]));
          }
        }

        const normalized = baseItems.map((item) => ({
          id: item.id,
          label: item.name,
          slug: item.slug,
          count: countMap.has(String(item.id)) ? countMap.get(String(item.id)) : Number(item.listing_count || 0),
          url: buildCategoryRoute(item),
        }));
        setApiItems(normalized);
      })
      .catch(() => {
        if (alive) setApiItems([]);
      })
      .finally(() => {
        if (alive) setLoading(false);
      });

    return () => {
      alive = false;
    };
  }, [country, depth, parentId, showCount]);

  const normalizedItems = apiItems.length
    ? apiItems
    : normalizeItems(['Alt Kategori 1', 'Alt Kategori 2', 'Alt Kategori 3'], 'sub-category');

  return (
    <section className="rounded-xl border bg-white p-4" data-testid="runtime-sub-category-block">
      <h3 className="text-sm font-semibold" data-testid="runtime-sub-category-title">Sub Category Block</h3>
      {loading ? <div className="mt-2 text-[11px] text-slate-500" data-testid="runtime-sub-category-loading">Alt kategoriler yükleniyor...</div> : null}
      <div className="mt-3 grid gap-2" style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }} data-testid="runtime-sub-category-items">
        {normalizedItems.map((item, index) => (
          <a key={`${item.id || index}`} href={item?.url || '#'} className="rounded border bg-slate-50 px-2 py-2 text-xs" data-testid={`runtime-sub-category-item-${index}`}>
            {item.label}
            {showCount ? <span className="ml-1 text-slate-500">({Number(item.count || 0)})</span> : null}
          </a>
        ))}
      </div>
    </section>
  );
};

export const ImageBlock = ({ props, runtimeContext }) => {
  const [dynamicImage, setDynamicImage] = useState('');
  const mode = String(props?.mode || 'static').toLowerCase();
  const placement = String(props?.placement || 'home_top').toLowerCase();
  const country = resolveRuntimeCountry(runtimeContext, props);

  useEffect(() => {
    let alive = true;
    if (mode !== 'dynamic') return () => {
      alive = false;
    };
    const params = new URLSearchParams();
    params.set('placement', placement);
    params.set('country', country);
    fetch(`${API}/banners?${params.toString()}`, { cache: 'no-store' })
      .then((response) => (response.ok ? response.json() : null))
      .then((payload) => {
        if (!alive) return;
        const first = Array.isArray(payload?.items) ? payload.items[0] : null;
        setDynamicImage(resolveMediaUrl(first?.image_url || ''));
      })
      .catch(() => {
        if (alive) setDynamicImage('');
      });
    return () => {
      alive = false;
    };
  }, [mode, placement, country]);

  const imageUrl = mode === 'dynamic' ? dynamicImage : resolveMediaUrl(props?.image_url || '');

  return (
    <section className="rounded-xl border bg-white p-4" data-testid="runtime-image-block">
      {imageUrl ? (
        <img src={imageUrl} alt={props?.alt || 'image'} className="w-full rounded border" data-testid="runtime-image-block-image" />
      ) : (
        <div className="rounded border border-dashed px-3 py-8 text-xs text-slate-500" data-testid="runtime-image-block-empty">Image URL tanımlanmadı.</div>
      )}
    </section>
  );
};

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
  const [publicListingPoint, setPublicListingPoint] = useState(null);
  const [showNearby, setShowNearby] = useState(props?.show_nearby_layers !== false);
  const [poiItems, setPoiItems] = useState([]);
  const [poiLoading, setPoiLoading] = useState(false);
  const country = resolveRuntimeCountry(runtimeContext, props);

  useEffect(() => {
    let alive = true;
    const source = String(props?.source || 'latest').toLowerCase();
    const params = new URLSearchParams();
    params.set('country', country);
    params.set('source', source === 'category' ? 'category' : 'latest');
    if (source === 'category') {
      const categoryId = String(props?.category_id || resolveQueryParam('category_id') || '').trim();
      if (categoryId) params.set('category_id', categoryId);
    }
    params.set('limit', '1');
    fetch(`${API}/public/listings?${params.toString()}`, { cache: 'no-store' })
      .then((response) => (response.ok ? response.json() : null))
      .then((payload) => {
        if (!alive) return;
        const first = Array.isArray(payload?.items) ? payload.items[0] : null;
        if (!first) {
          setPublicListingPoint(null);
          return;
        }
        setPublicListingPoint({
          lat: parseCoordinate(first?.location?.latitude),
          lng: parseCoordinate(first?.location?.longitude),
          city: first?.location?.city || first?.city || '',
        });
      })
      .catch(() => {
        if (alive) setPublicListingPoint(null);
      });

    return () => {
      alive = false;
    };
  }, [country, props?.source, props?.category_id]);

  const lat = parseCoordinate(props?.lat ?? publicListingPoint?.lat ?? listing?.location?.latitude) ?? 35.1856;
  const lng = parseCoordinate(props?.lng ?? publicListingPoint?.lng ?? listing?.location?.longitude) ?? 33.3823;
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
      <p className="mt-2 text-xs text-slate-500" data-testid="runtime-interactive-map-meta">Zoom: {zoom} • Şehir: {publicListingPoint?.city || listing?.location?.city || '-'}</p>
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
  'cta.block': ({ props, runtimeContext }) => <CTABlock props={props} runtimeContext={runtimeContext} />,
  'listing.grid': ({ props, runtimeContext }) => <ListingGridBlock props={props} runtimeContext={runtimeContext} />,
  'listing.list': ({ props, runtimeContext }) => <ListingListBlock props={props} runtimeContext={runtimeContext} />,
  'listing.card': ({ props, runtimeContext }) => <ListingCardBlock props={props} runtimeContext={runtimeContext} />,
  'category.sub-category-block': ({ props, runtimeContext }) => <SubCategoryBlock props={props} runtimeContext={runtimeContext} />,
  'ad.slot': ({ props, runtimeContext }) => <AdPromoSlotBlock props={{ ...props, placement: resolveAdPlacementToken(props?.placement) }} runtimeContext={runtimeContext} />,
  'content.heading': ({ props, runtimeContext }) => <HeadingBlock props={props} runtimeContext={runtimeContext} />,
  'content.text-block': ({ props, runtimeContext }) => <TextContentBlock props={props} runtimeContext={runtimeContext} />,
  'shared.text-block': ({ props, runtimeContext }) => <TextContentBlock props={{ ...props, text: props?.text || props?.body || props?.title }} runtimeContext={runtimeContext} />,
  'media.hero-banner': ({ props, runtimeContext }) => <AutoPlayCarouselHeroBlock props={props} runtimeContext={runtimeContext} />,
  'media.carousel': ({ props, runtimeContext }) => <AutoPlayCarouselHeroBlock props={props} runtimeContext={runtimeContext} />,
  'media.image': ({ props, runtimeContext }) => <ImageBlock props={props} runtimeContext={runtimeContext} />,
  'media.video': ({ props, runtimeContext }) => <Video3DTourPlayerBlock props={props} runtimeContext={runtimeContext} />,
  'map.block': ({ props, runtimeContext }) => <InteractiveMapBlock props={props} runtimeContext={runtimeContext} />,
  'layout.breadcrumb-header': ({ props, runtimeContext }) => <BreadcrumbHeaderBlock props={props} runtimeContext={runtimeContext} />,
  'layout.sticky-action-bar': ({ props, runtimeContext }) => <StickyActionBarBlock props={props} runtimeContext={runtimeContext} />,
  'layout.category-navigator-main-side': ({ props, runtimeContext }) => <CategoryNavigatorMainSideBlock props={props} runtimeContext={runtimeContext} />,
  'layout.category-navigator-category-side': ({ props, runtimeContext }) => <CategoryNavigatorCategorySideBlock props={props} runtimeContext={runtimeContext} />,
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
