import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { useAuth } from '@/contexts/AuthContext';
import { AdminEmptyState, AdminErrorState, AdminLoadingState } from '@/components/admin/standard/AdminStateBlocks';
import { AdminStatusBadge } from '@/components/admin/standard/AdminStatusBadge';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const ROLE_OPTIONS = [
  'all',
  'super_admin',
  'country_admin',
  'admin',
  'finance',
  'dealer',
  'user',
  'support',
  'moderator',
];

const cellKey = (userId, domain, action) => `${userId}:${domain}:${action}`;

export default function AdminPermissionsPage() {
  const { user: currentUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const [users, setUsers] = useState([]);
  const [overrides, setOverrides] = useState([]);
  const [countries, setCountries] = useState([]);
  const [flags, setFlags] = useState({
    domains: {
      finance: ['view', 'edit', 'publish', 'export', 'delete'],
      content: ['view', 'edit', 'publish', 'export', 'delete'],
    },
    fallback_matrix: {},
  });
  const [shadowDiff, setShadowDiff] = useState({ diff_count: 0, checked_user_count: 0, diffs: [] });

  const [filters, setFilters] = useState({
    user: '',
    role: 'all',
    country_scope: 'all',
  });

  const [selectedUserId, setSelectedUserId] = useState('');
  const [draft, setDraft] = useState(null);
  const [draftReason, setDraftReason] = useState('');
  const [draftScope, setDraftScope] = useState([]);
  const [draftGlobalScope, setDraftGlobalScope] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const authHeader = useMemo(
    () => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` }),
    [],
  );

  const queryParams = useMemo(() => {
    const params = new URLSearchParams();
    if (filters.user.trim()) params.set('user', filters.user.trim());
    if (filters.role !== 'all') params.set('role', filters.role);
    if (filters.country_scope !== 'all') params.set('country_scope', filters.country_scope);
    return params.toString();
  }, [filters]);

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      const [usersRes, overridesRes, flagsRes, shadowRes, countriesRes] = await Promise.all([
        axios.get(`${API}/admin/permissions/users?${queryParams}`, { headers: authHeader }),
        axios.get(`${API}/admin/permissions/overrides?${queryParams}`, { headers: authHeader }),
        axios.get(`${API}/admin/permissions/flags`, { headers: authHeader }),
        axios.get(`${API}/admin/permissions/shadow-diff?${queryParams}`, { headers: authHeader }),
        axios.get(`${API}/countries`, { headers: authHeader }),
      ]);

      setUsers(usersRes.data?.items || []);
      setOverrides(overridesRes.data?.items || []);
      setFlags(flagsRes.data || {});
      setShadowDiff(shadowRes.data || { diff_count: 0, checked_user_count: 0, diffs: [] });
      setCountries(countriesRes.data || []);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Permission verileri yüklenemedi.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [queryParams]);

  useEffect(() => {
    if (!users.length) {
      setSelectedUserId('');
      return;
    }
    if (!selectedUserId || !users.some((item) => item.id === selectedUserId)) {
      setSelectedUserId(users[0].id);
    }
  }, [users, selectedUserId]);

  const selectedUser = useMemo(
    () => users.find((item) => item.id === selectedUserId) || null,
    [users, selectedUserId],
  );

  const overrideMap = useMemo(() => {
    const map = new Map();
    (overrides || []).forEach((item) => {
      const userId = item?.user?.id;
      const domain = item?.override?.domain;
      const action = item?.override?.action;
      if (!userId || !domain || !action) return;
      map.set(cellKey(userId, domain, action), item);
    });
    return map;
  }, [overrides]);

  const fallbackAllowed = (role, domain, action) => {
    const matrix = flags?.fallback_matrix || {};
    const allowedRoles = matrix?.[domain]?.[action] || [];
    return allowedRoles.includes(role);
  };

  const openDraft = (mode, domain, action) => {
    if (!selectedUser) return;
    const existing = overrideMap.get(cellKey(selectedUser.id, domain, action));
    const existingScope = existing?.override?.country_scope || [];

    setDraft({ mode, domain, action });
    setDraftReason('');
    setDraftScope(existingScope.filter((code) => code !== '*'));
    setDraftGlobalScope(existingScope.length === 0 || existingScope.includes('*'));
    setNotice('');
    setError('');
  };

  const closeDraft = () => {
    setDraft(null);
    setDraftReason('');
    setDraftScope([]);
    setDraftGlobalScope(true);
  };

  const toggleScopeCode = (countryCode) => {
    setDraftScope((prev) => {
      if (prev.includes(countryCode)) {
        return prev.filter((item) => item !== countryCode);
      }
      return [...prev, countryCode];
    });
  };

  const submitDraft = async () => {
    if (!selectedUser || !draft) return;
    const reason = draftReason.trim();
    if (reason.length < 10) {
      setError('Reason en az 10 karakter olmalıdır.');
      return;
    }

    setSubmitting(true);
    setError('');
    setNotice('');
    try {
      if (draft.mode === 'grant') {
        await axios.post(
          `${API}/admin/permissions/grant`,
          {
            target_user_id: selectedUser.id,
            domain: draft.domain,
            action: draft.action,
            country_scope: draftGlobalScope ? [] : draftScope,
            reason,
          },
          { headers: authHeader },
        );
        setNotice('Grant/override işlemi kaydedildi.');
      } else {
        await axios.post(
          `${API}/admin/permissions/revoke`,
          {
            target_user_id: selectedUser.id,
            domain: draft.domain,
            action: draft.action,
            reason,
          },
          { headers: authHeader },
        );
        setNotice('Revoke işlemi tamamlandı. Kullanıcı role fallback ile değerlendirilecek.');
      }
      closeDraft();
      await loadData();
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'İşlem tamamlanamadı.');
    } finally {
      setSubmitting(false);
    }
  };

  const renderCell = (domain, action) => {
    if (!selectedUser) return null;
    const key = cellKey(selectedUser.id, domain, action);
    const overrideItem = overrideMap.get(key);
    const inherited = fallbackAllowed(selectedUser.role, domain, action);
    const explicit = Boolean(overrideItem);
    const effective = explicit
      ? Boolean(overrideItem?.effective_when_flag_on)
      : inherited;

    const isSelf = String(selectedUser.id) === String(currentUser?.id || '');
    const targetIsSuperAdmin = selectedUser.role === 'super_admin';

    return (
      <tr key={`${domain}-${action}`} className="border-t" data-testid={`permission-matrix-row-${domain}-${action}`}>
        <td className="px-3 py-2" data-testid={`permission-matrix-domain-${domain}-${action}`}>{domain}</td>
        <td className="px-3 py-2" data-testid={`permission-matrix-action-${domain}-${action}`}>{action}</td>
        <td className="px-3 py-2" data-testid={`permission-matrix-inherit-${domain}-${action}`}>
          <div className="flex items-center gap-2">
            <AdminStatusBadge
              label={inherited ? 'ALLOW' : 'DENY'}
              variant={inherited ? 'success' : 'danger'}
              testId={`permission-matrix-inherit-badge-${domain}-${action}`}
            />
            <span className="text-xs text-slate-500" data-testid={`permission-matrix-inherit-text-${domain}-${action}`}>
              inherit from role
            </span>
          </div>
        </td>
        <td className="px-3 py-2" data-testid={`permission-matrix-explicit-${domain}-${action}`}>
          {explicit ? (
            <div className="space-y-1" data-testid={`permission-matrix-explicit-wrap-${domain}-${action}`}>
              <AdminStatusBadge label="EXPLICIT OVERRIDE" variant="info" testId={`permission-matrix-explicit-badge-${domain}-${action}`} />
              <div className="text-xs text-slate-600" data-testid={`permission-matrix-explicit-scope-${domain}-${action}`}>
                Scope: {(overrideItem?.override?.country_scope || []).join(', ') || 'GLOBAL (*)'}
              </div>
            </div>
          ) : (
            <span className="text-xs text-slate-500" data-testid={`permission-matrix-explicit-none-${domain}-${action}`}>Override yok</span>
          )}
        </td>
        <td className="px-3 py-2" data-testid={`permission-matrix-effective-${domain}-${action}`}>
          <AdminStatusBadge
            label={effective ? 'ALLOW' : 'DENY'}
            variant={effective ? 'success' : 'danger'}
            testId={`permission-matrix-effective-badge-${domain}-${action}`}
          />
        </td>
        <td className="px-3 py-2 text-right" data-testid={`permission-matrix-actions-${domain}-${action}`}>
          <div className="inline-flex items-center gap-2">
            <button
              type="button"
              className="h-8 rounded-md border px-2 text-xs"
              onClick={() => openDraft('grant', domain, action)}
              data-testid={`permission-matrix-grant-${domain}-${action}`}
            >
              {explicit ? 'Güncelle Grant' : 'Grant'}
            </button>
            <button
              type="button"
              className="h-8 rounded-md border px-2 text-xs disabled:cursor-not-allowed disabled:opacity-50"
              onClick={() => openDraft('revoke', domain, action)}
              disabled={!explicit || isSelf || targetIsSuperAdmin}
              data-testid={`permission-matrix-revoke-${domain}-${action}`}
            >
              Revoke
            </button>
          </div>
        </td>
      </tr>
    );
  };

  return (
    <div className="space-y-5" data-testid="admin-permissions-page">
      <div className="flex flex-wrap items-start justify-between gap-3" data-testid="admin-permissions-header">
        <div>
          <h1 className="text-2xl font-semibold" data-testid="admin-permissions-title">Granular Permission Yönetimi</h1>
          <p className="text-sm text-slate-600" data-testid="admin-permissions-subtitle">
            Default deny + role inheritance görünür, explicit override işlemleri audit reason ile zorunlu tutulur.
          </p>
        </div>
        <div className="rounded-md border bg-white px-3 py-2" data-testid="admin-permissions-shadow-diff-card">
          <div className="text-xs text-slate-500">Shadow Diff</div>
          <div className="mt-1 flex items-center gap-2">
            <AdminStatusBadge
              label={`diff_count=${Number(shadowDiff?.diff_count || 0)}`}
              variant={Number(shadowDiff?.diff_count || 0) === 0 ? 'success' : 'warning'}
              testId="admin-permissions-shadow-diff-badge"
            />
            <span className="text-xs text-slate-600" data-testid="admin-permissions-shadow-diff-users">
              checked users: {Number(shadowDiff?.checked_user_count || 0)}
            </span>
          </div>
        </div>
      </div>

      <div className="rounded-lg border bg-white p-4" data-testid="admin-permissions-filters-card">
        <div className="grid gap-3 md:grid-cols-4" data-testid="admin-permissions-filters-grid">
          <input
            type="text"
            value={filters.user}
            onChange={(event) => setFilters((prev) => ({ ...prev, user: event.target.value }))}
            placeholder="User email veya ad"
            className="h-9 rounded-md border px-3 text-sm"
            data-testid="admin-permissions-filter-user"
          />
          <select
            value={filters.role}
            onChange={(event) => setFilters((prev) => ({ ...prev, role: event.target.value }))}
            className="h-9 rounded-md border px-3 text-sm"
            data-testid="admin-permissions-filter-role"
          >
            {ROLE_OPTIONS.map((role) => (
              <option key={role} value={role} data-testid={`admin-permissions-filter-role-option-${role}`}>
                {role}
              </option>
            ))}
          </select>
          <select
            value={filters.country_scope}
            onChange={(event) => setFilters((prev) => ({ ...prev, country_scope: event.target.value }))}
            className="h-9 rounded-md border px-3 text-sm"
            data-testid="admin-permissions-filter-country"
          >
            <option value="all" data-testid="admin-permissions-filter-country-option-all">all</option>
            {countries.map((country) => (
              <option key={country.code} value={country.code} data-testid={`admin-permissions-filter-country-option-${country.code}`}>
                {country.code}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={loadData}
            className="h-9 rounded-md border px-3 text-sm"
            data-testid="admin-permissions-filter-refresh"
          >
            Yenile
          </button>
        </div>
      </div>

      {notice ? (
        <div className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700" data-testid="admin-permissions-notice">
          {notice}
        </div>
      ) : null}

      {error ? <AdminErrorState message={error} testId="admin-permissions-error" /> : null}
      {loading ? <AdminLoadingState message="Permission verileri yükleniyor..." testId="admin-permissions-loading" /> : null}

      {!loading && !error && users.length === 0 ? (
        <AdminEmptyState message="Filtreye uygun kullanıcı bulunamadı." testId="admin-permissions-users-empty" />
      ) : null}

      {!loading && users.length > 0 ? (
        <div className="grid gap-4 lg:grid-cols-2" data-testid="admin-permissions-content-grid">
          <div className="rounded-lg border bg-white p-4" data-testid="admin-permissions-explicit-list-card">
            <div className="flex items-center justify-between" data-testid="admin-permissions-explicit-list-header">
              <h2 className="text-base font-semibold" data-testid="admin-permissions-explicit-list-title">Explicit Override Listesi</h2>
              <span className="text-xs text-slate-500" data-testid="admin-permissions-explicit-list-count">
                count: {overrides.length}
              </span>
            </div>
            <div className="mt-3 max-h-[420px] overflow-auto" data-testid="admin-permissions-explicit-list-wrap">
              {overrides.length === 0 ? (
                <AdminEmptyState message="Override kaydı yok. Tüm kararlar role inheritance ile çalışıyor." testId="admin-permissions-explicit-list-empty" />
              ) : (
                <table className="w-full text-xs" data-testid="admin-permissions-explicit-table">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="px-2 py-2 text-left">User</th>
                      <th className="px-2 py-2 text-left">Role</th>
                      <th className="px-2 py-2 text-left">Domain</th>
                      <th className="px-2 py-2 text-left">Action</th>
                      <th className="px-2 py-2 text-left">Scope</th>
                    </tr>
                  </thead>
                  <tbody>
                    {overrides.map((item) => (
                      <tr key={item.override.id} className="border-t" data-testid={`admin-permissions-explicit-row-${item.override.id}`}>
                        <td className="px-2 py-2" data-testid={`admin-permissions-explicit-user-${item.override.id}`}>{item.user.email}</td>
                        <td className="px-2 py-2" data-testid={`admin-permissions-explicit-role-${item.override.id}`}>{item.user.role}</td>
                        <td className="px-2 py-2" data-testid={`admin-permissions-explicit-domain-${item.override.id}`}>{item.override.domain}</td>
                        <td className="px-2 py-2" data-testid={`admin-permissions-explicit-action-${item.override.id}`}>{item.override.action}</td>
                        <td className="px-2 py-2" data-testid={`admin-permissions-explicit-scope-${item.override.id}`}>
                          {(item.override.country_scope || []).join(', ') || 'GLOBAL (*)'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>

          <div className="rounded-lg border bg-white p-4" data-testid="admin-permissions-matrix-card">
            <div className="flex items-center justify-between gap-2" data-testid="admin-permissions-matrix-header">
              <h2 className="text-base font-semibold" data-testid="admin-permissions-matrix-title">User Permission Matrix</h2>
              <select
                value={selectedUserId}
                onChange={(event) => setSelectedUserId(event.target.value)}
                className="h-8 rounded-md border px-2 text-xs"
                data-testid="admin-permissions-selected-user"
              >
                {users.map((item) => (
                  <option key={item.id} value={item.id} data-testid={`admin-permissions-selected-user-option-${item.id}`}>
                    {item.email}
                  </option>
                ))}
              </select>
            </div>

            {selectedUser ? (
              <div className="mt-2 space-y-3" data-testid="admin-permissions-selected-user-summary">
                <div className="text-xs text-slate-500" data-testid="admin-permissions-selected-user-role">
                  role: {selectedUser.role} · country: {selectedUser.country_code || '-'}
                </div>

                <div className="max-h-[380px] overflow-auto" data-testid="admin-permissions-matrix-wrap">
                  <table className="w-full text-xs" data-testid="admin-permissions-matrix-table">
                    <thead className="bg-slate-50">
                      <tr>
                        <th className="px-3 py-2 text-left">Domain</th>
                        <th className="px-3 py-2 text-left">Action</th>
                        <th className="px-3 py-2 text-left">Inherit</th>
                        <th className="px-3 py-2 text-left">Explicit</th>
                        <th className="px-3 py-2 text-left">Effective</th>
                        <th className="px-3 py-2 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(flags?.domains || {}).flatMap(([domain, actions]) => actions.map((action) => renderCell(domain, action)))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      ) : null}

      {draft && selectedUser ? (
        <div className="rounded-lg border bg-white p-4" data-testid="admin-permissions-draft-card">
          <div className="flex items-center justify-between" data-testid="admin-permissions-draft-header">
            <h3 className="text-sm font-semibold" data-testid="admin-permissions-draft-title">
              {draft.mode === 'grant' ? 'Grant / Update Override' : 'Revoke Override'}
            </h3>
            <button type="button" className="h-8 rounded-md border px-2 text-xs" onClick={closeDraft} data-testid="admin-permissions-draft-close">
              Kapat
            </button>
          </div>

          <div className="mt-2 text-xs text-slate-600" data-testid="admin-permissions-draft-target">
            target: {selectedUser.email} · {draft.domain}:{draft.action}
          </div>

          {draft.mode === 'grant' ? (
            <div className="mt-3 space-y-2" data-testid="admin-permissions-draft-scope">
              <label className="flex items-center gap-2 text-xs" data-testid="admin-permissions-draft-global-scope-label">
                <input
                  type="checkbox"
                  checked={draftGlobalScope}
                  onChange={(event) => setDraftGlobalScope(event.target.checked)}
                  data-testid="admin-permissions-draft-global-scope"
                />
                Global scope (*)
              </label>

              {!draftGlobalScope ? (
                <div className="grid grid-cols-2 gap-2 rounded-md border p-2" data-testid="admin-permissions-draft-country-multiselect">
                  {countries.map((country) => {
                    const checked = draftScope.includes(country.code);
                    return (
                      <label key={country.code} className="flex items-center gap-2 text-xs" data-testid={`admin-permissions-draft-country-label-${country.code}`}>
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={() => toggleScopeCode(country.code)}
                          data-testid={`admin-permissions-draft-country-${country.code}`}
                        />
                        {country.code}
                      </label>
                    );
                  })}
                </div>
              ) : null}
            </div>
          ) : null}

          <div className="mt-3" data-testid="admin-permissions-draft-reason-wrap">
            <textarea
              value={draftReason}
              onChange={(event) => setDraftReason(event.target.value)}
              placeholder="Reason (min 10 karakter)"
              className="min-h-[90px] w-full rounded-md border p-2 text-sm"
              data-testid="admin-permissions-draft-reason"
            />
          </div>

          <div className="mt-3 flex items-center justify-end gap-2" data-testid="admin-permissions-draft-actions">
            <button
              type="button"
              className="h-9 rounded-md border px-3 text-sm"
              onClick={submitDraft}
              disabled={submitting}
              data-testid="admin-permissions-draft-submit"
            >
              {submitting ? 'Kaydediliyor...' : draft.mode === 'grant' ? 'Grant Kaydet' : 'Revoke Uygula'}
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
