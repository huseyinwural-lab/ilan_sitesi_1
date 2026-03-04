import { Outlet } from 'react-router-dom';
import SiteHeader from '@/components/public/SiteHeader';
import SiteFooter from '@/components/public/SiteFooter';

export default function MainLayout() {
  return (
    <div className="min-h-screen bg-[var(--bg-page)]" data-testid="public-main-layout">
      <SiteHeader mode="guest" />

      <main className="mx-auto max-w-6xl px-4 py-6" data-testid="public-main-content">
        <Outlet />
      </main>

      <SiteFooter />
    </div>
  );
}
