import React from 'react';

export default function ServerErrorPage({ onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center space-y-4" data-testid="server-error-page">
      <h1 className="text-3xl font-semibold text-[var(--text-primary)]" data-testid="server-error-title">
        Bir hata oluştu
      </h1>
      <p className="text-sm text-[var(--text-secondary)]" data-testid="server-error-description">
        Beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.
      </p>
      <button
        type="button"
        onClick={onRetry || (() => window.location.reload())}
        className="h-10 px-5 rounded-md bg-[var(--color-primary)] text-[var(--text-inverse)]"
        data-testid="server-error-cta"
      >
        Yenile
      </button>
    </div>
  );
}
