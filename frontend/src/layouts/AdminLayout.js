import React from 'react';
import Layout from '@/components/Layout';

export default function AdminLayout({ children }) {
  return (
    <div data-testid="admin-layout">
      <Layout>{children}</Layout>
    </div>
  );
}
