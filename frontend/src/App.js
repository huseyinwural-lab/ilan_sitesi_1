import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from "@/components/ui/toaster";

// Public Pages
import HomePage from '@/pages/public/HomePage';
import SearchPage from '@/pages/public/SearchPage';
import LoginPage from '@/pages/Login';

// Admin Pages
import Dashboard from '@/pages/Dashboard';
import UserManagement from '@/pages/Users';
import FeatureFlags from '@/pages/FeatureFlags';
import CountrySettings from '@/pages/Countries';
import Categories from '@/pages/Categories';
import AdminAttributes from '@/pages/AdminAttributes';
import AdminOptions from '@/pages/AdminOptions';
import AdminVehicleMDM from '@/pages/AdminVehicleMDM';

import { AuthProvider, useAuth } from '@/contexts/AuthContext';

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
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<HomePage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/auth/login" element={<LoginPage />} />
          <Route path="/auth/register" element={<LoginPage />} /> {/* Temporary redirect to login */}

          {/* Admin Routes */}
          <Route
            path="/admin"
            element={
              <ProtectedRoute roles={['super_admin', 'country_admin', 'moderator', 'support', 'finance']}>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/users"
            element={
              <ProtectedRoute roles={['super_admin', 'country_admin']}>
                <UserManagement />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/feature-flags"
            element={
              <ProtectedRoute roles={['super_admin', 'country_admin']}>
                <FeatureFlags />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/countries"
            element={
              <ProtectedRoute roles={['super_admin', 'country_admin']}>
                <CountrySettings />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/categories"
            element={
              <ProtectedRoute roles={['super_admin', 'country_admin']}>
                <Categories />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/attributes"
            element={
              <ProtectedRoute roles={['super_admin', 'country_admin']}>
                <AdminAttributes />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/attributes/options"
            element={
              <ProtectedRoute roles={['super_admin', 'country_admin']}>
                <AdminOptions />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/master-data/vehicles"
            element={
              <ProtectedRoute roles={['super_admin', 'country_admin']}>
                <AdminVehicleMDM />
              </ProtectedRoute>
            }
          />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
        <Toaster />
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
