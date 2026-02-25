import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useLanguage } from '@/contexts/LanguageContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

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

  const title = page ? page[`title_${language}`] || page.title_tr : '';
  const content = page ? page[`content_${language}`] || page.content_tr : '';

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
