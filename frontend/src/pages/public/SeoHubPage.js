import React from 'react';
import { Link } from 'react-router-dom';

const SEO_LINKS = [
  { slug: 'nasil-calisir', label: 'Nasıl Çalışır?' },
  { slug: 'guvenli-alisveris', label: 'Güvenli Alışveriş Rehberi' },
  { slug: 'yardim-merkezi', label: 'Yardım Merkezi' },
  { slug: 'site-haritasi', label: 'Site Haritası' },
];

export default function SeoHubPage() {
  return (
    <section className="space-y-8" data-testid="seo-hub-page">
      <div className="rounded-2xl border bg-white p-6" data-testid="seo-hub-hero">
        <h1 className="text-4xl sm:text-5xl font-semibold text-[var(--text-primary)]" data-testid="seo-hub-title">Bilgi ve SEO Merkezi</h1>
        <p className="mt-3 text-sm text-[var(--text-secondary)]" data-testid="seo-hub-subtitle">
          Kullanıcı rehberleri, destek içerikleri ve keşif sayfalarıyla ürün deneyimini güçlendiren bilgilere hızlıca ulaşabilirsiniz.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2" data-testid="seo-hub-links">
        {SEO_LINKS.map((item) => (
          <Link
            key={item.slug}
            to={`/bilgi/${item.slug}`}
            className="rounded-xl border bg-white px-4 py-4 text-sm font-medium text-[var(--text-primary)] transition hover:-translate-y-0.5 hover:border-[var(--color-primary)]"
            data-testid={`seo-hub-link-${item.slug}`}
          >
            {item.label}
          </Link>
        ))}
      </div>
    </section>
  );
}
