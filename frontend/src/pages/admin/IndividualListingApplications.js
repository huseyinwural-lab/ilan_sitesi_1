import React from "react";
import AdminListingsPage from "./AdminListings";

export default function IndividualListingApplications() {
  return (
    <AdminListingsPage
      title="Bireysel İlan Başvuruları"
      dataTestId="individual-listing-applications-page"
      applicantType="individual"
      applicationsMode
    />
  );
}
