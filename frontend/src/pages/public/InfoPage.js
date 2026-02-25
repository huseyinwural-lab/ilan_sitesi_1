import React, { useEffect, useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useLanguage } from '@/contexts/LanguageContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const setMetaTag = (key, value, isProperty = false) => {
  if (!value) return;
  const selector = isProperty ? `meta[property="${key}"]` : `meta[name="${key}"]`;
  let tag = document.querySelector(selector);
  if (!tag) {
    tag = document.createElement('meta');
    if (isProperty) {
      tag.setAttribute('property', key);
    } else {
      tag.setAttribute('name', key);
    }
    document.head.appendChild(tag);
  }
  tag.setAttribute('content', value);
};

const setCanonical = (url) => {
  if (!url) return;
  let link = document.querySelector('link[rel="canonical"]');
  if (!link) {
    link = document.createElement('link');
    link.setAttribute('rel', 'canonical');
    document.head.appendChild(link);
  }
  link.setAttribute('href', url);
};

const setStructuredData = (data) => {
  const id = 'info-article-schema';
  let script = document.getElementById(id);
  if (!script) {
    script = document.createElement('script');
    script.type = 'application/ld+json';
    script.id = id;
    document.head.appendChild(script);
  }
  script.textContent = JSON.stringify(data);
};

export default function InfoPage() {
  const { slug } = useParams();
  const { language } = useLanguage();
  const [page, setPage] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    fetch(`${API}/info/${slug}`)
      .then((res) => {
        if (!res.ok) throw new Error('Not found');
        return res.json();
      })
      .then((data) => {
        if (!active) return;
        setPage(data);
      })
      .catch(() => {
        if (!active) return;
        setError('Sayfa bulunamadı');
      });
    return () => {
      active = false;
    };
  }, [slug]);

  const title = useMemo(() => (page ? page[`title_${language}`] || page.title_tr : ''), [page, language]);
  const content = useMemo(() => (page ? page[`content_${language}`] || page.content_tr : ''), [page, language]);

  useEffect(() => {
    if (!page) return;
    const summarySource = page.content_tr || '';
    const summary = summarySource.replace(/\s+/g, ' ').trim().slice(0, 160);
    const canonicalUrl = `${window.location.origin}${window.location.pathname}`;

    document.title = page.title_tr || 'Bilgi';
    setMetaTag('description', summary);
    setCanonical(canonicalUrl);

    setMetaTag('og:title', page.title_tr || '', True);
    setMetaTag('og:description', summary, True);
    setMetaTag('og:type', 'article', True);
    setMetaTag('og:url', canonicalUrl, True);

    setStructuredData({
      '@context': 'https://schema.org',
      '@type': 'Article',
      headline: page.title_tr || '',
      description: summary,
      datePublished: page.created_at || page.updated_at || new Date().toISOString(),
      dateModified: page.updated_at || page.created_at || new Date().toISOString(),
    });
  }, [page]);

  return (
    <div className="space-y-6" data-testid="info-page">
      {error && (
        <div className="text-sm text-rose-600" data-testid="info-page-error">
          {error}
        </div>
      )}
      {page && (
        <>
          <h1 className="text-2xl font-semibold text-[var(--text-primary)]" data-testid="info-page-title">
            {title}
          </h1>
          <div className="text-sm text-[var(--text-secondary)] whitespace-pre-line" data-testid="info-page-content">
            {content}
          </div>
        </>
      )}
    </div>
  );
}
