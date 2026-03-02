export const formatMoneyMinor = (amountMinor, currency = 'EUR', locale = 'tr-TR') => {
  const value = Number(amountMinor || 0) / 100;
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
};

export const resolveLocaleByCountry = (countryCode) => {
  const code = (countryCode || '').toUpperCase();
  if (code === 'DE') return 'de-DE';
  return 'tr-TR';
};

export const normalizePaymentMessage = (status) => {
  const value = (status || '').toLowerCase();
  if (value === 'succeeded') return 'Ödeme başarılı';
  if (value === 'failed') return 'Ödeme başarısız';
  if (value === 'pending' || value === 'processing' || value === 'requires_action') return 'Ödeme işleniyor';
  if (value === 'refunded') return 'Ödeme iade edildi';
  return 'Durum güncelleniyor';
};
