import React from 'react';
import { useNavigate } from 'react-router-dom';

export default function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center py-16 text-center space-y-4" data-testid="not-found-page">
      <h1 className="text-3xl font-semibold text-[var(--text-primary)]" data-testid="not-found-title">
        Sayfa bulunamadı
      </h1>
      <p className="text-sm text-[var(--text-secondary)]" data-testid="not-found-description">
        Aradığınız sayfa mevcut değil veya taşınmış olabilir.
      </p>
      <button
        type="button"
        onClick={() => navigate('/')}
        className="h-10 px-5 rounded-md bg-[var(--color-primary)] text-[var(--text-inverse)]"
        data-testid="not-found-cta"
      >
        Ana Sayfaya Dön
      </button>
    </div>
  );
}
