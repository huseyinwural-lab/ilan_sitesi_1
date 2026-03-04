import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const SUPPORTED_LANGUAGES = ['tr', 'de', 'fr'];
const FALLBACK_LANGUAGE = 'tr';

const localeLoaders = {
  tr: () => import('../locales/tr.json'),
  de: () => import('../locales/de.json'),
  fr: () => import('../locales/fr.json'),
};

const loadedLanguages = new Set();

const normalizeLanguage = (value) => {
  const normalized = String(value || '').trim().toLowerCase();
  return SUPPORTED_LANGUAGES.includes(normalized) ? normalized : FALLBACK_LANGUAGE;
};

const readStoredLanguage = () => {
  try {
    return normalizeLanguage(window.localStorage.getItem('language'));
  } catch {
    return FALLBACK_LANGUAGE;
  }
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

const ensureLanguageBundle = async (language) => {
  const normalized = normalizeLanguage(language);
  if (loadedLanguages.has(normalized)) {
    return normalized;
  }

  const module = await localeLoaders[normalized]();
  const resources = module?.default || module || {};
  i18n.addResourceBundle(normalized, 'translation', resources, true, true);
  loadedLanguages.add(normalized);
  return normalized;
};

const LanguageContext = createContext(null);

export function LanguageProvider({ children }) {
  const [language, setLanguageState] = useState(initialLanguage);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let active = true;

    const bootstrap = async () => {
      const targetLanguage = normalizeLanguage(language);
      await ensureLanguageBundle(FALLBACK_LANGUAGE);
      await ensureLanguageBundle(targetLanguage);
      await i18n.changeLanguage(targetLanguage);

      try {
        window.localStorage.setItem('language', targetLanguage);
      } catch {
        // noop
      }
      document.documentElement.lang = targetLanguage;

      if (active) {
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
  }, [language]);

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

  const t = useCallback((key, fallbackOrOptions = undefined, maybeOptions = undefined) => {
    const baseOptions = { lng: language };

    if (typeof fallbackOrOptions === 'string') {
      return i18n.t(key, { ...baseOptions, defaultValue: fallbackOrOptions, ...(maybeOptions || {}) });
    }
    if (fallbackOrOptions && typeof fallbackOrOptions === 'object') {
      return i18n.t(key, { ...baseOptions, ...fallbackOrOptions });
    }
    return i18n.t(key, { ...baseOptions, defaultValue: key });
  }, [language]);

  const value = useMemo(
    () => ({
      language,
      setLanguage,
      t,
      ready,
      supportedLanguages: SUPPORTED_LANGUAGES,
    }),
    [language, ready, setLanguage, t],
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
