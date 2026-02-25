import { createContext, useContext, useEffect, useState } from 'react';
import { DEFAULT_THEME_CONFIG } from '@/data/themeDefaults';
import { applyThemeConfig, normalizeThemeConfig } from '@/lib/themeUtils';

const ThemeContext = createContext(null);

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

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
    const stored = localStorage.getItem('theme');
    const preferred = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    const initialTheme = stored || preferred;
    document.documentElement.classList.remove('light', 'dark');
    document.documentElement.classList.add(initialTheme);
    document.documentElement.dataset.theme = initialTheme;
    return initialTheme;
  });
  const [themeConfig, setThemeConfig] = useState(() => readStoredThemeConfig());
  const [themeStatus, setThemeStatus] = useState('idle');

  useEffect(() => {
    localStorage.setItem('theme', theme);
    document.documentElement.classList.remove('light', 'dark');
    document.documentElement.classList.add(theme);
    document.documentElement.dataset.theme = theme;
  }, [theme]);

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
    setTheme(prev => (prev === 'dark' ? 'light' : 'dark'));
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
