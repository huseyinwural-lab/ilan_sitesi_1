import React from 'react';

const MAP = {
  issued: 'bg-blue-100 text-blue-700',
  paid: 'bg-emerald-100 text-emerald-700',
  refunded: 'bg-purple-100 text-purple-700',
  void: 'bg-slate-200 text-slate-700',
  succeeded: 'bg-emerald-100 text-emerald-700',
  failed: 'bg-red-100 text-red-700',
  pending: 'bg-amber-100 text-amber-700',
  processing: 'bg-amber-100 text-amber-700',
  trialing: 'bg-blue-100 text-blue-700',
  active: 'bg-emerald-100 text-emerald-700',
  past_due: 'bg-amber-100 text-amber-700',
  canceled: 'bg-slate-200 text-slate-700',
  unpaid: 'bg-red-100 text-red-700',
};

export const FinanceStatusBadge = ({ status, testId }) => {
  const value = (status || '-').toLowerCase();
  const cls = MAP[value] || 'bg-slate-100 text-slate-700';
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${cls}`} data-testid={testId}>
      {value}
    </span>
  );
};
