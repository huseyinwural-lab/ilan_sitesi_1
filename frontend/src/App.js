import React from 'react';
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
import LoginPage from '@/pages/Login';

// Admin Pages
import React, { Suspense, lazy } from 'react';

import PortalGate from '@/shared/auth/PortalGate';
import { PORTALS } from '@/shared/types/portals';

const BackofficePortalApp = lazy(() => import('@/portals/backoffice/BackofficePortalApp'));
const DealerPortalApp = lazy(() => import('@/portals/dealer/DealerPortalApp'));

// Login shells (kept simple; same Login component for now)
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
    return <Navigate to="/auth/login" />;
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

                  <Route path="/auth/login" element={<LoginPage />} />
                  <Route path="/auth/register" element={<LoginPage />} /> {/* Temporary redirect to login */}

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

                  {/* Admin Routes */}
                  <Route
                    path="/admin"
                    element={
                      <ProtectedRoute roles={['super_admin', 'country_admin', 'moderator', 'support', 'finance']}>
                        <Layout>
                          <Dashboard />
                        </Layout>
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/admin/users"
                    element={
                      <ProtectedRoute roles={['super_admin', 'country_admin']}>
                        <Layout>
                          <UserManagement />
                        </Layout>
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/admin/feature-flags"
                    element={
                      <ProtectedRoute roles={['super_admin', 'country_admin']}>
                        <Layout>
                          <FeatureFlags />
                        </Layout>
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/admin/countries"
                    element={
                      <ProtectedRoute roles={['super_admin', 'country_admin']}>
                        <Layout>
                          <CountrySettings />
                        </Layout>
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/admin/categories"
                    element={
                      <ProtectedRoute roles={['super_admin', 'country_admin']}>
                        <Layout>
                          <Categories />
                        </Layout>
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/admin/attributes"
                    element={
                      <ProtectedRoute roles={['super_admin', 'country_admin']}>
                        <Layout>
                          <AdminAttributes />
                        </Layout>
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/admin/attributes/options"
                    element={
                      <ProtectedRoute roles={['super_admin', 'country_admin']}>
                        <Layout>
                          <AdminOptions />
                        </Layout>
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/admin/master-data/vehicles"
                    element={
                      <ProtectedRoute roles={['super_admin', 'country_admin']}>
                        <Layout>
                          <AdminVehicleMDM />
                        </Layout>
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/admin/billing"
                    element={
                      <ProtectedRoute roles={['super_admin', 'country_admin', 'dealer']}>
                        <Layout>
                          <BillingPage />
                        </Layout>
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/admin/plans"
                    element={
                      <ProtectedRoute roles={['super_admin', 'country_admin', 'dealer', 'individual']}>
                        <Layout>
                          <PlansPage />
                        </Layout>
                      </ProtectedRoute>
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
