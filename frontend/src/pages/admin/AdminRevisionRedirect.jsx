import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AdminRevisionRedirect() {
  const navigate = useNavigate();
  const { revisionId } = useParams();
  const [error, setError] = useState('');

  const authHeaders = useMemo(() => {
    const pathLocale = String(window.location.pathname || '').split('/').filter(Boolean)[0]?.toLowerCase();
    const locale = ['tr', 'de', 'fr'].includes(pathLocale)
      ? pathLocale
      : String(localStorage.getItem('language') || 'tr').toLowerCase();
    return {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`,
      'Accept-Language': locale,
      'X-URL-Locale': locale,
    };
  }, []);

  useEffect(() => {
    let mounted = true;
    const run = async () => {
      if (!revisionId) {
        setError('revision_id bulunamadı');
        return;
      }

      try {
        const response = await axios.get(`${API}/admin/layouts/${revisionId}`, {
          headers: authHeaders,
          timeout: 20000,
        });
        if (!mounted) return;

        const page = response.data?.page;
        if (!page?.id) {
          setError('Revision context bulunamadı');
          return;
        }

        const params = new URLSearchParams();
        params.set('autoload_page_id', page.id);
        params.set('autoload_revision_id', revisionId);
        params.set('page_type', page.page_type || 'home');
        params.set('country', String(page.country || 'TR').toUpperCase());
        params.set('module', String(page.module || 'global'));
        if (page.category_id) {
          params.set('category_id', page.category_id);
        }

        navigate(`/admin/site-design/content-builder?${params.toString()}`, { replace: true });
      } catch (requestError) {
        if (!mounted) return;
        const message = requestError?.response?.data?.detail || requestError?.message || 'Revision açılamadı';
        setError(String(message));
      }
    };

    run();
    return () => {
      mounted = false;
    };
  }, [authHeaders, navigate, revisionId]);

  return (
    <section className="rounded-lg border bg-white p-4" data-testid="admin-revision-redirect-page">
      {error ? (
        <div data-testid="admin-revision-redirect-error-wrap">
          <p className="text-sm text-rose-700" data-testid="admin-revision-redirect-error-message">{error}</p>
          <button
            type="button"
            className="mt-3 h-9 rounded border px-3 text-xs"
            onClick={() => navigate('/admin/site-design/content-list')}
            data-testid="admin-revision-redirect-back-button"
          >
            Content List’e Dön
          </button>
        </div>
      ) : (
        <p className="text-sm text-slate-600" data-testid="admin-revision-redirect-loading">Revision açılıyor...</p>
      )}
    </section>
  );
}
