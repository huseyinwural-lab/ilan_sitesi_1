import { useEffect, useMemo, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import axios from 'axios';
import { useCountry } from '@/contexts/CountryContext';
import { useLanguage } from '@/contexts/LanguageContext';
import SiteHeader from '@/components/public/SiteHeader';
import SiteFooter from '@/components/public/SiteFooter';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function getTranslated(obj, lang, fallback = '') {
  if (!obj) return fallback;
  return obj[lang] || obj.tr || obj.de || obj.fr || fallback;
}

export default function PublicLayout({ children }) {
  const { selectedCountry } = useCountry();
  const { language } = useLanguage();
  const [menu, setMenu] = useState([]);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [vehicleOpen, setVehicleOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    setMobileOpen(false);
    setVehicleOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    let mounted = true;
    axios
      .get(`${API}/menu/top-items`)
      .then((res) => {
        if (!mounted) return;
        setMenu(Array.isArray(res.data) ? res.data : []);
      })
      .catch(() => {
        if (!mounted) return;
        setMenu([]);
      });
    return () => {
      mounted = false;
    };
  }, []);

  const items = useMemo(() => {
    const enabled = menu.filter((i) => i?.is_enabled);
    if (enabled.length > 0) return enabled.sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));

    return [
      { key: 'emlak', name: { tr: 'Emlak', de: 'Immobilien', fr: 'Immobilier' }, is_enabled: true, sort_order: 10 },
      { key: 'vasita', name: { tr: 'Vasıta', de: 'Fahrzeuge', fr: 'Véhicules' }, is_enabled: true, sort_order: 20, sections: [] },
    ];
  }, [menu]);

  const countrySlug = (selectedCountry || 'DE').toLowerCase();
  const emlakHref = `/${countrySlug}/emlak`;
  const vasitaHref = `/${countrySlug}/vasita`;

  const vehicleItem = items.find((i) => i.key === 'vasita');
  const vehicleLinks = (vehicleItem?.sections?.[0]?.links || []).map((l) => ({
    id: l.id,
    label: getTranslated(l.label, language),
    href: (l.url || '').replace('{country}', countrySlug),
  }));

  return (
    <div className="min-h-screen bg-[var(--bg-page)]">
      <SiteHeader />

      <nav className="border-b bg-white" data-testid="public-category-nav">
        <div className="mx-auto max-w-6xl px-4 py-2">
          <div className="hidden md:flex items-center gap-6 text-sm">
            <Link to={emlakHref} className="hover:underline" data-testid="public-nav-emlak">
              {getTranslated(items.find((i) => i.key === 'emlak')?.name, language, 'Emlak')}
            </Link>
            <div className="relative group">
              <Link to={vasitaHref} className="hover:underline" data-testid="public-nav-vasita">
                {getTranslated(vehicleItem?.name, language, 'Vasıta')}
              </Link>
              {vehicleLinks.length > 0 && (
                <div className="absolute left-0 top-full pt-2 hidden group-hover:block" data-testid="public-nav-vasita-menu">
                  <div className="w-[520px] rounded-lg border bg-card shadow-lg p-4">
                    <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                      {getTranslated(vehicleItem?.sections?.[0]?.title, language, 'Segmentler')}
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      {vehicleLinks.map((l) => (
                        <Link
                          key={l.id}
                          to={l.href || vasitaHref}
                          className="px-3 py-2 rounded-md hover:bg-muted text-sm"
                          data-testid={`public-nav-vasita-link-${l.id}`}
                        >
                          {l.label}
                        </Link>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
            <button
              type="button"
              className="ml-auto rounded-full border px-3 py-1 text-xs"
              onClick={() => setMobileOpen((v) => !v)}
              data-testid="public-nav-mobile-toggle"
            >
              Menü
            </button>
          </div>

          <div className="md:hidden">
            <button
              type="button"
              className="w-full rounded-md border px-3 py-2 text-sm"
              onClick={() => setMobileOpen((v) => !v)}
              data-testid="public-nav-mobile-toggle"
            >
              Menü
            </button>
            {mobileOpen && (
              <div className="mt-2 space-y-2" data-testid="public-nav-mobile-panel">
                <Link to={emlakHref} className="block px-3 py-2 rounded-md hover:bg-muted text-sm">
                  {getTranslated(items.find((i) => i.key === 'emlak')?.name, language, 'Emlak')}
                </Link>
                <button
                  type="button"
                  className="flex w-full items-center justify-between px-3 py-2 text-sm"
                  onClick={() => setVehicleOpen((v) => !v)}
                  data-testid="public-nav-mobile-vehicle-toggle"
                >
                  {getTranslated(vehicleItem?.name, language, 'Vasıta')}
                  <span className="text-xs">{vehicleOpen ? '−' : '+'}</span>
                </button>
                {vehicleOpen && (
                  <div className="pl-3 space-y-2" data-testid="public-nav-mobile-vehicle-links">
                    {vehicleLinks.map((l) => (
                      <Link key={l.id} to={l.href || vasitaHref} className="block text-sm">
                        {l.label}
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </nav>

      <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>

      <SiteFooter />
    </div>
  );
}
