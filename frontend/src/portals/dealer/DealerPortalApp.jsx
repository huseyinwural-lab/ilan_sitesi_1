import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import DealerOverview from '@/pages/dealer/DealerOverview';
import DealerListings from '@/pages/dealer/DealerListings';
import DealerMessages from '@/pages/dealer/DealerMessages';
import DealerCustomers from '@/pages/dealer/DealerCustomers';
import DealerFavorites from '@/pages/dealer/DealerFavorites';
import DealerReports from '@/pages/dealer/DealerReports';
import DealerConsultantTracking from '@/pages/dealer/DealerConsultantTracking';
import DealerPurchase from '@/pages/dealer/DealerPurchase';
import DealerSettings from '@/pages/dealer/DealerSettings';
import DealerInvoices from '@/pages/dealer/DealerInvoices';
import DealerCompanyProfile from '@/pages/dealer/DealerCompanyProfile';
import DealerPrivacyCenter from '@/pages/dealer/DealerPrivacyCenter';
import DealerAcademy from '@/pages/dealer/DealerAcademy';
import PaymentSuccess from '@/pages/dealer/PaymentSuccess';
import PaymentCancel from '@/pages/dealer/PaymentCancel';
import DealerLayoutV2 from '@/layouts/DealerLayoutV2';

export default function DealerPortalApp() {
  return (
    <Routes>
      <Route path="/" element={<DealerLayoutV2 />}>
        <Route index element={<Navigate to="overview" replace />} />
        <Route path="overview" element={<DealerOverview />} />
        <Route path="listings" element={<DealerListings />} />
        <Route path="messages" element={<DealerMessages />} />
        <Route path="customers" element={<DealerCustomers />} />
        <Route path="favorites" element={<DealerFavorites />} />
        <Route path="reports" element={<DealerReports />} />
        <Route path="consultant-tracking" element={<DealerConsultantTracking />} />
        <Route path="purchase" element={<DealerPurchase />} />
        <Route path="settings" element={<DealerSettings />} />
        <Route path="invoices" element={<DealerInvoices />} />
        <Route path="academy" element={<DealerAcademy />} />
        <Route path="company" element={<DealerCompanyProfile />} />
        <Route path="privacy" element={<DealerPrivacyCenter />} />
        <Route path="payments/success" element={<PaymentSuccess />} />
        <Route path="payments/cancel" element={<PaymentCancel />} />
      </Route>
      <Route path="*" element={<Navigate to="/dealer" replace />} />
    </Routes>
  );
}
