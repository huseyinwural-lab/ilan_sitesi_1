import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { defaultHomeForRole, defaultHomeForScope, ROLE_TO_PORTAL, PORTALS, portalFromScope } from '@/shared/types/portals';

/**
 * PortalGate (pre-layout guard)
 *
 * IMPORTANT: This component must wrap lazy portal imports.
 * If gate fails, it returns a <Navigate> and the lazy import is never evaluated,
 * ensuring "no-chunk-load" acceptance.
 */
export default function PortalGate({ portal, children, loginPath }) {
  const { user, loading } = useAuth();

  if (loading) return <div>Loading...</div>;

  if (!user) {
    return <Navigate to={loginPath} replace />;
  }

  const eligiblePortal = ROLE_TO_PORTAL[user.role];

  // Public portal gate is not used; public routes are always accessible.
  if (portal === PORTALS.BACKOFFICE || portal === PORTALS.DEALER || portal === PORTALS.INDIVIDUAL) {
    if (eligiblePortal !== portal) {
      const target = defaultHomeForRole(user.role);
      return <Navigate to={target} replace state={{ forbidden: true }} />;
    }
  }

  return children;
}
