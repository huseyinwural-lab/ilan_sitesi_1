import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function DealerMessages() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [items, setItems] = useState([]);
  const [notificationItems, setNotificationItems] = useState([]);
  const [summary, setSummary] = useState({ listing_messages: 0, notifications: 0 });
  const [activeTab, setActiveTab] = useState('listing');
  const [searchInput, setSearchInput] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  const formatDate = (value) => {
    if (!value) return '-';
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return '-';
    return parsed.toLocaleString('tr-TR');
  };

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
      setNotificationItems(Array.isArray(payload?.notification_items) ? payload.notification_items : []);
      setSummary(payload?.summary || { listing_messages: 0, notifications: 0 });
    } catch (err) {
      setError(err?.message || 'Mesajlar alınamadı');
      setItems([]);
      setNotificationItems([]);
      setSummary({ listing_messages: 0, notifications: 0 });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItems();
  }, []);

  const filteredListingItems = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return items;
    return items.filter((item) => {
      return [item.buyer_email, item.listing_title, item.last_message]
        .filter(Boolean)
        .some((value) => `${value}`.toLowerCase().includes(q));
    });
  }, [items, searchQuery]);

  const filteredNotificationItems = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return notificationItems;
    return notificationItems.filter((item) => {
      return [item.title, item.message, item.source_type]
        .filter(Boolean)
        .some((value) => `${value}`.toLowerCase().includes(q));
    });
  }, [notificationItems, searchQuery]);

  const handleApplyFilter = () => {
    setSearchQuery(searchInput);
  };

  return (
    <div className="space-y-4" data-testid="dealer-messages-page">
      <div className="flex flex-wrap items-center justify-between gap-3" data-testid="dealer-messages-header">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900" data-testid="dealer-messages-title">İlan Mesajlarım ({summary.listing_messages || 0})</h1>
          <p className="text-sm font-medium text-slate-700" data-testid="dealer-messages-subtitle">Mesaj ve bilgilendirme akışını tek ekrandan yönetin.</p>
        </div>
        <button
          type="button"
          onClick={fetchItems}
          className="h-9 rounded-md border border-slate-300 px-3 text-sm font-semibold text-slate-900"
          data-testid="dealer-messages-refresh-button"
        >
          Yenile
        </button>
      </div>
      {error && <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700" data-testid="dealer-messages-error">{error}</div>}

      <div className="rounded-lg border border-slate-200 bg-white p-4" data-testid="dealer-messages-toolbar">
        <div className="flex flex-wrap items-center gap-2" data-testid="dealer-messages-tab-wrap">
          <button
            type="button"
            onClick={() => setActiveTab('listing')}
            className={`rounded-full border px-3 py-1.5 text-xs font-semibold ${activeTab === 'listing' ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-300 text-slate-800'}`}
            data-testid="dealer-messages-tab-listing"
          >
            Yayında Olan İlanlar ({summary.listing_messages || 0})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('notifications')}
            className={`rounded-full border px-3 py-1.5 text-xs font-semibold ${activeTab === 'notifications' ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-300 text-slate-800'}`}
            data-testid="dealer-messages-tab-notifications"
          >
            Bilgilendirmeler ({summary.notifications || 0})
          </button>
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-2" data-testid="dealer-messages-filter-row">
          <input
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            placeholder="Kullanıcı / ilan / mesaj ara"
            className="h-10 min-w-[260px] rounded-md border border-slate-300 px-3 text-sm text-slate-900"
            data-testid="dealer-messages-search-input"
          />
          <button
            type="button"
            onClick={handleApplyFilter}
            className="h-10 rounded-md border border-slate-300 px-3 text-sm font-semibold text-slate-900"
            data-testid="dealer-messages-filter-button"
          >
            Filtrele
          </button>
        </div>
      </div>

      <div className="rounded-md border border-slate-200 overflow-x-auto" data-testid="dealer-messages-table-wrap">
        {activeTab === 'listing' ? (
          <table className="w-full text-sm" data-testid="dealer-messages-table-listing">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-3 py-2 text-left text-slate-800">Kullanıcı</th>
                <th className="px-3 py-2 text-left text-slate-800">İlan</th>
                <th className="px-3 py-2 text-left text-slate-800">Mesaj</th>
                <th className="px-3 py-2 text-left text-slate-800">Mesaj Sayısı</th>
                <th className="px-3 py-2 text-left text-slate-800">Son Mesaj</th>
                <th className="px-3 py-2 text-left text-slate-800">İşlem</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td className="px-3 py-4" colSpan={6} data-testid="dealer-messages-loading">Yükleniyor...</td></tr>
              ) : filteredListingItems.length === 0 ? (
                <tr><td className="px-3 py-4 text-slate-600" colSpan={6} data-testid="dealer-messages-empty">Kayıt yok</td></tr>
              ) : (
                filteredListingItems.map((item) => (
                  <tr key={item.conversation_id} className="border-t" data-testid={`dealer-message-row-${item.conversation_id}`}>
                    <td className="px-3 py-2 font-medium text-slate-900" data-testid={`dealer-message-buyer-${item.conversation_id}`}>{item.buyer_email || '-'}</td>
                    <td className="px-3 py-2" data-testid={`dealer-message-listing-${item.conversation_id}`}>{item.listing_title || item.listing_id || '-'}</td>
                    <td className="px-3 py-2" data-testid={`dealer-message-last-${item.conversation_id}`}>{item.last_message || '-'}</td>
                    <td className="px-3 py-2 font-semibold" data-testid={`dealer-message-count-${item.conversation_id}`}>{item.message_count}</td>
                    <td className="px-3 py-2" data-testid={`dealer-message-last-at-${item.conversation_id}`}>{formatDate(item.last_message_at)}</td>
                    <td className="px-3 py-2" data-testid={`dealer-message-action-${item.conversation_id}`}>
                      <button
                        type="button"
                        onClick={() => navigate('/dealer/messages')}
                        className="rounded border border-slate-300 px-2 py-1 text-xs font-semibold text-slate-900"
                        data-testid={`dealer-message-open-${item.conversation_id}`}
                      >
                        Aç
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        ) : (
          <table className="w-full text-sm" data-testid="dealer-messages-table-notifications">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-3 py-2 text-left text-slate-800">Başlık</th>
                <th className="px-3 py-2 text-left text-slate-800">Mesaj</th>
                <th className="px-3 py-2 text-left text-slate-800">Kaynak</th>
                <th className="px-3 py-2 text-left text-slate-800">Tarih</th>
                <th className="px-3 py-2 text-left text-slate-800">Durum</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td className="px-3 py-4" colSpan={5} data-testid="dealer-notifications-loading">Yükleniyor...</td></tr>
              ) : filteredNotificationItems.length === 0 ? (
                <tr><td className="px-3 py-4 text-slate-600" colSpan={5} data-testid="dealer-notifications-empty">Bilgilendirme yok</td></tr>
              ) : (
                filteredNotificationItems.map((item) => (
                  <tr key={item.notification_id} className="border-t" data-testid={`dealer-notification-row-${item.notification_id}`}>
                    <td className="px-3 py-2 font-medium text-slate-900" data-testid={`dealer-notification-title-${item.notification_id}`}>{item.title || '-'}</td>
                    <td className="px-3 py-2" data-testid={`dealer-notification-message-${item.notification_id}`}>{item.message || '-'}</td>
                    <td className="px-3 py-2" data-testid={`dealer-notification-source-${item.notification_id}`}>{item.source_type || '-'}</td>
                    <td className="px-3 py-2" data-testid={`dealer-notification-date-${item.notification_id}`}>{formatDate(item.created_at)}</td>
                    <td className="px-3 py-2" data-testid={`dealer-notification-read-${item.notification_id}`}>{item.read ? 'Okundu' : 'Yeni'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
