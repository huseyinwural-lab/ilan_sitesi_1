import React from 'react';
import Layout from '@/components/Layout';
import { Link } from 'react-router-dom';

export default function PlansPage() {
  return (
    <Layout>
      <div className="space-y-3" data-testid="admin-plans-legacy-removed-page">
        <h1 className="text-2xl font-semibold" data-testid="admin-plans-legacy-removed-title">Legacy Plan Satın Alma Akışı Kaldırıldı</h1>
        <p className="text-sm text-muted-foreground" data-testid="admin-plans-legacy-removed-description">
          Legacy plan satın alma akışı P0-04 kapsamında kaldırıldı. Plan yönetimi için güncel admin plan ekranını kullanın.
        </p>
        <Link className="text-sm text-primary underline" to="/admin/plans" data-testid="admin-plans-go-current-plans">
          Güncel Plan Yönetimine Git
        </Link>
      </div>
    </Layout>
  );
}
