import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const SUPPORTED_LANGUAGES = ['tr', 'de', 'fr'];
const FALLBACK_LANGUAGE = 'tr';
const AVAILABLE_NAMESPACES = ['common', 'auth', 'dealer', 'admin'];
const ROUTE_CHANGE_EVENT = 'emergent:route-change';
const APP_ENV = String(process.env.REACT_APP_ENVIRONMENT || process.env.NODE_ENV || 'development').toLowerCase();
const IS_PRODUCTION_ENV = APP_ENV === 'production';
const STRICT_MISSING_KEY_MODE = String(process.env.REACT_APP_I18N_STRICT_MODE || '').toLowerCase() === 'true';

const localeLoaders = {
  tr: {
    common: () => import('../locales/tr/common.json'),
    auth: () => import('../locales/tr/auth.json'),
    dealer: () => import('../locales/tr/dealer.json'),
    admin: () => import('../locales/tr/admin.json'),
  },
  de: {
    common: () => import('../locales/de/common.json'),
    auth: () => import('../locales/de/auth.json'),
    dealer: () => import('../locales/de/dealer.json'),
    admin: () => import('../locales/de/admin.json'),
  },
  fr: {
    common: () => import('../locales/fr/common.json'),
    auth: () => import('../locales/fr/auth.json'),
    dealer: () => import('../locales/fr/dealer.json'),
    admin: () => import('../locales/fr/admin.json'),
  },
};

const loadedBundles = new Set();
const pendingBundleLoads = new Map();
let historyPatched = false;
const missingKeyLogCache = new Set();

const normalizeLanguage = (value) => {
  const normalized = String(value || '').trim().toLowerCase();
  return SUPPORTED_LANGUAGES.includes(normalized) ? normalized : FALLBACK_LANGUAGE;
};

const normalizeNamespace = (value) => {
  const normalized = String(value || '').trim().toLowerCase();
  return AVAILABLE_NAMESPACES.includes(normalized) ? normalized : 'common';
};

const readStoredLanguage = () => {
  try {
    return normalizeLanguage(window.localStorage.getItem('language'));
  } catch {
    return FALLBACK_LANGUAGE;
  }
};

const readCurrentPathname = () => {
  try {
    return window.location.pathname || '/';
  } catch {
    return '/';
  }
};

const resolveRouteNamespaces = (pathname) => {
  const path = String(pathname || '').trim().toLowerCase();
  if (path === '/login' || path === '/register' || path === '/verify-email') {
    return ['common', 'auth'];
  }
  if (path === '/dealer' || path === '/dealer/login' || path.startsWith('/dealer/')) {
    return ['common', 'dealer'];
  }
  if (path === '/admin' || path.startsWith('/admin/') || path === '/backoffice' || path.startsWith('/backoffice/')) {
    return ['common', 'admin'];
  }
  return ['common'];
};

const inferNamespaceFromKey = (key) => {
  const normalizedKey = String(key || '').trim();
  if (normalizedKey.startsWith('auth.')) return 'auth';
  if (normalizedKey.startsWith('dealer.')) return 'dealer';
  if (normalizedKey.startsWith('admin.')) return 'admin';
  return 'common';
};

const logMissingKey = ({ key, language, namespace, pathname }) => {
  const cacheKey = `${language}:${namespace}:${pathname}:${key}`;
  if (missingKeyLogCache.has(cacheKey)) {
    return;
  }
  missingKeyLogCache.add(cacheKey);

  const payload = {
    event: 'i18n_missing_key',
    key,
    language,
    namespace,
    pathname,
    env: APP_ENV,
    timestamp: new Date().toISOString(),
  };

  if (IS_PRODUCTION_ENV) {
    console.info('[i18n_missing_key]', payload);
    return;
  }

  console.warn('[i18n_missing_key]', payload);
  if (STRICT_MISSING_KEY_MODE) {
    throw new Error(`i18n missing key: ${key}`);
  }
};

const patchHistoryForRouteEvents = () => {
  if (historyPatched || typeof window === 'undefined') {
    return;
  }

  const dispatch = () => {
    window.dispatchEvent(new Event(ROUTE_CHANGE_EVENT));
  };

  const originalPushState = window.history.pushState.bind(window.history);
  const originalReplaceState = window.history.replaceState.bind(window.history);

  window.history.pushState = (...args) => {
    const result = originalPushState(...args);
    dispatch();
    return result;
  };

  window.history.replaceState = (...args) => {
    const result = originalReplaceState(...args);
    dispatch();
    return result;
  };

  historyPatched = true;
};

const initialLanguage = readStoredLanguage();

if (!i18n.isInitialized) {
  i18n
    .use(initReactI18next)
    .init({
      resources: {},
      lng: initialLanguage,
      fallbackLng: FALLBACK_LANGUAGE,
      interpolation: {
        escapeValue: false,
      },
      react: {
        useSuspense: false,
      },
    })
    .catch(() => undefined);
}

