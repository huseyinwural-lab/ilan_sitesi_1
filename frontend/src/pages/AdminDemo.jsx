import React, { useState } from 'react';

const languageOptions = ['TR', 'DE', 'FR'];

const steps = [
  { id: 1, label: 'Kategori Seçimi' },
  { id: 2, label: 'İlan Detayları' },
  { id: 3, label: 'Gizleme' },
  { id: 4, label: 'Doping' },
  { id: 5, label: 'Tebrikler' },
];

const sidebarItems = [
  { key: 'dashboard', label: 'Genel Bakış' },
  { key: 'moderation', label: 'Moderasyon' },
  { key: 'listings', label: 'İlan Yönetimi' },
  { key: 'users', label: 'Kullanıcılar' },
  { key: 'billing', label: 'Faturalandırma' },
  { key: 'settings', label: 'Ayarlar' },
];

const AdminDemo = () => {
  const [language, setLanguage] = useState('TR');
  const [activeSidebar, setActiveSidebar] = useState('moderation');

  return (
    <div className="min-h-screen bg-[#f7f4ee]" data-testid="admin-demo">
      <header className="bg-[#1f2a44] text-white" data-testid="admin-demo-topbar">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-6 py-4">
          <div className="flex items-center gap-4" data-testid="admin-demo-topbar-left">
            <div
              className="flex h-10 w-28 items-center justify-center rounded bg-amber-400 text-sm font-bold text-slate-900"
              data-testid="admin-demo-logo"
            >
              ANNONCIA
            </div>
            <div className="text-xs uppercase tracking-[0.2em] text-white/60" data-testid="admin-demo-title">
              Admin Panel Demo
            </div>
          </div>
          <div className="flex items-center gap-3" data-testid="admin-demo-topbar-right">
            <div className="flex items-center gap-1 rounded-full bg-white/10 px-2 py-1" data-testid="admin-demo-language-toggle">
              {languageOptions.map((option) => (
                <button
                  key={option}
                  type="button"
                  onClick={() => setLanguage(option)}
                  className={`rounded-full px-2 py-1 text-xs font-semibold transition ${
                    language === option ? 'bg-white text-[#1f2a44]' : 'text-white/70 hover:text-white'
                  }`}
                  data-testid={`admin-demo-language-${option.toLowerCase()}`}
                >
                  {option}
                </button>
              ))}
            </div>
            <div className="text-sm" data-testid="admin-demo-user">Admin Görünümü</div>
            <button
              type="button"
              className="rounded-full border border-white/40 px-3 py-1 text-xs uppercase tracking-wide"
              data-testid="admin-demo-login"
            >
              Giriş
            </button>
          </div>
        </div>
      </header>

      <div className="border-b bg-white" data-testid="admin-demo-steps">
        <div className="mx-auto max-w-7xl px-6 py-4">
          <div className="flex flex-wrap items-center gap-4">
            {steps.map((step) => (
              <div key={step.id} className="flex items-center gap-2" data-testid={`admin-demo-step-${step.id}`}>
                <div
                  className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-semibold ${
                    step.id === 2 ? 'bg-[#1f2a44] text-white' : 'bg-slate-200 text-slate-600'
                  }`}
                  data-testid={`admin-demo-step-${step.id}-indicator`}
                >
                  {step.id}
                </div>
                <span className="text-sm font-medium text-slate-700" data-testid={`admin-demo-step-${step.id}-label`}>
                  {step.label}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <main className="mx-auto max-w-7xl px-6 py-6" data-testid="admin-demo-main">
        <div className="grid gap-6 lg:grid-cols-[260px_1fr]">
          <aside className="rounded-2xl bg-white p-4 shadow-sm" data-testid="admin-demo-sidebar">
            <div className="text-xs uppercase tracking-[0.2em] text-slate-400" data-testid="admin-demo-sidebar-title">
              Yönetim Menüsü
            </div>
            <div className="mt-4 space-y-1" data-testid="admin-demo-sidebar-items">
              {sidebarItems.map((item) => (
                <button
                  key={item.key}
                  type="button"
                  onClick={() => setActiveSidebar(item.key)}
                  className={`flex w-full items-center justify-between rounded-xl px-3 py-2 text-sm transition ${
                    activeSidebar === item.key
                      ? 'bg-amber-100 text-[#1f2a44]'
                      : 'text-slate-500 hover:bg-slate-100'
                  }`}
                  data-testid={`admin-demo-sidebar-${item.key}`}
                >
                  <span>{item.label}</span>
                  {item.key === 'moderation' && (
                    <span className="rounded-full bg-[#1f2a44] px-2 py-0.5 text-xs text-white" data-testid="admin-demo-sidebar-moderation-badge">
                      18
                    </span>
                  )}
                </button>
              ))}
            </div>
          </aside>

          <section className="space-y-6 rounded-2xl bg-white p-6 shadow-sm" data-testid="admin-demo-content">
            <div className="flex flex-wrap items-center justify-between gap-4" data-testid="admin-demo-header">
              <div>
                <h1 className="text-2xl font-bold" data-testid="admin-demo-header-title">
                  İlan Moderasyon İncelemesi
                </h1>
                <p className="text-sm text-muted-foreground" data-testid="admin-demo-header-subtitle">
                  Kategori ve ilan detaylarını AB standartlarına göre kontrol edin.
                </p>
              </div>
              <div className="flex items-center gap-2" data-testid="admin-demo-header-actions">
                <button className="rounded-full border px-4 py-2 text-xs" data-testid="admin-demo-header-draft">Taslak</button>
                <button className="rounded-full bg-[#1f2a44] px-4 py-2 text-xs text-white" data-testid="admin-demo-header-approve">
                  Onayla
                </button>
              </div>
            </div>

            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4" data-testid="admin-demo-breadcrumb">
              <div className="text-xs uppercase text-slate-500" data-testid="admin-demo-breadcrumb-title">Kategori Seçimi</div>
              <div className="mt-2 text-sm font-semibold text-slate-700" data-testid="admin-demo-breadcrumb-value">
                Emlak \ Konut \ Satılık \ Daire
              </div>
            </div>

            <div className="grid gap-4 lg:grid-cols-2" data-testid="admin-demo-core-fields">
              <div className="space-y-2" data-testid="admin-demo-title-field">
                <label className="text-sm font-medium">İlan Başlığı *</label>
                <input
                  className="w-full rounded-md border px-3 py-2 text-sm"
                  value="Merkezde 3+1 Balkonlu Daire"
                  readOnly
                  data-testid="admin-demo-title-input"
                />
              </div>
              <div className="space-y-2" data-testid="admin-demo-price-field">
                <label className="text-sm font-medium">Fiyat *</label>
                <input
                  className="w-full rounded-md border px-3 py-2 text-sm"
                  value="€ 245.000"
                  readOnly
                  data-testid="admin-demo-price-input"
                />
              </div>
              <div className="space-y-2 lg:col-span-2" data-testid="admin-demo-description-field">
                <label className="text-sm font-medium">Açıklama *</label>
                <textarea
                  className="w-full rounded-md border px-3 py-2 text-sm"
                  rows={4}
                  readOnly
                  data-testid="admin-demo-description"
                  value="Toplu ulaşıma 5 dk, yenilenmiş mutfak ve balkonlu."
                />
              </div>
            </div>

            <div className="grid gap-4 lg:grid-cols-3" data-testid="admin-demo-property-fields">
              {[
                { label: 'Brüt m²', value: '145' },
                { label: 'Net m²', value: '120' },
                { label: 'Oda Sayısı', value: '3+1' },
                { label: 'Bina Yaşı', value: '8' },
                { label: 'Bulunduğu Kat', value: '5' },
                { label: 'Isıtma', value: 'Kombi' },
              ].map((item, idx) => (
                <div key={item.label} className="space-y-2" data-testid={`admin-demo-property-${idx}`}>
                  <label className="text-sm font-medium">{item.label}</label>
                  <input className="w-full rounded-md border px-3 py-2 text-sm" value={item.value} readOnly data-testid={`admin-demo-property-${idx}-input`} />
                </div>
              ))}
            </div>

            <div className="rounded-xl border p-4" data-testid="admin-demo-address">
              <h2 className="text-lg font-semibold" data-testid="admin-demo-address-title">Adres Bilgileri</h2>
              <div className="mt-3 grid gap-4 md:grid-cols-3">
                {[
                  { label: 'İl', value: 'Berlin' },
                  { label: 'İlçe', value: 'Mitte' },
                  { label: 'Mahalle', value: 'Tiergarten' },
                ].map((item, idx) => (
                  <div key={item.label} className="space-y-2" data-testid={`admin-demo-address-${idx}`}>
                    <label className="text-sm font-medium">{item.label}</label>
                    <input className="w-full rounded-md border px-3 py-2 text-sm" value={item.value} readOnly data-testid={`admin-demo-address-${idx}-input`} />
                  </div>
                ))}
              </div>
            </div>

            <div className="grid gap-4 lg:grid-cols-2" data-testid="admin-demo-feature-groups">
              {[
                {
                  title: 'İç Özellikler',
                  items: ['Klima', 'Giyinme Odası', 'Çelik Kapı', 'Fiber İnternet'],
                },
                {
                  title: 'Dış Özellikler',
                  items: ['24 Saat Güvenlik', 'Kapalı Otopark', 'Spor Alanı', 'Asansör'],
                },
              ].map((group, idx) => (
                <div key={group.title} className="rounded-xl border p-4" data-testid={`admin-demo-feature-${idx}`}>
                  <h3 className="font-semibold" data-testid={`admin-demo-feature-${idx}-title`}>{group.title}</h3>
                  <div className="mt-3 grid grid-cols-2 gap-2">
                    {group.items.map((item) => (
                      <label key={item} className="flex items-center gap-2 text-sm" data-testid={`admin-demo-feature-${idx}-${item}`}>
                        <input type="checkbox" checked readOnly />
                        {item}
                      </label>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <div className="grid gap-4 lg:grid-cols-2" data-testid="admin-demo-media">
              <div className="rounded-xl border border-dashed p-4" data-testid="admin-demo-photos">
                <h3 className="font-semibold" data-testid="admin-demo-photos-title">Fotoğraflar</h3>
                <p className="text-sm text-muted-foreground" data-testid="admin-demo-photos-subtitle">12 fotoğraf yüklendi</p>
              </div>
              <div className="rounded-xl border border-dashed p-4" data-testid="admin-demo-video">
                <h3 className="font-semibold" data-testid="admin-demo-video-title">Video</h3>
                <p className="text-sm text-muted-foreground" data-testid="admin-demo-video-subtitle">1 video beklemede</p>
              </div>
            </div>

            <div className="rounded-xl border p-4" data-testid="admin-demo-contact">
              <h3 className="font-semibold" data-testid="admin-demo-contact-title">İletişim Bilgileri</h3>
              <div className="mt-3 grid gap-4 md:grid-cols-2">
                <div className="space-y-2" data-testid="admin-demo-contact-name">
                  <label className="text-sm font-medium">İlanda Görünen Ad Soyad</label>
                  <input className="w-full rounded-md border px-3 py-2 text-sm" value="Helena Müller" readOnly />
                </div>
                <div className="space-y-2" data-testid="admin-demo-contact-phone">
                  <label className="text-sm font-medium">Telefon</label>
                  <input className="w-full rounded-md border px-3 py-2 text-sm" value="+49 176 000 00 00" readOnly />
                </div>
              </div>
            </div>

            <div className="rounded-xl border p-4" data-testid="admin-demo-offers">
              <h3 className="font-semibold" data-testid="admin-demo-offers-title">İlan Süresi</h3>
              <div className="mt-4 grid gap-4 md:grid-cols-3">
                {[
                  { label: '1 Aylık', price: '€ 49', value: '1 ay' },
                  { label: '2 Aylık', price: '€ 79', value: '2 ay' },
                  { label: '3 Aylık', price: '€ 99', value: '3 ay' },
                ].map((item, idx) => (
                  <div key={item.label} className="rounded-xl border p-4" data-testid={`admin-demo-offer-${idx}`}>
                    <div className="text-sm font-semibold" data-testid={`admin-demo-offer-${idx}-label`}>{item.label}</div>
                    <div className="mt-2 text-2xl font-bold text-[#1f2a44]" data-testid={`admin-demo-offer-${idx}-price`}>{item.price}</div>
                    <div className="text-xs text-muted-foreground" data-testid={`admin-demo-offer-${idx}-value`}>{item.value}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-xl border border-amber-200 bg-amber-50 p-4" data-testid="admin-demo-gdpr">
              <div className="text-sm font-semibold" data-testid="admin-demo-gdpr-title">GDPR Kontrolü</div>
              <p className="text-sm text-slate-600" data-testid="admin-demo-gdpr-text">
                Kişisel veriler ve iletişim bilgileri yalnızca onaylı moderatörler tarafından görüntülenir.
              </p>
            </div>

            <div className="flex flex-wrap items-center justify-end gap-3" data-testid="admin-demo-actions">
              <button className="rounded-md border px-4 py-2 text-sm" data-testid="admin-demo-save">Taslak Kaydet</button>
              <button className="rounded-md bg-[#1f2a44] px-4 py-2 text-sm text-white" data-testid="admin-demo-next">Devam</button>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
};

export default AdminDemo;
