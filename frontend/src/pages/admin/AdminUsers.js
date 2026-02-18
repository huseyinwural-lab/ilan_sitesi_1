import React from "react";
import Users from "../Users";

const ADMIN_ROLES = [
  "super_admin",
  "country_admin",
  "moderator",
  "finance",
  "support",
];

export default function AdminUsers() {
  return (
    <div className="space-y-4" data-testid="admin-users-page">
      <div
        className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700"
        data-testid="admin-users-readonly-banner"
      >
        Read-only v1: Yeni admin oluşturma ve rol değişimi devre dışı.
      </div>
      <Users
        title="Admin Kullanıcıları"
        allowedRoles={ADMIN_ROLES}
        readOnly
        showRoleFilter={false}
        emptyStateLabel="Admin kullanıcı bulunamadı"
      />
    </div>
  );
}