const ensureNamespaceBundle = async (language, namespace) => {
  const normalizedLanguage = normalizeLanguage(language);
  const normalizedNamespace = normalizeNamespace(namespace);
  const cacheKey = `${normalizedLanguage}:${normalizedNamespace}`;

  if (loadedBundles.has(cacheKey)) {
    return cacheKey;
  }

  if (pendingBundleLoads.has(cacheKey)) {
    return pendingBundleLoads.get(cacheKey);
  }

  const loader = localeLoaders[normalizedLanguage]?.[normalizedNamespace];
  if (!loader) {
    return cacheKey;
  }

  const pending = loader()
    .then((module) => {
      const resources = module?.default || module || {};
      i18n.addResourceBundle(normalizedLanguage, 'translation', resources, true, true);
      loadedBundles.add(cacheKey);
      return cacheKey;
    })
    .finally(() => {
      pendingBundleLoads.delete(cacheKey);
    });

  pendingBundleLoads.set(cacheKey, pending);
  return pending;
};

const preloadNamespacesForRoute = async (pathname, language) => {
  const namespaces = resolveRouteNamespaces(pathname);
  if (!namespaces.length) {
    return;
  }

  const unique = Array.from(new Set(namespaces.map(normalizeNamespace)));
  await Promise.all(
    unique.flatMap((namespace) => [
      ensureNamespaceBundle(FALLBACK_LANGUAGE, namespace),
      ensureNamespaceBundle(language, namespace),
    ]),
  );
};

const LanguageContext = createContext(null);

export function LanguageProvider({ children }) {
  const [language, setLanguageState] = useState(initialLanguage);
  const [pathname, setPathname] = useState(readCurrentPathname());
  const [ready, setReady] = useState(false);
  const [bundleVersion, setBundleVersion] = useState(0);
  const activeLoadRef = useRef(new Set());

  useEffect(() => {
    patchHistoryForRouteEvents();

    const syncPath = () => {
      setPathname(readCurrentPathname());
    };

    window.addEventListener(ROUTE_CHANGE_EVENT, syncPath);
    window.addEventListener('popstate', syncPath);
    window.addEventListener('hashchange', syncPath);

    return () => {
      window.removeEventListener(ROUTE_CHANGE_EVENT, syncPath);
      window.removeEventListener('popstate', syncPath);
      window.removeEventListener('hashchange', syncPath);
    };
  }, []);

  useEffect(() => {
    let active = true;

    const bootstrap = async () => {
      const targetLanguage = normalizeLanguage(language);
      await preloadNamespacesForRoute(pathname, targetLanguage);
      await i18n.changeLanguage(targetLanguage);

      try {
        window.localStorage.setItem('language', targetLanguage);
      } catch {
        // noop
      }

      document.documentElement.lang = targetLanguage;

      if (active) {
        setBundleVersion((prev) => prev + 1);
        setReady(true);
      }
    };

    bootstrap().catch(() => {
      if (active) {
        setReady(true);
      }
    });

    return () => {
      active = false;
    };
  }, [language, pathname]);

  useEffect(() => {
    const handleLanguageChange = (nextLanguage) => {
      const normalized = normalizeLanguage(nextLanguage);
      setLanguageState((prev) => (prev === normalized ? prev : normalized));
    };

    i18n.on('languageChanged', handleLanguageChange);
    return () => {
      i18n.off('languageChanged', handleLanguageChange);
    };
  }, []);

  const setLanguage = useCallback((nextLanguage) => {
    setLanguageState(normalizeLanguage(nextLanguage));
  }, []);

  const lazyLoadNamespace = useCallback((namespaceKey) => {
    const namespace = normalizeNamespace(namespaceKey);
    const languageKey = normalizeLanguage(language);
    const cacheKey = `${languageKey}:${namespace}`;

    if (loadedBundles.has(cacheKey) || activeLoadRef.current.has(cacheKey)) {
      return;
    }

    activeLoadRef.current.add(cacheKey);
    Promise.all([
      ensureNamespaceBundle(FALLBACK_LANGUAGE, namespace),
      ensureNamespaceBundle(languageKey, namespace),
    ])
      .then(() => {
        setBundleVersion((prev) => prev + 1);
      })
      .catch(() => undefined)
      .finally(() => {
        activeLoadRef.current.delete(cacheKey);
      });
  }, [language]);

  const t = useCallback((key, fallbackOrOptions = undefined, maybeOptions = undefined) => {
    if (typeof key !== 'string' || !key) {
      return '';
    }

    const baseOptions = { lng: language };
    const keyNamespace = inferNamespaceFromKey(key);
    const exists = i18n.exists(key, baseOptions);

    if (!exists) {
      lazyLoadNamespace(keyNamespace);
      logMissingKey({
        key,
        language,
        namespace: keyNamespace,
        pathname,
      });

      if (IS_PRODUCTION_ENV) {
        return '—';
      }

      if (typeof fallbackOrOptions === 'string' && fallbackOrOptions.trim()) {
        return fallbackOrOptions;
      }
      return '—';
    }

    if (typeof fallbackOrOptions === 'string') {
      return i18n.t(key, { ...baseOptions, defaultValue: fallbackOrOptions, ...(maybeOptions || {}) });
    }
    if (fallbackOrOptions && typeof fallbackOrOptions === 'object') {
      return i18n.t(key, { ...baseOptions, ...fallbackOrOptions });
    }
    return i18n.t(key, { ...baseOptions, defaultValue: key });
  }, [language, lazyLoadNamespace, pathname]);

  const value = useMemo(
    () => ({
      language,
      setLanguage,
      t,
      ready,
      supportedLanguages: SUPPORTED_LANGUAGES,
    }),
    [language, ready, setLanguage, t, bundleVersion],
  );

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within LanguageProvider');
  }
  return context;
}
