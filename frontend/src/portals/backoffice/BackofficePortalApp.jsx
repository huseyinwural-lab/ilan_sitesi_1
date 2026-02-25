import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

import AdminRouteGuard from '@/components/AdminRouteGuard';
import AdminLayout from '@/layouts/AdminLayout';
import Dashboard from '@/pages/Dashboard';
import FeatureFlags from '@/pages/FeatureFlags';
import AdminUsersPage from '@/pages/admin/AdminUsers';
import AdminCategories from '@/pages/admin/AdminCategories';
import AdminCategoriesImportExport from '@/pages/admin/AdminCategoriesImportExport';
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
import AdminAdsManagement from '@/pages/admin/AdminAdsManagement';
import AdminAdsCampaigns from '@/pages/admin/AdminAdsCampaigns';
import AdminPricingCampaign from '@/pages/admin/AdminPricingCampaign';
import AdminPricingTiers from '@/pages/admin/AdminPricingTiers';
import AdminPricingPackages from '@/pages/admin/AdminPricingPackages';
import AdminHeaderManagement from '@/pages/admin/AdminHeaderManagement';
import AdminFooterManagement from '@/pages/admin/AdminFooterManagement';
import AdminInfoPages from '@/pages/admin/AdminInfoPages';

export default function BackofficePortalApp() {
  return (
    <Routes>
      <Route path="/" element={<AdminLayout><Dashboard /></AdminLayout>} />
      <Route path="/users" element={<Navigate to="/admin/admin-users" replace />} />
      <Route path="/user-management" element={<Navigate to="/admin/admin-users" replace />} />
      <Route path="/admin-users" element={<AdminLayout><AdminUsersPage /></AdminLayout>} />
      <Route path="/roles" element={<AdminLayout><AdminRolesPage /></AdminLayout>} />
      <Route path="/rbac-matrix" element={<AdminLayout><RBACMatrixPage /></AdminLayout>} />
      <Route path="/individual-users" element={<AdminLayout><IndividualUsersPage /></AdminLayout>} />
      <Route path="/individual-applications" element={<AdminLayout><IndividualApplicationsPage /></AdminLayout>} />
      <Route path="/feature-flags" element={<AdminLayout><FeatureFlags /></AdminLayout>} />
      <Route path="/categories" element={<AdminLayout><AdminCategories /></AdminLayout>} />
      <Route path="/categories/import-export" element={<AdminLayout><AdminCategoriesImportExport /></AdminLayout>} />
      <Route path="/attributes" element={<AdminLayout><AdminAttributes /></AdminLayout>} />
      <Route path="/menu-management" element={<AdminLayout><MenuManagementPage /></AdminLayout>} />
      <Route path="/audit" element={
        <AdminLayout>
          <AdminRouteGuard roles={["super_admin", "ROLE_AUDIT_VIEWER", "audit_viewer"]}>
            <AuditLogs />
          </AdminRouteGuard>
        </AdminLayout>
      } />
      <Route path="/audit-logs" element={
        <AdminLayout>
          <AdminRouteGuard roles={["super_admin", "ROLE_AUDIT_VIEWER", "audit_viewer"]}>
            <AuditLogs />
          </AdminRouteGuard>
        </AdminLayout>
      } />
      <Route path="/moderation" element={<AdminLayout><ModerationQueue /></AdminLayout>} />
      <Route path="/individual-listing-applications" element={<AdminLayout><IndividualListingApplicationsPage /></AdminLayout>} />
      <Route path="/corporate-listing-applications" element={<AdminLayout><CorporateListingApplicationsPage /></AdminLayout>} />
      <Route path="/individual-campaigns" element={<AdminLayout><IndividualCampaignsPage /></AdminLayout>} />
      <Route path="/corporate-campaigns" element={<AdminLayout><CorporateCampaignsPage /></AdminLayout>} />
      <Route path="/ads" element={<AdminLayout><AdminAdsManagement /></AdminLayout>} />
      <Route path="/ads/campaigns" element={<AdminLayout><AdminAdsCampaigns /></AdminLayout>} />
      <Route path="/pricing/campaign" element={<AdminLayout><AdminPricingCampaign /></AdminLayout>} />
      <Route path="/pricing/tiers" element={<AdminLayout><AdminPricingTiers /></AdminLayout>} />
      <Route path="/pricing/packages" element={<AdminLayout><AdminPricingPackages /></AdminLayout>} />
      <Route
        path="/site-design/header"
        element={
          <AdminLayout>
            <AdminRouteGuard roles={["super_admin"]}>
              <AdminHeaderManagement />
            </AdminRouteGuard>
          </AdminLayout>
        }
      />
      <Route path="/campaigns" element={<Navigate to="/admin/individual-campaigns" replace />} />
      <Route path="/dashboard" element={<AdminLayout><AdminDashboardPage /></AdminLayout>} />
      <Route path="/country-compare" element={<AdminLayout><AdminCountryComparePage /></AdminLayout>} />
      <Route path="/countries" element={
        <AdminLayout>
          <AdminRouteGuard roles={["super_admin", "country_admin"]}>
            <AdminCountriesPage />
          </AdminRouteGuard>
        </AdminLayout>
      } />
      <Route path="/system-settings" element={<AdminLayout><AdminSystemSettingsPage /></AdminLayout>} />
      <Route path="/listings" element={<AdminLayout><AdminListingsPage /></AdminLayout>} />
      <Route path="/invoices" element={<AdminLayout><AdminInvoicesPage /></AdminLayout>} />
      <Route path="/payments" element={<AdminLayout><AdminPaymentsPage /></AdminLayout>} />
      <Route path="/billing" element={<AdminLayout><BillingPlaceholderPage /></AdminLayout>} />
      <Route path="/tax-rates" element={<AdminLayout><AdminTaxRatesPage /></AdminLayout>} />
      <Route path="/plans" element={<AdminLayout><AdminPlansPage /></AdminLayout>} />
      <Route path="/dealers/:dealerId" element={<AdminLayout><AdminDealerDetailPage /></AdminLayout>} />

      <Route path="/dealers" element={<AdminLayout><DealersPage /></AdminLayout>} />
      <Route path="/dealer-applications" element={<AdminLayout><DealerApplicationsPage /></AdminLayout>} />
      <Route path="/vehicle-makes" element={<AdminLayout><AdminVehicleMakes /></AdminLayout>} />
      <Route path="/vehicle-models" element={<AdminLayout><AdminVehicleModels /></AdminLayout>} />
      

      <Route path="*" element={<Navigate to="/admin" replace />} />
    </Routes>
  );
}
