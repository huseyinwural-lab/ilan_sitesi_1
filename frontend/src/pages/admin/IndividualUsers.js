import React from "react";
import Users from "../Users";

const INDIVIDUAL_ROLES = ["user", "individual"];

export default function IndividualUsers() {
  return (
    <div className="space-y-4" data-testid="individual-users-page">
      <Users
        title="Bireysel Kullanıcılar"
        allowedRoles={INDIVIDUAL_ROLES}
        readOnly
        showRoleFilter={false}
        emptyStateLabel="Bireysel kullanıcı bulunamadı"
      />
    </div>
  );
}
