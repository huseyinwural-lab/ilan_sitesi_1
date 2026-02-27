import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { trackDealerEvent } from '@/lib/dealerAnalytics';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function DealerCustomers() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [items, setItems] = useState([]);
  const [nonStoreUsers, setNonStoreUsers] = useState([]);
  const [summary, setSummary] = useState({ users_count: 0, non_store_users_count: 0 });
  const [activeTab, setActiveTab] = useState('users');
  const [nameFilter, setNameFilter] = useState('');
  const [emailFilter, setEmailFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const fetchItems = async () => {
    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`${API}/dealer/customers`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(payload?.detail || 'Müşteri listesi alınamadı');
      setItems(Array.isArray(payload?.items) ? payload.items : []);
      setNonStoreUsers(Array.isArray(payload?.non_store_users) ? payload.non_store_users : []);
      setSummary(payload?.summary || { users_count: 0, non_store_users_count: 0 });
    } catch (err) {
      setError(err?.message || 'Müşteri listesi alınamadı');
      setItems([]);
      setNonStoreUsers([]);
      setSummary({ users_count: 0, non_store_users_count: 0 });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItems();
  }, []);

  const filteredUsers = useMemo(() => {
    return items.filter((item) => {
      const name = `${item.customer_name || ''}`.toLowerCase();
      const email = `${item.customer_email || ''}`.toLowerCase();
      const status = item.customer_is_active ? 'active' : 'removed';
      const nameOk = !nameFilter.trim() || name.includes(nameFilter.trim().toLowerCase());
      const emailOk = !emailFilter.trim() || email.includes(emailFilter.trim().toLowerCase());
      const statusOk = statusFilter === 'all' || status === statusFilter;
      return nameOk && emailOk && statusOk;
    });
  }, [items, nameFilter, emailFilter, statusFilter]);

  const filteredNonStoreUsers = useMemo(() => {
    return nonStoreUsers.filter((item) => {
      const name = `${item.full_name || ''}`.toLowerCase();
      const email = `${item.email || ''}`.toLowerCase();
      const status = item.is_active ? 'active' : 'removed';
      const nameOk = !nameFilter.trim() || name.includes(nameFilter.trim().toLowerCase());
      const emailOk = !emailFilter.trim() || email.includes(emailFilter.trim().toLowerCase());
      const statusOk = statusFilter === 'all' || status === statusFilter;
      return nameOk && emailOk && statusOk;
    });
  }, [nonStoreUsers, nameFilter, emailFilter, statusFilter]);

  const visibleRows = activeTab === 'users' ? filteredUsers : filteredNonStoreUsers;

  const statusText = (isActive) => (isActive ? 'Aktif' : 'Çıkarıldı');

  return (
    <div className="space-y-4" data-testid="dealer-customers-page">
      <div className="flex flex-wrap items-center justify-between gap-3" data-testid="dealer-customers-header">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900" data-testid="dealer-customers-title">Müşteri Yönetimi</h1>
          <p className="text-sm font-medium text-slate-700" data-testid="dealer-customers-subtitle">Kullanıcı listesi ve mağaza kullanıcısı olmayanlar yönetimi.</p>
        </div>
        <div className="flex items-center gap-2" data-testid="dealer-customers-header-actions">
          <button
            type="button"
            onClick={() => navigate('/dealer/settings')}
            className="h-9 rounded-md border border-slate-300 px-3 text-sm font-semibold text-slate-900"
            data-testid="dealer-customers-add-user-button"
          >
            Yeni Kullanıcı Ekle
          </button>
          <button
            type="button"
            onClick={fetchItems}
            className="h-9 rounded-md border border-slate-300 px-3 text-sm font-semibold text-slate-900"
            data-testid="dealer-customers-refresh-button"
          >
            Yenile
          </button>
        </div>
      </div>
      {error && <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700" data-testid="dealer-customers-error">{error}</div>}

      <div className="rounded-lg border border-slate-200 bg-white p-4" data-testid="dealer-customers-toolbar">
        <div className="flex flex-wrap items-center gap-2" data-testid="dealer-customers-tab-wrap">
          <button
            type="button"
            onClick={() => setActiveTab('users')}
            className={`rounded-full border px-3 py-1.5 text-xs font-semibold ${activeTab === 'users' ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-300 text-slate-800'}`}
            data-testid="dealer-customers-tab-users"
          >
            Kullanıcı Listesi ({summary.users_count || 0})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('non_store')}
            className={`rounded-full border px-3 py-1.5 text-xs font-semibold ${activeTab === 'non_store' ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-300 text-slate-800'}`}
            data-testid="dealer-customers-tab-non-store"
          >
            Mağaza Kullanıcısı Olmayanlar ({summary.non_store_users_count || 0})
          </button>
        </div>

        <div className="mt-3 grid gap-2 md:grid-cols-4" data-testid="dealer-customers-filter-row">
          <input
            value={nameFilter}
            onChange={(event) => setNameFilter(event.target.value)}
            placeholder="Ad Soyad"
            className="h-10 rounded-md border border-slate-300 px-3 text-sm text-slate-900"
            data-testid="dealer-customers-filter-name"
          />
          <input
            value={emailFilter}
            onChange={(event) => setEmailFilter(event.target.value)}
            placeholder="E-Posta"
            className="h-10 rounded-md border border-slate-300 px-3 text-sm text-slate-900"
            data-testid="dealer-customers-filter-email"
          />
          <select
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
            className="h-10 rounded-md border border-slate-300 px-3 text-sm text-slate-900"
            data-testid="dealer-customers-filter-status"
          >
            <option value="all">Durumu (Tümü)</option>
            <option value="active">Aktif</option>
            <option value="removed">Çıkarıldı</option>
          </select>
          <button
            type="button"
            onClick={() => {
              setNameFilter('');
              setEmailFilter('');
              setStatusFilter('all');
            }}
            className="h-10 rounded-md border border-slate-300 px-3 text-sm font-semibold text-slate-900"
            data-testid="dealer-customers-filter-reset"
          >
            Sıfırla
          </button>
        </div>
      </div>

      <div className="rounded-md border border-slate-200 overflow-x-auto" data-testid="dealer-customers-table-wrap">
        <table className="w-full text-sm" data-testid="dealer-customers-table">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-3 py-2 text-left text-slate-800">Ad Soyad</th>
              <th className="px-3 py-2 text-left text-slate-800">E-Posta</th>
              <th className="px-3 py-2 text-left text-slate-800">Durumu</th>
              <th className="px-3 py-2 text-left text-slate-800">İşlemler</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td className="px-3 py-4" colSpan={4} data-testid="dealer-customers-loading">Yükleniyor...</td></tr>
            ) : visibleRows.length === 0 ? (
              <tr><td className="px-3 py-4 text-slate-600" colSpan={4} data-testid="dealer-customers-empty">Kayıt yok</td></tr>
            ) : (
              visibleRows.map((item) => {
                const id = item.customer_id || item.user_id;
                const fullName = item.customer_name || item.full_name || '-';
                const email = item.customer_email || item.email || '-';
                const isActive = item.customer_is_active ?? item.is_active;
                return (
                  <tr key={id} className="border-t" data-testid={`dealer-customer-row-${id}`}>
                    <td className="px-3 py-2 font-medium text-slate-900" data-testid={`dealer-customer-name-${id}`}>{fullName}</td>
                    <td className="px-3 py-2" data-testid={`dealer-customer-email-${id}`}>{email}</td>
                    <td className="px-3 py-2" data-testid={`dealer-customer-status-${id}`}>
                      <span className={`rounded-full border px-2 py-1 text-xs font-semibold ${isActive ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-slate-300 bg-slate-100 text-slate-700'}`}>
                        {statusText(Boolean(isActive))}
                      </span>
                    </td>
                    <td className="px-3 py-2" data-testid={`dealer-customer-actions-${id}`}>
                      {activeTab === 'users' ? (
                        <button
                          type="button"
                          onClick={() => {
                            trackDealerEvent('dealer_contact_click', { customer_id: id });
                            navigate('/dealer/messages');
                          }}
                          className="h-8 rounded-md border border-slate-300 px-2 text-xs font-semibold text-slate-900"
                          data-testid={`dealer-customer-contact-click-${id}`}
                        >
                          Detay
                        </button>
                      ) : (
                        <button
                          type="button"
                          onClick={() => navigate('/dealer/settings')}
                          className="h-8 rounded-md border border-slate-300 px-2 text-xs font-semibold text-slate-900"
                          data-testid={`dealer-customer-add-store-user-${id}`}
                        >
                          Ekle
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
