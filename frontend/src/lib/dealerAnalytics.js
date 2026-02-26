const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const DEALER_ANALYTICS_SESSION_KEY = 'dealer_analytics_session_id';

const getSessionId = () => {
  const existing = localStorage.getItem(DEALER_ANALYTICS_SESSION_KEY);
  if (existing) return existing;
  const next = (window.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(16).slice(2)}`);
  localStorage.setItem(DEALER_ANALYTICS_SESSION_KEY, next);
  return next;
};

export const trackDealerEvent = async (eventName, metadata = {}, page = window.location.pathname) => {
  const token = localStorage.getItem('access_token');
  if (!token) return;

  try {
    await fetch(`${API}/analytics/events`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        event_name: eventName,
        session_id: getSessionId(),
        page,
        metadata,
      }),
    });
  } catch {
    // no-op
  }
};
