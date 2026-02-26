import React, { useEffect, useState } from 'react';
import { trackDealerEvent } from '@/lib/dealerAnalytics';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function DealerCustomers() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [items, setItems] = useState([]);

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
    } catch (err) {
      setError(err?.message || 'Müşteri listesi alınamadı');
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItems();
  }, []);

  return (
    <div className="space-y-4" data-testid="dealer-customers-page">
      <div className="flex items-center justify-between" data-testid="dealer-customers-header">
        <h1 className="text-xl font-semibold" data-testid="dealer-customers-title">Müşteriler</h1>
        <button onClick={fetchItems} className="h-9 rounded-md border px-3 text-sm" data-testid="dealer-customers-refresh-button">Yenile</button>
      </div>
      {error && <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700" data-testid="dealer-customers-error">{error}</div>}

      <div className="rounded-md border overflow-x-auto" data-testid="dealer-customers-table-wrap">
        <table className="w-full text-sm" data-testid="dealer-customers-table">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-3 py-2 text-left">Müşteri</th>
              <th className="px-3 py-2 text-left">Konuşma</th>
              <th className="px-3 py-2 text-left">Mesaj</th>
              <th className="px-3 py-2 text-left">Son İletişim</th>
              <th className="px-3 py-2 text-left">Aksiyon</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td className="px-3 py-4" colSpan={5} data-testid="dealer-customers-loading">Yükleniyor...</td></tr>
            ) : items.length === 0 ? (
              <tr><td className="px-3 py-4 text-slate-500" colSpan={5} data-testid="dealer-customers-empty">Kayıt yok</td></tr>
            ) : (
              items.map((item) => (
                <tr key={item.customer_id} className="border-t" data-testid={`dealer-customer-row-${item.customer_id}`}>
                  <td className="px-3 py-2" data-testid={`dealer-customer-email-${item.customer_id}`}>{item.customer_email || item.customer_name || item.customer_id}</td>
                  <td className="px-3 py-2" data-testid={`dealer-customer-conversations-${item.customer_id}`}>{item.conversation_count}</td>
                  <td className="px-3 py-2" data-testid={`dealer-customer-messages-${item.customer_id}`}>{item.total_messages}</td>
                  <td className="px-3 py-2" data-testid={`dealer-customer-last-contact-${item.customer_id}`}>{item.last_contact_at || '-'}</td>
                  <td className="px-3 py-2">
                    <button
                      type="button"
                      onClick={() => trackDealerEvent('dealer_contact_click', { customer_id: item.customer_id })}
                      className="h-8 rounded-md border px-2 text-xs"
                      data-testid={`dealer-customer-contact-click-${item.customer_id}`}
                    >
                      İletişim Tıkla
                    </button>
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
