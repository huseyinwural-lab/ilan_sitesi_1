import React from "react";

const PERMISSIONS = [
  "Dashboard",
  "Yönetim",
  "Üyeler",
  "İlan & Moderasyon",
  "Katalog & İçerik",
  "Araç Verisi",
  "Finans",
  "Sistem",
];

const ROLE_MATRIX = {
  super_admin: ["Dashboard", "Yönetim", "Üyeler", "İlan & Moderasyon", "Katalog & İçerik", "Araç Verisi", "Finans", "Sistem"],
  country_admin: ["Dashboard", "Üyeler", "İlan & Moderasyon", "Katalog & İçerik", "Araç Verisi", "Sistem"],
  moderator: ["İlan & Moderasyon", "Katalog & İçerik"],
  finance_admin: ["Dashboard", "Finans"],
  support_admin: ["Üyeler", "İlan & Moderasyon"],
};

const ROLE_LABELS = {
  super_admin: "Super Admin",
  country_admin: "Country Admin",
  moderator: "Moderator",
  finance_admin: "Finance Admin",
  support_admin: "Support Admin",
};

export default function RBACMatrix() {
  return (
    <div className="space-y-6" data-testid="rbac-matrix-page">
      <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700" data-testid="rbac-matrix-readonly-banner">
        Read-only v1: RBAC matrisi değiştirilemez. Değişiklik talepleri audit workflow ile ilerler.
      </div>
      <div className="rounded-lg border bg-white shadow-sm">
        <div className="border-b px-6 py-4">
          <h1 className="text-xl font-semibold text-gray-900" data-testid="rbac-matrix-title">Yetki Atama (RBAC Matrix)</h1>
          <p className="text-sm text-gray-500">Roller ve izin alanları özet görünüm.</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-xs uppercase text-gray-500">
              <tr>
                <th className="px-6 py-3 text-left">Rol</th>
                {PERMISSIONS.map((perm) => (
                  <th key={perm} className="px-4 py-3 text-center">{perm}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y">
              {Object.keys(ROLE_MATRIX).map((roleKey) => (
                <tr key={roleKey} data-testid={`rbac-row-${roleKey}`}>
                  <td className="px-6 py-4 font-medium text-gray-900">{ROLE_LABELS[roleKey]}</td>
                  {PERMISSIONS.map((perm) => (
                    <td key={perm} className="px-4 py-4 text-center">
                      <span
                        className={ROLE_MATRIX[roleKey].includes(perm) ? "text-emerald-600" : "text-gray-300"}
                        data-testid={`rbac-cell-${roleKey}-${perm.replace(/\s+/g, '-').toLowerCase()}`}
                      >
                        {ROLE_MATRIX[roleKey].includes(perm) ? "✓" : "—"}
                      </span>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
