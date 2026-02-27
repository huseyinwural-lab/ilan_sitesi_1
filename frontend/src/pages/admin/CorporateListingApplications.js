import React from "react";
import AdminListingsPage from "./AdminListings";

export default function CorporateListingApplications() {
  return (
    <AdminListingsPage
      title="Kurumsal İlan Başvuruları"
      dataTestId="corporate-listing-applications-page"
      applicantType="corporate"
      applicationsMode
    />
  );
}
