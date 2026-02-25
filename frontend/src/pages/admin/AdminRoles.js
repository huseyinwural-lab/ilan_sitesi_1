import React from "react";

const ROLE_DEFINITIONS = [
  {
    key: "SUPER_ADMIN",
    label: "SUPER_ADMIN",
    runtime: "super_admin",
    summary: "Tüm admin modülleri + RBAC yönetimi",
  },
  {
    key: "ADMIN",
    label: "ADMIN",
    runtime: "country_admin",
    summary: "Ülke kapsamlı yönetim + içerik",
  },
  {
    key: "MODERATOR",
    label: "MODERATOR",
    runtime: "moderator",
    summary: "Moderation queue + ilan aksiyonları",
  },
  {
    key: "SUPPORT",
    label: "SUPPORT",
    runtime: "support",
    summary: "Üye operasyonları + destek",
  },
  {
    key: "DEALER_ADMIN",
    label: "DEALER_ADMIN",
    runtime: "dealer",
    summary: "Dealer portal yönetimi (v1 ayrım yok)",
  },
  {
    key: "DEALER_USER",
    label: "DEALER_USER",
    runtime: "dealer",
    summary: "Dealer portal standart kullanım (v1 ayrım yok)",
  },
  {
    key: "CONSUMER",
    label: "CONSUMER",
    runtime: "individual",
    summary: "Consumer portal kullanım",
  },
  {
    key: "MASTERDATA_MANAGER",
    label: "MASTERDATA_MANAGER",
    runtime: "masterdata_manager",
    summary: "Araç Master Data Import modülü",
  },
  {
    key: "AUDIT_VIEWER",
    label: "AUDIT_VIEWER (legacy)",
    runtime: "ROLE_AUDIT_VIEWER / audit_viewer",
    summary: "Denetim kayıtlarını görüntüleme",
  },
  {
    key: "CAMPAIGNS_ADMIN",
    label: "CAMPAIGNS_ADMIN (legacy)",
    runtime: "campaigns_admin",
    summary: "Kampanyalar admin yetkileri",
  },
  {
    key: "CAMPAIGNS_SUPERVISOR",
    label: "CAMPAIGNS_SUPERVISOR (legacy)",
    runtime: "campaigns_supervisor",
    summary: "Kampanya onay/denetim",
  },
];

export default function AdminRoles() {
  return (
    <div className="space-y-6" data-testid="admin-roles-page">
      <div
        className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700"
        data-testid="admin-roles-readonly-banner"
      >
        Read-only v1: Rol tanımları değiştirilemez.
      </div>
      <div className="rounded-lg border bg-white shadow-sm">
        <div className="border-b px-6 py-4">
          <h1 className="text-xl font-semibold text-gray-900" data-testid="admin-roles-title">
            Rol Tanımları
          </h1>
          <p className="text-sm text-gray-500">Kanonik roller ve runtime eşlemesi.</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-xs uppercase text-gray-500">
              <tr>
                <th className="px-6 py-3 text-left">Rol</th>
                <th className="px-6 py-3 text-left">Runtime Rol</th>
                <th className="px-6 py-3 text-left">Yetki Özeti</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {ROLE_DEFINITIONS.map((role) => (
                <tr key={role.key} data-testid={`admin-role-row-${role.key.toLowerCase()}`}>
                  <td className="px-6 py-4 font-medium text-gray-900">{role.label}</td>
                  <td className="px-6 py-4 text-gray-600">{role.runtime}</td>
                  <td className="px-6 py-4 text-gray-600">{role.summary}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
