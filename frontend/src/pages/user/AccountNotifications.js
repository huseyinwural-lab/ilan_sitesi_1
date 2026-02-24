import React from 'react';

export default function AccountNotifications() {
  return (
    <div className="space-y-4" data-testid="account-notifications">
      <h1 className="text-lg font-semibold" data-testid="account-notifications-title">Bildirimler</h1>
      <div className="rounded-md border bg-white p-4 text-sm text-muted-foreground" data-testid="account-notifications-empty">
        Bildirim bulunamadı.
      </div>
    </div>
  );
}
