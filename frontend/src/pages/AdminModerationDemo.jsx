import React, { useMemo, useState } from 'react';

const countries = ['DE', 'FR', 'NL', 'TR'];
const modules = ['vehicle', 'real_estate', 'services'];

const mockRows = [
  {
    id: 'L-1024',
    title: 'Merkezde 3+1 Balkonlu Daire',
    module: 'real_estate',
    country: 'DE',
    city: 'Berlin',
    price: '€245.000',
    status: 'pending_moderation',
    submittedAt: '2026-02-20 12:04',
  },
  {
    id: 'L-2045',
    title: '2021 Model Elektrikli SUV',
    module: 'vehicle',
    country: 'FR',
    city: 'Lyon',
    price: '€41.500',
    status: 'pending_moderation',
    submittedAt: '2026-02-20 13:18',
  },
  {
    id: 'L-3041',
    title: 'Premium Kurumsal Taşımacılık Hizmeti',
    module: 'services',
    country: 'NL',
    city: 'Amsterdam',
    price: '€750 / gün',
    status: 'pending_moderation',
    submittedAt: '2026-02-19 16:22',
  },
  {
    id: 'L-5102',
    title: 'Kiralık Loft – Şehir Merkezi',
    module: 'real_estate',
    country: 'TR',
    city: 'İstanbul',
    price: '₺38.000',
    status: 'pending_moderation',
    submittedAt: '2026-02-19 10:45',
  },
];

const statusBadge = {
  pending_moderation: 'Beklemede',
};

const AdminModerationDemo = () => {
  const [country, setCountry] = useState('all');
  const [module, setModule] = useState('all');
  const [query, setQuery] = useState('');

  const filteredRows = useMemo(() => {
    return mockRows.filter((row) => {
      const matchCountry = country === 'all' || row.country === country;
      const matchModule = module === 'all' || row.module === module;
      const matchQuery = row.title.toLowerCase().includes(query.toLowerCase());
      return matchCountry && matchModule && matchQuery;
    });
  }, [country, module, query]);

  return (
    <div className="min-h-screen bg-[#f7f4ee]" data-testid="admin-moderation-demo">
      <header className="bg-[#1f2a44] text-white" data-testid="admin-moderation-topbar">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-6 py-4">
          <div className="flex items-center gap-4" data-testid="admin-moderation-topbar-left">
            <div className="flex h-10 w-28 items-center justify-center rounded bg-amber-400 text-sm font-bold text-slate-900" data-testid="admin-moderation-logo">
              ANNONCIA
            </div>
            <div className="text-xs uppercase tracking-[0.2em] text-white/60" data-testid="admin-moderation-title">
              Admin Panel
            </div>
          </div>
          <div className="text-sm" data-testid="admin-moderation-user">
            System Administrator
          </div>
        </div>
      </header>

      <div className="bg-amber-100 text-amber-900" data-testid="admin-moderation-banner">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3 text-sm font-semibold">
          DEMO MODE – DB bağlantısı yok
        </div>
      </div>

      <main className="mx-auto max-w-7xl px-6 py-6" data-testid="admin-moderation-main">
        <div className="grid gap-6 lg:grid-cols-[240px_1fr]">
          <aside className="rounded-2xl bg-white p-4 shadow-sm" data-testid="admin-moderation-sidebar">
            <div className="text-xs uppercase tracking-[0.2em] text-slate-400" data-testid="admin-moderation-sidebar-title">
              Yönetim Menüsü
            </div>
            <div className="mt-4 space-y-1" data-testid="admin-moderation-sidebar-items">
              {['Kontrol Paneli', 'Genel Bakış', 'Kullanıcı Yönetimi', 'Moderation Queue', 'İlan Yönetimi'].map((item) => (
                <div key={item} className={`rounded-xl px-3 py-2 text-sm ${item === 'Moderation Queue' ? 'bg-amber-100 text-[#1f2a44]' : 'text-slate-500'}`} data-testid={`admin-moderation-sidebar-${item}`}>
                  {item}
                </div>
              ))}
            </div>
          </aside>

          <section className="space-y-6 rounded-2xl bg-white p-6 shadow-sm" data-testid="admin-moderation-content">
            <div data-testid="admin-moderation-header">
              <h1 className="text-2xl font-bold" data-testid="admin-moderation-title-main">Moderation Queue</h1>
              <p className="text-sm text-muted-foreground" data-testid="admin-moderation-subtitle">
                İlanlar AB standartlarına göre incelenir. Demo modunda mock veriler gösterilir.
              </p>
            </div>

            <div className="grid gap-3 md:grid-cols-3" data-testid="admin-moderation-filters">
              <input
                className="rounded-md border px-3 py-2 text-sm"
                placeholder="Ara..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                data-testid="admin-moderation-search"
              />
              <select
                className="rounded-md border px-3 py-2 text-sm"
                value={country}
                onChange={(e) => setCountry(e.target.value)}
                data-testid="admin-moderation-country-filter"
              >
                <option value="all">Tüm Ülkeler</option>
                {countries.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
              <select
                className="rounded-md border px-3 py-2 text-sm"
                value={module}
                onChange={(e) => setModule(e.target.value)}
                data-testid="admin-moderation-module-filter"
              >
                <option value="all">Tüm Modüller</option>
                {modules.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </div>

            <div className="overflow-hidden rounded-xl border" data-testid="admin-moderation-table">
              <div className="grid grid-cols-[160px_1.4fr_120px_100px_120px_120px_160px] gap-4 bg-slate-50 px-4 py-3 text-xs font-semibold uppercase text-slate-500" data-testid="admin-moderation-table-head">
                <div>ID</div>
                <div>Başlık</div>
                <div>Modül</div>
                <div>Ülke</div>
                <div>Şehir</div>
                <div>Fiyat</div>
                <div>İşlemler</div>
              </div>
              {filteredRows.map((row) => (
                <div key={row.id} className="grid grid-cols-[160px_1.4fr_120px_100px_120px_120px_160px] gap-4 border-t px-4 py-3 text-sm" data-testid={`admin-moderation-row-${row.id}`}>
                  <div className="font-semibold text-slate-700" data-testid={`admin-moderation-id-${row.id}`}>{row.id}</div>
                  <div data-testid={`admin-moderation-title-${row.id}`}>{row.title}</div>
                  <div className="uppercase" data-testid={`admin-moderation-module-${row.id}`}>{row.module}</div>
                  <div data-testid={`admin-moderation-country-${row.id}`}>{row.country}</div>
                  <div data-testid={`admin-moderation-city-${row.id}`}>{row.city}</div>
                  <div data-testid={`admin-moderation-price-${row.id}`}>{row.price}</div>
                  <div className="flex flex-wrap gap-2" data-testid={`admin-moderation-actions-${row.id}`}>
                    <button className="rounded-md border px-3 py-1 text-xs" data-testid={`admin-moderation-approve-${row.id}`}>Approve</button>
                    <button className="rounded-md border px-3 py-1 text-xs" data-testid={`admin-moderation-reject-${row.id}`}>Reject</button>
                    <button className="rounded-md border px-3 py-1 text-xs" data-testid={`admin-moderation-warning-${row.id}`}>Warning</button>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      </main>
    </div>
  );
};

export default AdminModerationDemo;
