import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { useCountry } from '@/contexts/CountryContext';
import { useLanguage } from '@/contexts/LanguageContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function CategoryLandingPage() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const { selectedCountry } = useCountry();
  const { language } = useLanguage();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [category, setCategory] = useState(null);

  const canonicalUrl = useMemo(() => {
    const origin = window.location.origin;
    return `${origin}/kategori/${encodeURIComponent(slug || '')}`;
  }, [slug]);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setLoading(true);
      setError('');
      try {
        const params = new URLSearchParams();
        params.set('country', (selectedCountry || 'DE').toUpperCase());
        params.set('lang', (language || 'tr').toLowerCase());
        params.set('_ts', String(Date.now()));

        const response = await fetch(`${API}/v2/categories/${encodeURIComponent(slug || '')}?${params.toString()}`, {
          cache: 'no-store',
        });

        if (!response.ok) {
          throw new Error(response.status === 404 ? 'Kategori bulunamadı' : 'Kategori verisi alınamadı');
        }

        const payload = await response.json();
        if (cancelled) return;

        if (!Array.isArray(payload?.children) || payload.children.length === 0) {
          navigate(`/search?category=${encodeURIComponent(payload.id)}`, { replace: true });
          return;
        }

        setCategory(payload);
      } catch (err) {
        if (cancelled) return;
        setError(err.message || 'Kategori verisi alınamadı');
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();
    return () => {
      cancelled = true;
    };
  }, [slug, selectedCountry, language, navigate]);

  const seoTitle = String(category?.seo_meta?.title || category?.name || 'Kategori');
  const seoDescription = String(category?.seo_meta?.description || category?.description || 'Kategori ilanlarını keşfedin.');

  if (loading) {
    return <div className="py-10 text-sm" data-testid="category-landing-loading">Yükleniyor...</div>;
  }

  if (error) {
    return <div className="py-10 text-sm text-red-600" data-testid="category-landing-error">{error}</div>;
  }

  if (!category) {
    return null;
  }

  return (
    <div className="space-y-8" data-testid="category-landing-page">
      <Helmet>
        <title>{seoTitle}</title>
        <meta name="description" content={seoDescription} />
        <link rel="canonical" href={canonicalUrl} />
      </Helmet>

      <nav className="text-sm text-muted-foreground" aria-label="Breadcrumb" data-testid="category-landing-breadcrumb">
        <ol className="flex items-center gap-2">
          <li>
            <Link to="/" className="hover:underline" data-testid="category-landing-breadcrumb-home">Ana Sayfa</Link>
          </li>
          <li>/</li>
          <li className="text-foreground" data-testid="category-landing-breadcrumb-current">{category.name}</li>
        </ol>
      </nav>

      <header className="space-y-2" data-testid="category-landing-header">
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold" data-testid="category-landing-title">{category.name}</h1>
        {category.description ? (
          <p className="text-sm md:text-base text-muted-foreground" data-testid="category-landing-description">{category.description}</p>
        ) : null}
      </header>

      <section className="space-y-4" data-testid="category-landing-children-section">
        <h2 className="text-base md:text-lg font-semibold" data-testid="category-landing-children-heading">Alt Kategoriler</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" data-testid="category-landing-children-grid">
          {category.children.map((child) => (
            <Link
              key={child.id}
              to={`/search?category=${encodeURIComponent(child.id)}`}
              className="rounded-xl border bg-card p-4 hover:border-primary transition-colors"
              data-testid={`category-landing-child-card-${child.id}`}
            >
              <div className="flex items-start gap-3">
                <div className="h-10 w-10 rounded-full bg-muted flex items-center justify-center text-sm" data-testid={`category-landing-child-icon-${child.id}`}>
                  {child.icon || (child.name || '?').slice(0, 1).toUpperCase()}
                </div>
                <div className="min-w-0">
                  <div className="font-medium truncate" data-testid={`category-landing-child-name-${child.id}`}>{child.name}</div>
                  <div className="text-xs text-muted-foreground" data-testid={`category-landing-child-count-${child.id}`}>
                    {Number(child.listing_count || 0)} ilan
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </section>

      <section className="pt-2" data-testid="category-landing-cta-section">
        <Link
          to={`/search?category=${encodeURIComponent(category.id)}`}
          className="inline-flex items-center rounded-full bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground hover:opacity-90"
          data-testid="category-landing-cta-button"
        >
          Bu kategoride detaylı ara
        </Link>
      </section>
    </div>
  );
}
