import { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { Search, X, ChevronLeft, ChevronRight } from 'lucide-react';
import { toast } from '@/components/ui/use-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const STATUS_OPTIONS = [
  { value: 'open', label: 'Açık' },
  { value: 'in_review', label: 'İncelemede' },
  { value: 'closed', label: 'Kapalı' },
];

const statusBadge = (status) => {
  switch (status) {
    case 'open':
      return { label: 'Açık', className: 'bg-amber-100 text-amber-700' };
    case 'in_review':
      return { label: 'İncelemede', className: 'bg-blue-100 text-blue-700' };
    case 'closed':
      return { label: 'Kapalı', className: 'bg-slate-200 text-slate-700' };
    default:
      return { label: status || '-', className: 'bg-slate-100 text-slate-600' };
  }
};

const priorityLabel = (value) => {
  switch (value) {
    case 'low':
      return 'Düşük';
    case 'high':
      return 'Yüksek';
    default:
      return 'Orta';
  }
};

const formatDate = (value) => {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '-';
  return date.toLocaleString();
};

export default function SupportApplications({ applicationType, title, subtitle, testIdPrefix }) {
  const [items, setItems] = useState([]);
  const [assignees, setAssignees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);
  const [limit] = useState(20);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [assigningId, setAssigningId] = useState('');
  const [statusUpdatingId, setStatusUpdatingId] = useState('');

  const authHeader = useMemo(() => ({
    Authorization: `Bearer ${localStorage.getItem('access_token')}`,
  }), []);

  const fetchAssignees = async () => {
    try {
      const res = await axios.get(`${API}/admin/applications/assignees`, { headers: authHeader });
      setAssignees(res.data.items || []);
    } catch (e) {
      setAssignees([]);
    }
  };

  const fetchApplications = async () => {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams();
      params.set('type', applicationType);
      params.set('page', String(page));
      params.set('limit', String(limit));
      if (searchQuery) params.set('search', searchQuery);

      const res = await axios.get(`${API}/applications?${params.toString()}`, { headers: authHeader });
      setItems(res.data.items || []);
      setTotalCount(res.data.total_count ?? 0);
      setTotalPages(res.data.total_pages ?? 1);
    } catch (e) {
      setError('Başvuru listesi yüklenemedi.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssignees();
  }, []);

  useEffect(() => {
    fetchApplications();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [applicationType, page, searchQuery]);

  const handleSearchSubmit = (event) => {
    event.preventDefault();
    setPage(1);
    setSearchQuery(searchInput.trim());
  };

  const handleClearSearch = () => {
    setSearchInput('');
    setSearchQuery('');
    setPage(1);
  };

  const handleAssign = async (applicationId, value) => {
    setAssigningId(applicationId);
    try {
      await axios.patch(
        `${API}/admin/applications/${applicationId}/assign`,
        { assigned_admin_id: value || null },
        { headers: authHeader }
      );
      toast({ title: 'Atama güncellendi.' });
      fetchApplications();
    } catch (e) {
      const message = e.response?.data?.detail || 'Atama başarısız.';
      toast({ title: typeof message === 'string' ? message : 'Atama başarısız.', variant: 'destructive' });
    } finally {
      setAssigningId('');
    }
  };

  const handleStatusChange = async (applicationId, value) => {
    setStatusUpdatingId(applicationId);
    try {
      await axios.patch(
        `${API}/admin/applications/${applicationId}/status`,
        { status: value },
        { headers: authHeader }
      );
      toast({ title: 'Durum güncellendi.' });
      fetchApplications();
    } catch (e) {
      const message = e.response?.data?.detail || 'Durum güncelleme başarısız.';
      toast({ title: typeof message === 'string' ? message : 'Durum güncelleme başarısız.', variant: 'destructive' });
    } finally {
      setStatusUpdatingId('');
    }
  };

  const resultLabel = searchQuery ? `${totalCount} sonuç bulundu` : `Toplam ${totalCount} kayıt`;

  return (
    <div className="space-y-6" data-testid={`${testIdPrefix}-page`}>
      <div>
        <h1 className="text-2xl font-bold" data-testid={`${testIdPrefix}-title`}>{title}</h1>
        <p className="text-sm text-muted-foreground" data-testid={`${testIdPrefix}-subtitle`}>{subtitle}</p>
      </div>

      <div className="bg-card border rounded-md p-4 space-y-4" data-testid={`${testIdPrefix}-filters`}>
        <form onSubmit={handleSearchSubmit} className="flex flex-wrap items-center gap-3">
          <div className="relative flex items-center gap-2 border rounded-md px-3 h-10 bg-background w-full sm:w-96">
            <Search size={16} className="text-muted-foreground" />
            <input
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
              placeholder="Konu içinde ara"
              className="bg-transparent outline-none text-sm flex-1"
              data-testid={`${testIdPrefix}-search-input`}
            />
            {searchInput && (
              <button
                type="button"
                onClick={handleClearSearch}
                className="text-muted-foreground hover:text-foreground"
                data-testid={`${testIdPrefix}-search-clear`}
              >
                <X size={14} />
              </button>
            )}
          </div>
          <button type="submit" className="h-10 px-4 rounded-md border text-sm" data-testid={`${testIdPrefix}-search-button`}>
            Ara
          </button>
          <div className="text-xs text-muted-foreground" data-testid={`${testIdPrefix}-result-count`}>{resultLabel}</div>
        </form>
      </div>

      {error && (
        <div className="text-sm text-rose-600" data-testid={`${testIdPrefix}-error`}>{error}</div>
      )}

      <div className="rounded-md border bg-card overflow-hidden" data-testid={`${testIdPrefix}-table`}>
        <div className="overflow-x-auto">
          <table className="min-w-[1100px] w-full text-sm">
            <thead className="bg-muted">
              <tr>
                <th className="p-3 text-left" data-testid={`${testIdPrefix}-header-created`}>Tarih</th>
                <th className="p-3 text-left" data-testid={`${testIdPrefix}-header-user`}>Kullanıcı</th>
                <th className="p-3 text-left" data-testid={`${testIdPrefix}-header-subject`}>Konu</th>
                <th className="p-3 text-left" data-testid={`${testIdPrefix}-header-status`}>Durum</th>
                <th className="p-3 text-left" data-testid={`${testIdPrefix}-header-priority`}>Öncelik</th>
                <th className="p-3 text-left" data-testid={`${testIdPrefix}-header-assigned`}>Atanan</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} className="p-6 text-center text-muted-foreground" data-testid={`${testIdPrefix}-loading`}>
                    Yükleniyor...
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-6 text-center text-muted-foreground" data-testid={`${testIdPrefix}-empty`}>
                    Başvuru bulunamadı.
                  </td>
                </tr>
              ) : (
                items.map((item) => {
                  const badge = statusBadge(item.status);
                  return (
                    <tr key={item.id} className="border-b last:border-none" data-testid={`${testIdPrefix}-row-${item.id}`}>
                      <td className="p-3" data-testid={`${testIdPrefix}-created-${item.id}`}>{formatDate(item.created_at)}</td>
                      <td className="p-3" data-testid={`${testIdPrefix}-user-${item.id}`}>
                        <div className="font-medium">{item.user?.name || '-'}</div>
                        <div className="text-xs text-muted-foreground">{item.user?.email || '-'}</div>
                      </td>
                      <td className="p-3" data-testid={`${testIdPrefix}-subject-${item.id}`}>{item.subject || '-'}</td>
                      <td className="p-3" data-testid={`${testIdPrefix}-status-${item.id}`}>
                        <div className="flex items-center gap-2">
                          <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs ${badge.className}`}>{badge.label}</span>
                          <select
                            value={item.status}
                            onChange={(event) => handleStatusChange(item.id, event.target.value)}
                            className="h-8 rounded-md border bg-background px-2 text-xs"
                            disabled={statusUpdatingId === item.id}
                            data-testid={`${testIdPrefix}-status-select-${item.id}`}
                          >
                            {STATUS_OPTIONS.map((option) => (
                              <option key={option.value} value={option.value}>{option.label}</option>
                            ))}
                          </select>
                        </div>
                      </td>
                      <td className="p-3" data-testid={`${testIdPrefix}-priority-${item.id}`}>{priorityLabel(item.priority)}</td>
                      <td className="p-3" data-testid={`${testIdPrefix}-assigned-${item.id}`}>
                        <select
                          value={item.assigned_admin?.id || ''}
                          onChange={(event) => handleAssign(item.id, event.target.value)}
                          className="h-9 rounded-md border bg-background px-2 text-xs w-full"
                          disabled={assigningId === item.id}
                          data-testid={`${testIdPrefix}-assign-select-${item.id}`}
                        >
                          <option value="">Atanmamış</option>
                          {assignees.map((assignee) => (
                            <option key={assignee.id} value={assignee.id}>{assignee.name}</option>
                          ))}
                        </select>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="flex items-center justify-between" data-testid={`${testIdPrefix}-pagination`}>
        <button
          type="button"
          className="h-9 px-3 rounded-md border text-sm flex items-center gap-2 disabled:opacity-50"
          onClick={() => setPage((prev) => Math.max(prev - 1, 1))}
          disabled={page <= 1}
          data-testid={`${testIdPrefix}-prev`}
        >
          <ChevronLeft size={14} /> Önceki
        </button>
        <div className="text-sm text-muted-foreground" data-testid={`${testIdPrefix}-page-indicator`}>
          Sayfa {page} / {totalPages}
        </div>
        <button
          type="button"
          className="h-9 px-3 rounded-md border text-sm flex items-center gap-2 disabled:opacity-50"
          onClick={() => setPage((prev) => Math.min(prev + 1, totalPages))}
          disabled={page >= totalPages}
          data-testid={`${testIdPrefix}-next`}
        >
          Sonraki <ChevronRight size={14} />
        </button>
      </div>
    </div>
  );
}
