import React from 'react';

export default function AdminPricingCampaign() {
  return (
    <div className="space-y-4" data-testid="admin-pricing-campaign-page">
      <div>
        <h1 className="text-2xl font-semibold" data-testid="admin-pricing-campaign-title">Lansman Kampanyası Modu</h1>
        <p className="text-sm text-muted-foreground" data-testid="admin-pricing-campaign-subtitle">
          Pricing campaign policy ayarları Parça 2'de devreye alınacak.
        </p>
      </div>
      <div className="rounded-lg border bg-white p-4 text-sm text-muted-foreground" data-testid="admin-pricing-campaign-placeholder">
        Scaffolding: Bu ekran Parça 2'de aktif hale gelecek.
      </div>
    </div>
  );
}
