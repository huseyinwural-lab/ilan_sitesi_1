import { Outlet } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import SiteHeader from '@/components/public/SiteHeader';
import SiteFooter from '@/components/public/SiteFooter';

export default function MainLayout() {
  const { user, loading } = useAuth();

  const headerMode = loading ? 'guest' : (user ? 'auth' : 'guest');

  return (
    <div className="min-h-screen bg-[var(--bg-page)]" data-testid="public-main-layout">
      <SiteHeader mode={headerMode} />

      <main className="mx-auto max-w-6xl px-4 py-6" data-testid="public-main-content">
        <Outlet />
      </main>

      <SiteFooter />
    </div>
  );
}
