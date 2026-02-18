import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

import Layout from '@/components/Layout';
import Dashboard from '@/pages/Dashboard';
import UserManagement from '@/pages/Users';
import FeatureFlags from '@/pages/FeatureFlags';
import Categories from '@/pages/Categories';
import AdminAttributes from '@/pages/AdminAttributes';
import AdminOptions from '@/pages/AdminOptions';
import AdminVehicleMDM from '@/pages/AdminVehicleMDM';

import AuditLogs from '@/pages/AuditLogs';
import ModerationQueue from '@/pages/ModerationQueue';
import DealersPage from '@/pages/admin/Dealers';
import DealerApplicationsPage from '@/pages/admin/DealerApplications';
import AdminListingsPage from '@/pages/admin/AdminListings';
import AdminReportsPage from '@/pages/admin/AdminReports';
import AdminInvoicesPage from '@/pages/admin/AdminInvoices';
import AdminTaxRatesPage from '@/pages/admin/AdminTaxRates';
import AdminPlansPage from '@/pages/admin/AdminPlans';
import AdminDealerDetailPage from '@/pages/admin/AdminDealerDetail';
import AdminCountriesPage from '@/pages/admin/AdminCountries';
import AdminSystemSettingsPage from '@/pages/admin/AdminSystemSettings';
import AdminDashboardPage from '@/pages/admin/AdminDashboard';
import AdminCountryComparePage from '@/pages/admin/AdminCountryCompare';

export default function BackofficePortalApp() {
  return (
    <Routes>
      <Route path="/" element={<Layout><Dashboard /></Layout>} />
      <Route path="/users" element={<Layout><UserManagement /></Layout>} />
      <Route path="/feature-flags" element={<Layout><FeatureFlags /></Layout>} />
      <Route path="/categories" element={<Layout><Categories /></Layout>} />
      <Route path="/attributes" element={<Layout><AdminAttributes /></Layout>} />
      <Route path="/attributes/options" element={<Layout><AdminOptions /></Layout>} />
      <Route path="/audit-logs" element={<Layout><AuditLogs /></Layout>} />
      <Route path="/moderation" element={<Layout><ModerationQueue /></Layout>} />
      <Route path="/dashboard" element={<Layout><AdminDashboardPage /></Layout>} />
      <Route path="/country-compare" element={<Layout><AdminCountryComparePage /></Layout>} />
      <Route path="/countries" element={<Layout><AdminCountriesPage /></Layout>} />
      <Route path="/system-settings" element={<Layout><AdminSystemSettingsPage /></Layout>} />
      <Route path="/listings" element={<Layout><AdminListingsPage /></Layout>} />
      <Route path="/reports" element={<Layout><AdminReportsPage /></Layout>} />
      <Route path="/invoices" element={<Layout><AdminInvoicesPage /></Layout>} />
      <Route path="/tax-rates" element={<Layout><AdminTaxRatesPage /></Layout>} />
      <Route path="/plans" element={<Layout><AdminPlansPage /></Layout>} />
      <Route path="/dealers/:dealerId" element={<Layout><AdminDealerDetailPage /></Layout>} />

      <Route path="/dealers" element={<Layout><DealersPage /></Layout>} />
      <Route path="/dealer-applications" element={<Layout><DealerApplicationsPage /></Layout>} />


      <Route path="/master-data/vehicles" element={<Layout><AdminVehicleMDM /></Layout>} />
      

      <Route path="*" element={<Navigate to="/admin" replace />} />
    </Routes>
  );
}
