export const PORTALS = {
  PUBLIC: 'public',
  INDIVIDUAL: 'individual',
  DEALER: 'dealer',
  BACKOFFICE: 'backoffice',
};

export const ROLE_TO_PORTAL = {
  super_admin: PORTALS.BACKOFFICE,
  country_admin: PORTALS.BACKOFFICE,
  moderator: PORTALS.BACKOFFICE,
  finance: PORTALS.BACKOFFICE,
  support: PORTALS.BACKOFFICE,
  ROLE_AUDIT_VIEWER: PORTALS.BACKOFFICE,
  dealer: PORTALS.DEALER,
  individual: PORTALS.INDIVIDUAL,
};

export function defaultHomeForRole(role) {
  if (!role) return '/';
  const p = ROLE_TO_PORTAL[role];
  if (p === PORTALS.BACKOFFICE) return '/admin';
  if (p === PORTALS.DEALER) return '/dealer';
  if (p === PORTALS.INDIVIDUAL) return '/account';
  return '/';
}
