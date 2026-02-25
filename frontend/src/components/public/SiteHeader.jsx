import React, { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Bell, Heart, Mail, Search, User, ChevronDown, Menu } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function SiteHeader({ mode, refreshToken }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [logoUrl, setLogoUrl] = useState(null);
  const [searchOpen, setSearchOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [profileOpen, setProfileOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  const isAuthenticated = mode ? mode === 'auth' : Boolean(user);
  const displayName = useMemo(() => {
    if (isAuthenticated) {
      return user?.full_name || user?.email || 'Kullanıcı';
    }
    return '';
  }, [isAuthenticated, user]);

  useEffect(() => {
    let active = true;
    const loadHeader = () => {
      fetch(`${API}/site/header`)
        .then((res) => res.json())
        .then((data) => {
          if (!active) return;
          setLogoUrl(data?.logo_url || null);
        })
        .catch(() => {
          if (!active) return;
          setLogoUrl(null);
        });
    };
    loadHeader();
    const interval = setInterval(loadHeader, 10 * 60 * 1000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [refreshToken]);

  const handleSearch = (evt) => {
    evt.preventDefault();
    const target = query.trim();
    if (!target) return;
    navigate(`/search?q=${encodeURIComponent(target)}`);
    setSearchOpen(false);
  };

  const handleLogout = () => {
    logout();
    setProfileOpen(false);
    navigate('/');
  };

  return (
    <header className="sticky top-0 z-40 border-b bg-[var(--bg-surface)]" data-testid="site-header">
      <div className="mx-auto flex max-w-6xl items-center gap-4 px-4 py-3" data-testid="site-header-container">
        <Link to="/" className="flex items-center gap-2" data-testid="site-header-logo">
          {logoUrl ? (
            <img src={logoUrl} alt="Logo" className="h-8 object-contain" data-testid="site-header-logo-image" />
          ) : (
            <span className="text-lg font-bold text-[var(--text-primary)]" data-testid="site-header-logo-text">ANNONCIA</span>
          )}
        </Link>

        <form
          onSubmit={handleSearch}
          className={`relative flex-1 ${searchOpen ? 'block' : 'hidden'} md:block`}
          data-testid="site-header-search-form"
        >
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Arama yap"
            className="h-10 w-full rounded-full border bg-[var(--bg-surface-muted)] px-4 pr-10 text-sm"
            data-testid="site-header-search-input"
          />
          <button
            type="submit"
            className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-secondary)]"
            data-testid="site-header-search-submit"
          >
            <Search size={18} />
          </button>
        </form>

        <div className="flex items-center gap-2" data-testid="site-header-controls">
          <button
            type="button"
            className="md:hidden rounded-full border p-2"
            onClick={() => setSearchOpen((prev) => !prev)}
            data-testid="site-header-search-toggle"
          >
            <Search size={18} />
          </button>
          <button
            type="button"
            className="md:hidden rounded-full border p-2"
            onClick={() => setMenuOpen((prev) => !prev)}
            data-testid="site-header-menu-toggle"
          >
            <Menu size={18} />
          </button>
        </div>

        <div
          className={`items-center gap-3 ${menuOpen ? 'flex' : 'hidden'} md:flex`}
          data-testid="site-header-actions"
        >
          {!isAuthenticated && (
            <div className="flex items-center gap-2" data-testid="site-header-guest">
              <Link
                to="/login"
                className="text-sm font-semibold text-[#415A77]"
                data-testid="site-header-login"
              >
                Giriş Yap
              </Link>
              <Link
                to="/register"
                className="rounded-full bg-[#F57C00] px-4 py-2 text-sm font-semibold text-white"
                data-testid="site-header-register"
              >
                Üye Ol
              </Link>
            </div>
          )}

          {isAuthenticated && (
            <div className="flex items-center gap-3" data-testid="site-header-auth">
              <button
                type="button"
                onClick={() => navigate('/account/messages')}
                className="relative rounded-full border p-2"
                data-testid="site-header-messages"
              >
                <Mail size={18} />
                <span className="sr-only">Mesajlar</span>
              </button>
              <button
                type="button"
                onClick={() => navigate('/account/notifications')}
                className="relative rounded-full border p-2"
                data-testid="site-header-notifications"
              >
                <Bell size={18} />
                <span className="sr-only">Bildirimler</span>
              </button>
              <button
                type="button"
                onClick={() => navigate('/account/favorites')}
                className="relative rounded-full border p-2"
                data-testid="site-header-favorites"
              >
                <Heart size={18} />
                <span className="sr-only">Favoriler</span>
              </button>

              <div className="relative" data-testid="site-header-profile">
                <button
                  type="button"
                  onClick={() => setProfileOpen((prev) => !prev)}
                  className="flex items-center gap-2 rounded-full border px-3 py-2 text-sm"
                  data-testid="site-header-profile-toggle"
                >
                  <User size={16} />
                  <span>{displayName}</span>
                  <ChevronDown size={14} />
                </button>
                {profileOpen && (
                  <div
                    className="absolute right-0 mt-2 w-48 rounded-md border bg-white shadow-lg"
                    data-testid="site-header-profile-menu"
                  >
                    <button
                      type="button"
                      onClick={() => {
                        navigate('/account');
                        setProfileOpen(false);
                      }}
                      className="block w-full px-4 py-2 text-left text-sm hover:bg-slate-100"
                      data-testid="site-header-profile-dashboard"
                    >
                      Profil
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        navigate('/account/security');
                        setProfileOpen(false);
                      }}
                      className="block w-full px-4 py-2 text-left text-sm hover:bg-slate-100"
                      data-testid="site-header-profile-settings"
                    >
                      Ayarlar
                    </button>
                    <button
                      type="button"
                      onClick={handleLogout}
                      className="block w-full px-4 py-2 text-left text-sm hover:bg-slate-100"
                      data-testid="site-header-profile-logout"
                    >
                      Çıkış
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
