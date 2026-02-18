import React, { useEffect, useMemo, useState } from "react";
import axios from "axios";
import { toast } from "sonner";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const STATUS_LABELS = {
  pending: "pending",
  approved: "approved",
  rejected: "rejected",
};

const REJECT_REASONS = [
  "incomplete_documents",
  "failed_verification",
  "duplicate_application",
  "country_not_supported",
  "other",
];

export default function IndividualApplications() {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("pending");
  const [search, setSearch] = useState("");
  const [rejecting, setRejecting] = useState(null);
  const [rejectReason, setRejectReason] = useState(REJECT_REASONS[0]);
  const [rejectNote, setRejectNote] = useState("");

  const fetchApplications = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter) {
        params.append("status", statusFilter);
      }
      if (search) {
        params.append("search", search);
      }
      const response = await axios.get(`${API_URL}/api/admin/individual-applications?${params.toString()}`);
      setApplications(response.data.items || []);
    } catch (error) {
      console.error("Individual applications fetch error", error);
      toast.error("Başvurular alınamadı.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApplications();
  }, [statusFilter, search]);

  const filteredApplications = useMemo(() => {
    if (!search) return applications;
    const query = search.toLowerCase();
    return applications.filter((app) =>
      [app.full_name, app.email].some((field) =>
        (field || "").toLowerCase().includes(query)
      )
    );
  }, [applications, search]);

  const handleApprove = async (appId) => {
    try {
      await axios.post(`${API_URL}/api/admin/individual-applications/${appId}/approve`);
      toast.success("Başvuru onaylandı.");
      fetchApplications();
    } catch (error) {
      console.error("Approve error", error);
      toast.error("Onaylama işlemi başarısız.");
    }
  };

  const handleReject = async () => {
    if (!rejecting) return;
    try {
      await axios.post(`${API_URL}/api/admin/individual-applications/${rejecting}/reject`, {
        reason: rejectReason,
        reason_note: rejectNote,
      });
      toast.success("Başvuru reddedildi.");
      setRejecting(null);
      setRejectNote("");
      fetchApplications();
    } catch (error) {
      console.error("Reject error", error);
      toast.error("Red işlemi başarısız.");
    }
  };

  return (
    <div className="space-y-6" data-testid="individual-applications-page">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900" data-testid="individual-applications-title">Bireysel Üye Başvurular</h1>
          <p className="text-sm text-gray-500">Yeni üyelik başvuruları ve karar geçmişi.</p>
        </div>
        <div className="flex gap-2">
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Ara (isim/e-posta)"
            className="w-60 rounded-md border px-3 py-2 text-sm"
            data-testid="individual-applications-search"
          />
          <select
            className="rounded-md border px-3 py-2 text-sm"
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
            data-testid="individual-applications-status-filter"
          >
            <option value="">Tümü</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
          </select>
        </div>
      </div>

      <div className="overflow-hidden rounded-lg border bg-white">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
            <tr>
              <th className="px-4 py-3">Ad Soyad</th>
              <th className="px-4 py-3">E-posta</th>
              <th className="px-4 py-3">Ülke</th>
              <th className="px-4 py-3">Durum</th>
              <th className="px-4 py-3">Başvuru Tarihi</th>
              <th className="px-4 py-3 text-right">İşlem</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {loading ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-500" data-testid="individual-applications-loading">
                  Yükleniyor...
                </td>
              </tr>
            ) : filteredApplications.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-500" data-testid="individual-applications-empty">
                  Başvuru bulunamadı.
                </td>
              </tr>
            ) : (
              filteredApplications.map((app) => (
                <tr key={app.id} data-testid={`individual-application-row-${app.id}`}>
                  <td className="px-4 py-3 font-medium text-gray-900">{app.full_name || "—"}</td>
                  <td className="px-4 py-3 text-gray-600">{app.email}</td>
                  <td className="px-4 py-3 text-gray-600">{app.country_code}</td>
                  <td className="px-4 py-3">
                    <span className="rounded-full bg-gray-100 px-2 py-1 text-xs" data-testid={`individual-application-status-${app.id}`}>
                      {STATUS_LABELS[app.status] || app.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{app.created_at ? new Date(app.created_at).toLocaleString() : "—"}</td>
                  <td className="px-4 py-3 text-right">
                    {app.status === "pending" ? (
                      <div className="flex justify-end gap-2">
                        <button
                          className="rounded-md bg-emerald-600 px-3 py-1 text-xs font-semibold text-white"
                          onClick={() => handleApprove(app.id)}
                          data-testid={`individual-application-approve-${app.id}`}
                        >
                          Onayla
                        </button>
                        <button
                          className="rounded-md border border-red-200 px-3 py-1 text-xs font-semibold text-red-600"
                          onClick={() => setRejecting(app.id)}
                          data-testid={`individual-application-reject-${app.id}`}
                        >
                          Reddet
                        </button>
                      </div>
                    ) : (
                      <span className="text-xs text-gray-400">—</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {rejecting && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" data-testid="individual-application-reject-modal">
          <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-lg">
            <h2 className="text-lg font-semibold" data-testid="individual-application-reject-title">Başvuruyu Reddet</h2>
            <div className="mt-4 space-y-3">
              <select
                className="w-full rounded-md border px-3 py-2 text-sm"
                value={rejectReason}
                onChange={(event) => setRejectReason(event.target.value)}
                data-testid="individual-application-reject-reason"
              >
                {REJECT_REASONS.map((reason) => (
                  <option key={reason} value={reason}>{reason}</option>
                ))}
              </select>
              <textarea
                className="w-full rounded-md border px-3 py-2 text-sm"
                rows={3}
                value={rejectNote}
                onChange={(event) => setRejectNote(event.target.value)}
                placeholder="Not (opsiyonel)"
                data-testid="individual-application-reject-note"
              />
            </div>
            <div className="mt-6 flex justify-end gap-2">
              <button
                className="rounded-md border px-4 py-2 text-sm"
                onClick={() => setRejecting(null)}
                data-testid="individual-application-reject-cancel"
              >
                Vazgeç
              </button>
              <button
                className="rounded-md bg-red-600 px-4 py-2 text-sm text-white"
                onClick={handleReject}
                data-testid="individual-application-reject-confirm"
              >
                Reddet
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
