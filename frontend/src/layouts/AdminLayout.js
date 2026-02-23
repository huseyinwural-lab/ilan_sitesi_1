import React from 'react';
import { useLocation } from 'react-router-dom';
import Layout from '@/components/Layout';
import AdminRouteGuard from '@/components/AdminRouteGuard';
import { resolveAdminRouteRoles } from '@/shared/adminRbac';

export default function AdminLayout({ children }) {
  const location = useLocation();
  const routeRoles = resolveAdminRouteRoles(location.pathname);
  const enforcedRoles = routeRoles && routeRoles.length ? routeRoles : ['__deny__'];

  return (
    <div data-testid="admin-layout">
      <Layout>
        <AdminRouteGuard roles={enforcedRoles}>{children}</AdminRouteGuard>
      </Layout>
    </div>
  );
}
