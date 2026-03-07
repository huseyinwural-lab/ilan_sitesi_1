import { useEffect, useMemo, useState } from 'react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const useContentLayoutResolve = ({
  country,
  module,
  pageType,
  categoryId,
  sourcePolicy,
  allowDraftPreview = true,
  enabled = true,
}) => {
  const [loading, setLoading] = useState(false);
  const [layout, setLayout] = useState(null);
  const [error, setError] = useState('');

  const queryString = useMemo(() => {
    if (!enabled || !country || !module || !pageType) return '';
    const params = new URLSearchParams();
    params.set('country', String(country).toUpperCase());
    params.set('module', String(module));
    params.set('page_type', String(pageType));
    if (categoryId) params.set('category_id', String(categoryId));
    if (sourcePolicy) params.set('source_policy', String(sourcePolicy));
    if (allowDraftPreview && typeof window !== 'undefined') {
      const mode = new URLSearchParams(window.location.search).get('layout_preview');
      if (mode && mode.toLowerCase() === 'draft') {
        params.set('layout_preview', 'draft');
      }
    }
    return params.toString();
  }, [enabled, country, module, pageType, categoryId, sourcePolicy, allowDraftPreview]);

  useEffect(() => {
    if (!queryString) {
      setLayout(null);
      setError('');
      return;
    }

    let active = true;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 8000);

    const fetchLayout = async () => {
      setLoading(true);
      setError('');
      try {
        const shouldUseDraftPreview = queryString.includes('layout_preview=draft');
        const headers = {};
        if (shouldUseDraftPreview) {
          const accessToken = localStorage.getItem('access_token') || localStorage.getItem('token');
          if (accessToken) headers.Authorization = `Bearer ${accessToken}`;
        }
        const res = await fetch(`${API}/site/content-layout/resolve?${queryString}`, {
          cache: 'no-store',
          signal: controller.signal,
          headers,
        });
        if (!active) return;
        if (!res.ok) {
          setLayout(null);
          const payload = await res.json().catch(() => ({}));
          setError(payload?.detail || 'layout_not_available');
          return;
        }
        const payload = await res.json();
        setLayout(payload || null);
      } catch (err) {
        if (!active) return;
        if (err?.name === 'AbortError') return;
        setLayout(null);
        setError('layout_fetch_failed');
      } finally {
        clearTimeout(timeoutId);
        if (active) setLoading(false);
      }
    };

    fetchLayout();
    return () => {
      active = false;
      clearTimeout(timeoutId);
      controller.abort();
    };
  }, [queryString]);

  return {
    loading,
    layout,
    error,
    hasLayoutRows: Boolean(layout?.revision?.payload_json?.rows?.length),
  };
};
