import { useEffect, useMemo, useState } from 'react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

export const usePermissionFlags = (country = '') => {
  const [loading, setLoading] = useState(true);
  const [enabled, setEnabled] = useState(false);
  const [domains, setDomains] = useState({});

  const authHeader = useMemo(
    () => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` }),
    [],
  );

  useEffect(() => {
    let mounted = true;

    const fetchPermissions = async () => {
      try {
        const params = country ? { country } : {};
        const response = await axios.get(`${API}/api/admin/permissions/me`, { headers: authHeader, params });
        if (!mounted) return;
        setEnabled(Boolean(response.data?.permission_flags_enabled));
        setDomains(response.data?.domains || {});
      } catch (error) {
        if (!mounted) return;
        setEnabled(false);
        setDomains({});
      } finally {
        if (mounted) setLoading(false);
      }
    };

    fetchPermissions();
    return () => {
      mounted = false;
    };
  }, [authHeader, country]);

  const can = (domain, action, fallback = false) => {
    if (!enabled) return fallback;
    return Boolean(domains?.[domain]?.[action]);
  };

  return {
    loading,
    enabled,
    domains,
    can,
  };
};