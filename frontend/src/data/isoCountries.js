import countries from 'i18n-iso-countries';
import enLocale from 'i18n-iso-countries/langs/en.json';
import trLocale from 'i18n-iso-countries/langs/tr.json';

countries.registerLocale(enLocale);
countries.registerLocale(trLocale);

const BASE_COUNTRY_META = [
  { code: 'DE', currency: 'EUR', locale: 'de-DE' },
  { code: 'CH', currency: 'CHF', locale: 'de-CH' },
  { code: 'AT', currency: 'EUR', locale: 'de-AT' },
  { code: 'FR', currency: 'EUR', locale: 'fr-FR' },
  { code: 'PL', currency: 'PLN', locale: 'pl-PL' },
  { code: 'TR', currency: 'TRY', locale: 'tr-TR' },
  { code: 'IT', currency: 'EUR', locale: 'it-IT' },
  { code: 'ES', currency: 'EUR', locale: 'es-ES' },
  { code: 'NL', currency: 'EUR', locale: 'nl-NL' },
  { code: 'BE', currency: 'EUR', locale: 'nl-BE' },
  { code: 'LU', currency: 'EUR', locale: 'fr-LU' },
  { code: 'PT', currency: 'EUR', locale: 'pt-PT' },
  { code: 'IE', currency: 'EUR', locale: 'en-IE' },
  { code: 'GB', currency: 'GBP', locale: 'en-GB' },
  { code: 'US', currency: 'USD', locale: 'en-US' },
  { code: 'CA', currency: 'CAD', locale: 'en-CA' },
  { code: 'AU', currency: 'AUD', locale: 'en-AU' },
  { code: 'NZ', currency: 'NZD', locale: 'en-NZ' },
  { code: 'JP', currency: 'JPY', locale: 'ja-JP' },
  { code: 'CN', currency: 'CNY', locale: 'zh-CN' },
  { code: 'IN', currency: 'INR', locale: 'en-IN' },
  { code: 'BR', currency: 'BRL', locale: 'pt-BR' },
  { code: 'MX', currency: 'MXN', locale: 'es-MX' },
  { code: 'ZA', currency: 'ZAR', locale: 'en-ZA' },
  { code: 'AE', currency: 'AED', locale: 'ar-AE' },
  { code: 'SA', currency: 'SAR', locale: 'ar-SA' },
  { code: 'NO', currency: 'NOK', locale: 'nb-NO' },
  { code: 'SE', currency: 'SEK', locale: 'sv-SE' },
  { code: 'DK', currency: 'DKK', locale: 'da-DK' },
  { code: 'FI', currency: 'EUR', locale: 'fi-FI' },
  { code: 'CZ', currency: 'CZK', locale: 'cs-CZ' },
  { code: 'HU', currency: 'HUF', locale: 'hu-HU' },
  { code: 'SK', currency: 'EUR', locale: 'sk-SK' },
  { code: 'SI', currency: 'EUR', locale: 'sl-SI' },
  { code: 'HR', currency: 'EUR', locale: 'hr-HR' },
  { code: 'RO', currency: 'RON', locale: 'ro-RO' },
  { code: 'BG', currency: 'BGN', locale: 'bg-BG' },
  { code: 'GR', currency: 'EUR', locale: 'el-GR' },
  { code: 'EE', currency: 'EUR', locale: 'et-EE' },
  { code: 'LV', currency: 'EUR', locale: 'lv-LV' },
  { code: 'LT', currency: 'EUR', locale: 'lt-LT' },
  { code: 'IS', currency: 'ISK', locale: 'is-IS' },
  { code: 'UA', currency: 'UAH', locale: 'uk-UA' },
  { code: 'RU', currency: 'RUB', locale: 'ru-RU' },
  { code: 'IL', currency: 'ILS', locale: 'he-IL' },
  { code: 'EG', currency: 'EGP', locale: 'ar-EG' },
  { code: 'MA', currency: 'MAD', locale: 'ar-MA' },
  { code: 'TN', currency: 'TND', locale: 'ar-TN' },
  { code: 'NG', currency: 'NGN', locale: 'en-NG' },
  { code: 'KE', currency: 'KES', locale: 'en-KE' },
  { code: 'AR', currency: 'ARS', locale: 'es-AR' },
  { code: 'CL', currency: 'CLP', locale: 'es-CL' },
  { code: 'CO', currency: 'COP', locale: 'es-CO' },
  { code: 'PE', currency: 'PEN', locale: 'es-PE' },
  { code: 'VE', currency: 'VES', locale: 'es-VE' },
  { code: 'KR', currency: 'KRW', locale: 'ko-KR' },
  { code: 'TH', currency: 'THB', locale: 'th-TH' },
  { code: 'SG', currency: 'SGD', locale: 'en-SG' },
  { code: 'MY', currency: 'MYR', locale: 'ms-MY' },
  { code: 'ID', currency: 'IDR', locale: 'id-ID' },
  { code: 'PH', currency: 'PHP', locale: 'en-PH' },
];

const BASE_META_MAP = new Map(BASE_COUNTRY_META.map((country) => [country.code, country]));
const COUNTRY_NAMES = countries.getNames('tr', { select: 'official' });

const ISO_COUNTRIES = Object.entries(COUNTRY_NAMES)
  .map(([code, name]) => {
    const meta = BASE_META_MAP.get(code) || {};
    return {
      code,
      name,
      currency: meta.currency || '',
      locale: meta.locale || '',
    };
  })
  .sort((a, b) => (a.name || '').localeCompare(b.name || ''));

export default ISO_COUNTRIES;
