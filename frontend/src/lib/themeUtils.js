import { DEFAULT_THEME_CONFIG, THEME_REQUIRED_KEYS } from '@/data/themeDefaults';

const sanitizeHex = (value) => {
  if (!value || typeof value !== 'string') return null;
  const trimmed = value.trim();
  return /^#[0-9a-fA-F]{6}$/.test(trimmed) ? trimmed : null;
};

export const normalizeThemeConfig = (config) => {
  const normalized = {
    light: { ...DEFAULT_THEME_CONFIG.light },
    dark: { ...DEFAULT_THEME_CONFIG.dark },
  };
  if (!config || typeof config !== 'object') return normalized;
  ['light', 'dark'].forEach((mode) => {
    if (!config[mode] || typeof config[mode] !== 'object') return;
    THEME_REQUIRED_KEYS.forEach((key) => {
      const value = sanitizeHex(config[mode][key]);
      if (value) {
        normalized[mode][key] = value;
      }
    });
  });
  return normalized;
};

export const hexToHsl = (hex) => {
  const value = sanitizeHex(hex);
  if (!value) return null;
  const raw = value.replace('#', '');
  const r = parseInt(raw.slice(0, 2), 16) / 255;
  const g = parseInt(raw.slice(2, 4), 16) / 255;
  const b = parseInt(raw.slice(4, 6), 16) / 255;

  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  let h = 0;
  let s = 0;
  const l = (max + min) / 2;

  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case r:
        h = (g - b) / d + (g < b ? 6 : 0);
        break;
      case g:
        h = (b - r) / d + 2;
        break;
      default:
        h = (r - g) / d + 4;
    }
    h /= 6;
  }

  return `${Math.round(h * 360)} ${Math.round(s * 100)}% ${Math.round(l * 100)}%`;
};

export const buildThemeCssVars = (config) => {
  const normalized = normalizeThemeConfig(config);
  const vars = {};
  ['light', 'dark'].forEach((mode) => {
    THEME_REQUIRED_KEYS.forEach((key) => {
      const value = normalized[mode][key];
      vars[`--theme-${mode}-${key}`] = value;
      const hsl = hexToHsl(value);
      if (hsl) {
        vars[`--theme-${mode}-${key}-hsl`] = hsl;
      }
    });
  });
  return vars;
};

export const applyThemeConfig = (config, target = document.documentElement) => {
  if (!target) return;
  const vars = buildThemeCssVars(config);
  Object.entries(vars).forEach(([key, value]) => {
    target.style.setProperty(key, value);
  });
};
