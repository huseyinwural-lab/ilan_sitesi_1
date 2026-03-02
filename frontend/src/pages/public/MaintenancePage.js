import React from 'react';

export default function MaintenancePage() {
  return (
    <section className="py-16" data-testid="maintenance-page">
      <div className="mx-auto max-w-2xl rounded-2xl border bg-white p-8 text-center" data-testid="maintenance-card">
        <h1 className="text-4xl sm:text-5xl font-semibold text-[var(--text-primary)]" data-testid="maintenance-title">Planlı Bakım Çalışması</h1>
        <p className="mt-4 text-sm text-[var(--text-secondary)]" data-testid="maintenance-description">
          Sistemlerimizde planlı bakım yürütülmektedir. Lütfen kısa bir süre sonra tekrar deneyiniz.
        </p>
        <button
          type="button"
          onClick={() => window.location.reload()}
          className="mt-6 h-10 rounded-md bg-[var(--color-primary)] px-5 text-sm font-medium text-[var(--text-inverse)]"
          data-testid="maintenance-retry-button"
        >
          Yeniden Dene
        </button>
      </div>
    </section>
  );
}
