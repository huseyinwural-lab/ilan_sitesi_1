import React, { Suspense, lazy, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Toaster } from "@/components/ui/toaster";

import AccountLayout from './layouts/AccountLayout';
import MyListings from './pages/user/MyListings';
import WizardContainer from './pages/user/wizard/WizardContainer';
import CreateListing from './pages/user/CreateListing';
import AccountDashboard from './pages/user/AccountDashboard';
import AccountFavorites from './pages/user/AccountFavorites';
import AccountSavedSearches from './pages/user/AccountSavedSearches';
import AccountMessages from './pages/user/AccountMessages';
import AccountSupportList from './pages/user/AccountSupportList';
import AccountSupportDetail from './pages/user/AccountSupportDetail';
import AccountInvoicesPage from './pages/user/AccountInvoices';
import AccountPaymentsPage from './pages/user/AccountPayments';
import AccountSubscriptionPage from './pages/user/AccountSubscription';
import AccountProfile from './pages/user/AccountProfile';
import AccountPrivacyCenter from './pages/user/AccountPrivacyCenter';
import { HelmetProvider } from 'react-helmet-async';

// Public Pages
import ErrorBoundary from '@/components/ErrorBoundary';
import MainLayout from '@/layouts/MainLayout';
import HomePageRefreshed from '@/pages/public/HomePageRefreshed';
import SearchPage from '@/pages/public/SearchPage';
import DetailPage from '@/pages/public/DetailPage';
import CategoryLandingPage from '@/pages/public/CategoryLandingPage';
import VehicleLandingPage from '@/pages/public/VehicleLandingPage';
import VehicleMakeModelPage from '@/pages/public/VehicleMakeModelPage';
import VehicleSegmentPage from '@/pages/public/VehicleSegmentPage';
import RedirectToCountry from '@/pages/public/RedirectToCountry';
import InfoPage from '@/pages/public/InfoPage';
import NotFoundPage from '@/pages/public/NotFoundPage';
import ServerErrorPage from '@/pages/public/ServerErrorPage';
import MaintenancePage from '@/pages/public/MaintenancePage';
import TrustCenterPage from '@/pages/public/TrustCenterPage';
import CorporateHubPage from '@/pages/public/CorporateHubPage';
import SeoHubPage from '@/pages/public/SeoHubPage';
// Login moved under portal-specific paths

// Admin/Dealer Portal (lazy)

import PortalGate from '@/shared/auth/PortalGate';
import { PORTALS } from '@/shared/types/portals';

const BackofficePortalApp = lazy(() => import('@/portals/backoffice/BackofficePortalApp'));
const DealerPortalApp = lazy(() => import('@/portals/dealer/DealerPortalApp'));

// Login shells (kept in main bundle to satisfy no-chunk-load on redirects)
import PublicLogin from '@/portals/public/PublicLogin';
import DealerLogin from '@/portals/dealer/DealerLogin';
import BackofficeLogin from '@/portals/backoffice/BackofficeLogin';
import AdminInviteAccept from '@/pages/admin/AdminInviteAccept';
import SupportPage from '@/pages/Support';
import Register from '@/pages/Register';
import VerifyEmail from '@/pages/VerifyEmail';
import GoogleCallbackPage from '@/pages/auth/GoogleCallbackPage';
import ListingCategorySelect from '@/pages/listing/ListingCategorySelect';
import VehicleSelector from '@/pages/listing/VehicleSelector';
import ListingDetails from '@/pages/listing/ListingDetails';
import ListingPreview from '@/pages/listing/ListingPreview';
import ListingDoping from '@/pages/listing/ListingDoping';
import ListingEditEntry from '@/pages/listing/ListingEditEntry';

import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import { LanguageProvider } from '@/contexts/LanguageContext';
import { CountryProvider } from '@/contexts/CountryContext';
import { ThemeProvider } from '@/contexts/ThemeContext';

const ProtectedRoute = ({ children, roles = [], portalScope = null }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return <div data-testid="route-loading">Loading...</div>;
  }

  if (!user) {
    return <Navigate to="/login" />;
  }

  if (user.is_verified === false && (portalScope === 'account' || portalScope === 'dealer')) {
    const verifyPath = portalScope === 'dealer' ? '/dealer/verify-email' : '/verify-email';
    return <Navigate to={verifyPath} replace state={{ email: user.email }} />;
  }

  if (portalScope && user.portal_scope && user.portal_scope !== portalScope) {
    return <Navigate to="/" />;
  }

  if (roles.length > 0 && !roles.includes(user.role)) {
    return <Navigate to="/" />;
  }

  return children;
};

const AccountRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return <div data-testid="account-route-loading">Loading...</div>;
  }

  if (!user) {
    return <Navigate to="/login" />;
  }

  if (user.is_verified === false) {
    return <Navigate to="/verify-email" replace state={{ email: user.email }} />;
  }

  const portalScope = user.portal_scope || null;

  if (portalScope === 'dealer') {
    return <Navigate to="/dealer" />;
  }

  if (portalScope === 'admin') {
    return <Navigate to="/admin" />;
  }

  if (portalScope !== 'account') {
    return <Navigate to="/" />;
  }

  return children;
};

const CanonicalRouteSync = () => {
  const location = useLocation();

  useEffect(() => {
    const canonicalElement = document.querySelector('link[rel="canonical"]') || document.createElement('link');
    canonicalElement.setAttribute('rel', 'canonical');

    let pathname = location.pathname || '/';
    pathname = pathname.replace(/\/+/g, '/');
    if (pathname !== '/' && pathname.endsWith('/')) {
      pathname = pathname.slice(0, -1);
    }
    const canonicalHref = `${window.location.origin}${pathname || '/'}`;
    canonicalElement.setAttribute('href', canonicalHref);

    if (!canonicalElement.parentNode) {
      document.head.appendChild(canonicalElement);
    }
  }, [location.pathname]);

  return null;
};

