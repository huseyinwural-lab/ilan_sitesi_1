import React from "react";
import AdminPlaceholder from "../../components/AdminPlaceholder";

export default function CorporateListingApplications() {
  return (
    <AdminPlaceholder
      title="Kurumsal İlan Başvuruları"
      description="Bu görünüm Moderation Queue filtresi üzerinden yönetilir. Şimdilik Moderation Queue kullanınız."
      status="PLACEHOLDER"
      note="Dealer/individual ayrımı API’de netleştiğinde filtreli görünüm aktive edilecek."
      testId="corporate-listing-applications-placeholder"
      actionLabel="Moderation Queue'a Git"
      actionHref="/admin/moderation"
    />
  );
}
