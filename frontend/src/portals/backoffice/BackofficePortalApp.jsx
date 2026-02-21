import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

import AdminRouteGuard from '@/components/AdminRouteGuard';
import AdminLayout from '@/layouts/AdminLayout';
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
import AdminInvoicesPage from '@/pages/admin/AdminInvoices';
import AdminPaymentsPage from '@/pages/admin/AdminPayments';
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
      <Route path="/" element={<AdminLayout><Dashboard /></Layout>} />
      <Route path="/users" element={<Navigate to="/admin/admin-users" replace />} />
      <Route path="/user-management" element={<Navigate to="/admin/admin-users" replace />} />
      <Route path="/admin-users" element={<AdminLayout><AdminUsersPage /></Layout>} />
      <Route path="/roles" element={<AdminLayout><AdminRolesPage /></Layout>} />
      <Route path="/rbac-matrix" element={<AdminLayout><RBACMatrixPage /></Layout>} />
      <Route path="/individual-users" element={<AdminLayout><IndividualUsersPage /></Layout>} />
      <Route path="/individual-applications" element={<AdminLayout><IndividualApplicationsPage /></Layout>} />
      <Route path="/feature-flags" element={<AdminLayout><FeatureFlags /></Layout>} />
      <Route path="/categories" element={<AdminLayout><AdminCategories /></Layout>} />
      <Route path="/attributes" element={<AdminLayout><AdminAttributes /></Layout>} />
      <Route path="/menu-management" element={<AdminLayout><MenuManagementPage /></Layout>} />
      <Route path="/audit" element={
        <AdminLayout>
          <AdminRouteGuard roles={["super_admin", "ROLE_AUDIT_VIEWER", "audit_viewer"]}>
            <AuditLogs />
          </AdminRouteGuard>
        </Layout>
      } />
      <Route path="/audit-logs" element={
        <AdminLayout>
          <AdminRouteGuard roles={["super_admin", "ROLE_AUDIT_VIEWER", "audit_viewer"]}>
            <AuditLogs />
          </AdminRouteGuard>
        </Layout>
      } />
      <Route path="/moderation" element={<AdminLayout><ModerationQueue /></Layout>} />
      <Route path="/individual-listing-applications" element={<AdminLayout><IndividualListingApplicationsPage /></Layout>} />
      <Route path="/corporate-listing-applications" element={<AdminLayout><CorporateListingApplicationsPage /></Layout>} />
      <Route path="/individual-campaigns" element={<AdminLayout><IndividualCampaignsPage /></Layout>} />
      <Route path="/corporate-campaigns" element={<AdminLayout><CorporateCampaignsPage /></Layout>} />
      <Route path="/dashboard" element={<AdminLayout><AdminDashboardPage /></Layout>} />
      <Route path="/country-compare" element={<AdminLayout><AdminCountryComparePage /></Layout>} />
      <Route path="/countries" element={
        <AdminLayout>
          <AdminRouteGuard roles={["super_admin", "ROLE_AUDIT_VIEWER", "audit_viewer"]}>
            <AdminCountriesPage />
          </AdminRouteGuard>
        </Layout>
      } />
      <Route path="/system-settings" element={<AdminLayout><AdminSystemSettingsPage /></Layout>} />
      <Route path="/listings" element={<AdminLayout><AdminListingsPage /></Layout>} />
      <Route path="/invoices" element={<AdminLayout><AdminInvoicesPage /></Layout>} />
      <Route path="/payments" element={<AdminLayout><AdminPaymentsPage /></Layout>} />
      <Route path="/billing" element={<AdminLayout><BillingPlaceholderPage /></Layout>} />
      <Route path="/tax-rates" element={<AdminLayout><AdminTaxRatesPage /></Layout>} />
      <Route path="/plans" element={<AdminLayout><AdminPlansPage /></Layout>} />
      <Route path="/dealers/:dealerId" element={<AdminLayout><AdminDealerDetailPage /></Layout>} />

      <Route path="/dealers" element={<AdminLayout><DealersPage /></Layout>} />
      <Route path="/dealer-applications" element={<AdminLayout><DealerApplicationsPage /></Layout>} />
      <Route path="/vehicle-makes" element={<AdminLayout><AdminVehicleMakes /></Layout>} />
      <Route path="/vehicle-models" element={<AdminLayout><AdminVehicleModels /></Layout>} />
      

      <Route path="*" element={<Navigate to="/admin" replace />} />
    </Routes>
  );
}
