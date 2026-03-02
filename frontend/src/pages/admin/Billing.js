import React from 'react';
import Layout from '@/components/Layout';
import { Link } from 'react-router-dom';

export default function BillingPage() {
  return (
    <Layout>
      <div className="space-y-3" data-testid="admin-billing-legacy-removed-page">
        <h1 className="text-2xl font-semibold" data-testid="admin-billing-legacy-removed-title">Billing Sayfası Kaldırıldı</h1>
        <p className="text-sm text-muted-foreground" data-testid="admin-billing-legacy-removed-description">
          Legacy billing akışı P0-04 kapsamında kaldırıldı. Finans işlemleri için güncel ekranları kullanın.
        </p>
        <div className="flex flex-wrap items-center gap-3" data-testid="admin-billing-legacy-removed-links">
          <Link className="text-sm text-primary underline" to="/admin/finance-overview" data-testid="admin-billing-go-finance-overview">
            Finans Overview
          </Link>
          <Link className="text-sm text-primary underline" to="/admin/invoices" data-testid="admin-billing-go-invoices">
            Faturalar
          </Link>
          <Link className="text-sm text-primary underline" to="/admin/payments" data-testid="admin-billing-go-payments">
            Transactions Log
          </Link>
        </div>
      </div>
    </Layout>
  );
}
