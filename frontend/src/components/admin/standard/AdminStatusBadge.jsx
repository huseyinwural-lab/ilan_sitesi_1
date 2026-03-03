import React from 'react';

const VARIANT_CLASS = {
  neutral: 'border-slate-200 bg-slate-100 text-slate-700',
  success: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  warning: 'border-amber-200 bg-amber-50 text-amber-700',
  danger: 'border-rose-200 bg-rose-50 text-rose-700',
  info: 'border-blue-200 bg-blue-50 text-blue-700',
};

export const AdminStatusBadge = ({
  label,
  variant = 'neutral',
  testId = 'admin-status-badge',
}) => {
  const cls = VARIANT_CLASS[variant] || VARIANT_CLASS.neutral;
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${cls}`}
      data-testid={testId}
    >
      {label}
    </span>
  );
};
