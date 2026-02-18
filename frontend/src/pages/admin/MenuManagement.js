import React, { useEffect, useMemo, useState } from "react";
import axios from "axios";
import { useSearchParams } from "react-router-dom";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const emptyForm = {
  label: "",
  slug: "",
  url: "",
  parent_id: "",
  country_code: "",
  sort_order: 0,
  active_flag: true,
};

export default function MenuManagement() {
  const [searchParams] = useSearchParams();
  const countryParam = searchParams.get("country") || "";
  const [items, setItems] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [form, setForm] = useState({ ...emptyForm, country_code: countryParam || "" });

  const fetchItems = async () => {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams();
      if (countryParam) params.append("country", countryParam);
      const response = await axios.get(`${API_URL}/api/admin/menu-items?${params.toString()}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("access_token")}`,
        },
      });
      setItems(response.data.items || []);
    } catch (err) {
      setError("Menü öğeleri alınamadı.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItems();
  }, [countryParam]);

  const filteredItems = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return items;
    return items.filter((item) => {
      const haystack = `${item.label} ${item.slug} ${item.url || ""}`.toLowerCase();
      return haystack.includes(query);
    });
  }, [items, search]);

  const parentOptions = useMemo(() => {
    const blockedId = editingItem?.id;
    return items.filter((item) => item.id !== blockedId);
  }, [items, editingItem]);

  const openCreate = () => {
    setEditingItem(null);
    setForm({ ...emptyForm, country_code: countryParam || "" });
    setShowForm(true);
  };

  const openEdit = (item) => {
    setEditingItem(item);
    setForm({
      label: item.label || "",
      slug: item.slug || "",
      url: item.url || "",
      parent_id: item.parent_id || "",
      country_code: item.country_code || "",
      sort_order: item.sort_order ?? 0,
      active_flag: item.active_flag ?? true,
    });
    setShowForm(true);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const payload = {
        label: form.label.trim(),
        slug: form.slug.trim(),
        url: form.url.trim() || null,
        parent_id: form.parent_id || null,
        country_code: form.country_code.trim() || null,
        sort_order: Number(form.sort_order) || 0,
        active_flag: form.active_flag,
      };
      if (editingItem) {
        await axios.patch(`${API_URL}/api/admin/menu-items/${editingItem.id}`, payload, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("access_token")}`,
          },
        });
      } else {
        await axios.post(`${API_URL}/api/admin/menu-items`, payload, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("access_token")}`,
          },
        });
      }
      setShowForm(false);
      await fetchItems();
    } catch (err) {
      setError(err?.response?.data?.detail || "Menü öğesi kaydedilemedi.");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (item) => {
    if (!window.confirm("Menü öğesini pasif etmek istediğinizden emin misiniz?")) return;
    setLoading(true);
    try {
      await axios.delete(`${API_URL}/api/admin/menu-items/${item.id}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("access_token")}`,
        },
      });
      await fetchItems();
    } catch (err) {
      setError("Menü öğesi pasif edilemedi.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="menu-management-page">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold" data-testid="menu-management-title">Menü Yönetimi</h1>
          <p className="text-sm text-muted-foreground">Menü öğelerini oluşturun, sıralayın ve ülke bazlı yönetin.</p>
          {countryParam && (
            <p className="text-xs text-muted-foreground mt-1" data-testid="menu-management-country">Country: {countryParam}</p>
          )}
        </div>
        <button
          onClick={openCreate}
          className="h-9 px-4 rounded-md bg-primary text-primary-foreground text-sm"
          data-testid="menu-management-create-open"
        >
          Yeni Menü Öğesi
        </button>
      </div>

      <div className="flex flex-wrap gap-3 items-center">
        <input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          className="h-9 px-3 rounded-md border bg-background text-sm w-64"
          placeholder="Ara (label / slug / url)"
          data-testid="menu-management-search"
        />
      </div>

      {error && (
        <div className="rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700" data-testid="menu-management-error">
          {error}
        </div>
      )}

      <div className="rounded-xl border bg-white" data-testid="menu-management-table">
        <div className="grid grid-cols-6 gap-4 px-4 py-3 text-xs font-semibold text-muted-foreground">
          <div>Label</div>
          <div>Slug</div>
          <div>URL</div>
          <div>Parent</div>
          <div>Country</div>
          <div>İşlem</div>
        </div>
        <div className="divide-y">
          {loading ? (
            <div className="px-4 py-6 text-sm text-muted-foreground">Yükleniyor...</div>
          ) : filteredItems.length === 0 ? (
            <div className="px-4 py-6 text-sm text-muted-foreground">Kayıt bulunamadı.</div>
          ) : (
            filteredItems.map((item) => (
              <div key={item.id} className="grid grid-cols-6 gap-4 px-4 py-3 text-sm items-center">
                <div className="font-medium">{item.label}</div>
                <div>{item.slug}</div>
                <div className="truncate" title={item.url || ""}>{item.url || "—"}</div>
                <div>{items.find((parent) => parent.id === item.parent_id)?.label || "—"}</div>
                <div>{item.country_code || "global"}</div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => openEdit(item)}
                    className="px-3 py-1 rounded-md border text-xs"
                    data-testid={`menu-management-edit-${item.id}`}
                  >
                    Düzenle
                  </button>
                  <button
                    onClick={() => handleDelete(item)}
                    className="px-3 py-1 rounded-md border text-xs text-rose-600"
                    data-testid={`menu-management-delete-${item.id}`}
                  >
                    Pasif Et
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {showForm && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4" data-testid="menu-management-modal">
          <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-xl w-full max-w-lg p-6 space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-lg font-semibold">{editingItem ? "Menü Öğesini Düzenle" : "Menü Öğesi Oluştur"}</h2>
                <p className="text-xs text-muted-foreground">Slug + country_code benzersiz olmalıdır.</p>
              </div>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="text-sm text-muted-foreground"
                data-testid="menu-management-close"
              >
                Kapat
              </button>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-medium">Label</label>
              <input
                value={form.label}
                onChange={(event) => setForm({ ...form, label: event.target.value })}
                className="w-full h-9 px-3 rounded-md border text-sm"
                data-testid="menu-management-label"
                required
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium">Slug</label>
              <input
                value={form.slug}
                onChange={(event) => setForm({ ...form, slug: event.target.value })}
                className="w-full h-9 px-3 rounded-md border text-sm"
                data-testid="menu-management-slug"
                required
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium">URL</label>
              <input
                value={form.url}
                onChange={(event) => setForm({ ...form, url: event.target.value })}
                className="w-full h-9 px-3 rounded-md border text-sm"
                data-testid="menu-management-url"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium">Parent</label>
              <select
                value={form.parent_id}
                onChange={(event) => setForm({ ...form, parent_id: event.target.value })}
                className="w-full h-9 px-3 rounded-md border text-sm"
                data-testid="menu-management-parent"
              >
                <option value="">Root</option>
                {parentOptions.map((option) => (
                  <option key={option.id} value={option.id}>{option.label}</option>
                ))}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-xs font-medium">Country Code</label>
                <input
                  value={form.country_code}
                  onChange={(event) => setForm({ ...form, country_code: event.target.value })}
                  className="w-full h-9 px-3 rounded-md border text-sm"
                  data-testid="menu-management-country-input"
                />
              </div>
              <div className="space-y-2">
                <label className="text-xs font-medium">Sort Order</label>
                <input
                  type="number"
                  value={form.sort_order}
                  onChange={(event) => setForm({ ...form, sort_order: event.target.value })}
                  className="w-full h-9 px-3 rounded-md border text-sm"
                  data-testid="menu-management-sort-order"
                />
              </div>
            </div>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={form.active_flag}
                onChange={(event) => setForm({ ...form, active_flag: event.target.checked })}
                data-testid="menu-management-active-flag"
              />
              Aktif
            </label>

            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="h-9 px-4 rounded-md border text-sm"
                data-testid="menu-management-cancel"
              >
                Vazgeç
              </button>
              <button
                type="submit"
                className="h-9 px-4 rounded-md bg-primary text-primary-foreground text-sm"
                data-testid="menu-management-submit"
              >
                Kaydet
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
