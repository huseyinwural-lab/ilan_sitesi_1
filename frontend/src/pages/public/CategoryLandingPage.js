import React from 'react';
import { Navigate, useParams } from 'react-router-dom';

export default function CategoryLandingPage() {
  const { slug = '', locale = '' } = useParams();
  const localePrefix = ['tr', 'de', 'fr'].includes(String(locale || '').toLowerCase()) ? `/${String(locale).toLowerCase()}` : '';
  const target = `${localePrefix}/search?category=${encodeURIComponent(slug)}`;

  return (
    <div data-testid="category-landing-redirect-wrap">
      <Navigate to={target} replace />
    </div>
  );
}
