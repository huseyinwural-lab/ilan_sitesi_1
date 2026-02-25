export const PORTALS = {
  PUBLIC: 'public',
  INDIVIDUAL: 'account',
  DEALER: 'dealer',
  BACKOFFICE: 'admin',
};

export const PORTAL_SCOPES = {
  ADMIN: 'admin',
  DEALER: 'dealer',
  ACCOUNT: 'account',
};

export const ROLE_TO_PORTAL = {
  super_admin: PORTALS.BACKOFFICE,
  country_admin: PORTALS.BACKOFFICE,
  moderator: PORTALS.BACKOFFICE,
  finance: PORTALS.BACKOFFICE,
  support: PORTALS.BACKOFFICE,
  ads_manager: PORTALS.BACKOFFICE,
  pricing_manager: PORTALS.BACKOFFICE,
  masterdata_manager: PORTALS.BACKOFFICE,
  ROLE_AUDIT_VIEWER: PORTALS.BACKOFFICE,
  dealer: PORTALS.DEALER,
  individual: PORTALS.INDIVIDUAL,
};

export function portalFromScope(scope) {
  if (!scope) return PORTALS.PUBLIC;
  if (scope === PORTAL_SCOPES.ADMIN) return PORTALS.BACKOFFICE;
  if (scope === PORTAL_SCOPES.DEALER) return PORTALS.DEALER;
  if (scope === PORTAL_SCOPES.ACCOUNT) return PORTALS.INDIVIDUAL;
  return PORTALS.PUBLIC;
}

export function defaultHomeForRole(role) {
  if (!role) return '/';
  if (role === 'pricing_manager') return '/admin/pricing/tiers';
  if (role === 'ads_manager') return '/admin/ads';
  if (role === 'masterdata_manager') return '/admin/vehicle-master-import';
  const p = ROLE_TO_PORTAL[role];
  if (p === PORTALS.BACKOFFICE) return '/admin';
  if (p === PORTALS.DEALER) return '/dealer';
  if (p === PORTALS.INDIVIDUAL) return '/account';
  return '/';
}

export function defaultHomeForScope(scope) {
  const p = portalFromScope(scope);
  if (p === PORTALS.BACKOFFICE) return '/admin';
  if (p === PORTALS.DEALER) return '/dealer';
  if (p === PORTALS.INDIVIDUAL) return '/account';
  return '/';
}
