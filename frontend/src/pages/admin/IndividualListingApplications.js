import React from "react";
import ModerationQueue from "../ModerationQueue";

export default function IndividualListingApplications() {
  return (
    <ModerationQueue
      title="Bireysel İlan Başvuruları"
      description="Bireysel kullanıcı ilan başvuruları ve moderasyon aksiyonları."
      dealerOnly={false}
      pageTestId="individual-listing-applications-page"
    />
  );
}
