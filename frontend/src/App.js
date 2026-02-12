import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { LanguageProvider } from "./contexts/LanguageContext";
import { CountryProvider } from "./contexts/CountryContext";
import { ThemeProvider } from "./contexts/ThemeContext";

import Layout from "./components/Layout";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Users from "./pages/Users";
import Countries from "./pages/Countries";
import FeatureFlags from "./pages/FeatureFlags";
import AuditLogs from "./pages/AuditLogs";
import Categories from "./pages/Categories";
import Attributes from "./pages/Attributes";
import Invoices from "./pages/Invoices";
import MenuManager from "./pages/MenuManager";
import TaxRates from "./pages/TaxRates";
import PremiumProducts from "./pages/PremiumProducts";
import DealerManagement from "./pages/DealerManagement";
import ModerationQueue from "./pages/ModerationQueue";

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <Layout>{children}</Layout>;
}

function PublicRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );
  }

  if (user) {
    return <Navigate to="/" replace />;
  }

  return children;
}

function AppRoutes() {
  return (
    <Routes>
      <Route
        path="/login"
        element={
          <PublicRoute>
            <Login />
          </PublicRoute>
        }
      />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/users"
        element={
          <ProtectedRoute>
            <Users />
          </ProtectedRoute>
        }
      />
      <Route
        path="/countries"
        element={
          <ProtectedRoute>
            <Countries />
          </ProtectedRoute>
        }
      />
      <Route
        path="/feature-flags"
        element={
          <ProtectedRoute>
            <FeatureFlags />
          </ProtectedRoute>
        }
      />
      <Route
        path="/audit-logs"
        element={
          <ProtectedRoute>
            <AuditLogs />
          </ProtectedRoute>
        }
      />
      <Route
        path="/categories"
        element={
          <ProtectedRoute>
            <Categories />
          </ProtectedRoute>
        }
      />
      <Route
        path="/attributes"
        element={
          <ProtectedRoute>
            <Attributes />
          </ProtectedRoute>
        }
      />
      <Route
        path="/menu"
        element={
          <ProtectedRoute>
            <MenuManager />
          </ProtectedRoute>
        }
      />
      <Route
        path="/dealers"
        element={
          <ProtectedRoute>
            <DealerManagement />
          </ProtectedRoute>
        }
      />
      <Route
        path="/premium"
        element={
          <ProtectedRoute>
            <PremiumProducts />
          </ProtectedRoute>
        }
      />
      <Route
        path="/moderation"
        element={
          <ProtectedRoute>
            <ModerationQueue />
          </ProtectedRoute>
        }
      />
      <Route
        path="/invoices"
        element={
          <ProtectedRoute>
            <Invoices />
          </ProtectedRoute>
        }
      />
      <Route
        path="/tax-rates"
        element={
          <ProtectedRoute>
            <TaxRates />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <ThemeProvider>
      <LanguageProvider>
        <CountryProvider>
          <BrowserRouter>
            <AuthProvider>
              <AppRoutes />
            </AuthProvider>
          </BrowserRouter>
        </CountryProvider>
      </LanguageProvider>
    </ThemeProvider>
  );
}

export default App;
