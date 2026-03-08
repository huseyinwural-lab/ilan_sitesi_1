import React from 'react';

const isSafeCategoryIconSvg = (value = '') => {
  const raw = String(value || '').trim();
  if (!raw) return false;
  const lowered = raw.toLowerCase();
  if (!lowered.includes('<svg') || !lowered.includes('</svg>')) return false;
  if (/<\s*\/?\s*script/.test(lowered)) return false;
  if (/on[a-z]+\s*=/.test(lowered)) return false;
  if (lowered.includes('javascript:')) return false;
  if (lowered.includes('<foreignobject')) return false;
  return true;
};

export const CategoryIconSvg = ({
  iconSvg,
  testId,
  wrapperClassName = 'h-7 w-7 rounded-full border bg-white p-1',
  fallbackClassName = 'h-7 w-7 rounded-full border bg-slate-100 text-slate-500',
  fallbackText = '•',
}) => {
  if (isSafeCategoryIconSvg(iconSvg)) {
    return (
      <span
        className={wrapperClassName}
        dangerouslySetInnerHTML={{ __html: String(iconSvg).trim() }}
        data-testid={testId}
      />
    );
  }

  return (
    <span className={`${fallbackClassName} inline-flex items-center justify-center text-xs font-semibold`} data-testid={testId}>
      {fallbackText}
    </span>
  );
};
