import React from 'react';

export const AdminLoadingState = ({ message = 'Yükleniyor...', testId = 'admin-loading-state' }) => (
  <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-600" data-testid={testId}>
    {message}
  </div>
);

export const AdminEmptyState = ({ message = 'Kayıt bulunamadı.', testId = 'admin-empty-state' }) => (
  <div className="rounded-md border border-dashed border-slate-300 bg-white px-3 py-2 text-sm text-slate-500" data-testid={testId}>
    {message}
  </div>
);

export const AdminErrorState = ({ message = 'Bir hata oluştu.', testId = 'admin-error-state' }) => (
  <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700" data-testid={testId}>
    {message}
  </div>
);
