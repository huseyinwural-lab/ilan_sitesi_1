import React from 'react';

export const FinanceLoadingState = ({ testId, message = 'Yükleniyor...' }) => (
  <div className="rounded-md border bg-muted/40 p-4 text-sm text-muted-foreground" data-testid={testId}>{message}</div>
);

export const FinanceEmptyState = ({ testId, message = 'Kayıt bulunamadı.' }) => (
  <div className="rounded-md border border-dashed p-6 text-center text-sm text-muted-foreground" data-testid={testId}>{message}</div>
);

export const FinanceErrorState = ({ testId, message = 'Bir hata oluştu.' }) => (
  <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700" data-testid={testId}>{message}</div>
);
