import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const tabs = [
  { key: 'list', label: 'Müşteri Listesi' },
  { key: 'add', label: 'Müşteri Ekle' },
  { key: 'potential', label: 'Potansiyel Müşteriler' },
  { key: 'contracts', label: 'Sözleşmeler' },
];

export default function DealerCustomers() {
  const [searchParams, setSearchParams] = useSearchParams();
  const tab = tabs.some((row) => row.key === searchParams.get('tab')) ? searchParams.get('tab') : 'list';
  const contractStatus = ['active', 'expired', 'draft'].includes(searchParams.get('status')) ? searchParams.get('status') : 'all';

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [summary, setSummary] = useState({ users_count: 0, potential_customers_count: 0, contracts_count: 0, contracts_active_count: 0, contracts_expired_count: 0, contracts_draft_count: 0 });

  const [customers, setCustomers] = useState([]);
  const [potentialItems, setPotentialItems] = useState([]);
  const [contractItems, setContractItems] = useState([]);

  const [storeUserForm, setStoreUserForm] = useState({ full_name: '', email: '', password: '', role: 'staff' });
  const [potentialForm, setPotentialForm] = useState({ full_name: '', email: '', phone: '', notes: '', status: 'new' });
  const [contractForm, setContractForm] = useState({ customer_name: '', customer_email: '', title: '', status: 'draft', start_date: '', end_date: '', amount: '', currency: 'EUR', notes: '' });

  const fetchAll = async () => {
    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('access_token');
      const [baseRes, potentialRes, contractRes] = await Promise.all([
        fetch(`${API}/dealer/customers`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API}/dealer/customers/potential`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API}/dealer/customers/contracts${contractStatus !== 'all' ? `?status=${contractStatus}` : ''}`, { headers: { Authorization: `Bearer ${token}` } }),
      ]);
      const basePayload = await baseRes.json().catch(() => ({}));
      const potentialPayload = await potentialRes.json().catch(() => ({}));
      const contractPayload = await contractRes.json().catch(() => ({}));

      if (!baseRes.ok) throw new Error(basePayload?.detail || 'Müşteri listesi alınamadı');
      if (!potentialRes.ok) throw new Error(potentialPayload?.detail || 'Potansiyel müşteriler alınamadı');
      if (!contractRes.ok) throw new Error(contractPayload?.detail || 'Sözleşmeler alınamadı');

      setCustomers(Array.isArray(basePayload?.items) ? basePayload.items : []);
      setSummary(basePayload?.summary || { users_count: 0, potential_customers_count: 0, contracts_count: 0 });
      setPotentialItems(Array.isArray(potentialPayload?.items) ? potentialPayload.items : []);
      setContractItems(Array.isArray(contractPayload?.items) ? contractPayload.items : []);
    } catch (requestError) {
      setError(requestError?.message || 'Müşteri verisi alınamadı');
      setCustomers([]);
      setPotentialItems([]);
      setContractItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAll();
  }, [contractStatus]);

  const postJson = async (url, payload) => {
    const token = localStorage.getItem('access_token');
    const res = await fetch(url, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data?.detail || 'İşlem başarısız');
    return data;
  };

  return (
    <div className="space-y-4" data-testid="dealer-customers-page">
      <div className="flex flex-wrap items-center justify-between gap-3" data-testid="dealer-customers-header">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900" data-testid="dealer-customers-title">Müşteri Yönetimi</h1>
          <p className="text-sm font-medium text-slate-700" data-testid="dealer-customers-subtitle">Müşteri listesi, ekleme, potansiyel ve sözleşme yönetimi.</p>
        </div>
        <button type="button" onClick={fetchAll} className="h-9 rounded-md border border-slate-300 px-3 text-sm font-semibold text-slate-900" data-testid="dealer-customers-refresh-button">Yenile</button>
      </div>

      {error ? <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700" data-testid="dealer-customers-error">{error}</div> : null}

      <div className="rounded-lg border border-slate-200 bg-white p-4" data-testid="dealer-customers-toolbar">
        <div className="flex flex-wrap items-center gap-2" data-testid="dealer-customers-tab-wrap">
          {tabs.map((item) => (
            <button
              key={item.key}
              type="button"
              onClick={() => setSearchParams(item.key === 'contracts' ? { tab: item.key, status: contractStatus } : { tab: item.key })}
              className={`rounded-full border px-3 py-1.5 text-xs font-semibold ${tab === item.key ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-300 text-slate-800'}`}
              data-testid={`dealer-customers-tab-${item.key}`}
            >
              {item.label}
            </button>
          ))}
        </div>

        <div className="mt-3 grid gap-3 md:grid-cols-3" data-testid="dealer-customers-summary-grid">
          <div className="rounded-md border border-slate-200 bg-slate-50 p-2 text-xs" data-testid="dealer-customers-summary-users">Müşteri Listesi: <strong>{summary.users_count || 0}</strong></div>
          <div className="rounded-md border border-slate-200 bg-slate-50 p-2 text-xs" data-testid="dealer-customers-summary-potential">Potansiyel: <strong>{summary.potential_customers_count || 0}</strong></div>
          <div className="rounded-md border border-slate-200 bg-slate-50 p-2 text-xs" data-testid="dealer-customers-summary-contracts">Sözleşme: <strong>{summary.contracts_count || 0}</strong></div>
        </div>
      </div>

      {tab === 'list' ? (
        <div className="rounded-md border border-slate-200 overflow-x-auto" data-testid="dealer-customers-list-table-wrap">
          <table className="w-full text-sm" data-testid="dealer-customers-list-table">
            <thead className="bg-slate-50"><tr><th className="px-3 py-2 text-left">Ad Soyad</th><th className="px-3 py-2 text-left">E-Posta</th><th className="px-3 py-2 text-left">Mesaj</th><th className="px-3 py-2 text-left">Son İletişim</th></tr></thead>
            <tbody>
              {loading ? <tr><td className="px-3 py-4" colSpan={4} data-testid="dealer-customers-loading">Yükleniyor...</td></tr> : customers.length === 0 ? <tr><td className="px-3 py-4 text-slate-600" colSpan={4} data-testid="dealer-customers-empty">Kayıt yok</td></tr> : customers.map((item) => (
                <tr key={item.customer_id} className="border-t" data-testid={`dealer-customer-row-${item.customer_id}`}>
                  <td className="px-3 py-2 font-medium" data-testid={`dealer-customer-name-${item.customer_id}`}>{item.customer_name || '-'}</td>
                  <td className="px-3 py-2" data-testid={`dealer-customer-email-${item.customer_id}`}>{item.customer_email || '-'}</td>
                  <td className="px-3 py-2" data-testid={`dealer-customer-message-count-${item.customer_id}`}>{item.total_messages || 0}</td>
                  <td className="px-3 py-2" data-testid={`dealer-customer-last-contact-${item.customer_id}`}>{item.last_contact_at ? new Date(item.last_contact_at).toLocaleString('tr-TR') : '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {tab === 'add' ? (
        <form
          className="grid gap-3 rounded-lg border border-slate-200 bg-white p-4 md:grid-cols-2"
          data-testid="dealer-customers-add-form"
          onSubmit={async (event) => {
            event.preventDefault();
            try {
              await postJson(`${API}/dealer/customers/store-users`, storeUserForm);
              setStoreUserForm({ full_name: '', email: '', password: '', role: 'staff' });
              await fetchAll();
            } catch (requestError) {
              setError(requestError?.message || 'Kullanıcı eklenemedi');
            }
          }}
        >
          <input value={storeUserForm.full_name} onChange={(event) => setStoreUserForm((prev) => ({ ...prev, full_name: event.target.value }))} placeholder="Ad Soyad" className="h-10 rounded-md border border-slate-300 px-3 text-sm" data-testid="dealer-customers-add-name" required />
          <input type="email" value={storeUserForm.email} onChange={(event) => setStoreUserForm((prev) => ({ ...prev, email: event.target.value }))} placeholder="E-Posta" className="h-10 rounded-md border border-slate-300 px-3 text-sm" data-testid="dealer-customers-add-email" required />
          <input type="password" value={storeUserForm.password} onChange={(event) => setStoreUserForm((prev) => ({ ...prev, password: event.target.value }))} placeholder="Şifre" className="h-10 rounded-md border border-slate-300 px-3 text-sm" data-testid="dealer-customers-add-password" required />
          <select value={storeUserForm.role} onChange={(event) => setStoreUserForm((prev) => ({ ...prev, role: event.target.value }))} className="h-10 rounded-md border border-slate-300 px-3 text-sm" data-testid="dealer-customers-add-role"><option value="staff">Staff</option><option value="consultant">Consultant</option><option value="dealer_agent">Dealer Agent</option><option value="sales_agent">Sales Agent</option></select>
          <button type="submit" className="h-10 rounded-md bg-slate-900 px-4 text-sm font-semibold text-white md:col-span-2" data-testid="dealer-customers-add-submit">Müşteri/Kullanıcı Ekle</button>
        </form>
      ) : null}

      {tab === 'potential' ? (
        <div className="space-y-3" data-testid="dealer-customers-potential-section">
          <form
            className="grid gap-3 rounded-lg border border-slate-200 bg-white p-4 md:grid-cols-2"
            data-testid="dealer-customers-potential-form"
            onSubmit={async (event) => {
              event.preventDefault();
              try {
                await postJson(`${API}/dealer/customers/potential`, potentialForm);
                setPotentialForm({ full_name: '', email: '', phone: '', notes: '', status: 'new' });
                await fetchAll();
              } catch (requestError) {
                setError(requestError?.message || 'Potansiyel müşteri eklenemedi');
              }
            }}
          >
            <input value={potentialForm.full_name} onChange={(event) => setPotentialForm((prev) => ({ ...prev, full_name: event.target.value }))} placeholder="Ad Soyad" className="h-10 rounded-md border border-slate-300 px-3 text-sm" data-testid="dealer-customers-potential-name" required />
            <input type="email" value={potentialForm.email} onChange={(event) => setPotentialForm((prev) => ({ ...prev, email: event.target.value }))} placeholder="E-Posta" className="h-10 rounded-md border border-slate-300 px-3 text-sm" data-testid="dealer-customers-potential-email" required />
            <input value={potentialForm.phone} onChange={(event) => setPotentialForm((prev) => ({ ...prev, phone: event.target.value }))} placeholder="Telefon" className="h-10 rounded-md border border-slate-300 px-3 text-sm" data-testid="dealer-customers-potential-phone" />
            <select value={potentialForm.status} onChange={(event) => setPotentialForm((prev) => ({ ...prev, status: event.target.value }))} className="h-10 rounded-md border border-slate-300 px-3 text-sm" data-testid="dealer-customers-potential-status"><option value="new">Yeni</option><option value="contacted">İletişim Kuruldu</option><option value="qualified">Nitelikli</option><option value="converted">Dönüştü</option><option value="lost">Kaybedildi</option></select>
            <textarea value={potentialForm.notes} onChange={(event) => setPotentialForm((prev) => ({ ...prev, notes: event.target.value }))} placeholder="Not" className="min-h-[90px] rounded-md border border-slate-300 px-3 py-2 text-sm md:col-span-2" data-testid="dealer-customers-potential-notes" />
            <button type="submit" className="h-10 rounded-md bg-slate-900 px-4 text-sm font-semibold text-white md:col-span-2" data-testid="dealer-customers-potential-submit">Potansiyel Müşteri Ekle</button>
          </form>

          <div className="rounded-md border border-slate-200 overflow-x-auto" data-testid="dealer-customers-potential-table-wrap">
            <table className="w-full text-sm" data-testid="dealer-customers-potential-table">
              <thead className="bg-slate-50"><tr><th className="px-3 py-2 text-left">Ad Soyad</th><th className="px-3 py-2 text-left">E-Posta</th><th className="px-3 py-2 text-left">Durum</th><th className="px-3 py-2 text-left">Not</th></tr></thead>
              <tbody>{potentialItems.length === 0 ? <tr><td className="px-3 py-4 text-slate-600" colSpan={4} data-testid="dealer-customers-potential-empty">Kayıt yok</td></tr> : potentialItems.map((item) => <tr key={item.id} className="border-t" data-testid={`dealer-customers-potential-row-${item.id}`}><td className="px-3 py-2">{item.full_name}</td><td className="px-3 py-2">{item.email}</td><td className="px-3 py-2">{item.status}</td><td className="px-3 py-2">{item.notes || '-'}</td></tr>)}</tbody>
            </table>
          </div>
        </div>
      ) : null}

      {tab === 'contracts' ? (
        <div className="space-y-3" data-testid="dealer-customers-contracts-section">
          <div className="flex flex-wrap items-center gap-2" data-testid="dealer-customers-contracts-status-filter">
            {['all', 'active', 'expired', 'draft'].map((status) => (
              <button
                key={status}
                type="button"
                onClick={() => setSearchParams(status === 'all' ? { tab: 'contracts' } : { tab: 'contracts', status })}
                className={`rounded-full border px-3 py-1 text-xs font-semibold ${contractStatus === status ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-300 text-slate-800'}`}
                data-testid={`dealer-customers-contracts-filter-${status}`}
              >
                {status === 'all' ? 'Tümü' : status}
              </button>
            ))}
          </div>

          <form
            className="grid gap-3 rounded-lg border border-slate-200 bg-white p-4 md:grid-cols-2"
            data-testid="dealer-customers-contract-form"
            onSubmit={async (event) => {
              event.preventDefault();
              try {
                await postJson(`${API}/dealer/customers/contracts`, {
                  ...contractForm,
                  amount: contractForm.amount ? Number(contractForm.amount) : null,
                  start_date: contractForm.start_date ? `${contractForm.start_date}T00:00:00+00:00` : null,
                  end_date: contractForm.end_date ? `${contractForm.end_date}T23:59:59+00:00` : null,
                });
                setContractForm({ customer_name: '', customer_email: '', title: '', status: 'draft', start_date: '', end_date: '', amount: '', currency: 'EUR', notes: '' });
                await fetchAll();
              } catch (requestError) {
                setError(requestError?.message || 'Sözleşme eklenemedi');
              }
            }}
          >
            <input value={contractForm.customer_name} onChange={(event) => setContractForm((prev) => ({ ...prev, customer_name: event.target.value }))} placeholder="Müşteri Adı" className="h-10 rounded-md border border-slate-300 px-3 text-sm" data-testid="dealer-customers-contract-customer-name" required />
            <input type="email" value={contractForm.customer_email} onChange={(event) => setContractForm((prev) => ({ ...prev, customer_email: event.target.value }))} placeholder="Müşteri E-Posta" className="h-10 rounded-md border border-slate-300 px-3 text-sm" data-testid="dealer-customers-contract-customer-email" required />
            <input value={contractForm.title} onChange={(event) => setContractForm((prev) => ({ ...prev, title: event.target.value }))} placeholder="Sözleşme Başlığı" className="h-10 rounded-md border border-slate-300 px-3 text-sm" data-testid="dealer-customers-contract-title" required />
            <select value={contractForm.status} onChange={(event) => setContractForm((prev) => ({ ...prev, status: event.target.value }))} className="h-10 rounded-md border border-slate-300 px-3 text-sm" data-testid="dealer-customers-contract-status"><option value="draft">Taslak</option><option value="active">Aktif</option><option value="expired">Süresi Dolan</option></select>
            <input type="date" value={contractForm.start_date} onChange={(event) => setContractForm((prev) => ({ ...prev, start_date: event.target.value }))} className="h-10 rounded-md border border-slate-300 px-3 text-sm" data-testid="dealer-customers-contract-start-date" />
            <input type="date" value={contractForm.end_date} onChange={(event) => setContractForm((prev) => ({ ...prev, end_date: event.target.value }))} className="h-10 rounded-md border border-slate-300 px-3 text-sm" data-testid="dealer-customers-contract-end-date" />
            <input type="number" value={contractForm.amount} onChange={(event) => setContractForm((prev) => ({ ...prev, amount: event.target.value }))} placeholder="Tutar" className="h-10 rounded-md border border-slate-300 px-3 text-sm" data-testid="dealer-customers-contract-amount" />
            <input value={contractForm.currency} onChange={(event) => setContractForm((prev) => ({ ...prev, currency: event.target.value.toUpperCase() }))} placeholder="Para Birimi" className="h-10 rounded-md border border-slate-300 px-3 text-sm" data-testid="dealer-customers-contract-currency" />
            <textarea value={contractForm.notes} onChange={(event) => setContractForm((prev) => ({ ...prev, notes: event.target.value }))} placeholder="Sözleşme notları" className="min-h-[90px] rounded-md border border-slate-300 px-3 py-2 text-sm md:col-span-2" data-testid="dealer-customers-contract-notes" />
            <button type="submit" className="h-10 rounded-md bg-slate-900 px-4 text-sm font-semibold text-white md:col-span-2" data-testid="dealer-customers-contract-submit">Sözleşme Ekle</button>
          </form>

          <div className="rounded-md border border-slate-200 overflow-x-auto" data-testid="dealer-customers-contracts-table-wrap">
            <table className="w-full text-sm" data-testid="dealer-customers-contracts-table">
              <thead className="bg-slate-50"><tr><th className="px-3 py-2 text-left">Müşteri</th><th className="px-3 py-2 text-left">Başlık</th><th className="px-3 py-2 text-left">Durum</th><th className="px-3 py-2 text-left">Tarih Aralığı</th><th className="px-3 py-2 text-left">Tutar</th></tr></thead>
              <tbody>{contractItems.length === 0 ? <tr><td className="px-3 py-4 text-slate-600" colSpan={5} data-testid="dealer-customers-contract-empty">Kayıt yok</td></tr> : contractItems.map((item) => <tr key={item.id} className="border-t" data-testid={`dealer-customers-contract-row-${item.id}`}><td className="px-3 py-2">{item.customer_name}<div className="text-xs text-slate-500">{item.customer_email}</div></td><td className="px-3 py-2">{item.title}</td><td className="px-3 py-2">{item.status}</td><td className="px-3 py-2">{item.start_date ? new Date(item.start_date).toLocaleDateString('tr-TR') : '-'} - {item.end_date ? new Date(item.end_date).toLocaleDateString('tr-TR') : '-'}</td><td className="px-3 py-2">{item.amount ?? '-'} {item.currency || ''}</td></tr>)}</tbody>
            </table>
          </div>
        </div>
      ) : null}
    </div>
  );
}
