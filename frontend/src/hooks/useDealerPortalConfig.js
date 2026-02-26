import { useCallback, useEffect, useState } from 'react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const useDealerPortalConfig = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [headerItems, setHeaderItems] = useState([]);
  const [headerRow1Items, setHeaderRow1Items] = useState([]);
  const [headerRow1FixedBlocks, setHeaderRow1FixedBlocks] = useState([]);
  const [headerRow2Modules, setHeaderRow2Modules] = useState([]);
  const [headerRow3Controls, setHeaderRow3Controls] = useState({
    store_filter_enabled: true,
    user_dropdown_enabled: true,
    stores: [{ key: 'all', label: 'Tüm Mağazalar' }],
    default_store_key: 'all',
  });
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
      setHeaderRow1Items(Array.isArray(payload?.header_row1_items) ? payload.header_row1_items : (Array.isArray(payload?.header_items) ? payload.header_items : []));
      setHeaderRow1FixedBlocks(Array.isArray(payload?.header_row1_fixed_blocks) ? payload.header_row1_fixed_blocks : []);
      setHeaderRow2Modules(Array.isArray(payload?.header_row2_modules) ? payload.header_row2_modules : (Array.isArray(payload?.modules) ? payload.modules : []));
      setHeaderRow3Controls(payload?.header_row3_controls || {
        store_filter_enabled: true,
        user_dropdown_enabled: true,
        stores: [{ key: 'all', label: 'Tüm Mağazalar' }],
        default_store_key: 'all',
      });
      setSidebarItems(Array.isArray(payload?.sidebar_items) ? payload.sidebar_items : []);
      setModules(Array.isArray(payload?.modules) ? payload.modules : []);
    } catch (err) {
      setError(err?.message || 'Dealer portal config yüklenemedi');
      setHeaderItems([]);
      setHeaderRow1Items([]);
      setHeaderRow1FixedBlocks([]);
      setHeaderRow2Modules([]);
      setHeaderRow3Controls({
        store_filter_enabled: true,
        user_dropdown_enabled: true,
        stores: [{ key: 'all', label: 'Tüm Mağazalar' }],
        default_store_key: 'all',
      });
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
    headerRow1Items,
    headerRow1FixedBlocks,
    headerRow2Modules,
    headerRow3Controls,
    sidebarItems,
    modules,
    refresh: fetchConfig,
  };
};
