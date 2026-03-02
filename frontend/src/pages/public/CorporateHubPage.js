import React from 'react';
import { Link } from 'react-router-dom';

const CORPORATE_LINKS = [
  { slug: 'hakkimizda', label: 'Hakkımızda' },
  { slug: 'iletisim', label: 'İletişim' },
  { slug: 'magaza-cozumleri', label: 'Mağaza Çözümleri' },
  { slug: 'kurumsal-ilan-cozumleri', label: 'Kurumsal İlan Çözümleri' },
];

export default function CorporateHubPage() {
  return (
    <section className="space-y-8" data-testid="corporate-hub-page">
      <div className="rounded-2xl border bg-white p-6" data-testid="corporate-hub-hero">
        <h1 className="text-4xl sm:text-5xl font-semibold text-[var(--text-primary)]" data-testid="corporate-hub-title">Kurumsal Sayfalar</h1>
        <p className="mt-3 text-sm text-[var(--text-secondary)]" data-testid="corporate-hub-subtitle">
          Kurumsal tanıtım, mağaza görünürlüğü ve iş birliği süreçlerine yönelik içeriklere bu merkezden erişebilirsiniz.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2" data-testid="corporate-hub-links">
        {CORPORATE_LINKS.map((item) => (
          <Link
            key={item.slug}
            to={`/bilgi/${item.slug}`}
            className="rounded-xl border bg-white px-4 py-4 text-sm font-medium text-[var(--text-primary)] transition hover:-translate-y-0.5 hover:border-[var(--color-primary)]"
            data-testid={`corporate-hub-link-${item.slug}`}
          >
            {item.label}
          </Link>
        ))}
      </div>
    </section>
  );
}
