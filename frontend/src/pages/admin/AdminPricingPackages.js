import React from 'react';

export default function AdminPricingPackages() {
  return (
    <div className="space-y-4" data-testid="admin-pricing-packages-page">
      <div>
        <h1 className="text-2xl font-semibold" data-testid="admin-pricing-packages-title">Kurumsal Paketler</h1>
        <p className="text-sm text-muted-foreground" data-testid="admin-pricing-packages-subtitle">
          Paket/Quota yönetimi Parça 3'te devreye alınacak.
        </p>
      </div>
      <div className="rounded-lg border bg-white p-4 text-sm text-muted-foreground" data-testid="admin-pricing-packages-placeholder">
        Scaffolding: Bu ekran Parça 3'te aktif hale gelecek.
      </div>
    </div>
  );
}
