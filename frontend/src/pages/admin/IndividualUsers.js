import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import { Search, X, ChevronLeft, ChevronRight, Download } from "lucide-react";
import { useAuth } from "../../contexts/AuthContext";
import { toast } from "../../components/ui/use-toast";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const SORT_OPTIONS = [
  { value: "last_name_asc", label: "Soyad (A→Z)" },
  { value: "last_name_desc", label: "Soyad (Z→A)" },
];

const formatDate = (value) => {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  return date.toLocaleString();
};

const getSortParams = (value) => {
  if (value === "last_name_desc") {
    return { sort_by: "last_name", sort_dir: "desc" };
  }
  return { sort_by: "last_name", sort_dir: "asc" };
};

const resolveFirstName = (user) => {
  if (user?.first_name) return user.first_name;
  if (user?.full_name) return user.full_name.split(" ")[0] || "-";
  return "-";
};

const resolveLastName = (user) => {
  if (user?.last_name) return user.last_name;
  if (user?.full_name) {
    const parts = user.full_name.split(" ");
    return parts.length > 1 ? parts.slice(1).join(" ") : "-";
  }
  return "-";
};

export default function IndividualUsers() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [sortOption, setSortOption] = useState("last_name_asc");
  const [page, setPage] = useState(1);
  const [limit] = useState(25);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [exporting, setExporting] = useState(false);

  const authHeader = useMemo(
    () => ({ Authorization: `Bearer ${localStorage.getItem("access_token")}` }),
    []
  );

  const canExport = ["super_admin", "marketing"].includes(currentUser?.role);

  const fetchUsers = async () => {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams();
      params.set("page", String(page));
      params.set("limit", String(limit));
      const { sort_by, sort_dir } = getSortParams(sortOption);
      params.set("sort_by", sort_by);
      params.set("sort_dir", sort_dir);
      if (searchQuery) params.set("search", searchQuery);
      const qs = params.toString() ? `?${params.toString()}` : "";
      const res = await axios.get(`${API}/admin/individual-users${qs}`, { headers: authHeader });
      setUsers(res.data.items || []);
      setTotalCount(res.data.total_count ?? 0);
      setTotalPages(res.data.total_pages ?? 1);
    } catch (err) {
      setError("Bireysel kullanıcı listesi yüklenemedi.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, sortOption, searchQuery]);

  const handleSearchSubmit = (event) => {
    event.preventDefault();
    setPage(1);
    setSearchQuery(searchInput.trim());
  };

  const handleClearSearch = () => {
    setSearchInput("");
    setSearchQuery("");
    setPage(1);
  };

  const handleExport = async () => {
    if (!canExport) return;
    setExporting(true);
    try {
      const params = new URLSearchParams();
      const { sort_by, sort_dir } = getSortParams(sortOption);
      params.set("sort_by", sort_by);
      params.set("sort_dir", sort_dir);
      if (searchQuery) params.set("search", searchQuery);
      const qs = params.toString() ? `?${params.toString()}` : "";
      const res = await axios.get(`${API}/admin/individual-users/export/csv${qs}`, {
        headers: authHeader,
        responseType: "blob",
      });
      const blob = new Blob([res.data], { type: "text/csv" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
      link.href = url;
      link.download = `individual-users-${timestamp}.csv`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast({ title: "CSV export hazır." });
    } catch (err) {
      const message = err.response?.data?.detail || "CSV export başarısız.";
      toast({ title: typeof message === "string" ? message : "CSV export başarısız.", variant: "destructive" });
    } finally {
      setExporting(false);
    }
  };

  const safeUsers = users.filter((user) => user.user_type === "individual");
  const resultLabel = searchQuery
    ? `${totalCount} sonuç bulundu`
    : `Toplam ${totalCount} kayıt`;

  return (
    <div className="space-y-6" data-testid="individual-users-page">
      <div>
        <h1 className="text-2xl font-bold" data-testid="individual-users-title">Bireysel Kullanıcılar</h1>
        <p className="text-sm text-muted-foreground" data-testid="individual-users-subtitle">
          Bireysel kullanıcı listesi, arama ve alfabetik sıralama
        </p>
      </div>

      <div className="bg-card border rounded-md p-4 space-y-4" data-testid="individual-users-controls">
        <form onSubmit={handleSearchSubmit} className="flex flex-wrap items-center gap-3">
          <div className="relative flex items-center gap-2 border rounded-md px-3 h-10 bg-background w-full sm:w-96">
            <Search size={16} className="text-muted-foreground" />
            <input
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
              placeholder="Ad, soyad veya e-posta ara"
              className="bg-transparent outline-none text-sm flex-1"
              data-testid="individual-users-search-input"
            />
            {searchInput && (
              <button
                type="button"
                onClick={handleClearSearch}
                className="text-muted-foreground hover:text-foreground"
                data-testid="individual-users-search-clear"
              >
                <X size={14} />
              </button>
            )}
          </div>
          <button
            type="submit"
            className="h-10 px-4 rounded-md border text-sm"
            data-testid="individual-users-search-button"
          >
            Ara
          </button>
          <div className="text-xs text-muted-foreground" data-testid="individual-users-result-count">
            {resultLabel}
          </div>
          {canExport && (
            <button
              type="button"
              className="h-10 px-4 rounded-md border text-sm inline-flex items-center gap-2"
              onClick={handleExport}
              disabled={exporting}
              data-testid="individual-users-export-button"
            >
              <Download size={16} /> {exporting ? "Dışa Aktarılıyor" : "CSV Export"}
            </button>
          )}
        </form>

        <div className="grid gap-3 md:grid-cols-2" data-testid="individual-users-filters">
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">Sıralama</div>
            <select
              value={sortOption}
              onChange={(e) => setSortOption(e.target.value)}
              className="h-10 rounded-md border bg-background px-3 text-sm w-full"
              data-testid="individual-users-sort-select"
            >
              {SORT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {error && (
        <div className="text-sm text-rose-600" data-testid="individual-users-error">{error}</div>
      )}

      <div className="rounded-md border bg-card overflow-hidden" data-testid="individual-users-table">
        <div className="overflow-x-auto">
          <table className="min-w-[900px] w-full text-sm">
            <thead className="bg-muted">
              <tr>
                <th className="p-3 text-left" data-testid="individual-users-header-first-name">Ad</th>
                <th className="p-3 text-left" data-testid="individual-users-header-last-name">Soyad</th>
                <th className="p-3 text-left" data-testid="individual-users-header-email">E-posta</th>
                <th className="p-3 text-left" data-testid="individual-users-header-phone">Telefon</th>
                <th className="p-3 text-left" data-testid="individual-users-header-created">Kayıt Tarihi</th>
                <th className="p-3 text-left" data-testid="individual-users-header-last-login">Son Giriş</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} className="p-6 text-center text-muted-foreground" data-testid="individual-users-loading">
                    Yükleniyor...
                  </td>
                </tr>
              ) : safeUsers.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-6 text-center text-muted-foreground" data-testid="individual-users-empty">
                    Bireysel kullanıcı bulunamadı.
                  </td>
                </tr>
              ) : (
                safeUsers.map((user) => (
                  <tr key={user.id} className="border-b last:border-none" data-testid={`individual-user-row-${user.id}`}>
                    <td className="p-3" data-testid={`individual-user-first-name-${user.id}`}>
                      {resolveFirstName(user)}
                    </td>
                    <td className="p-3" data-testid={`individual-user-last-name-${user.id}`}>
                      {resolveLastName(user)}
                    </td>
                    <td className="p-3" data-testid={`individual-user-email-${user.id}`}>{user.email}</td>
                    <td className="p-3" data-testid={`individual-user-created-${user.id}`}>{formatDate(user.created_at)}</td>
                    <td className="p-3" data-testid={`individual-user-last-login-${user.id}`}>{formatDate(user.last_login)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="flex items-center justify-between" data-testid="individual-users-pagination">
        <button
          type="button"
          className="h-9 px-3 rounded-md border text-sm flex items-center gap-2 disabled:opacity-50"
          onClick={() => setPage((prev) => Math.max(prev - 1, 1))}
          disabled={page <= 1}
          data-testid="individual-users-prev"
        >
          <ChevronLeft size={14} /> Önceki
        </button>
        <div className="text-sm text-muted-foreground" data-testid="individual-users-page-indicator">
          Sayfa {page} / {totalPages}
        </div>
        <button
          type="button"
          className="h-9 px-3 rounded-md border text-sm flex items-center gap-2 disabled:opacity-50"
          onClick={() => setPage((prev) => Math.min(prev + 1, totalPages))}
          disabled={page >= totalPages}
          data-testid="individual-users-next"
        >
          Sonraki <ChevronRight size={14} />
        </button>
      </div>
    </div>
  );
}
