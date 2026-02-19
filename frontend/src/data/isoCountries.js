const BASE_COUNTRIES = [
  { code: 'DE', name: 'Germany', currency: 'EUR', locale: 'de-DE' },
  { code: 'CH', name: 'Switzerland', currency: 'CHF', locale: 'de-CH' },
  { code: 'AT', name: 'Austria', currency: 'EUR', locale: 'de-AT' },
  { code: 'FR', name: 'France', currency: 'EUR', locale: 'fr-FR' },
  { code: 'PL', name: 'Poland', currency: 'PLN', locale: 'pl-PL' },
  { code: 'TR', name: 'Turkey', currency: 'TRY', locale: 'tr-TR' },
  { code: 'IT', name: 'Italy', currency: 'EUR', locale: 'it-IT' },
  { code: 'ES', name: 'Spain', currency: 'EUR', locale: 'es-ES' },
  { code: 'NL', name: 'Netherlands', currency: 'EUR', locale: 'nl-NL' },
  { code: 'BE', name: 'Belgium', currency: 'EUR', locale: 'nl-BE' },
  { code: 'LU', name: 'Luxembourg', currency: 'EUR', locale: 'fr-LU' },
  { code: 'PT', name: 'Portugal', currency: 'EUR', locale: 'pt-PT' },
  { code: 'IE', name: 'Ireland', currency: 'EUR', locale: 'en-IE' },
  { code: 'GB', name: 'United Kingdom', currency: 'GBP', locale: 'en-GB' },
  { code: 'US', name: 'United States', currency: 'USD', locale: 'en-US' },
  { code: 'CA', name: 'Canada', currency: 'CAD', locale: 'en-CA' },
  { code: 'AU', name: 'Australia', currency: 'AUD', locale: 'en-AU' },
  { code: 'NZ', name: 'New Zealand', currency: 'NZD', locale: 'en-NZ' },
  { code: 'JP', name: 'Japan', currency: 'JPY', locale: 'ja-JP' },
  { code: 'CN', name: 'China', currency: 'CNY', locale: 'zh-CN' },
  { code: 'IN', name: 'India', currency: 'INR', locale: 'en-IN' },
  { code: 'BR', name: 'Brazil', currency: 'BRL', locale: 'pt-BR' },
  { code: 'MX', name: 'Mexico', currency: 'MXN', locale: 'es-MX' },
  { code: 'ZA', name: 'South Africa', currency: 'ZAR', locale: 'en-ZA' },
  { code: 'AE', name: 'United Arab Emirates', currency: 'AED', locale: 'ar-AE' },
  { code: 'SA', name: 'Saudi Arabia', currency: 'SAR', locale: 'ar-SA' },
  { code: 'NO', name: 'Norway', currency: 'NOK', locale: 'nb-NO' },
  { code: 'SE', name: 'Sweden', currency: 'SEK', locale: 'sv-SE' },
  { code: 'DK', name: 'Denmark', currency: 'DKK', locale: 'da-DK' },
  { code: 'FI', name: 'Finland', currency: 'EUR', locale: 'fi-FI' },
  { code: 'CZ', name: 'Czechia', currency: 'CZK', locale: 'cs-CZ' },
  { code: 'HU', name: 'Hungary', currency: 'HUF', locale: 'hu-HU' },
  { code: 'SK', name: 'Slovakia', currency: 'EUR', locale: 'sk-SK' },
  { code: 'SI', name: 'Slovenia', currency: 'EUR', locale: 'sl-SI' },
  { code: 'HR', name: 'Croatia', currency: 'EUR', locale: 'hr-HR' },
  { code: 'RO', name: 'Romania', currency: 'RON', locale: 'ro-RO' },
  { code: 'BG', name: 'Bulgaria', currency: 'BGN', locale: 'bg-BG' },
  { code: 'GR', name: 'Greece', currency: 'EUR', locale: 'el-GR' },
  { code: 'EE', name: 'Estonia', currency: 'EUR', locale: 'et-EE' },
  { code: 'LV', name: 'Latvia', currency: 'EUR', locale: 'lv-LV' },
  { code: 'LT', name: 'Lithuania', currency: 'EUR', locale: 'lt-LT' },
  { code: 'IS', name: 'Iceland', currency: 'ISK', locale: 'is-IS' },
  { code: 'UA', name: 'Ukraine', currency: 'UAH', locale: 'uk-UA' },
  { code: 'RU', name: 'Russia', currency: 'RUB', locale: 'ru-RU' },
  { code: 'IL', name: 'Israel', currency: 'ILS', locale: 'he-IL' },
  { code: 'EG', name: 'Egypt', currency: 'EGP', locale: 'ar-EG' },
  { code: 'MA', name: 'Morocco', currency: 'MAD', locale: 'ar-MA' },
  { code: 'TN', name: 'Tunisia', currency: 'TND', locale: 'ar-TN' },
  { code: 'NG', name: 'Nigeria', currency: 'NGN', locale: 'en-NG' },
  { code: 'KE', name: 'Kenya', currency: 'KES', locale: 'en-KE' },
  { code: 'AR', name: 'Argentina', currency: 'ARS', locale: 'es-AR' },
  { code: 'CL', name: 'Chile', currency: 'CLP', locale: 'es-CL' },
  { code: 'CO', name: 'Colombia', currency: 'COP', locale: 'es-CO' },
  { code: 'PE', name: 'Peru', currency: 'PEN', locale: 'es-PE' },
  { code: 'VE', name: 'Venezuela', currency: 'VES', locale: 'es-VE' },
  { code: 'KR', name: 'South Korea', currency: 'KRW', locale: 'ko-KR' },
  { code: 'TH', name: 'Thailand', currency: 'THB', locale: 'th-TH' },
  { code: 'SG', name: 'Singapore', currency: 'SGD', locale: 'en-SG' },
  { code: 'MY', name: 'Malaysia', currency: 'MYR', locale: 'ms-MY' },
  { code: 'ID', name: 'Indonesia', currency: 'IDR', locale: 'id-ID' },
  { code: 'PH', name: 'Philippines', currency: 'PHP', locale: 'en-PH' }
];

const BASE_MAP = new Map(BASE_COUNTRIES.map((country) => [country.code, country]));

const buildIsoCountries = () => {
  const hasIntlRegions = typeof Intl !== 'undefined' && typeof Intl.supportedValuesOf === 'function';
  const regions = hasIntlRegions ? Intl.supportedValuesOf('region') : BASE_COUNTRIES.map((country) => country.code);
  const displayNames = typeof Intl !== 'undefined' && typeof Intl.DisplayNames === 'function'
    ? new Intl.DisplayNames(['tr', 'en'], { type: 'region' })
    : null;

  const list = regions.map((code) => {
    const upper = code.toUpperCase();
    const base = BASE_MAP.get(upper);
    return {
      code: upper,
      name: base?.name || (displayNames ? displayNames.of(upper) : upper),
      currency: base?.currency || '',
      locale: base?.locale || '',
    };
  });

  return list
    .filter((item) => item.code && item.name)
    .sort((a, b) => (a.name || '').localeCompare(b.name || ''));
};

const ISO_COUNTRIES = buildIsoCountries();

export default ISO_COUNTRIES;
