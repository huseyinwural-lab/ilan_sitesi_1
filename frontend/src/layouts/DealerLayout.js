import React from 'react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { LayoutDashboard, FileText, LogOut, ListChecks } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

const menuItems = [
  { key: 'dashboard', path: '/dealer', label: 'Dashboard', icon: LayoutDashboard, testId: 'dealer-nav-dashboard' },
  { key: 'invoices', path: '/dealer/invoices', label: 'Faturalar', icon: FileText, testId: 'dealer-nav-invoices' },
];

const navClass = ({ isActive }) =>
  `flex items-center gap-3 px-4 py-3 rounded-lg text-sm transition ${
    isActive
      ? 'bg-slate-900 text-white font-semibold'
      : 'text-muted-foreground hover:bg-muted/60 hover:text-foreground'
  }`;

export default function DealerLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate('/dealer/login');
  };

  return (
    <div className="min-h-screen bg-slate-50" data-testid="dealer-layout">
      <div className="flex">
        <aside className="hidden lg:flex w-72 flex-col border-r bg-white" data-testid="dealer-sidebar">
          <div className="p-6 border-b" data-testid="dealer-sidebar-header">
            <div className="text-xs uppercase tracking-wide text-muted-foreground">Kurumsal Panel</div>
            <div className="text-xl font-bold text-slate-900" data-testid="dealer-sidebar-title">Dealer</div>
          </div>
          <div className="p-4" data-testid="dealer-sidebar-user">
            <div className="rounded-lg border bg-slate-50 p-4">
              <div className="text-xs text-muted-foreground">Giriş yapan</div>
              <div className="font-semibold text-slate-900" data-testid="dealer-user-name">{user?.full_name || user?.email}</div>
              <div className="text-xs text-muted-foreground" data-testid="dealer-user-role">{user?.role || 'dealer'}</div>
            </div>
          </div>
          <nav className="flex-1 px-4 space-y-1" data-testid="dealer-sidebar-nav">
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
          <div className="p-4 border-t" data-testid="dealer-sidebar-footer">
            <button
              type="button"
              onClick={handleLogout}
              className="flex w-full items-center justify-center gap-2 rounded-md border px-3 py-2 text-sm"
              data-testid="dealer-logout"
            >
              <LogOut size={16} /> Çıkış
            </button>
          </div>
        </aside>

        <main className="flex-1 min-w-0" data-testid="dealer-main">
          <header className="sticky top-0 z-10 border-b bg-white/90 backdrop-blur" data-testid="dealer-topbar">
            <div className="flex items-center justify-between px-6 py-4">
              <div>
                <div className="text-xs uppercase tracking-wide text-muted-foreground">Kurumsal Portal</div>
                <div className="text-lg font-semibold" data-testid="dealer-topbar-title">
                  {menuItems.find((item) => location.pathname === item.path || location.pathname.startsWith(`${item.path}/`))?.label || 'Dashboard'}
                </div>
              </div>
              <button
                type="button"
                onClick={handleLogout}
                className="lg:hidden inline-flex items-center gap-2 rounded-md border px-3 py-2 text-xs"
                data-testid="dealer-mobile-logout"
              >
                <LogOut size={14} /> Çıkış
              </button>
            </div>
          </header>
          <div className="p-6" data-testid="dealer-content">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
