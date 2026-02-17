import { useEffect, useMemo, useState } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const REJECT_REASONS_V1 = [
  { value: 'incomplete_documents', label: 'incomplete_documents' },
  { value: 'invalid_company_info', label: 'invalid_company_info' },
  { value: 'duplicate_application', label: 'duplicate_application' },
  { value: 'compliance_issue', label: 'compliance_issue' },
  { value: 'other', label: 'other' },
];

export default function DealerApplicationsPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState('pending');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);

  const [actionDialog, setActionDialog] = useState(null); // { app, action }
  const [reason, setReason] = useState('');
  const [reasonNote, setReasonNote] = useState('');

  const limit = 20;

  const authHeader = useMemo(() => ({
    Authorization: `Bearer ${localStorage.getItem('access_token')}`,
  }), []);

  const fetchApps = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set('skip', String(page * limit));
      params.set('limit', String(limit));
      if (status) params.set('status', status);
      if (search) params.set('search', search);

      const res = await axios.get(`${API}/admin/dealer-applications?${params.toString()}`, {
        headers: authHeader,
      });
      setItems(res.data.items || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApps();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, search, page]);

  const approve = async (app) => {
    const res = await axios.post(`${API}/admin/dealer-applications/${app.id}/approve`, {}, { headers: authHeader });
    alert(`Approved. Temp password: ${res.data?.dealer_user?.temp_password}`);
    await fetchApps();
  };

  const reject = async (app, payload) => {
    await axios.post(`${API}/admin/dealer-applications/${app.id}/reject`, payload, { headers: authHeader });
    await fetchApps();
  };

  const openReject = (app) => {
    setActionDialog({ app, action: 'reject' });
    setReason('');
    setReasonNote('');
  };

  const submitReject = async () => {
    if (!actionDialog?.app) return;
    if (!reason) {
      alert('Reason is required');
      return;
    }
    if (reason === 'other' && !reasonNote.trim()) {
      alert('Reason note is required for other');
      return;
    }

    await reject(actionDialog.app, { reason, reason_note: reason === 'other' ? reasonNote.trim() : undefined });
    setActionDialog(null);
  };

  return (
    <div className="space-y-6" data-testid="admin-dealer-applications-page">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Başvurular</h1>
        <p className="text-sm text-muted-foreground">Dealer Onboarding (Sprint 1.2)</p>
      </div>

      <div className="flex flex-wrap gap-3">
        <input
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(0); }}
          placeholder="Search (email/company)"
          className="h-9 px-3 rounded-md border bg-background text-sm"
        />
        <select
          value={status}
          onChange={(e) => { setStatus(e.target.value); setPage(0); }}
          className="h-9 px-3 rounded-md border bg-background text-sm"
        >
          <option value="pending">pending</option>
          <option value="approved">approved</option>
          <option value="rejected">rejected</option>
        </select>
      </div>

      <div className="rounded-md border bg-card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-muted">
            <tr>
              <th className="text-left p-3">Email</th>
              <th className="text-left p-3">Company</th>
              <th className="text-left p-3">Country</th>
              <th className="text-left p-3">Status</th>
              <th className="text-right p-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={5} className="p-6 text-center">Loading…</td></tr>
            ) : items.length === 0 ? (
              <tr><td colSpan={5} className="p-6 text-center text-muted-foreground">No applications</td></tr>
            ) : (
              items.map((a) => (
                <tr key={a.id} className="border-t">
                  <td className="p-3">{a.email}</td>
                  <td className="p-3">{a.company_name}</td>
                  <td className="p-3 text-muted-foreground">{a.country_code}</td>
                  <td className="p-3"><span className="font-mono text-xs">{a.status}</span></td>
                  <td className="p-3 text-right">
                    {a.status === 'pending' ? (
                      <div className="inline-flex gap-2">
                        <button
                          onClick={() => approve(a)}
                          className="h-8 px-3 rounded-md border text-xs hover:bg-muted"
                        >
                          Approve
                        </button>
                        <button
                          onClick={() => openReject(a)}
                          className="h-8 px-3 rounded-md border text-xs hover:bg-muted text-rose-600"
                        >
                          Reject
                        </button>
                      </div>
                    ) : (
                      <span className="text-xs text-muted-foreground">—</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-end gap-2">
        <button
          onClick={() => setPage(Math.max(0, page - 1))}
          disabled={page === 0}
          className="h-9 px-3 rounded-md border text-sm disabled:opacity-50"
        >
          Prev
        </button>
        <button
          onClick={() => setPage(page + 1)}
          className="h-9 px-3 rounded-md border text-sm"
        >
          Next
        </button>
      </div>

      {actionDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-card rounded-lg border shadow-xl w-full max-w-md">
            <div className="p-4 border-b">
              <h3 className="text-lg font-semibold">Reject application</h3>
              <p className="text-sm text-muted-foreground mt-1">Select reason</p>
            </div>

            <div className="p-4 space-y-4">
              <div>
                <label className="text-sm font-medium">Reason</label>
                <select
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  className="mt-1 w-full h-9 px-3 rounded-md border bg-background text-sm"
                >
                  <option value="">Select…</option>
                  {REJECT_REASONS_V1.map((r) => (
                    <option key={r.value} value={r.value}>{r.label}</option>
                  ))}
                </select>
              </div>

              {reason === 'other' && (
                <div>
                  <label className="text-sm font-medium">Reason note (required)</label>
                  <textarea
                    value={reasonNote}
                    onChange={(e) => setReasonNote(e.target.value)}
                    className="mt-1 w-full min-h-[90px] p-3 rounded-md border bg-background text-sm"
                    placeholder="Explain…"
                  />
                </div>
              )}
            </div>

            <div className="p-4 border-t flex items-center justify-end gap-2">
              <button
                onClick={() => setActionDialog(null)}
                className="h-9 px-3 rounded-md border hover:bg-muted text-sm"
              >
                Cancel
              </button>
              <button
                onClick={submitReject}
                className="h-9 px-3 rounded-md bg-primary text-primary-foreground hover:opacity-90 text-sm"
              >
                Submit
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
