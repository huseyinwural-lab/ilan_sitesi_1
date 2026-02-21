import React from 'react';
import { useAuth } from '../contexts/AuthContext';

export default function AdminRouteGuard({ roles = [], children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="p-6" data-testid="admin-route-loading">
        Yükleniyor...
      </div>
    );
  }

  if (!user) {
    return (
      <div className="p-6" data-testid="admin-route-forbidden">
        <h1 className="text-xl font-semibold text-slate-900">403</h1>
        <p className="text-sm text-slate-700">Bu sayfayı görüntüleme yetkiniz yok.</p>
      </div>
    );
  }

  if (user.portal_scope && user.portal_scope !== 'admin') {
    return (
      <div className="p-6" data-testid="admin-route-forbidden">
        <h1 className="text-xl font-semibold text-slate-900">403</h1>
        <p className="text-sm text-slate-700">Admin portalına erişim izniniz yok.</p>
      </div>
    );
  }

  if (roles.length && !roles.includes(user.role)) {
    return (
      <div className="p-6" data-testid="admin-route-forbidden">
        <h1 className="text-xl font-semibold text-slate-900">403</h1>
        <p className="text-sm text-slate-700">Bu sayfayı görüntüleme yetkiniz yok.</p>
      </div>
    );
  }

  return children;
}
