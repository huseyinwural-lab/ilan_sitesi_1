import React from 'react';
import { formatMoneyMinor } from '@/utils/financeFormat';

export const AdminMoneyText = ({
  amountMinor = 0,
  currency = 'EUR',
  locale = 'tr-TR',
  testId = 'admin-money-text',
}) => (
  <span className="tabular-nums font-semibold" data-testid={testId}>
    {formatMoneyMinor(amountMinor, currency, locale)}
  </span>
);
