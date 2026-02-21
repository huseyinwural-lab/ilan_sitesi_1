import React from 'react';
import { Routes, Route, Navigate, Link } from 'react-router-dom';
import DealerInvoices from '@/pages/dealer/DealerInvoices';
import PaymentSuccess from '@/pages/dealer/PaymentSuccess';
import PaymentCancel from '@/pages/dealer/PaymentCancel';
import DealerLayout from '@/layouts/DealerLayout';

function DealerHome() {
  return (
    <div className="space-y-3" data-testid="dealer-home">
      <h1 className="text-2xl font-bold tracking-tight" data-testid="dealer-home-title">Dealer Panel</h1>
      <p className="text-sm text-muted-foreground" data-testid="dealer-home-subtitle">
        Yakında: dashboard, lead yönetimi, kota, faturalama.
      </p>
      <div>
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
      <Route path="/" element={<DealerLayout />}>
        <Route index element={<DealerHome />} />
        <Route path="invoices" element={<DealerInvoices />} />
        <Route path="payments/success" element={<PaymentSuccess />} />
        <Route path="payments/cancel" element={<PaymentCancel />} />
      </Route>
      <Route path="*" element={<Navigate to="/dealer" replace />} />
    </Routes>
  );
}
