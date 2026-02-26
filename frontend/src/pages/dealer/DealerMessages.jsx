import React, { useEffect, useState } from 'react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function DealerMessages() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [items, setItems] = useState([]);

  const fetchItems = async () => {
    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`${API}/dealer/messages`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(payload?.detail || 'Mesajlar alınamadı');
      setItems(Array.isArray(payload?.items) ? payload.items : []);
    } catch (err) {
      setError(err?.message || 'Mesajlar alınamadı');
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItems();
  }, []);

  return (
    <div className="space-y-4" data-testid="dealer-messages-page">
      <div className="flex items-center justify-between" data-testid="dealer-messages-header">
        <h1 className="text-xl font-semibold" data-testid="dealer-messages-title">Mesajlar</h1>
        <button onClick={fetchItems} className="h-9 rounded-md border px-3 text-sm" data-testid="dealer-messages-refresh-button">Yenile</button>
      </div>
      {error && <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700" data-testid="dealer-messages-error">{error}</div>}

      <div className="rounded-md border overflow-x-auto" data-testid="dealer-messages-table-wrap">
        <table className="w-full text-sm" data-testid="dealer-messages-table">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-3 py-2 text-left">Listing</th>
              <th className="px-3 py-2 text-left">Müşteri</th>
              <th className="px-3 py-2 text-left">Mesaj</th>
              <th className="px-3 py-2 text-left">Mesaj Sayısı</th>
              <th className="px-3 py-2 text-left">Son Mesaj</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td className="px-3 py-4" colSpan={5} data-testid="dealer-messages-loading">Yükleniyor...</td></tr>
            ) : items.length === 0 ? (
              <tr><td className="px-3 py-4 text-slate-500" colSpan={5} data-testid="dealer-messages-empty">Kayıt yok</td></tr>
            ) : (
              items.map((item) => (
                <tr key={item.conversation_id} className="border-t" data-testid={`dealer-message-row-${item.conversation_id}`}>
                  <td className="px-3 py-2" data-testid={`dealer-message-listing-${item.conversation_id}`}>{item.listing_title || item.listing_id || '-'}</td>
                  <td className="px-3 py-2" data-testid={`dealer-message-buyer-${item.conversation_id}`}>{item.buyer_email || '-'}</td>
                  <td className="px-3 py-2" data-testid={`dealer-message-last-${item.conversation_id}`}>{item.last_message || '-'}</td>
                  <td className="px-3 py-2" data-testid={`dealer-message-count-${item.conversation_id}`}>{item.message_count}</td>
                  <td className="px-3 py-2" data-testid={`dealer-message-last-at-${item.conversation_id}`}>{item.last_message_at || '-'}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
