import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

function DealerHome() {
  return (
    <div className="p-8" data-testid="dealer-home">
      <h1 className="text-2xl font-bold tracking-tight">Dealer Panel</h1>
      <p className="text-sm text-muted-foreground mt-2">Yakında: dashboard, lead yönetimi, kota, faturalama.</p>
    </div>
  );
}

export default function DealerPortalApp() {
  return (
    <Routes>
      <Route path="/" element={<DealerHome />} />
      <Route path="*" element={<Navigate to="/dealer" replace />} />
    </Routes>
  );
}
