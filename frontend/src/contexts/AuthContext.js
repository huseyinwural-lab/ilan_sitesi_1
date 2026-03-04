import { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const EMERGENT_AUTH_URL = 'https://auth.emergentagent.com/';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('access_token'));

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    const handleStorage = (event) => {
      if (event.key === 'access_token' && !event.newValue) {
        delete axios.defaults.headers.common['Authorization'];
        localStorage.removeItem('token');
        setToken(null);
        setUser(null);
      }
    };
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, []);

  const fetchUser = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
      return response.data;
    } catch (error) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('token');
      setToken(null);
      delete axios.defaults.headers.common['Authorization'];
      return null;
    } finally {
      setLoading(false);
    }
  };

  const refreshUser = async () => {
    return fetchUser();
  };

  const applySession = (payload) => {
    if (!payload) return null;
    const { access_token, refresh_token, user: userData } = payload;
    if (!access_token || !refresh_token) return null;

    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    localStorage.setItem('token', access_token);
    axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

    setToken(access_token);
    setUser(userData || null);

    return userData || null;
  };

  const login = async (email, password, totpCode) => {
    const payload = { email, password };
    if (totpCode) {
      payload.totp_code = totpCode;
    }
    const response = await axios.post(`${API}/auth/login`, payload);
    return applySession(response.data);
  };

  const startGoogleLogin = (portalScope = 'account') => {
    const resolvedPortal = portalScope === 'dealer' ? 'dealer' : 'account';
    localStorage.setItem('oauth_portal_scope', resolvedPortal);
    const redirectUri = `${window.location.origin}/auth/google/callback`;
    // REMINDER: Emergent auth endpoints are fixed. Do not change URL/method/headers without re-validating against /app/auth_testing.md.
    const authUrl = `${EMERGENT_AUTH_URL}?redirect=${encodeURIComponent(redirectUri)}`;
    window.location.assign(authUrl);
  };

  const loginWithEmergentGoogleSession = async (sessionId, portalScope = 'account') => {
    const response = await axios.post(`${API}/auth/google/emergent/exchange`, {
      session_id: sessionId,
      portal_scope: portalScope,
    });
    return applySession(response.data);
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    setToken(null);
    setUser(null);
  };

  const hasPermission = (roles) => {
    if (!user) return false;
    return roles.includes(user.role);
  };

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      login,
      logout,
      hasPermission,
      token,
      refreshUser,
      applySession,
      startGoogleLogin,
      loginWithEmergentGoogleSession,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
