import { useEffect, useMemo, useState } from 'react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const defaultHeaderConfig = {
  rows: [],
  logo: {
    url: null,
    fallback_text: 'ANNONCIA',
    aspect_ratio: '3:1',
  },
};

const extractLogoUrl = (configData) => {
  const logoUrl = configData?.logo?.url;
  if (typeof logoUrl === 'string' && logoUrl.trim()) {
    return logoUrl.trim();
  }
  return null;
};

export const useUIHeaderConfig = ({ segment = 'individual', tenantId = '', userId = '', authRequired = false } = {}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [configData, setConfigData] = useState(defaultHeaderConfig);
  const [sourceScope, setSourceScope] = useState('default');

  const tenantPart = useMemo(() => (tenantId || '').trim(), [tenantId]);
  const userPart = useMemo(() => (userId || '').trim(), [userId]);

  useEffect(() => {
    let active = true;
    const controller = new AbortController();

    const loadConfig = async () => {
      setLoading(true);
      setError('');
      try {
        const params = new URLSearchParams();
        params.set('segment', segment);
        if (tenantPart) params.set('tenant_id', tenantPart);
        if (userPart) params.set('user_id', userPart);

        const headers = {};
        if (authRequired) {
          headers.Authorization = `Bearer ${localStorage.getItem('access_token')}`;
        }

        const response = await fetch(`${API}/ui/header?${params.toString()}`, {
          signal: controller.signal,
          headers,
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
          const detail = payload?.detail;
          if (detail && typeof detail === 'object') {
            throw new Error(detail.message || 'Header config okunamadı');
          }
          throw new Error(detail || 'Header config okunamadı');
        }

        if (!active) return;
        setConfigData(payload?.config_data || defaultHeaderConfig);
        setSourceScope(payload?.source_scope || 'default');
      } catch (requestError) {
        if (!active) return;
        setConfigData(defaultHeaderConfig);
        setSourceScope('default');
        setError(requestError.message || 'Header config okunamadı');
      } finally {
        if (active) setLoading(false);
      }
    };

    loadConfig();
    return () => {
      active = false;
      controller.abort();
    };
  }, [segment, tenantPart, userPart, authRequired]);

  return {
    loading,
    error,
    configData,
    sourceScope,
    logoUrl: extractLogoUrl(configData),
  };
};
