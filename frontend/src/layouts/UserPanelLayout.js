import React from 'react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  Heart,
  MessageSquare,
  LifeBuoy,
  User,
  LogOut,
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

const menuItems = [
  { key: 'dashboard', path: '/account', label: 'Dashboard', icon: LayoutDashboard, testId: 'account-nav-dashboard' },
  { key: 'listings', path: '/account/listings', label: 'İlanlarım', icon: FileText, testId: 'account-nav-listings' },
  { key: 'favorites', path: '/account/favorites', label: 'Favoriler', icon: Heart, testId: 'account-nav-favorites' },
  { key: 'messages', path: '/account/messages', label: 'Mesajlar', icon: MessageSquare, testId: 'account-nav-messages' },
  { key: 'support', path: '/account/support', label: 'Destek', icon: LifeBuoy, testId: 'account-nav-support' },
  { key: 'profile', path: '/account/profile', label: 'Hesap', icon: User, testId: 'account-nav-profile' },
];

const navClass = ({ isActive }) =>
  `flex items-center gap-3 px-4 py-3 rounded-lg text-sm transition ${
    isActive
      ? 'bg-primary/10 text-primary font-semibold'
      : 'text-muted-foreground hover:bg-muted/60 hover:text-foreground'
  }`;

const UserPanelLayout = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-slate-50" data-testid="account-layout">
      <div className="flex">
        <aside className="hidden lg:flex w-72 flex-col border-r bg-white" data-testid="account-sidebar">
          <div className="p-6 border-b" data-testid="account-sidebar-header">
            <div className="text-xs uppercase tracking-wide text-muted-foreground" data-testid="account-sidebar-label">Bireysel Panel</div>
            <div className="text-xl font-bold text-slate-900" data-testid="account-sidebar-title">Hesabım</div>
          </div>
          <div className="p-4" data-testid="account-sidebar-user">
            <div className="rounded-lg border bg-slate-50 p-4">
              <div className="text-xs text-muted-foreground">Giriş yapan</div>
              <div className="font-semibold text-slate-900" data-testid="account-user-name">{user?.full_name || user?.email}</div>
              <div className="text-xs text-muted-foreground" data-testid="account-user-role">{user?.role || 'individual'}</div>
            </div>
          </div>
          <nav className="flex-1 px-4 space-y-1" data-testid="account-sidebar-nav">
            {menuItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink key={item.key} to={item.path} className={navClass} data-testid={item.testId}>
                  <Icon size={18} />
                  <span data-testid={`${item.testId}-label`}>{item.label}</span>
                </NavLink>
              );
            })}
          </nav>
          <div className="p-4 border-t" data-testid="account-sidebar-footer">
            <button
              type="button"
              onClick={handleLogout}
              className="flex w-full items-center justify-center gap-2 rounded-md border px-3 py-2 text-sm"
              data-testid="account-logout"
            >
              <LogOut size={16} /> Çıkış
            </button>
          </div>
        </aside>

        <main className="flex-1 min-w-0" data-testid="account-main">
          <header className="sticky top-0 z-10 border-b bg-white/90 backdrop-blur" data-testid="account-topbar">
            <div className="flex items-center justify-between px-6 py-4">
              <div>
                <div className="text-xs uppercase tracking-wide text-muted-foreground">Bireysel Portal</div>
                <div className="text-lg font-semibold" data-testid="account-topbar-title">{menuItems.find((item) => location.pathname === item.path)?.label || 'Dashboard'}</div>
              </div>
              <button
                type="button"
                onClick={handleLogout}
                className="lg:hidden inline-flex items-center gap-2 rounded-md border px-3 py-2 text-xs"
                data-testid="account-mobile-logout"
              >
                <LogOut size={14} /> Çıkış
              </button>
            </div>
          </header>
          <div className="p-6" data-testid="account-content">
            <Outlet />
          </div>
        </main>
      </div>

      <nav className="lg:hidden fixed bottom-0 left-0 right-0 border-t bg-white" data-testid="account-mobile-nav">
        <div className="grid grid-cols-5">
          {menuItems.slice(0, 5).map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <NavLink
                key={item.key}
                to={item.path}
                className={`flex flex-col items-center gap-1 py-2 text-xs ${
                  isActive ? 'text-primary' : 'text-muted-foreground'
                }`}
                data-testid={`${item.testId}-mobile`}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </div>
      </nav>
    </div>
  );
};

export default UserPanelLayout;
