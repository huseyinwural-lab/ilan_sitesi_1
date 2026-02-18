import { useState, useEffect } from 'react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { 
  Search, Filter, Plus, MoreHorizontal, UserCheck, UserX, 
  Pencil, Trash2, Shield, X, Check
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const roleColors = {
  super_admin: 'bg-rose-100 text-rose-800 dark:bg-rose-900/30 dark:text-rose-400',
  country_admin: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-400',
  moderator: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400',
  support: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
  finance: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400',
};

export default function Users({
  title,
  allowedRoles = null,
  readOnly = false,
  showRoleFilter = true,
  emptyStateLabel,
}) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [actionMenuOpen, setActionMenuOpen] = useState(null);
  const { t } = useLanguage();

  useEffect(() => {
    fetchUsers();
  }, [search, roleFilter, allowedRoles]);

  const fetchUsers = async () => {
    try {
      const params = new URLSearchParams();
      if (search) params.append('search', search);
      if (roleFilter) params.append('role', roleFilter);
      
      const country = new URLSearchParams(window.location.search).get('country');
      if (country) params.append('country', country);

      const response = await axios.get(`${API}/users?${params}`);
      let fetchedUsers = response.data || [];
      if (allowedRoles?.length) {
        fetchedUsers = fetchedUsers.filter((user) => allowedRoles.includes(user.role));
      }
      setUsers(fetchedUsers);
    } catch (error) {
      console.error('Failed to fetch users:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSuspend = async (userId) => {
    try {
      await axios.post(`${API}/users/${userId}/suspend`);
      fetchUsers();
    } catch (error) {
      console.error('Failed to suspend user:', error);
    }
    setActionMenuOpen(null);
  };

  const handleActivate = async (userId) => {
    try {
      await axios.post(`${API}/users/${userId}/activate`);
      fetchUsers();
    } catch (error) {
      console.error('Failed to activate user:', error);
    }
    setActionMenuOpen(null);
  };

  const handleDelete = async (userId) => {
    if (!window.confirm('Are you sure you want to delete this user?')) return;
    try {
      await axios.delete(`${API}/users/${userId}`);
      fetchUsers();
    } catch (error) {
      console.error('Failed to delete user:', error);
    }
    setActionMenuOpen(null);
  };

  const handleUpdateRole = async (userId, newRole) => {
    try {
      await axios.patch(`${API}/users/${userId}`, { role: newRole });
      fetchUsers();
      setEditingUser(null);
    } catch (error) {
      console.error('Failed to update user:', error);
    }
  };

  return (
    <div className="space-y-6" data-testid="users-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{title || t('users')}</h1>
          <p className="text-muted-foreground text-sm mt-1">{users.length} {title ? title.toLowerCase() : t('users').toLowerCase()} found</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={18} />
          <input
            type="text"
            placeholder={`${t('search')}...`}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full h-10 pl-10 pr-4 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
            data-testid="users-search"
          />
        </div>
        {showRoleFilter && (
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className="h-10 px-3 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
            data-testid="users-role-filter"
          >
            <option value="">{t('all')} {t('role')}</option>
            <option value="super_admin">{t('super_admin')}</option>
            <option value="country_admin">{t('country_admin')}</option>
            <option value="moderator">{t('moderator')}</option>
            <option value="support">{t('support')}</option>
            <option value="finance">{t('finance')}</option>
            <option value="dealer">{t('dealer')}</option>
            <option value="user">{t('user')}</option>
          </select>
        )}
      </div>

      {/* Table */}
      <div className="rounded-md border bg-card overflow-hidden">
        <table className="data-table">
          <thead>
            <tr>
              <th>{t('name')}</th>
              <th>{t('email')}</th>
              <th>{t('role')}</th>
              <th>Countries</th>
              <th>{t('status')}</th>
              <th className="text-right">{t('actions')}</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6} className="text-center py-8">
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary" />
                  </div>
                </td>
              </tr>
            ) : users.length === 0 ? (
              <tr>
                <td colSpan={6} className="text-center py-8 text-muted-foreground">
                  No users found
                </td>
              </tr>
            ) : (
              users.map((user) => (
                <tr key={user.id} data-testid={`user-row-${user.id}`}>
                  <td>
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-medium text-sm">
                        {user.full_name.charAt(0).toUpperCase()}
                      </div>
                      <span className="font-medium">{user.full_name}</span>
                    </div>
                  </td>
                  <td className="text-muted-foreground">{user.email}</td>
                  <td>
                    {readOnly ? (
                      <span
                        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${roleColors[user.role] || 'bg-muted'}`}
                        data-testid={`user-role-${user.id}`}
                      >
                        {t(user.role)}
                      </span>
                    ) : editingUser === user.id ? (
                      <select
                        defaultValue={user.role}
                        onChange={(e) => handleUpdateRole(user.id, e.target.value)}
                        onBlur={() => setEditingUser(null)}
                        autoFocus
                        className="h-8 px-2 rounded border text-xs"
                        data-testid={`user-role-select-${user.id}`}
                      >
                        <option value="super_admin">{t('super_admin')}</option>
                        <option value="country_admin">{t('country_admin')}</option>
                        <option value="moderator">{t('moderator')}</option>
                        <option value="support">{t('support')}</option>
                        <option value="finance">{t('finance')}</option>
                      </select>
                    ) : (
                      <button
                        type="button"
                        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${roleColors[user.role] || 'bg-muted'}`}
                        onClick={() => setEditingUser(user.id)}
                        data-testid={`user-role-${user.id}`}
                      >
                        {t(user.role)}
                      </button>
                    )}
                  </td>
                  <td>
                    <div className="flex flex-wrap gap-1">
                      {user.country_scope?.includes('*') ? (
                        <span className="text-xs px-1.5 py-0.5 rounded bg-muted">All</span>
                      ) : (
                        user.country_scope?.map((c) => (
                          <span key={c} className="text-xs px-1.5 py-0.5 rounded bg-muted">{c}</span>
                        ))
                      )}
                    </div>
                  </td>
                  <td>
                    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${
                      user.is_active 
                        ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400' 
                        : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'
                    }`}>
                      {user.is_active ? <Check size={12} /> : <X size={12} />}
                      {user.is_active ? t('active') : t('inactive')}
                    </span>
                  </td>
                  <td className="text-right">
                    <div className="relative inline-block">
                      <button
                        onClick={() => setActionMenuOpen(actionMenuOpen === user.id ? null : user.id)}
                        className="p-1.5 rounded hover:bg-muted transition-colors"
                        data-testid={`user-actions-${user.id}`}
                      >
                        <MoreHorizontal size={16} />
                      </button>
                      {actionMenuOpen === user.id && (
                        <div className="absolute right-0 top-full mt-1 w-40 rounded-md border bg-popover shadow-lg z-10">
                          <div className="p-1">
                            {user.is_active ? (
                              <button
                                onClick={() => handleSuspend(user.id)}
                                className="w-full flex items-center gap-2 px-3 py-2 text-sm rounded hover:bg-muted text-amber-600"
                              >
                                <UserX size={14} />
                                Suspend
                              </button>
                            ) : (
                              <button
                                onClick={() => handleActivate(user.id)}
                                className="w-full flex items-center gap-2 px-3 py-2 text-sm rounded hover:bg-muted text-emerald-600"
                              >
                                <UserCheck size={14} />
                                Activate
                              </button>
                            )}
                            <button
                              onClick={() => handleDelete(user.id)}
                              className="w-full flex items-center gap-2 px-3 py-2 text-sm rounded hover:bg-muted text-destructive"
                            >
                              <Trash2 size={14} />
                              {t('delete')}
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
