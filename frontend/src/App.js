import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from "@/components/ui/toaster";

// Public Pages
import HomePage from '@/pages/public/HomePage';
import SearchPage from '@/pages/public/SearchPage';
import LoginPage from '@/pages/auth/LoginPage';
import RegisterPage from '@/pages/auth/RegisterPage';

// Admin Pages
import Dashboard from '@/pages/admin/Dashboard';
import UserManagement from '@/pages/admin/UserManagement';
import FeatureFlags from '@/pages/admin/FeatureFlags';
import CountrySettings from '@/pages/admin/CountrySettings';
import Categories from '@/pages/admin/Categories';
import AdminAttributes from '@/pages/admin/AdminAttributes';
import AdminOptions from '@/pages/admin/AdminOptions';
import AdminVehicleMDM from '@/pages/admin/AdminVehicleMDM';

import { AuthProvider, useAuth } from '@/context/AuthContext';

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
          <Route path="/auth/register" element={<RegisterPage />} />

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
