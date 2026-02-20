import React, { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { EmptyState } from '@/components/account/AccountStates';

const readThreads = () => {
  try {
    return JSON.parse(localStorage.getItem('account_messages') || '[]');
  } catch (e) {
    return [];
  }
};

const saveThreads = (threads) => {
  localStorage.setItem('account_messages', JSON.stringify(threads));
};

export default function AccountMessages() {
  const [searchParams] = useSearchParams();
  const [threads, setThreads] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [messageText, setMessageText] = useState('');

  useEffect(() => {
    const initial = readThreads();
    const listingId = searchParams.get('listing');
    if (listingId) {
      const existing = initial.find((t) => t.listing_id === listingId);
      if (!existing) {
        const newThread = {
          id: `thread-${Date.now()}`,
          listing_id: listingId,
          listing_title: `İlan #${listingId}`,
          last_message: 'Yeni mesaj başlatıldı',
          last_at: new Date().toISOString(),
          unread_count: 0,
          messages: [],
        };
        initial.unshift(newThread);
        saveThreads(initial);
      }
    }
    setThreads(initial);
    if (initial.length > 0) {
      setActiveId(initial[0].id);
    }
  }, [searchParams]);

  const activeThread = useMemo(() => threads.find((t) => t.id === activeId), [threads, activeId]);

  const handleSelect = (threadId) => {
    const next = threads.map((t) =>
      t.id === threadId ? { ...t, unread_count: 0 } : t
    );
    setThreads(next);
    saveThreads(next);
    setActiveId(threadId);
  };

  const handleSend = () => {
    if (!messageText.trim() || !activeThread) return;
    const newMessage = {
      id: `msg-${Date.now()}`,
      sender: 'me',
      body: messageText.trim(),
      created_at: new Date().toISOString(),
    };
    const next = threads.map((t) => {
      if (t.id !== activeThread.id) return t;
      return {
        ...t,
        last_message: newMessage.body,
        last_at: newMessage.created_at,
        messages: [...(t.messages || []), newMessage],
      };
    });
    setThreads(next);
    saveThreads(next);
    setMessageText('');
  };

  if (threads.length === 0) {
    return (
      <EmptyState
        title="Mesaj yok"
        description="Henüz mesajlaşma başlatılmadı."
        testId="account-messages-empty"
      />
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-4" data-testid="account-messages">
      <div className="rounded-lg border bg-white" data-testid="account-messages-list">
        <div className="border-b px-4 py-3" data-testid="account-messages-list-header">
          <div className="text-sm font-semibold" data-testid="account-messages-title">Mesajlar</div>
        </div>
        <div className="divide-y" data-testid="account-messages-list-items">
          {threads.map((thread) => (
            <button
              key={thread.id}
              type="button"
              onClick={() => handleSelect(thread.id)}
              className={`w-full text-left px-4 py-3 hover:bg-muted/40 ${
                activeId === thread.id ? 'bg-muted/30' : ''
              }`}
              data-testid={`account-message-thread-${thread.id}`}
            >
              <div className="flex items-center justify-between">
                <div className="font-medium" data-testid={`account-message-thread-title-${thread.id}`}>
                  {thread.listing_title || 'Mesaj'}
                </div>
                {thread.unread_count > 0 && (
                  <span className="rounded-full bg-primary px-2 py-0.5 text-xs text-primary-foreground" data-testid={`account-message-thread-unread-${thread.id}`}>
                    {thread.unread_count}
                  </span>
                )}
              </div>
              <div className="text-xs text-muted-foreground line-clamp-1" data-testid={`account-message-thread-preview-${thread.id}`}>
                {thread.last_message}
              </div>
            </button>
          ))}
        </div>
      </div>

      <div className="rounded-lg border bg-white flex flex-col" data-testid="account-message-thread">
        {activeThread ? (
          <>
            <div className="border-b px-4 py-3" data-testid="account-message-thread-header">
              <div className="text-sm font-semibold" data-testid="account-message-thread-header-title">
                {activeThread.listing_title || 'Mesaj Detayı'}
              </div>
              <div className="text-xs text-muted-foreground" data-testid="account-message-thread-header-sub">
                İlan: {activeThread.listing_id || '-'}
              </div>
            </div>
            <div className="flex-1 overflow-auto p-4 space-y-3" data-testid="account-message-thread-body">
              {(activeThread.messages || []).length === 0 ? (
                <div className="text-sm text-muted-foreground" data-testid="account-message-thread-empty">Henüz mesaj yok.</div>
              ) : (
                activeThread.messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`max-w-[70%] rounded-lg px-3 py-2 text-sm ${
                      msg.sender === 'me' ? 'ml-auto bg-primary text-primary-foreground' : 'bg-muted'
                    }`}
                    data-testid={`account-message-${msg.id}`}
                  >
                    {msg.body}
                    <div className="mt-1 text-[10px] opacity-70" data-testid={`account-message-time-${msg.id}`}>
                      {new Date(msg.created_at).toLocaleString('tr-TR')}
                    </div>
                  </div>
                ))
              )}
            </div>
            <div className="border-t p-3 flex items-center gap-2" data-testid="account-message-input">
              <input
                value={messageText}
                onChange={(e) => setMessageText(e.target.value)}
                placeholder="Mesaj yazın"
                className="flex-1 h-10 rounded-md border px-3 text-sm"
                data-testid="account-message-input-field"
              />
              <button
                type="button"
                onClick={handleSend}
                className="h-10 px-4 rounded-md bg-primary text-primary-foreground text-sm"
                data-testid="account-message-send"
              >
                Gönder
              </button>
            </div>
          </>
        ) : (
          <div className="p-6 text-sm text-muted-foreground" data-testid="account-message-no-selection">
            Bir konuşma seçin.
          </div>
        )}
      </div>
    </div>
  );
}
