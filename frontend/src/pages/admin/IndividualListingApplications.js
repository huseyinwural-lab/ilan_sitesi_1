import React from "react";
import AdminPlaceholder from "../../components/AdminPlaceholder";

export default function IndividualListingApplications() {
  return (
    <AdminPlaceholder
      title="Bireysel İlan Başvuruları"
      description="Bu görünüm Moderation Queue filtresi üzerinden yönetilir. Şimdilik Moderation Queue kullanınız."
      status="PLACEHOLDER"
      note="Dealer/individual ayrımı API’de netleştiğinde filtreli görünüm aktive edilecek."
      testId="individual-listing-applications-placeholder"
      actionLabel="Moderation Queue'a Git"
      actionHref="/admin/moderation"
    />
  );
}