function App() {
  return (
    <HelmetProvider>
      <AuthProvider>
        <LanguageProvider>
          <CountryProvider>
            <ThemeProvider>
              <BrowserRouter>
                <CanonicalRouteSync />
                <Routes>
                  {/* Public Routes */}
                  <Route element={<MainLayout />}>
                    <Route path="/" element={<HomePageRefreshed />} />
                    <Route path="/search" element={<SearchPage />} />
                    <Route path="/kategori/:slug" element={<CategoryLandingPage />} />
                    <Route path="/ilan/:id" element={<ErrorBoundary><DetailPage /></ErrorBoundary>} />
                    <Route path="/vasita/otomobil/:make/:model" element={<VehicleMakeModelPage />} />
                    <Route path="/:country/vasita/otomobil/:make/:model" element={<VehicleMakeModelPage />} />
                    <Route path="/ilan-olustur" element={<Navigate to="/ilan-ver/kategori-secimi" />} />

                    {/* Vehicle (country-aware) */}
                    <Route path="/:country/vasita" element={<VehicleLandingPage />} />
                    <Route path="/:country/vasita/:segment" element={<VehicleSegmentPage />} />
                    <Route path="/vasita" element={<RedirectToCountry to="/{country}/vasita" />} />
                    <Route path="/info/:slug" element={<InfoPage />} />
                    <Route path="/bilgi/:slug" element={<InfoPage />} />
                    <Route path="/trust" element={<TrustCenterPage />} />
                    <Route path="/kurumsal" element={<CorporateHubPage />} />
                    <Route path="/seo" element={<SeoHubPage />} />
                    <Route path="/500" element={<ServerErrorPage />} />
                    <Route path="/maintenance" element={<MaintenancePage />} />
                    <Route path="*" element={<NotFoundPage />} />
                  </Route>

                  {/* Portal login surfaces */}
                  <Route path="/login" element={<PublicLogin />} />
                  <Route path="/dealer/login" element={<DealerLogin />} />
                  <Route path="/register" element={<Register portalContext="account" />} />
                  <Route path="/dealer/register" element={<Register portalContext="dealer" />} />
                  <Route path="/verify-email" element={<VerifyEmail portalContext="account" />} />
                  <Route path="/dealer/verify-email" element={<VerifyEmail portalContext="dealer" />} />
                  <Route path="/auth/google/callback" element={<GoogleCallbackPage />} />
                  <Route path="/admin/invite/accept" element={<AdminInviteAccept />} />
                  <Route path="/admin/login" element={<BackofficeLogin />} />

                  {/* Back-compat: old auth paths redirect to /login */}
                  <Route path="/auth/login" element={<Navigate to="/login" replace />} />
                  <Route path="/auth/register" element={<Navigate to="/login" replace />} />

                  {/* Legacy consumer redirects */}
                  <Route path="/dashboard" element={<Navigate to="/account" replace />} />
                  <Route path="/account/dashboard" element={<Navigate to="/account" replace />} />
                  <Route path="/user" element={<Navigate to="/account" replace />} />
                  <Route path="/user/listings" element={<Navigate to="/account/listings" replace />} />
                  <Route path="/user/favorites" element={<Navigate to="/account/favorites" replace />} />
                  <Route path="/user/messages" element={<Navigate to="/account/messages" replace />} />
                  <Route path="/user/support" element={<Navigate to="/account/support" replace />} />
                  <Route path="/user/profile" element={<Navigate to="/account/security" replace />} />
                  <Route path="/dealer/dashboard" element={<Navigate to="/dealer/overview" replace />} />

                  {/* User Panel Routes */}
                  <Route
                    path="/account"
                    element={
                      <AccountRoute>
                        <AccountLayout />
                      </AccountRoute>
                    }
                  >
                    <Route index element={<AccountDashboard />} />
                    <Route path="listings" element={<MyListings />} />
                    <Route path="invoices" element={<AccountInvoicesPage />} />
                    <Route path="payments" element={<AccountPaymentsPage />} />
                    <Route path="subscription" element={<AccountSubscriptionPage />} />
                    <Route path="favorites" element={<AccountFavorites />} />
                    <Route path="saved-searches" element={<AccountSavedSearches />} />
                    <Route path="messages" element={<AccountMessages />} />
                    <Route path="support" element={<AccountSupportList />} />
                    <Route path="support/:id" element={<AccountSupportDetail />} />
                    <Route path="profile" element={<Navigate to="/account/security" replace />} />
                    <Route path="security" element={<AccountProfile />} />
                    <Route path="privacy" element={<AccountPrivacyCenter />} />
                    <Route path="create" element={<Navigate to="/ilan-ver/kategori-secimi" />} />
                    <Route path="create/vehicle-wizard" element={<WizardContainer />} />
                    <Route path="create/listing-wizard" element={<CreateListing />} />
                  </Route>

                  <Route
                    path="/ilan-ver"
                    element={
                      <ProtectedRoute portalScope="account">
                        <ListingCategorySelect />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/ilan-ver/kategori-secimi"
                    element={<Navigate to="/ilan-ver" replace />}
                  />
                  <Route
                    path="/ilan-ver/arac-sec"
                    element={
                      <ProtectedRoute portalScope="account">
                        <VehicleSelector />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/ilan-ver/detaylar"
                    element={
                      <ProtectedRoute portalScope="account">
                        <ListingDetails />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/ilan-duzenle/:id"
                    element={
                      <ProtectedRoute portalScope="account">
                        <ListingEditEntry />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/ilan-ver/onizleme"
                    element={
                      <ProtectedRoute portalScope="account">
                        <ListingPreview />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/ilan-ver/doping"
                    element={
                      <ProtectedRoute portalScope="account">
                        <ListingDoping />
                      </ProtectedRoute>
                    }
                  />

                  <Route
                    path="/support"
                    element={
                      <ProtectedRoute portalScope="account">
                        <SupportPage />
                      </ProtectedRoute>
                    }
                  />

                  {/* Backoffice Portal (lazy chunk) */}
                  <Route
                    path="/admin/*"
                    element={
                      <PortalGate portal={PORTALS.BACKOFFICE} loginPath="/admin/login">
                        <Suspense fallback={<div>Loading...</div>}>
                          <BackofficePortalApp />
                        </Suspense>
                      </PortalGate>
                    }
                  />

                  {/* Dealer Portal (lazy chunk) */}
                  <Route
                    path="/dealer/*"
                    element={
                      <PortalGate portal={PORTALS.DEALER} loginPath="/dealer/login">
                        <Suspense fallback={<div>Loading...</div>}>
                          <DealerPortalApp />
                        </Suspense>
                      </PortalGate>
                    }
                  />
                </Routes>
                <Toaster />
              </BrowserRouter>
            </ThemeProvider>
          </CountryProvider>
        </LanguageProvider>
      </AuthProvider>
    </HelmetProvider>
  );
}

export default App;
