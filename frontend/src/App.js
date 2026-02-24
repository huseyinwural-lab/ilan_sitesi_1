import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from "@/components/ui/toaster";

import AccountLayout from './layouts/AccountLayout';
import MyListings from './pages/user/MyListings';
import WizardContainer from './pages/user/wizard/WizardContainer';
import CreateListing from './pages/user/CreateListing';
import AccountDashboard from './pages/user/AccountDashboard';
import AccountFavorites from './pages/user/AccountFavorites';
import AccountMessages from './pages/user/AccountMessages';
import AccountSupportList from './pages/user/AccountSupportList';
import AccountSupportDetail from './pages/user/AccountSupportDetail';
import AccountProfile from './pages/user/AccountProfile';
import AccountPrivacyCenter from './pages/user/AccountPrivacyCenter';
import { HelmetProvider } from 'react-helmet-async';

// Public Pages
import HomePage from '@/pages/public/HomePage';
import SearchPage from '@/pages/public/SearchPage';
import DetailPage from '@/pages/public/DetailPage';
import VehicleLandingPage from '@/pages/public/VehicleLandingPage';
import VehicleMakeModelPage from '@/pages/public/VehicleMakeModelPage';
import VehicleSegmentPage from '@/pages/public/VehicleSegmentPage';
import RedirectToCountry from '@/pages/public/RedirectToCountry';
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
import ListingCategorySelect from '@/pages/listing/ListingCategorySelect';
import ListingDetails from '@/pages/listing/ListingDetails';

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

function App() {
  return (
    <HelmetProvider>
      <AuthProvider>
        <LanguageProvider>
          <CountryProvider>
            <ThemeProvider>
              <BrowserRouter>
                <Routes>
                  {/* Public Routes */}
                  <Route path="/" element={<HomePage />} />
                  <Route path="/search" element={<SearchPage />} />
                  <Route path="/ilan/:id" element={<DetailPage />} /> {/* P8: Detail Route (captures slug-id) */}
                  <Route path="/vasita/otomobil/:make/:model" element={<VehicleMakeModelPage />} />
                  <Route path="/:country/vasita/otomobil/:make/:model" element={<VehicleMakeModelPage />} />
                  <Route path="/ilan-olustur" element={<Navigate to="/ilan-ver/kategori-secimi" />} />

                  {/* Vehicle (country-aware) */}
                  <Route path="/:country/vasita" element={<VehicleLandingPage />} />
                  <Route path="/:country/vasita/:segment" element={<VehicleSegmentPage />} />
                  {/* Convenience redirect */}
                  <Route path="/vasita" element={<RedirectToCountry to="/{country}/vasita" />} />

                  {/* Portal login surfaces */}
                  <Route path="/login" element={<PublicLogin />} />
                  <Route path="/dealer/login" element={<DealerLogin />} />
                  <Route path="/register" element={<Register portalContext="account" />} />
                  <Route path="/dealer/register" element={<Register portalContext="dealer" />} />
                  <Route path="/verify-email" element={<VerifyEmail portalContext="account" />} />
                  <Route path="/dealer/verify-email" element={<VerifyEmail portalContext="dealer" />} />
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
                  <Route path="/user/profile" element={<Navigate to="/account/profile" replace />} />
                  <Route path="/dealer/dashboard" element={<Navigate to="/dealer" replace />} />

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
                    <Route path="favorites" element={<AccountFavorites />} />
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
                    path="/ilan-ver/kategori-secimi"
                    element={
                      <ProtectedRoute portalScope="account">
                        <ListingCategorySelect />
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

                  {/* Fallback */}
                  <Route path="*" element={<Navigate to="/" />} />
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
