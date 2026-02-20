import React from 'react';

export function LoadingState({ label = 'Yükleniyor...' }) {
  return (
    <div className="flex items-center justify-center rounded-lg border bg-white p-6 text-sm text-muted-foreground" data-testid="account-loading-state">
      {label}
    </div>
  );
}

export function ErrorState({ message = 'Bir hata oluştu.', onRetry, testId = 'account-error-state' }) {
  return (
    <div className="rounded-lg border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700" data-testid={testId}>
      <div className="font-semibold" data-testid="account-error-title">Hata</div>
      <div className="mt-1" data-testid="account-error-message">{message}</div>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-3 inline-flex h-9 items-center rounded-md border px-3 text-xs"
          data-testid="account-error-retry"
        >
          Tekrar Dene
        </button>
      )}
    </div>
  );
}

export function EmptyState({
  title = 'Kayıt bulunamadı',
  description = 'Henüz içerik yok.',
  actionLabel,
  onAction,
  testId = 'account-empty-state',
}) {
  return (
    <div className="rounded-lg border bg-white p-8 text-center" data-testid={testId}>
      <div className="text-lg font-semibold" data-testid="account-empty-title">{title}</div>
      <div className="mt-2 text-sm text-muted-foreground" data-testid="account-empty-description">{description}</div>
      {actionLabel && onAction && (
        <button
          type="button"
          onClick={onAction}
          className="mt-4 inline-flex h-10 items-center rounded-md bg-primary px-4 text-sm text-primary-foreground"
          data-testid="account-empty-action"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}
