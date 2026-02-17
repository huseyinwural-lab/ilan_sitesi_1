import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

import Layout from '@/components/Layout';
import Dashboard from '@/pages/Dashboard';
import UserManagement from '@/pages/Users';
import FeatureFlags from '@/pages/FeatureFlags';
import CountrySettings from '@/pages/Countries';
import Categories from '@/pages/Categories';
import AdminAttributes from '@/pages/AdminAttributes';
import AdminOptions from '@/pages/AdminOptions';
import AdminVehicleMDM from '@/pages/AdminVehicleMDM';
import BillingPage from '@/pages/admin/Billing';
import PlansPage from '@/pages/admin/Plans';

import AuditLogs from '@/pages/AuditLogs';
import ModerationQueue from '@/pages/ModerationQueue';

export default function BackofficePortalApp() {
  return (
    <Routes>
      <Route path="/" element={<Layout><Dashboard /></Layout>} />
      <Route path="/users" element={<Layout><UserManagement /></Layout>} />
      <Route path="/feature-flags" element={<Layout><FeatureFlags /></Layout>} />
      <Route path="/countries" element={<Layout><CountrySettings /></Layout>} />
      <Route path="/categories" element={<Layout><Categories /></Layout>} />
      <Route path="/attributes" element={<Layout><AdminAttributes /></Layout>} />
      <Route path="/attributes/options" element={<Layout><AdminOptions /></Layout>} />
      <Route path="/audit-logs" element={<Layout><AuditLogs /></Layout>} />
      <Route path="/moderation" element={<Layout><ModerationQueue /></Layout>} />

      <Route path="/master-data/vehicles" element={<Layout><AdminVehicleMDM /></Layout>} />
      <Route path="/billing" element={<Layout><BillingPage /></Layout>} />
      <Route path="/plans" element={<Layout><PlansPage /></Layout>} />

      <Route path="*" element={<Navigate to="/admin" replace />} />
    </Routes>
  );
}
