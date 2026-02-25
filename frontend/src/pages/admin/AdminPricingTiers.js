import React from 'react';

export default function AdminPricingTiers() {
  return (
    <div className="space-y-4" data-testid="admin-pricing-tiers-page">
      <div>
        <h1 className="text-2xl font-semibold" data-testid="admin-pricing-tiers-title">Bireysel Tier Pricing</h1>
        <p className="text-sm text-muted-foreground" data-testid="admin-pricing-tiers-subtitle">
          Tier fiyatlandırma kurgusu Parça 3'te devreye alınacak.
        </p>
      </div>
      <div className="rounded-lg border bg-white p-4 text-sm text-muted-foreground" data-testid="admin-pricing-tiers-placeholder">
        Scaffolding: Bu ekran Parça 3'te aktif hale gelecek.
      </div>
    </div>
  );
}
