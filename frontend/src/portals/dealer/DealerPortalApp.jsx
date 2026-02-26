import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import DealerOverview from '@/pages/dealer/DealerOverview';
import DealerListings from '@/pages/dealer/DealerListings';
import DealerMessages from '@/pages/dealer/DealerMessages';
import DealerCustomers from '@/pages/dealer/DealerCustomers';
import DealerReports from '@/pages/dealer/DealerReports';
import DealerPurchase from '@/pages/dealer/DealerPurchase';
import DealerSettings from '@/pages/dealer/DealerSettings';
import PaymentSuccess from '@/pages/dealer/PaymentSuccess';
import PaymentCancel from '@/pages/dealer/PaymentCancel';
import DealerLayout from '@/layouts/DealerLayout';

export default function DealerPortalApp() {
  return (
    <Routes>
      <Route path="/" element={<DealerLayout />}>
        <Route index element={<Navigate to="overview" replace />} />
        <Route path="overview" element={<DealerOverview />} />
        <Route path="listings" element={<DealerListings />} />
        <Route path="messages" element={<DealerMessages />} />
        <Route path="customers" element={<DealerCustomers />} />
        <Route path="reports" element={<DealerReports />} />
        <Route path="purchase" element={<DealerPurchase />} />
        <Route path="settings" element={<DealerSettings />} />
        <Route path="invoices" element={<Navigate to="/dealer/purchase" replace />} />
        <Route path="company" element={<Navigate to="/dealer/settings" replace />} />
        <Route path="privacy" element={<Navigate to="/dealer/settings" replace />} />
        <Route path="payments/success" element={<PaymentSuccess />} />
        <Route path="payments/cancel" element={<PaymentCancel />} />
      </Route>
      <Route path="*" element={<Navigate to="/dealer" replace />} />
    </Routes>
  );
}
