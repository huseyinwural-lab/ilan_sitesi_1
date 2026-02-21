import React from 'react';
import { Routes, Route, Navigate, Link } from 'react-router-dom';
import DealerInvoices from '@/pages/dealer/DealerInvoices';
import DealerListings from '@/pages/dealer/DealerListings';
import DealerDashboard from '@/pages/dealer/DealerDashboard';
import PaymentSuccess from '@/pages/dealer/PaymentSuccess';
import PaymentCancel from '@/pages/dealer/PaymentCancel';
import DealerLayout from '@/layouts/DealerLayout';

function DealerHome() {
  return <DealerDashboard />;
}

export default function DealerPortalApp() {
  return (
    <Routes>
      <Route path="/" element={<DealerLayout />}>
        <Route index element={<DealerHome />} />
        <Route path="listings" element={<DealerListings />} />
        <Route path="invoices" element={<DealerInvoices />} />
        <Route path="payments/success" element={<PaymentSuccess />} />
        <Route path="payments/cancel" element={<PaymentCancel />} />
      </Route>
      <Route path="*" element={<Navigate to="/dealer" replace />} />
    </Routes>
  );
}
