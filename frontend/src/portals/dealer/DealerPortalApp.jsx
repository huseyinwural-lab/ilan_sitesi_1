import React from 'react';
import { Routes, Route, Navigate, Link } from 'react-router-dom';
import DealerInvoices from '@/pages/dealer/DealerInvoices';
import PaymentSuccess from '@/pages/dealer/PaymentSuccess';
import PaymentCancel from '@/pages/dealer/PaymentCancel';

function DealerHome() {
  return (
    <div className="p-8" data-testid="dealer-home">
      <h1 className="text-2xl font-bold tracking-tight">Dealer Panel</h1>
      <p className="text-sm text-muted-foreground mt-2">Yakında: dashboard, lead yönetimi, kota, faturalama.</p>
      <div className="mt-4">
        <Link className="text-sm text-primary" to="/dealer/invoices" data-testid="dealer-home-invoices-link">
          Faturalarımı Gör
        </Link>
      </div>
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
