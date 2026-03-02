export const normalizeCanonicalUrl = (rawUrl) => {
  if (!rawUrl) return '';
  try {
    const parsed = new URL(rawUrl, window.location.origin);
    parsed.hash = '';
    parsed.search = '';

    let path = parsed.pathname || '/';
    path = path.replace(/\/+/g, '/');
    if (path !== '/' && path.endsWith('/')) {
      path = path.slice(0, -1);
    }
    parsed.pathname = path || '/';
    return `${parsed.origin}${parsed.pathname}`;
  } catch {
    return String(rawUrl || '').trim();
  }
};

export const buildCanonicalFromPath = (pathname) => {
  const safePath = `/${String(pathname || '').replace(/^\/+/, '')}`;
  return normalizeCanonicalUrl(`${window.location.origin}${safePath}`);
};
