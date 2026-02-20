import { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { Search, UserPlus, Filter, Shield, Pencil, XCircle } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ROLE_OPTIONS = [
  { value: 'super_admin', label: 'Super Admin' },
  { value: 'country_admin', label: 'Ülke Admin' },
  { value: 'moderator', label: 'Moderatör' },
  { value: 'support', label: 'Destek' },
  { value: 'finance', label: 'Finans' },
];

const STATUS_OPTIONS = [
  { value: 'all', label: 'Tümü' },
  { value: 'active', label: 'Aktif' },
  { value: 'inactive', label: 'Pasif' },
  { value: 'invited', label: 'Davet Bekliyor' },
];

const SORT_OPTIONS = [
  { value: 'created_at', label: 'Oluşturma Tarihi' },
  { value: 'last_login', label: 'Son Giriş' },
  { value: 'email', label: 'E-posta' },
  { value: 'role', label: 'Rol' },
];

const emptyForm = {
  full_name: '',
  email: '',
  role: 'country_admin',
  country_scope: [],
  is_active: true,
};

const formatDate = (value) => {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '-';
  return date.toLocaleString();
};

const formatScope = (scope) => {
  if (!scope || scope.length === 0) return '-';
  if (scope.includes('*')) return 'All Countries';
  return scope.join(', ');
};

const statusLabel = (user) => {
  if (user.invite_status === 'pending') return { text: 'Davet Bekliyor', color: 'bg-amber-100 text-amber-700' };
  return user.is_active
    ? { text: 'Aktif', color: 'bg-emerald-100 text-emerald-700' }
    : { text: 'Pasif', color: 'bg-rose-100 text-rose-700' };
};

const roleLabel = (role) => ROLE_OPTIONS.find((opt) => opt.value === role)?.label || role;

export default function AdminUsers() {
  const [users, setUsers] = useState([]);
  const [countries, setCountries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [countryFilter, setCountryFilter] = useState('all');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortDir, setSortDir] = useState('desc');
  const [selectedIds, setSelectedIds] = useState([]);
  const [bulkError, setBulkError] = useState('');
  const [createOpen, setCreateOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [createForm, setCreateForm] = useState({ ...emptyForm });
  const [editForm, setEditForm] = useState({ ...emptyForm });
  const [editingUser, setEditingUser] = useState(null);
  const [formError, setFormError] = useState('');
  const [formSuccess, setFormSuccess] = useState('');
  const [saving, setSaving] = useState(false);

  const authHeader = useMemo(
    () => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` }),
    []
  );

  const fetchCountries = async () => {
    try {
      const res = await axios.get(`${API}/admin/countries`, { headers: authHeader });
      const active = (res.data.items || []).filter((item) => item.active_flag);
      setCountries(active.map((item) => item.country_code));
    } catch (err) {
      setCountries([]);
    }
  };

  const fetchUsers = async (overrideSearch) => {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams();
      const q = overrideSearch ?? search;
      if (q) params.set('search', q);
      if (roleFilter !== 'all') params.set('role', roleFilter);
      if (statusFilter !== 'all') params.set('status', statusFilter);
      if (countryFilter !== 'all') params.set('country', countryFilter);
      if (sortBy) params.set('sort_by', sortBy);
      if (sortDir) params.set('sort_dir', sortDir);
      const qs = params.toString() ? `?${params.toString()}` : '';
      const res = await axios.get(`${API}/admin/users${qs}`, { headers: authHeader });
      setUsers(res.data.items || []);
    } catch (err) {
      setError('Admin kullanıcı listesi yüklenemedi.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCountries();
    fetchUsers('');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    fetchUsers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [roleFilter, statusFilter, countryFilter, sortBy, sortDir]);

  const handleSearchSubmit = (event) => {
    event.preventDefault();
    fetchUsers();
  };

  const handleToggleSelect = (userId) => {
    setBulkError('');
    setSelectedIds((prev) =>
      prev.includes(userId) ? prev.filter((id) => id !== userId) : [...prev, userId]
    );
  };

  const handleSelectAll = () => {
    setBulkError('');
    if (selectedIds.length === users.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(users.map((user) => user.id));
    }
  };

  const handleOpenCreate = () => {
    setCreateForm({ ...emptyForm });
    setFormError('');
    setFormSuccess('');
    setCreateOpen(true);
  };

  const handleOpenEdit = (user) => {
    setEditingUser(user);
    setEditForm({
      full_name: user.full_name || '',
      email: user.email || '',
      role: user.role || 'support',
      country_scope: user.country_scope || [],
      is_active: Boolean(user.is_active),
    });
    setFormError('');
    setFormSuccess('');
    setEditOpen(true);
  };

  const handleCloseModal = () => {
    setCreateOpen(false);
    setEditOpen(false);
    setSaving(false);
    setEditingUser(null);
  };

  const updateRoleForm = (setter, form, roleValue) => {
    if (roleValue === 'super_admin') {
      setter({ ...form, role: roleValue, country_scope: ['*'] });
    } else {
      const filtered = (form.country_scope || []).filter((code) => code !== '*');
      setter({ ...form, role: roleValue, country_scope: filtered });
    }
  };

  const toggleScopeValue = (setter, form, code) => {
    const current = form.country_scope || [];
    if (current.includes(code)) {
      setter({ ...form, country_scope: current.filter((item) => item !== code) });
    } else {
      setter({ ...form, country_scope: [...current, code] });
    }
  };

  const validateForm = (form) => {
    if (!form.full_name.trim()) return 'Ad Soyad zorunludur.';
    if (!form.email.trim()) return 'E-posta zorunludur.';
    if (!form.role) return 'Rol seçimi zorunludur.';
    if (form.role === 'country_admin' && (!form.country_scope || form.country_scope.length === 0)) {
      return 'Country admin için en az 1 ülke seçin.';
    }
    return '';
  };

  const handleCreateSubmit = async () => {
    setFormError('');
    setFormSuccess('');
    const validation = validateForm(createForm);
    if (validation) {
      setFormError(validation);
      return;
    }
    setSaving(true);
    try {
      await axios.post(
        `${API}/admin/users`,
        {
          full_name: createForm.full_name.trim(),
          email: createForm.email.trim(),
          role: createForm.role,
          country_scope: createForm.country_scope,
          is_active: createForm.is_active,
        },
        { headers: authHeader }
      );
      setFormSuccess('Admin daveti gönderildi.');
      fetchUsers();
    } catch (err) {
      const message = err.response?.data?.detail || 'Admin oluşturulamadı.';
      setFormError(typeof message === 'string' ? message : 'Admin oluşturulamadı.');
    } finally {
      setSaving(false);
    }
  };

  const handleEditSubmit = async () => {
    if (!editingUser) return;
    setFormError('');
    setFormSuccess('');
    const validation = validateForm(editForm);
    if (validation) {
      setFormError(validation);
      return;
    }
    setSaving(true);
    try {
      await axios.patch(
        `${API}/admin/users/${editingUser.id}`,
        {
          role: editForm.role,
          country_scope: editForm.country_scope,
          is_active: editForm.is_active,
        },
        { headers: authHeader }
      );
      setFormSuccess('Admin güncellendi.');
      fetchUsers();
    } catch (err) {
      const message = err.response?.data?.detail || 'Admin güncellenemedi.';
      setFormError(typeof message === 'string' ? message : 'Admin güncellenemedi.');
    } finally {
      setSaving(false);
    }
  };

  const handleBulkDeactivate = async () => {
    setBulkError('');
    if (selectedIds.length === 0) {
      setBulkError('Önce admin seçin.');
      return;
    }
    if (selectedIds.length > 20) {
      setBulkError('Toplu pasif etme limiti 20 kullanıcıdır.');
      return;
    }
    try {
      await axios.post(
        `${API}/admin/users/bulk-deactivate`,
        { user_ids: selectedIds },
        { headers: authHeader }
      );
      setSelectedIds([]);
      fetchUsers();
    } catch (err) {
      const message = err.response?.data?.detail || 'Toplu pasif etme başarısız.';
      setBulkError(typeof message === 'string' ? message : 'Toplu pasif etme başarısız.');
    }
  };

  return (
    <div className="space-y-6" data-testid="admin-users-page">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold" data-testid="admin-users-title">Admin Kullanıcıları Yönetimi</h1>
          <p className="text-sm text-muted-foreground" data-testid="admin-users-subtitle">
            Yetkilendirilmiş admin hesapları ve erişim kapsamları
          </p>
        </div>
        <button
          type="button"
          className="h-10 px-4 rounded-md bg-primary text-primary-foreground text-sm font-medium flex items-center gap-2"
          onClick={handleOpenCreate}
          data-testid="admin-users-create-button"
        >
          <UserPlus size={16} /> Yeni Admin Ekle
        </button>
      </div>

      <div className="bg-card border rounded-md p-4 space-y-4" data-testid="admin-users-filters">
        <form onSubmit={handleSearchSubmit} className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 border rounded-md px-3 h-10 bg-background">
            <Search size={16} className="text-muted-foreground" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Ad, e-posta ara"
              className="bg-transparent outline-none text-sm"
              data-testid="admin-users-search-input"
            />
          </div>
          <button
            type="submit"
            className="h-10 px-4 rounded-md border text-sm"
            data-testid="admin-users-search-button"
          >
            Ara
          </button>
          <div className="flex items-center gap-2 text-xs text-muted-foreground" data-testid="admin-users-filter-icon">
            <Filter size={14} /> Filtreler
          </div>
        </form>

        <div className="grid gap-3 md:grid-cols-4">
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">Rol</div>
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className="h-10 rounded-md border bg-background px-3 text-sm w-full"
              data-testid="admin-users-role-filter"
            >
              <option value="all">Tümü</option>
              {ROLE_OPTIONS.map((role) => (
                <option key={role.value} value={role.value}>{role.label}</option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">Durum</div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="h-10 rounded-md border bg-background px-3 text-sm w-full"
              data-testid="admin-users-status-filter"
            >
              {STATUS_OPTIONS.map((status) => (
                <option key={status.value} value={status.value}>{status.label}</option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">Ülke</div>
            <select
              value={countryFilter}
              onChange={(e) => setCountryFilter(e.target.value)}
              className="h-10 rounded-md border bg-background px-3 text-sm w-full"
              data-testid="admin-users-country-filter"
            >
              <option value="all">Tümü</option>
              {countries.map((code) => (
                <option key={code} value={code}>{code}</option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">Sıralama</div>
            <div className="flex items-center gap-2">
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="h-10 rounded-md border bg-background px-3 text-sm w-full"
                data-testid="admin-users-sort-select"
              >
                {SORT_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
              <button
                type="button"
                onClick={() => setSortDir(sortDir === 'desc' ? 'asc' : 'desc')}
                className="h-10 w-10 rounded-md border flex items-center justify-center"
                data-testid="admin-users-sort-direction"
              >
                <Shield size={16} />
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3" data-testid="admin-users-bulk-actions">
        <div className="text-sm text-muted-foreground">
          Seçili: <span data-testid="admin-users-selected-count">{selectedIds.length}</span>
        </div>
        <button
          type="button"
          className="h-10 px-4 rounded-md border text-sm flex items-center gap-2"
          onClick={handleBulkDeactivate}
          data-testid="admin-users-bulk-deactivate"
        >
          <XCircle size={16} /> Toplu Pasif Et (max 20)
        </button>
      </div>
      {bulkError && (
        <div className="text-sm text-rose-600" data-testid="admin-users-bulk-error">{bulkError}</div>
      )}
      {error && (
        <div className="text-sm text-rose-600" data-testid="admin-users-error">{error}</div>
      )}

      <div className="rounded-md border bg-card overflow-hidden" data-testid="admin-users-table">
        <div className="overflow-x-auto">
          <table className="min-w-[900px] w-full text-sm">
            <thead className="bg-muted">
              <tr>
                <th className="p-3 text-left">
                  <input
                    type="checkbox"
                    checked={selectedIds.length === users.length && users.length > 0}
                    onChange={handleSelectAll}
                    data-testid="admin-users-select-all"
                  />
                </th>
                <th className="p-3 text-left">Ad Soyad</th>
                <th className="p-3 text-left">E-posta</th>
                <th className="p-3 text-left">Rol</th>
                <th className="p-3 text-left">Country Scope</th>
                <th className="p-3 text-left">Durum</th>
                <th className="p-3 text-left">Son Giriş</th>
                <th className="p-3 text-left">Aksiyon</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={8} className="p-6 text-center text-muted-foreground" data-testid="admin-users-loading">
                    Yükleniyor...
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={8} className="p-6 text-center text-muted-foreground" data-testid="admin-users-empty">
                    Admin kullanıcı bulunamadı.
                  </td>
                </tr>
              ) : (
                users.map((user) => {
                  const status = statusLabel(user);
                  return (
                    <tr key={user.id} className="border-b last:border-none" data-testid={`admin-user-row-${user.id}`}>
                      <td className="p-3">
                        <input
                          type="checkbox"
                          checked={selectedIds.includes(user.id)}
                          onChange={() => handleToggleSelect(user.id)}
                          data-testid={`admin-user-select-${user.id}`}
                        />
                      </td>
                      <td className="p-3" data-testid={`admin-user-name-${user.id}`}>{user.full_name || '-'}</td>
                      <td className="p-3" data-testid={`admin-user-email-${user.id}`}>{user.email}</td>
                      <td className="p-3" data-testid={`admin-user-role-${user.id}`}>{roleLabel(user.role)}</td>
                      <td className="p-3" data-testid={`admin-user-scope-${user.id}`}>{formatScope(user.country_scope)}</td>
                      <td className="p-3" data-testid={`admin-user-status-${user.id}`}>
                        <span className={`px-2 py-1 rounded-full text-xs ${status.color}`}>{status.text}</span>
                      </td>
                      <td className="p-3" data-testid={`admin-user-last-login-${user.id}`}>{formatDate(user.last_login)}</td>
                      <td className="p-3">
                        <button
                          type="button"
                          className="inline-flex items-center gap-1 text-primary text-xs"
                          onClick={() => handleOpenEdit(user)}
                          data-testid={`admin-user-edit-${user.id}`}
                        >
                          <Pencil size={14} /> Düzenle
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {(createOpen || editOpen) && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" data-testid="admin-users-modal">
          <div className="bg-card rounded-lg shadow-lg max-w-xl w-full" data-testid="admin-users-modal-content">
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="text-lg font-semibold" data-testid="admin-users-modal-title">
                {editOpen ? 'Admin Düzenle' : 'Yeni Admin Ekle'}
              </h3>
              <button
                type="button"
                onClick={handleCloseModal}
                className="text-sm text-muted-foreground"
                data-testid="admin-users-modal-close"
              >
                Kapat
              </button>
            </div>
            <div className="p-4 space-y-3">
              <div>
                <label className="text-xs text-muted-foreground">Ad Soyad</label>
                <input
                  className="h-10 w-full rounded-md border bg-background px-3 text-sm"
                  value={editOpen ? editForm.full_name : createForm.full_name}
                  onChange={(e) =>
                    editOpen
                      ? setEditForm({ ...editForm, full_name: e.target.value })
                      : setCreateForm({ ...createForm, full_name: e.target.value })
                  }
                  data-testid="admin-users-form-full-name"
                />
              </div>
              <div>
                <label className="text-xs text-muted-foreground">E-posta</label>
                <input
                  className="h-10 w-full rounded-md border bg-background px-3 text-sm"
                  value={editOpen ? editForm.email : createForm.email}
                  onChange={(e) =>
                    editOpen
                      ? setEditForm({ ...editForm, email: e.target.value })
                      : setCreateForm({ ...createForm, email: e.target.value })
                  }
                  disabled={editOpen}
                  data-testid="admin-users-form-email"
                />
              </div>
              <div>
                <label className="text-xs text-muted-foreground">Rol</label>
                <select
                  className="h-10 w-full rounded-md border bg-background px-3 text-sm"
                  value={editOpen ? editForm.role : createForm.role}
                  onChange={(e) =>
                    editOpen
                      ? updateRoleForm(setEditForm, editForm, e.target.value)
                      : updateRoleForm(setCreateForm, createForm, e.target.value)
                  }
                  data-testid="admin-users-form-role"
                >
                  {ROLE_OPTIONS.map((role) => (
                    <option key={role.value} value={role.value}>{role.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs text-muted-foreground">Country Scope</label>
                <div className="border rounded-md p-3 space-y-2" data-testid="admin-users-form-scope">
                  {(editOpen ? editForm.role : createForm.role) === 'super_admin' ? (
                    <div className="text-sm text-muted-foreground" data-testid="admin-users-form-scope-all">
                      All Countries
                    </div>
                  ) : (
                    <div className="grid grid-cols-2 gap-2">
                      {countries.map((code) => (
                        <label key={code} className="flex items-center gap-2 text-sm" data-testid={`admin-users-scope-${code}`}>
                          <input
                            type="checkbox"
                            checked={(editOpen ? editForm.country_scope : createForm.country_scope).includes(code)}
                            onChange={() =>
                              editOpen
                                ? toggleScopeValue(setEditForm, editForm, code)
                                : toggleScopeValue(setCreateForm, createForm, code)
                            }
                            data-testid={`admin-users-scope-toggle-${code}`}
                          />
                          {code}
                        </label>
                      ))}
                    </div>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={editOpen ? editForm.is_active : createForm.is_active}
                  onChange={(e) =>
                    editOpen
                      ? setEditForm({ ...editForm, is_active: e.target.checked })
                      : setCreateForm({ ...createForm, is_active: e.target.checked })
                  }
                  data-testid="admin-users-form-active"
                />
                <span className="text-sm">Aktif</span>
              </div>

              {formError && (
                <div className="text-sm text-rose-600" data-testid="admin-users-form-error">{formError}</div>
              )}
              {formSuccess && (
                <div className="text-sm text-emerald-600" data-testid="admin-users-form-success">{formSuccess}</div>
              )}
            </div>
            <div className="flex items-center justify-between px-4 pb-4">
              <button
                type="button"
                className="h-10 px-4 rounded-md border text-sm"
                onClick={handleCloseModal}
                data-testid="admin-users-form-cancel"
              >
                Vazgeç
              </button>
              <button
                type="button"
                className="h-10 px-4 rounded-md bg-primary text-primary-foreground text-sm flex items-center gap-2"
                disabled={saving}
                onClick={editOpen ? handleEditSubmit : handleCreateSubmit}
                data-testid="admin-users-form-submit"
              >
                {saving ? 'Kaydediliyor' : editOpen ? 'Güncelle' : 'Davet Gönder'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
