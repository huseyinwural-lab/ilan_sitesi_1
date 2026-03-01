import { createContext, useContext, useEffect, useState } from 'react';
import { DEFAULT_THEME_CONFIG } from '@/data/themeDefaults';
import { applyThemeConfig, normalizeThemeConfig } from '@/lib/themeUtils';

const ThemeContext = createContext(null);

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const THEME_STORAGE_KEY = 'theme';
const VALID_THEME_SET = new Set(['light', 'dark']);

const resolveSystemTheme = () => {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
    return 'light';
  }
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
};

const normalizeThemeValue = (value) => (VALID_THEME_SET.has(value) ? value : 'light');

const applyThemeMode = (nextTheme) => {
  if (typeof document === 'undefined') return;
  const normalized = normalizeThemeValue(nextTheme);
  const root = document.documentElement;
  const body = document.body;

  root.classList.toggle('dark', normalized === 'dark');
  root.classList.remove(normalized === 'dark' ? 'light' : 'dark');
  root.dataset.theme = normalized;
  root.style.colorScheme = normalized;

  if (body) {
    body.classList.remove('light', 'dark');
    body.classList.add(normalized);
    body.dataset.theme = normalized;
  }
};

const resolveInitialTheme = () => {
  try {
    const stored = localStorage.getItem(THEME_STORAGE_KEY);
    if (VALID_THEME_SET.has(stored)) {
      return stored;
    }
  } catch (_error) {
    // no-op
  }
  return resolveSystemTheme();
};

const readStoredThemeConfig = () => {
  const stored = localStorage.getItem('site_theme_config');
  if (!stored) return DEFAULT_THEME_CONFIG;
  try {
    const parsed = JSON.parse(stored);
    if (parsed?.config) {
      return normalizeThemeConfig(parsed.config);
    }
    return normalizeThemeConfig(parsed);
  } catch (error) {
    return DEFAULT_THEME_CONFIG;
  }
};

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => {
    const initialTheme = resolveInitialTheme();
    applyThemeMode(initialTheme);
    return initialTheme;
  });
  const [themeConfig, setThemeConfig] = useState(() => readStoredThemeConfig());
  const [themeStatus, setThemeStatus] = useState('idle');

  useEffect(() => {
    try {
      localStorage.setItem(THEME_STORAGE_KEY, theme);
    } catch (_error) {
      // no-op
    }
    applyThemeMode(theme);
  }, [theme]);

  useEffect(() => {
    const handleStorage = (event) => {
      if (event.key !== THEME_STORAGE_KEY) return;
      if (!VALID_THEME_SET.has(event.newValue)) return;
      setTheme(event.newValue);
    };
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, []);

  useEffect(() => {
    applyThemeConfig(themeConfig, document.documentElement);
  }, [themeConfig]);

  const refreshThemeConfig = async () => {
    try {
      setThemeStatus('loading');
      const res = await fetch(`${API}/site/theme`);
      if (!res.ok) {
        setThemeStatus('error');
        return;
      }
      const data = await res.json();
      const normalized = normalizeThemeConfig(data?.config || data);
      setThemeConfig(normalized);
      localStorage.setItem('site_theme_config', JSON.stringify({
        config: normalized,
        version: data?.version || 0,
        updated_at: data?.updated_at || null,
      }));
      setThemeStatus('ok');
    } catch (error) {
      setThemeStatus('error');
    }
  };

  useEffect(() => {
    refreshThemeConfig();
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      refreshThemeConfig();
    }, 10 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  return (
    <ThemeContext.Provider value={{ theme, setTheme, toggleTheme, themeConfig, themeStatus, refreshThemeConfig }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
