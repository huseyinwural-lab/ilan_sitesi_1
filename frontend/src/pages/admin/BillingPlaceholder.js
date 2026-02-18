import React from "react";
import AdminPlaceholder from "../../components/AdminPlaceholder";

export default function BillingPlaceholder() {
  return (
    <AdminPlaceholder
      title="Ödemeler (Billing)"
      description="Ödeme kayıtları v1 kapsamında henüz bulunmuyor."
      status="P1"
      note="Finans ödeme entegrasyonu tamamlandığında aktive edilecektir."
      testId="billing-placeholder"
    />
  );
}
