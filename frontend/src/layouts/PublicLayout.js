import { useEffect, useMemo, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import axios from 'axios';
import { useCountry } from '@/contexts/CountryContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { Button } from '@/components/ui/button';

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
        // non-blocking: allow static fallback
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

    // fallback (if backend menu not ready)
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
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-40 border-b bg-background/90 backdrop-blur">
        <div className="mx-auto max-w-6xl px-4 h-14 flex items-center justify-between">
          <Link to="/" className="font-semibold">MarketListing</Link>

          <nav className="hidden md:flex items-center gap-6 text-sm">
            <Link to={emlakHref} className="hover:underline">{getTranslated(items.find(i => i.key === 'emlak')?.name, language, 'Emlak')}</Link>

            <div className="relative group">
              <Link to={vasitaHref} className="hover:underline">{getTranslated(vehicleItem?.name, language, 'Vasıta')}</Link>

              {/* Mega menu */}
              {vehicleLinks.length > 0 && (
                <div className="absolute left-0 top-full pt-2 hidden group-hover:block">
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
                        >
                          {l.label}
                        </Link>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </nav>

          <div className="flex items-center gap-2">
            <Button variant="outline" className="hidden sm:inline-flex" asChild>
              <Link to="/admin/login">Admin</Link>
            </Button>
            <Button data-testid="public-mobile-menu" variant="outline" className="md:hidden" onClick={() => setMobileOpen((v) => !v)}>
              Menü
            </Button>
          </div>
        </div>

        {mobileOpen && (
          <div className="md:hidden border-t bg-background">
            <div className="mx-auto max-w-6xl px-4 py-3 space-y-2">
              <Link to={emlakHref} className="block px-3 py-2 rounded-md hover:bg-muted text-sm">
                {getTranslated(items.find(i => i.key === 'emlak')?.name, language, 'Emlak')}
              </Link>

              <button
                className="w-full text-left px-3 py-2 rounded-md hover:bg-muted text-sm flex items-center justify-between"
                onClick={() => setVehicleOpen((v) => !v)}
              >
                <span>{getTranslated(vehicleItem?.name, language, 'Vasıta')}</span>
                <span className="text-muted-foreground">{vehicleOpen ? '−' : '+'}</span>
              </button>

              {vehicleOpen && vehicleLinks.length > 0 && (
                <div className="pl-3 space-y-1">
                  {vehicleLinks.map((l) => (
                    <Link
                      key={l.id}
                      to={l.href || vasitaHref}
                      className="block px-3 py-2 rounded-md hover:bg-muted text-sm text-muted-foreground"
                    >
                      {l.label}
                    </Link>
                  ))}
                </div>
              )}

              <Link to="/admin/login" className="block px-3 py-2 rounded-md hover:bg-muted text-sm">
                Admin
              </Link>
            </div>
          </div>
        )}
      </header>

      <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>

      <footer className="border-t mt-10">
        <div className="mx-auto max-w-6xl px-4 py-6 text-xs text-muted-foreground">
          © {new Date().getFullYear()} MarketListing
        </div>
      </footer>
    </div>
  );
}
