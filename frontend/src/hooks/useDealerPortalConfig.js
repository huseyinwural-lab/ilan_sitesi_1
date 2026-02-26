import { useCallback, useEffect, useState } from 'react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const useDealerPortalConfig = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [headerItems, setHeaderItems] = useState([]);
  const [sidebarItems, setSidebarItems] = useState([]);
  const [modules, setModules] = useState([]);

  const fetchConfig = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`${API}/dealer/portal/config`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        const payload = await res.json().catch(() => ({}));
        throw new Error(payload?.detail || 'Dealer portal config yüklenemedi');
      }
      const payload = await res.json();
      setHeaderItems(Array.isArray(payload?.header_items) ? payload.header_items : []);
      setSidebarItems(Array.isArray(payload?.sidebar_items) ? payload.sidebar_items : []);
      setModules(Array.isArray(payload?.modules) ? payload.modules : []);
    } catch (err) {
      setError(err?.message || 'Dealer portal config yüklenemedi');
      setHeaderItems([]);
      setSidebarItems([]);
      setModules([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  return {
    loading,
    error,
    headerItems,
    sidebarItems,
    modules,
    refresh: fetchConfig,
  };
};
