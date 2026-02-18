import React from "react";
import ModerationQueue from "../ModerationQueue";

export default function CorporateListingApplications() {
  return (
    <ModerationQueue
      title="Kurumsal İlan Başvuruları"
      description="Kurumsal (dealer) ilan başvuruları ve moderasyon aksiyonları."
      dealerOnly={true}
      pageTestId="corporate-listing-applications-page"
    />
  );
}
