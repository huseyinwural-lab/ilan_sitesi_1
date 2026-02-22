import React, { useMemo, useState } from 'react';
import { useLanguage } from '@/contexts/LanguageContext';

const languageOptions = [
  { key: 'tr', label: 'TR' },
  { key: 'de', label: 'DE' },
  { key: 'fr', label: 'FR' },
];

const PortalDemo = () => {
  const { t, language, setLanguage } = useLanguage();
  const [portalType, setPortalType] = useState('consumer');
  const [activeTopKey, setActiveTopKey] = useState('listings');

  const config = useMemo(() => {
    const consumer = {
      top: [
        { key: 'listings', labelKey: 'nav_listings' },
        { key: 'favorites', labelKey: 'nav_favorites' },
        { key: 'messages', labelKey: 'nav_messages' },
        { key: 'services', labelKey: 'nav_services' },
        { key: 'account', labelKey: 'nav_account' },
      ],
      side: {
        listings: [
          { key: 'overview', labelKey: 'nav_overview' },
          { key: 'my_listings', labelKey: 'nav_my_listings' },
          { key: 'create_listing', labelKey: 'nav_create_listing' },
        ],
        favorites: [
          { key: 'favorite_listings', labelKey: 'nav_favorite_listings' },
          { key: 'favorite_searches', labelKey: 'nav_favorite_searches' },
        ],
        messages: [
          { key: 'inbox', labelKey: 'nav_inbox' },
          { key: 'notifications', labelKey: 'nav_notifications' },
        ],
        services: [
          { key: 'support', labelKey: 'nav_support_center' },
          { key: 'security', labelKey: 'nav_security' },
        ],
        account: [
          { key: 'profile', labelKey: 'nav_profile' },
          { key: 'privacy', labelKey: 'nav_privacy_center' },
          { key: 'data_export', labelKey: 'nav_data_export' },
          { key: 'account_delete', labelKey: 'nav_account_delete' },
          { key: 'permissions', labelKey: 'nav_permissions' },
        ],
      },
      cards: [
        { key: 'active_listings', labelKey: 'card_active_listings', value: '2' },
        { key: 'favorites', labelKey: 'card_favorites', value: '8' },
        { key: 'messages', labelKey: 'card_messages', value: '3' },
      ],
    };

    const dealer = {
      top: [
        { key: 'dashboard', labelKey: 'nav_dealer_dashboard' },
        { key: 'listings', labelKey: 'nav_listings' },
        { key: 'billing', labelKey: 'nav_invoices' },
        { key: 'company', labelKey: 'nav_company' },
        { key: 'privacy', labelKey: 'nav_privacy_center' },
      ],
      side: {
        dashboard: [
          { key: 'overview', labelKey: 'nav_overview' },
          { key: 'plan_quota', labelKey: 'nav_plan_quota' },
        ],
        listings: [
          { key: 'my_listings', labelKey: 'nav_my_listings' },
          { key: 'active_listings', labelKey: 'nav_active_listings' },
          { key: 'draft_listings', labelKey: 'nav_draft_listings' },
          { key: 'archived_listings', labelKey: 'nav_archived_listings' },
        ],
        billing: [
          { key: 'billing_overview', labelKey: 'nav_billing_overview' },
          { key: 'invoice_history', labelKey: 'nav_invoice_history' },
          { key: 'payment_methods', labelKey: 'nav_payment_methods' },
        ],
        company: [
          { key: 'company_profile', labelKey: 'nav_company_profile' },
          { key: 'company_team', labelKey: 'nav_company_team' },
          { key: 'company_branches', labelKey: 'nav_company_branches' },
        ],
        privacy: [
          { key: 'privacy_center', labelKey: 'nav_privacy_center' },
          { key: 'data_export', labelKey: 'nav_data_export' },
          { key: 'account_delete', labelKey: 'nav_account_delete' },
          { key: 'permissions', labelKey: 'nav_permissions' },
        ],
      },
      cards: [
        { key: 'quota', labelKey: 'card_quota', value: '42 / 100' },
        { key: 'messages', labelKey: 'card_messages', value: '12' },
        { key: 'billing', labelKey: 'card_balance', value: '€ 1.250' },
      ],
    };

    return portalType === 'dealer' ? dealer : consumer;
  }, [portalType]);

  const topItems = config.top;
  const sideItems = config.side[activeTopKey] || [];

  const handlePortalSwitch = (value) => {
    setPortalType(value);
    setActiveTopKey(value === 'dealer' ? 'dashboard' : 'listings');
  };

  return (
    <div className="min-h-screen bg-[#f6c27a]" data-testid="portal-demo">
      <header className="bg-[#2f3854] text-white" data-testid="portal-demo-header">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-4">
          <div className="flex items-center gap-4" data-testid="portal-demo-header-left">
            <div
              className="flex h-10 w-28 items-center justify-center rounded bg-yellow-400 text-sm font-bold text-slate-900"
              data-testid="portal-demo-logo"
            >
              ANNONCIA
            </div>
            <div className="text-xs uppercase tracking-[0.2em] text-white/70" data-testid="portal-demo-portal-label">
              {portalType === 'dealer' ? t('portal_dealer') : t('portal_consumer')}
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-3" data-testid="portal-demo-header-right">
            <div className="flex items-center gap-1 rounded-full bg-white/10 px-2 py-1" data-testid="portal-demo-language-toggle">
              {languageOptions.map((option) => (
                <button
                  key={option.key}
                  type="button"
                  onClick={() => setLanguage(option.key)}
                  className={`rounded-full px-2 py-1 text-xs font-semibold transition ${
                    language === option.key ? 'bg-white text-[#2f3854]' : 'text-white/70 hover:text-white'
                  }`}
                  data-testid={`portal-demo-language-${option.key}`}
                >
                  {option.label}
                </button>
              ))}
            </div>
            <div className="text-sm" data-testid="portal-demo-user">
              Hämmermann V.
            </div>
            <button
              type="button"
              className="inline-flex items-center gap-2 rounded-full border border-white/40 px-3 py-1 text-xs uppercase tracking-wide"
              data-testid="portal-demo-login"
            >
              {t('login')}
            </button>
          </div>
        </div>
      </header>

      <div className="bg-white/95" data-testid="portal-demo-toggle">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-3">
          <div className="text-sm font-semibold" data-testid="portal-demo-title">
            {t('portal_demo_title')}
          </div>
          <div className="flex items-center gap-2" data-testid="portal-demo-portal-toggle">
            <button
              type="button"
              onClick={() => handlePortalSwitch('consumer')}
              className={`rounded-full px-4 py-1 text-xs font-semibold ${
                portalType === 'consumer' ? 'bg-[#2f3854] text-white' : 'bg-white text-slate-500 border'
              }`}
              data-testid="portal-demo-consumer-toggle"
            >
              {t('portal_demo_consumer')}
            </button>
            <button
              type="button"
              onClick={() => handlePortalSwitch('dealer')}
              className={`rounded-full px-4 py-1 text-xs font-semibold ${
                portalType === 'dealer' ? 'bg-[#2f3854] text-white' : 'bg-white text-slate-500 border'
              }`}
              data-testid="portal-demo-dealer-toggle"
            >
              {t('portal_demo_dealer')}
            </button>
          </div>
        </div>
      </div>

      <nav className="border-b bg-white/95" data-testid="portal-demo-top-nav">
        <div className="mx-auto max-w-6xl px-6">
          <div className="flex gap-6 overflow-x-auto py-3 text-sm font-semibold">
            {topItems.map((item) => (
              <button
                key={item.key}
                type="button"
                onClick={() => setActiveTopKey(item.key)}
                className={`border-b-2 pb-2 transition ${
                  activeTopKey === item.key
                    ? 'border-[#2f3854] text-[#2f3854]'
                    : 'border-transparent text-slate-500 hover:text-[#2f3854]'
                }`}
                data-testid={`portal-demo-top-${item.key}`}
              >
                {t(item.labelKey)}
              </button>
            ))}
          </div>
        </div>
      </nav>

      <main className="mx-auto max-w-6xl px-6 py-8" data-testid="portal-demo-main">
        <div className="grid gap-6 lg:grid-cols-[240px_1fr]">
          <aside className="rounded-2xl bg-white p-4 shadow-sm" data-testid="portal-demo-side-nav">
            <div className="text-xs uppercase tracking-[0.2em] text-slate-400" data-testid="portal-demo-side-title">
              {t('nav_section')}
            </div>
            <div className="mt-4 space-y-1" data-testid="portal-demo-side-items">
              {sideItems.map((item) => (
                <div
                  key={item.key}
                  className="flex items-center justify-between rounded-xl px-3 py-2 text-sm text-slate-500"
                  data-testid={`portal-demo-side-${item.key}`}
                >
                  <span>{t(item.labelKey)}</span>
                </div>
              ))}
            </div>
          </aside>

          <section className="space-y-6 rounded-2xl bg-white p-6 shadow-sm" data-testid="portal-demo-content">
            <div data-testid="portal-demo-content-header">
              <h1 className="text-2xl font-bold" data-testid="portal-demo-content-title">
                {portalType === 'dealer' ? t('portal_demo_dealer_title') : t('portal_demo_consumer_title')}
              </h1>
              <p className="text-sm text-muted-foreground" data-testid="portal-demo-content-subtitle">
                {t('portal_demo_subtitle')}
              </p>
            </div>

            <div className="grid gap-4 md:grid-cols-3" data-testid="portal-demo-metrics">
              {config.cards.map((card) => (
                <div key={card.key} className="rounded-xl border p-4" data-testid={`portal-demo-card-${card.key}`}>
                  <div className="text-xs uppercase tracking-wide text-slate-500" data-testid={`portal-demo-card-${card.key}-label`}>
                    {t(card.labelKey)}
                  </div>
                  <div className="mt-2 text-2xl font-semibold text-[#2f3854]" data-testid={`portal-demo-card-${card.key}-value`}>
                    {card.value}
                  </div>
                </div>
              ))}
            </div>

            <div className="rounded-xl border border-amber-200 bg-amber-50 p-4" data-testid="portal-demo-gdpr">
              <div className="text-sm font-semibold" data-testid="portal-demo-gdpr-title">
                {t('portal_demo_gdpr_title')}
              </div>
              <p className="text-sm text-slate-600" data-testid="portal-demo-gdpr-text">
                {t('portal_demo_gdpr_text')}
              </p>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
};

export default PortalDemo;
