import React, { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const messageTabs = [
  { key: 'inbox', label: 'Gelen Mesajlar' },
  { key: 'sent', label: 'Gönderilen Mesajlar' },
  { key: 'archive', label: 'Arşiv' },
  { key: 'spam', label: 'Spam' },
];

const formatDate = (value) => {
  if (!value) return '-';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return '-';
  return parsed.toLocaleString('tr-TR');
};

export default function DealerMessages() {
  const [searchParams, setSearchParams] = useSearchParams();
  const requestedFolder = (searchParams.get('folder') || 'inbox').toLowerCase();
  const folder = messageTabs.some((tab) => tab.key === requestedFolder) ? requestedFolder : 'inbox';

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [items, setItems] = useState([]);
  const [summary, setSummary] = useState({ inbox_count: 0, sent_count: 0, archive_count: 0, spam_count: 0, unread_listing_messages: 0 });
  const [searchInput, setSearchInput] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [markingReadId, setMarkingReadId] = useState('');
  const [updatingFolderId, setUpdatingFolderId] = useState('');

  const fetchItems = async (targetFolder = folder) => {
    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`${API}/dealer/messages?folder=${encodeURIComponent(targetFolder)}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(payload?.detail || 'Mesajlar alınamadı');
      setItems(Array.isArray(payload?.items) ? payload.items : []);
      setSummary(payload?.summary || { inbox_count: 0, sent_count: 0, archive_count: 0, spam_count: 0, unread_listing_messages: 0 });
    } catch (requestError) {
      setError(requestError?.message || 'Mesajlar alınamadı');
      setItems([]);
      setSummary({ inbox_count: 0, sent_count: 0, archive_count: 0, spam_count: 0, unread_listing_messages: 0 });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItems(folder);
  }, [folder]);

  const filteredItems = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return items;
    return items.filter((item) => [item.buyer_email, item.listing_title, item.last_message].filter(Boolean).some((value) => `${value}`.toLowerCase().includes(q)));
  }, [items, searchQuery]);

  const moveFolder = async (conversationId, nextFolder) => {
    if (!conversationId) return;
    setUpdatingFolderId(conversationId);
    setError('');
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`${API}/dealer/messages/${conversationId}/folder`, {
        method: 'PATCH',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ folder: nextFolder }),
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(payload?.detail || 'Mesaj klasörü güncellenemedi');
      await fetchItems(folder);
    } catch (requestError) {
      setError(requestError?.message || 'Mesaj klasörü güncellenemedi');
    } finally {
      setUpdatingFolderId('');
    }
  };

  const handleMarkAsRead = async (conversationId) => {
    if (!conversationId) return;
    setMarkingReadId(conversationId);
    setError('');
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`${API}/dealer/messages/${conversationId}/read`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(payload?.detail || 'Okundu bilgisi güncellenemedi');
      await fetchItems(folder);
    } catch (requestError) {
      setError(requestError?.message || 'Okundu bilgisi güncellenemedi');
    } finally {
      setMarkingReadId('');
    }
  };

  const folderCountMap = {
    inbox: Number(summary.inbox_count || 0),
    sent: Number(summary.sent_count || 0),
    archive: Number(summary.archive_count || 0),
    spam: Number(summary.spam_count || 0),
  };

  return (
    <div className="space-y-4" data-testid="dealer-messages-page">
      <div className="flex flex-wrap items-center justify-between gap-3" data-testid="dealer-messages-header">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900" data-testid="dealer-messages-title">Mesajlar</h1>
          <p className="text-sm font-medium text-slate-700" data-testid="dealer-messages-subtitle">Okunmamış konuşma: {summary.unread_listing_messages || 0}</p>
        </div>
        <button type="button" onClick={() => fetchItems(folder)} className="h-9 rounded-md border border-slate-300 px-3 text-sm font-semibold text-slate-900" data-testid="dealer-messages-refresh-button">Yenile</button>
      </div>

      {error ? <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700" data-testid="dealer-messages-error">{error}</div> : null}

      <div className="rounded-lg border border-slate-200 bg-white p-4" data-testid="dealer-messages-toolbar">
        <div className="flex flex-wrap items-center gap-2" data-testid="dealer-messages-tab-wrap">
          {messageTabs.map((tab) => (
            <button
              key={tab.key}
              type="button"
              onClick={() => setSearchParams({ folder: tab.key })}
              className={`rounded-full border px-3 py-1.5 text-xs font-semibold ${folder === tab.key ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-300 text-slate-800'}`}
              data-testid={`dealer-messages-tab-${tab.key}`}
            >
              {tab.label} ({folderCountMap[tab.key] || 0})
            </button>
          ))}
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-2" data-testid="dealer-messages-filter-row">
          <input value={searchInput} onChange={(event) => setSearchInput(event.target.value)} placeholder="Kullanıcı / ilan / mesaj ara" className="h-10 min-w-[260px] rounded-md border border-slate-300 px-3 text-sm text-slate-900" data-testid="dealer-messages-search-input" />
          <button type="button" onClick={() => setSearchQuery(searchInput)} className="h-10 rounded-md border border-slate-300 px-3 text-sm font-semibold text-slate-900" data-testid="dealer-messages-filter-button">Filtrele</button>
        </div>
      </div>

      <div className="rounded-md border border-slate-200 overflow-x-auto" data-testid="dealer-messages-table-wrap">
        <table className="w-full text-sm" data-testid="dealer-messages-table">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-3 py-2 text-left text-slate-800">Kullanıcı</th>
              <th className="px-3 py-2 text-left text-slate-800">İlan</th>
              <th className="px-3 py-2 text-left text-slate-800">Son Mesaj</th>
              <th className="px-3 py-2 text-left text-slate-800">Gelen/Giden</th>
              <th className="px-3 py-2 text-left text-slate-800">Tarih</th>
              <th className="px-3 py-2 text-left text-slate-800">Durum</th>
              <th className="px-3 py-2 text-right text-slate-800">İşlem</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td className="px-3 py-4" colSpan={7} data-testid="dealer-messages-loading">Yükleniyor...</td></tr>
            ) : filteredItems.length === 0 ? (
              <tr><td className="px-3 py-4 text-slate-600" colSpan={7} data-testid="dealer-messages-empty">Kayıt yok</td></tr>
            ) : filteredItems.map((item) => (
              <tr key={item.conversation_id} className="border-t" data-testid={`dealer-message-row-${item.conversation_id}`}>
                <td className="px-3 py-2 font-medium text-slate-900" data-testid={`dealer-message-buyer-${item.conversation_id}`}>{item.buyer_email || '-'}</td>
                <td className="px-3 py-2" data-testid={`dealer-message-listing-${item.conversation_id}`}>{item.listing_title || item.listing_id || '-'}</td>
                <td className="px-3 py-2" data-testid={`dealer-message-last-${item.conversation_id}`}>{item.last_message || '-'}</td>
                <td className="px-3 py-2" data-testid={`dealer-message-count-${item.conversation_id}`}>{item.buyer_message_count || 0} / {item.dealer_sent_count || 0}</td>
                <td className="px-3 py-2" data-testid={`dealer-message-last-at-${item.conversation_id}`}>{formatDate(item.last_message_at)}</td>
                <td className="px-3 py-2" data-testid={`dealer-message-read-status-${item.conversation_id}`}>
                  {Number(item.unread_count || 0) > 0 ? (
                    <span className="rounded-full border border-amber-200 bg-amber-50 px-2 py-1 text-xs font-semibold text-amber-700" data-testid={`dealer-message-read-badge-unread-${item.conversation_id}`}>Okunmadı ({item.unread_count})</span>
                  ) : (
                    <span className="rounded-full border border-emerald-200 bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-700" data-testid={`dealer-message-read-badge-read-${item.conversation_id}`}>Okundu</span>
                  )}
                </td>
                <td className="px-3 py-2 text-right" data-testid={`dealer-message-action-${item.conversation_id}`}>
                  <div className="inline-flex flex-wrap items-center justify-end gap-1">
                    {Number(item.unread_count || 0) > 0 ? (
                      <button
                        type="button"
                        onClick={() => handleMarkAsRead(item.conversation_id)}
                        disabled={markingReadId === item.conversation_id}
                        className="rounded border border-slate-300 px-2 py-1 text-xs font-semibold text-slate-900 disabled:opacity-50"
                        data-testid={`dealer-message-mark-read-${item.conversation_id}`}
                      >
                        {markingReadId === item.conversation_id ? 'İşleniyor...' : 'Okundu'}
                      </button>
                    ) : null}

                    {folder !== 'archive' ? (
                      <button type="button" onClick={() => moveFolder(item.conversation_id, 'archive')} disabled={updatingFolderId === item.conversation_id} className="rounded border border-slate-300 px-2 py-1 text-xs font-semibold text-slate-900 disabled:opacity-50" data-testid={`dealer-message-move-archive-${item.conversation_id}`}>Arşivle</button>
                    ) : (
                      <button type="button" onClick={() => moveFolder(item.conversation_id, 'inbox')} disabled={updatingFolderId === item.conversation_id} className="rounded border border-slate-300 px-2 py-1 text-xs font-semibold text-slate-900 disabled:opacity-50" data-testid={`dealer-message-move-inbox-${item.conversation_id}`}>Geri Al</button>
                    )}

                    {folder !== 'spam' ? (
                      <button type="button" onClick={() => moveFolder(item.conversation_id, 'spam')} disabled={updatingFolderId === item.conversation_id} className="rounded border border-rose-200 px-2 py-1 text-xs font-semibold text-rose-700 disabled:opacity-50" data-testid={`dealer-message-move-spam-${item.conversation_id}`}>Spam</button>
                    ) : (
                      <button type="button" onClick={() => moveFolder(item.conversation_id, 'inbox')} disabled={updatingFolderId === item.conversation_id} className="rounded border border-slate-300 px-2 py-1 text-xs font-semibold text-slate-900 disabled:opacity-50" data-testid={`dealer-message-remove-spam-${item.conversation_id}`}>Spamdan Çıkar</button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
