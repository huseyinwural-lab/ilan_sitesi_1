import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { EmptyState, LoadingState, ErrorState } from '@/components/account/AccountStates';
import { useAuth } from '@/contexts/AuthContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const buildWsUrl = (token) => {
  if (!BACKEND_URL) return null;
  const wsBase = BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://');
  return `${wsBase}/api/ws/messages?token=${token}`;
};

const formatDate = (value) => {
  if (!value) return '-';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return '-';
  return d.toLocaleString('tr-TR');
};

export default function AccountMessages() {
  const { user } = useAuth();
  const [searchParams] = useSearchParams();
  const [threads, setThreads] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loadingThreads, setLoadingThreads] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [error, setError] = useState('');
  const [messageText, setMessageText] = useState('');
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [typingUser, setTypingUser] = useState(null);

  const socketRef = useRef(null);
  const reconnectRef = useRef(null);
  const lastMessageAtRef = useRef(null);

  const authHeader = useMemo(() => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` }), []);

  const fetchThreads = async () => {
    setLoadingThreads(true);
    try {
      const res = await fetch(`${API}/v1/messages/threads`, { headers: authHeader });
      if (!res.ok) {
        throw new Error('Mesajlar yüklenemedi');
      }
      const data = await res.json();
      setThreads(data.items || []);
      if (!activeId && data.items?.length) {
        setActiveId(data.items[0].id);
      }
      setError('');
    } catch (err) {
      setError('Mesajlar yüklenemedi');
    } finally {
      setLoadingThreads(false);
    }
  };

  const fetchMessages = async (threadId, since = null) => {
    if (!threadId) return;
    setLoadingMessages(true);
    try {
      const params = new URLSearchParams();
      if (since) params.set('since', since);
      const res = await fetch(`${API}/v1/messages/threads/${threadId}/messages?${params.toString()}`, { headers: authHeader });
      if (!res.ok) {
        throw new Error('Mesaj detayı alınamadı');
      }
      const data = await res.json();
      const items = data.items || [];
      if (since) {
        setMessages((prev) => [...prev, ...items]);
      } else {
        setMessages(items);
      }
      if (items.length) {
        lastMessageAtRef.current = items[items.length - 1].created_at;
      }
      setError('');
    } catch (err) {
      setError('Mesaj detayı alınamadı');
    } finally {
      setLoadingMessages(false);
    }
  };

  const markRead = async (threadId) => {
    if (!threadId) return;
    try {
      await fetch(`${API}/v1/messages/threads/${threadId}/read`, {
        method: 'POST',
        headers: authHeader,
      });
      setThreads((prev) => prev.map((thread) => (thread.id === threadId ? { ...thread, unread_count: 0 } : thread)));
    } catch (err) {
      // ignore
    }
  };

  const createThreadFromListing = async (listingId) => {
    try {
      const res = await fetch(`${API}/v1/messages/threads`, {
        method: 'POST',
        headers: { ...authHeader, 'Content-Type': 'application/json' },
        body: JSON.stringify({ listing_id: listingId }),
      });
      if (!res.ok) {
        throw new Error('Thread oluşturulamadı');
      }
      const data = await res.json();
      const thread = data.thread;
      setThreads((prev) => {
        const exists = prev.find((item) => item.id === thread.id);
        if (exists) return prev;
        return [thread, ...prev];
      });
      setActiveId(thread.id);
      await fetchMessages(thread.id);
    } catch (err) {
      setError('Mesajlaşma başlatılamadı');
    }
  };

  const connectSocket = () => {
    const token = localStorage.getItem('access_token');
    const wsUrl = buildWsUrl(token);
    if (!wsUrl) return;

    if (socketRef.current) {
      socketRef.current.close();
    }

    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;
    setConnectionStatus('connecting');

    socket.onopen = () => {
      setConnectionStatus('connected');
      if (activeId) {
        socket.send(JSON.stringify({ type: 'subscribe', thread_id: activeId }));
      }
      if (activeId && lastMessageAtRef.current) {
        fetchMessages(activeId, lastMessageAtRef.current);
      }
    };

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === 'message:new') {
          const msg = payload.message;
          if (payload.thread_id === activeId) {
            setMessages((prev) => [...prev, msg]);
            lastMessageAtRef.current = msg.created_at;
            markRead(activeId);
          } else {
            setThreads((prev) =>
              prev.map((thread) =>
                thread.id === payload.thread_id
                  ? {
                      ...thread,
                      last_message: msg.body,
                      last_message_at: msg.created_at,
                      unread_count: (thread.unread_count || 0) + 1,
                    }
                  : thread
              )
            );
          }
        }
        if (payload.type === 'message:read' && payload.thread_id && payload.user_id === user?.id) {
          setThreads((prev) =>
            prev.map((thread) =>
              thread.id === payload.thread_id ? { ...thread, unread_count: 0 } : thread
            )
          );
        }
        if (payload.type === 'typing:start' && payload.thread_id === activeId) {
          setTypingUser(payload.user_id);
        }
        if (payload.type === 'typing:stop' && payload.thread_id === activeId) {
          setTypingUser(null);
        }
      } catch (err) {
        // ignore
      }
    };

    socket.onclose = () => {
      setConnectionStatus('disconnected');
      if (reconnectRef.current) {
        clearTimeout(reconnectRef.current);
      }
      reconnectRef.current = setTimeout(() => {
        connectSocket();
      }, 2000);
    };
  };

  useEffect(() => {
    fetchThreads();
    connectSocket();
    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
      if (reconnectRef.current) {
        clearTimeout(reconnectRef.current);
      }
    };
  }, []);

  useEffect(() => {
    const listingId = searchParams.get('listing');
    const threadId = searchParams.get('thread');
    if (threadId) {
      setActiveId(threadId);
      return;
    }
    if (listingId) {
      createThreadFromListing(listingId);
    }
  }, [searchParams]);

  useEffect(() => {
    if (!activeId) return;
    fetchMessages(activeId);
    markRead(activeId);
    if (socketRef.current && connectionStatus === 'connected') {
      socketRef.current.send(JSON.stringify({ type: 'subscribe', thread_id: activeId }));
    }
  }, [activeId]);

  const activeThread = useMemo(() => threads.find((t) => t.id === activeId), [threads, activeId]);

  const handleSend = async () => {
    if (!messageText.trim() || !activeId) return;
    const clientMessageId = (crypto?.randomUUID && crypto.randomUUID()) || `msg-${Date.now()}`;
    const payload = { body: messageText.trim(), client_message_id: clientMessageId };
    try {
      const res = await fetch(`${API}/v1/messages/threads/${activeId}/messages`, {
        method: 'POST',
        headers: { ...authHeader, 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        throw new Error('Mesaj gönderilemedi');
      }
      const data = await res.json();
      setMessages((prev) => [...prev, data.message]);
      lastMessageAtRef.current = data.message.created_at;
      setMessageText('');
      setThreads((prev) =>
        prev.map((thread) =>
          thread.id === activeId
            ? { ...thread, last_message: data.message.body, last_message_at: data.message.created_at }
            : thread
        )
      );
    } catch (err) {
      setError('Mesaj gönderilemedi');
    }
  };

  const handleTyping = () => {
    if (socketRef.current && connectionStatus === 'connected' && activeId) {
      socketRef.current.send(JSON.stringify({ type: 'typing:start', thread_id: activeId }));
      setTimeout(() => {
        if (socketRef.current && connectionStatus === 'connected') {
          socketRef.current.send(JSON.stringify({ type: 'typing:stop', thread_id: activeId }));
        }
      }, 800);
    }
  };

  if (loadingThreads) {
    return <LoadingState label="Mesajlar yükleniyor..." />;
  }

  if (error && threads.length === 0) {
    return <ErrorState message={error} onRetry={fetchThreads} testId="account-messages-error" />;
  }

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
          <div className="text-xs text-muted-foreground" data-testid="account-messages-connection">
            Bağlantı: {connectionStatus}
          </div>
        </div>
        <div className="divide-y" data-testid="account-messages-list-items">
          {threads.map((thread) => (
            <button
              key={thread.id}
              type="button"
              onClick={() => setActiveId(thread.id)}
              className={`w-full text-left px-4 py-3 hover:bg-muted/40 ${activeId === thread.id ? 'bg-muted/30' : ''}`}
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
                {thread.last_message || 'Yeni konuşma'}
              </div>
              <div className="text-[11px] text-muted-foreground" data-testid={`account-message-thread-time-${thread.id}`}>
                {thread.last_message_at ? formatDate(thread.last_message_at) : '-'}
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
              {loadingMessages ? (
                <div className="text-sm text-muted-foreground" data-testid="account-message-thread-loading">Yükleniyor...</div>
              ) : messages.length === 0 ? (
                <div className="text-sm text-muted-foreground" data-testid="account-message-thread-empty">Henüz mesaj yok.</div>
              ) : (
                messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`max-w-[70%] rounded-lg px-3 py-2 text-sm ${
                      msg.sender_id === user?.id ? 'ml-auto bg-primary text-primary-foreground' : 'bg-muted'
                    }`}
                    data-testid={`account-message-${msg.id}`}
                  >
                    {msg.body}
                    <div className="mt-1 text-[10px] opacity-70" data-testid={`account-message-time-${msg.id}`}>
                      {formatDate(msg.created_at)}
                    </div>
                  </div>
                ))
              )}
              {typingUser && (
                <div className="text-xs text-muted-foreground" data-testid="account-message-typing">Karşı taraf yazıyor...</div>
              )}
            </div>
            <div className="border-t p-3 flex items-center gap-2" data-testid="account-message-input">
              <input
                value={messageText}
                onChange={(e) => setMessageText(e.target.value)}
                onKeyUp={handleTyping}
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
