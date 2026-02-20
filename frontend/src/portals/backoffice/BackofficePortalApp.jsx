import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

import AdminRouteGuard from '@/components/AdminRouteGuard';
import Layout from '@/components/Layout';
import Dashboard from '@/pages/Dashboard';
import FeatureFlags from '@/pages/FeatureFlags';
import AdminUsersPage from '@/pages/admin/AdminUsers';
import AdminCategories from '@/pages/admin/AdminCategories';
import AdminAttributes from '@/pages/admin/AdminAttributes';
import AdminVehicleMakes from '@/pages/admin/AdminVehicleMakes';
import AdminVehicleModels from '@/pages/admin/AdminVehicleModels';

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
import AdminRolesPage from '@/pages/admin/AdminRoles';
import RBACMatrixPage from '@/pages/admin/RBACMatrix';
import IndividualUsersPage from '@/pages/admin/IndividualUsers';
import IndividualApplicationsPage from '@/pages/admin/IndividualApplications';
import IndividualListingApplicationsPage from '@/pages/admin/IndividualListingApplications';
import CorporateListingApplicationsPage from '@/pages/admin/CorporateListingApplications';
import IndividualCampaignsPage from '@/pages/admin/IndividualCampaigns';
import CorporateCampaignsPage from '@/pages/admin/CorporateCampaigns';
import MenuManagementPage from '@/pages/admin/MenuManagement';
import BillingPlaceholderPage from '@/pages/admin/BillingPlaceholder';

export default function BackofficePortalApp() {
  return (
    <Routes>
      <Route path="/" element={<Layout><Dashboard /></Layout>} />
      <Route path="/users" element={
        <Layout>
          <AdminRouteGuard roles={["super_admin", "country_admin"]}>
            <UserManagement />
          </AdminRouteGuard>
        </Layout>
      } />
      <Route path="/admin-users" element={<Layout><AdminUsersPage /></Layout>} />
      <Route path="/roles" element={<Layout><AdminRolesPage /></Layout>} />
      <Route path="/rbac-matrix" element={<Layout><RBACMatrixPage /></Layout>} />
      <Route path="/individual-users" element={<Layout><IndividualUsersPage /></Layout>} />
      <Route path="/individual-applications" element={<Layout><IndividualApplicationsPage /></Layout>} />
      <Route path="/feature-flags" element={<Layout><FeatureFlags /></Layout>} />
      <Route path="/categories" element={<Layout><AdminCategories /></Layout>} />
      <Route path="/attributes" element={<Layout><AdminAttributes /></Layout>} />
      <Route path="/menu-management" element={<Layout><MenuManagementPage /></Layout>} />
      <Route path="/audit" element={
        <Layout>
          <AdminRouteGuard roles={["super_admin", "country_admin"]}>
            <AuditLogs />
          </AdminRouteGuard>
        </Layout>
      } />
      <Route path="/audit-logs" element={
        <Layout>
          <AdminRouteGuard roles={["super_admin", "country_admin"]}>
            <AuditLogs />
          </AdminRouteGuard>
        </Layout>
      } />
      <Route path="/moderation" element={<Layout><ModerationQueue /></Layout>} />
      <Route path="/individual-listing-applications" element={<Layout><IndividualListingApplicationsPage /></Layout>} />
      <Route path="/corporate-listing-applications" element={<Layout><CorporateListingApplicationsPage /></Layout>} />
      <Route path="/individual-campaigns" element={<Layout><IndividualCampaignsPage /></Layout>} />
      <Route path="/corporate-campaigns" element={<Layout><CorporateCampaignsPage /></Layout>} />
      <Route path="/dashboard" element={<Layout><AdminDashboardPage /></Layout>} />
      <Route path="/country-compare" element={<Layout><AdminCountryComparePage /></Layout>} />
      <Route path="/countries" element={
        <Layout>
          <AdminRouteGuard roles={["super_admin", "country_admin"]}>
            <AdminCountriesPage />
          </AdminRouteGuard>
        </Layout>
      } />
      <Route path="/system-settings" element={<Layout><AdminSystemSettingsPage /></Layout>} />
      <Route path="/listings" element={<Layout><AdminListingsPage /></Layout>} />
      <Route path="/reports" element={<Layout><AdminReportsPage /></Layout>} />
      <Route path="/invoices" element={<Layout><AdminInvoicesPage /></Layout>} />
      <Route path="/billing" element={<Layout><BillingPlaceholderPage /></Layout>} />
      <Route path="/tax-rates" element={<Layout><AdminTaxRatesPage /></Layout>} />
      <Route path="/plans" element={<Layout><AdminPlansPage /></Layout>} />
      <Route path="/dealers/:dealerId" element={<Layout><AdminDealerDetailPage /></Layout>} />

      <Route path="/dealers" element={<Layout><DealersPage /></Layout>} />
      <Route path="/dealer-applications" element={<Layout><DealerApplicationsPage /></Layout>} />
      <Route path="/vehicle-makes" element={<Layout><AdminVehicleMakes /></Layout>} />
      <Route path="/vehicle-models" element={<Layout><AdminVehicleModels /></Layout>} />
      

      <Route path="*" element={<Navigate to="/admin" replace />} />
    </Routes>
  );
}
