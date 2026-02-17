import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from "@/components/ui/toaster";

import UserPanelLayout from './layouts/UserPanelLayout';
import MyListings from './pages/user/MyListings';
import CreateListing from './pages/user/CreateListing';
import WizardContainer from './pages/user/wizard/WizardContainer';
import { HelmetProvider } from 'react-helmet-async';

// Public Pages
import HomePage from '@/pages/public/HomePage';
import SearchPage from '@/pages/public/SearchPage';
import DetailPage from '@/pages/public/DetailPage';
import VehicleLandingPage from '@/pages/public/VehicleLandingPage';
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

import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import { LanguageProvider } from '@/contexts/LanguageContext';
import { CountryProvider } from '@/contexts/CountryContext';
import { ThemeProvider } from '@/contexts/ThemeContext';

const ProtectedRoute = ({ children, roles = [] }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!user) {
    return <Navigate to="/login" />;
  }

  if (roles.length > 0 && !roles.includes(user.role)) {
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

                  {/* Vehicle (country-aware) */}
                  <Route path="/:country/vasita" element={<VehicleLandingPage />} />
                  <Route path="/:country/vasita/:segment" element={<VehicleSegmentPage />} />
                  {/* Convenience redirect */}
                  <Route path="/vasita" element={<RedirectToCountry to="/{country}/vasita" />} />

                  {/* Portal login surfaces */}
                  <Route path="/login" element={<PublicLogin />} />
                  <Route path="/dealer/login" element={<DealerLogin />} />
                  <Route path="/admin/login" element={<BackofficeLogin />} />

                  {/* Back-compat: old auth paths redirect to /login */}
                  <Route path="/auth/login" element={<Navigate to="/login" replace />} />
                  <Route path="/auth/register" element={<Navigate to="/login" replace />} />

                  {/* User Panel Routes */}
                  <Route
                    path="/account"
                    element={
                      <ProtectedRoute roles={['individual', 'dealer', 'super_admin', 'country_admin']}>
                        <UserPanelLayout />
                      </ProtectedRoute>
                    }
                  >
                    <Route index element={<Navigate to="/account/listings" />} />
                    <Route path="listings" element={<MyListings />} />
                    <Route path="create" element={<CreateListing />} />
                    <Route path="create/vehicle-wizard" element={<WizardContainer />} />
                  </Route>

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
