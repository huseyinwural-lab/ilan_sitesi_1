import React from 'react';
import { Link } from 'react-router-dom';

const TRUST_LINKS = [
  { slug: 'kullanim-kosullari', label: 'Kullanım Koşulları' },
  { slug: 'gizlilik-politikasi', label: 'Gizlilik Politikası' },
  { slug: 'cerez-politikasi', label: 'Çerez Politikası' },
  { slug: 'kvkk-aydinlatma', label: 'KVKK Aydınlatma Metni' },
  { slug: 'mesafeli-satis-sozlesmesi', label: 'Mesafeli Satış Sözleşmesi' },
];

export default function TrustCenterPage() {
  return (
    <section className="space-y-8" data-testid="trust-center-page">
      <div className="rounded-2xl border bg-white p-6" data-testid="trust-center-hero">
        <h1 className="text-4xl sm:text-5xl font-semibold text-[var(--text-primary)]" data-testid="trust-center-title">Güven ve Politika Merkezi</h1>
        <p className="mt-3 text-sm text-[var(--text-secondary)]" data-testid="trust-center-subtitle">
          Yasal metinler, veri işleme prensipleri ve platform kullanım kurallarına aşağıdaki bağlantılardan erişebilirsiniz.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2" data-testid="trust-center-links">
        {TRUST_LINKS.map((item) => (
          <Link
            key={item.slug}
            to={`/bilgi/${item.slug}`}
            className="rounded-xl border bg-white px-4 py-4 text-sm font-medium text-[var(--text-primary)] transition hover:-translate-y-0.5 hover:border-[var(--color-primary)]"
            data-testid={`trust-center-link-${item.slug}`}
          >
            {item.label}
          </Link>
        ))}
      </div>
    </section>
  );
}
