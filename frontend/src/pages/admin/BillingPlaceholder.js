import React from "react";
import AdminPlaceholder from "../../components/AdminPlaceholder";

export default function BillingPlaceholder() {
  return (
    <AdminPlaceholder
      title="Legacy Billing Kaldırıldı"
      description="Bu placeholder P0-04 kapsamında pasif bırakıldı."
      status="DONE"
      note="Güncel finans ekranları: /admin/finance-overview, /admin/invoices, /admin/payments"
      testId="admin-billing-placeholder-removed"
    />
  );
}
