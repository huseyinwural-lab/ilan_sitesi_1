import React from "react";

const ROLE_DEFINITIONS = [
  {
    key: "super_admin",
    label: "Super Admin",
    summary: "Tüm modüller + yönetim yetkileri",
  },
  {
    key: "country_admin",
    label: "Country Admin",
    summary: "Ülke kapsamlı yönetim + içerik",
  },
  {
    key: "moderator",
    label: "Moderator",
    summary: "Moderation queue + şikayet yönetimi",
  },
  {
    key: "finance",
    label: "Finance Admin",
    summary: "Finans (planlar, faturalar, vergi oranları)",
  },
  {
    key: "support",
    label: "Support Admin",
    summary: "Kullanıcı yönetimi + şikayetler",
  },
];

export default function AdminRoles() {
  return (
    <div className="space-y-6" data-testid="admin-roles-page">
      <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700" data-testid="admin-roles-readonly-banner">
        Read-only v1: Rol tanımları değiştirilemez.
      </div>
      <div className="rounded-lg border bg-white shadow-sm">
        <div className="border-b px-6 py-4">
          <h1 className="text-xl font-semibold text-gray-900" data-testid="admin-roles-title">Rol Tanımları</h1>
          <p className="text-sm text-gray-500">Role yetki özetleri aşağıdadır.</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-xs uppercase text-gray-500">
              <tr>
                <th className="px-6 py-3 text-left">Rol</th>
                <th className="px-6 py-3 text-left">Yetki Özeti</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {ROLE_DEFINITIONS.map((role) => (
                <tr key={role.key} data-testid={`admin-role-row-${role.key}`}>
                  <td className="px-6 py-4 font-medium text-gray-900">{role.label}</td>
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
