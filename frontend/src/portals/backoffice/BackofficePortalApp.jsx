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
import AdminDealerPortalConfig from '@/pages/admin/AdminDealerPortalConfigDraft';
import AdminVehicleMakes from '@/pages/admin/AdminVehicleMakes';
import AdminVehicleModels from '@/pages/admin/AdminVehicleModels';
import AdminVehicleMasterImport from '@/pages/admin/AdminVehicleMasterImport';

import AuditLogs from '@/pages/AuditLogs';
import ModerationQueue from '@/pages/ModerationQueue';
import AdminReportsPage from '@/pages/admin/AdminReports';
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
import BillingPlaceholderPage from '@/pages/admin/BillingPlaceholder';
import AdminAdsManagement from '@/pages/admin/AdminAdsManagement';
import AdminAdsCampaigns from '@/pages/admin/AdminAdsCampaigns';
import AdminPricingCampaign from '@/pages/admin/AdminPricingCampaign';
import AdminPricingTiers from '@/pages/admin/AdminPricingTiers';
import AdminPricingPackages from '@/pages/admin/AdminPricingPackages';
import AdminHeaderManagement from '@/pages/admin/AdminHeaderManagement';
import AdminFooterManagement from '@/pages/admin/AdminFooterManagement';
import AdminThemeManagement from '@/pages/admin/AdminThemeManagement';
import AdminInfoPages from '@/pages/admin/AdminInfoPages';
import AdminUserInterfaceDesignV2 from '@/pages/admin/AdminUserInterfaceDesignV2';
import AdminPublishHealthPage from '@/pages/admin/ops/AdminPublishHealthPage';

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
      <Route path="/dealer-portal-config" element={<AdminLayout><AdminDealerPortalConfig /></AdminLayout>} />
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
      <Route path="/reports" element={<AdminLayout><AdminReportsPage /></AdminLayout>} />
      <Route
        path="/listings/featured"
        element={<AdminLayout><AdminListingsPage title="Vitrin İlanlar" dataTestId="admin-listings-featured-page" initialDopingType="showcase" /></AdminLayout>}
      />
      <Route
        path="/listings/urgent"
        element={<AdminLayout><AdminListingsPage title="Acil İlanlar" dataTestId="admin-listings-urgent-page" initialDopingType="urgent" /></AdminLayout>}
      />
      <Route
        path="/listings/paid"
        element={<AdminLayout><AdminListingsPage title="Ücretli İlanlar" dataTestId="admin-listings-paid-page" initialDopingType="paid" /></AdminLayout>}
      />
      <Route path="/individual-listing-applications" element={<AdminLayout><IndividualListingApplicationsPage /></AdminLayout>} />
      <Route
        path="/individual-listing-applications/paid"
        element={<AdminLayout><AdminListingsPage title="Bireysel Ücretli İlan Başvuruları" dataTestId="individual-listing-applications-paid-page" applicantType="individual" applicationsMode initialDopingType="paid" /></AdminLayout>}
      />
      <Route
        path="/individual-listing-applications/featured"
        element={<AdminLayout><AdminListingsPage title="Bireysel Vitrin İlan Başvuruları" dataTestId="individual-listing-applications-featured-page" applicantType="individual" applicationsMode initialDopingType="showcase" /></AdminLayout>}
      />
      <Route
        path="/individual-listing-applications/urgent"
        element={<AdminLayout><AdminListingsPage title="Bireysel Acil İlan Başvuruları" dataTestId="individual-listing-applications-urgent-page" applicantType="individual" applicationsMode initialDopingType="urgent" /></AdminLayout>}
      />
      <Route path="/corporate-listing-applications" element={<AdminLayout><CorporateListingApplicationsPage /></AdminLayout>} />
      <Route
        path="/corporate-listing-applications/paid"
        element={<AdminLayout><AdminListingsPage title="Kurumsal Ücretli İlan Başvuruları" dataTestId="corporate-listing-applications-paid-page" applicantType="corporate" applicationsMode initialDopingType="paid" /></AdminLayout>}
      />
      <Route
        path="/corporate-listing-applications/featured"
        element={<AdminLayout><AdminListingsPage title="Kurumsal Vitrin İlan Başvuruları" dataTestId="corporate-listing-applications-featured-page" applicantType="corporate" applicationsMode initialDopingType="showcase" /></AdminLayout>}
      />
      <Route
        path="/corporate-listing-applications/urgent"
        element={<AdminLayout><AdminListingsPage title="Kurumsal Acil İlan Başvuruları" dataTestId="corporate-listing-applications-urgent-page" applicantType="corporate" applicationsMode initialDopingType="urgent" /></AdminLayout>}
      />
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
      <Route
        path="/site-design/footer"
        element={
          <AdminLayout>
            <AdminRouteGuard roles={["super_admin"]}>
              <AdminFooterManagement />
            </AdminRouteGuard>
          </AdminLayout>
        }
      />
      <Route
        path="/site-design/theme"
        element={
          <AdminLayout>
            <AdminRouteGuard roles={["super_admin"]}>
              <AdminThemeManagement />
            </AdminRouteGuard>
          </AdminLayout>
        }
      />
      <Route
        path="/user-interface-design"
        element={
          <AdminLayout>
            <AdminRouteGuard roles={["super_admin", "country_admin"]}>
              <AdminUserInterfaceDesignV2 />
            </AdminRouteGuard>
          </AdminLayout>
        }
      />
      <Route
        path="/ops/publish-health"
        element={
          <AdminLayout>
            <AdminRouteGuard roles={["super_admin", "country_admin", "ops"]}>
              <AdminPublishHealthPage />
            </AdminRouteGuard>
          </AdminLayout>
        }
      />
      <Route
        path="/info-pages"
        element={
          <AdminLayout>
            <AdminRouteGuard roles={["super_admin"]}>
              <AdminInfoPages />
            </AdminRouteGuard>
          </AdminLayout>
        }
      />
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
      <Route
        path="/vehicle-master-import"
        element={
          <AdminLayout>
            <AdminRouteGuard roles={["super_admin", "masterdata_manager"]}>
              <AdminVehicleMasterImport />
            </AdminRouteGuard>
          </AdminLayout>
        }
      />
      

      <Route path="*" element={<Navigate to="/admin" replace />} />
    </Routes>
  );
}
