import React, { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

const emptyForm = {
  name: '',
  slug: '',
  parent_id: '',
  country_code: '',
  sort_order: 0,
  active_flag: true,
};

const AdminCategories = () => {
  const [searchParams] = useSearchParams();
  const urlCountry = (searchParams.get('country') || '').toUpperCase();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ ...emptyForm });
  const [error, setError] = useState(null);

  const authHeader = useMemo(() => ({
    Authorization: `Bearer ${localStorage.getItem('access_token')}`,
  }), []);

  const fetchItems = async () => {
    try {
      setLoading(true);
      const params = urlCountry ? `?country=${urlCountry}` : '';
      const res = await axios.get(`${API_BASE_URL}/api/admin/categories${params}`, { headers: authHeader });
      setItems(res.data.items || []);
    } catch (e) {
      console.error('Failed to load categories', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItems();
  }, [urlCountry]);

  const parentOptions = useMemo(() => {
    return items.filter((item) => !editing || item.id !== editing.id);
  }, [items, editing]);

  const openCreate = () => {
    setEditing(null);
    setForm({ ...emptyForm, country_code: urlCountry || '' });
    setError(null);
    setModalOpen(true);
  };

  const openEdit = (item) => {
    setEditing(item);
    setForm({
      name: item.name || '',
      slug: item.slug || '',
      parent_id: item.parent_id || '',
      country_code: item.country_code || '',
      sort_order: item.sort_order || 0,
      active_flag: item.active_flag !== false,
    });
    setError(null);
    setModalOpen(true);
  };

  const handleSave = async () => {
    if (!form.name || !form.slug) {
      setError('Name ve slug zorunlu');
      return;
    }
    const payload = {
      ...form,
      slug: form.slug.trim().toLowerCase(),
      parent_id: form.parent_id || null,
      country_code: form.country_code || null,
      sort_order: Number(form.sort_order || 0),
    };
    try {
      if (editing) {
        await axios.patch(`${API_BASE_URL}/api/admin/categories/${editing.id}`, payload, { headers: authHeader });
      } else {
        await axios.post(`${API_BASE_URL}/api/admin/categories`, payload, { headers: authHeader });
      }
      setModalOpen(false);
      fetchItems();
    } catch (e) {
      setError(e?.response?.data?.detail || 'Kaydetme başarısız');
    }
  };

  const handleDelete = async (item) => {
    if (!window.confirm('Kategori pasif edilsin mi?')) return;
    try {
      await axios.delete(`${API_BASE_URL}/api/admin/categories/${item.id}`, { headers: authHeader });
      fetchItems();
    } catch (e) {
      alert('Silme başarısız');
    }
  };

  return (
    <div className="p-6 space-y-6" data-testid="admin-categories-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Kategoriler</h1>
          <p className="text-sm text-muted-foreground">Country: {urlCountry || 'Global'}</p>
        </div>
        <button
          onClick={openCreate}
          className="bg-blue-600 text-white px-4 py-2 rounded-md"
          data-testid="categories-create-open"
        >
          Yeni Kategori
        </button>
      </div>

      <div className="border rounded-lg overflow-hidden" data-testid="categories-table">
        <table className="min-w-full text-sm">
          <thead className="bg-muted">
            <tr>
              <th className="text-left px-3 py-2">Name</th>
              <th className="text-left px-3 py-2">Slug</th>
              <th className="text-left px-3 py-2">Parent</th>
              <th className="text-left px-3 py-2">Country</th>
              <th className="text-left px-3 py-2">Active</th>
              <th className="text-left px-3 py-2">Sort</th>
              <th className="text-right px-3 py-2">Aksiyon</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td className="px-3 py-4" colSpan="7">Yükleniyor...</td></tr>
            ) : items.length === 0 ? (
              <tr><td className="px-3 py-4" colSpan="7">Kayıt yok</td></tr>
            ) : (
              items.map((item) => (
                <tr key={item.id} className="border-t" data-testid={`categories-row-${item.id}`}>
                  <td className="px-3 py-2">{item.name}</td>
                  <td className="px-3 py-2 text-muted-foreground">{item.slug}</td>
                  <td className="px-3 py-2">{items.find((c) => c.id === item.parent_id)?.name || '-'}</td>
                  <td className="px-3 py-2">{item.country_code || 'global'}</td>
                  <td className="px-3 py-2">{item.active_flag ? 'yes' : 'no'}</td>
                  <td className="px-3 py-2">{item.sort_order}</td>
                  <td className="px-3 py-2 text-right space-x-2">
                    <button
                      className="px-2 py-1 border rounded"
                      onClick={() => openEdit(item)}
                      data-testid={`categories-edit-${item.id}`}
                    >
                      Düzenle
                    </button>
                    <button
                      className="px-2 py-1 border rounded text-red-600"
                      onClick={() => handleDelete(item)}
                      data-testid={`categories-delete-${item.id}`}
                    >
                      Sil
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {modalOpen && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center" data-testid="categories-modal">
          <div className="bg-white rounded-lg shadow-lg w-full max-w-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">{editing ? 'Kategori Düzenle' : 'Kategori Oluştur'}</h2>
              <button onClick={() => setModalOpen(false)} data-testid="categories-modal-close">Kapat</button>
            </div>

            {error && <div className="text-sm text-red-600 mb-2" data-testid="categories-error">{error}</div>}

            <div className="space-y-3">
              <input
                className="w-full border rounded p-2"
                placeholder="Name"
                value={form.name}
                onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
                data-testid="categories-name-input"
              />
              <input
                className="w-full border rounded p-2"
                placeholder="Slug"
                value={form.slug}
                onChange={(e) => setForm((prev) => ({ ...prev, slug: e.target.value }))}
                data-testid="categories-slug-input"
              />
              <select
                className="w-full border rounded p-2"
                value={form.parent_id}
                onChange={(e) => setForm((prev) => ({ ...prev, parent_id: e.target.value }))}
                data-testid="categories-parent-select"
              >
                <option value="">Parent (optional)</option>
                {parentOptions.map((cat) => (
                  <option key={cat.id} value={cat.id}>{cat.name}</option>
                ))}
              </select>
              <input
                className="w-full border rounded p-2"
                placeholder="Country code (optional)"
                value={form.country_code}
                onChange={(e) => setForm((prev) => ({ ...prev, country_code: e.target.value.toUpperCase() }))}
                data-testid="categories-country-input"
              />
              <input
                type="number"
                className="w-full border rounded p-2"
                placeholder="Sort order"
                value={form.sort_order}
                onChange={(e) => setForm((prev) => ({ ...prev, sort_order: e.target.value }))}
                data-testid="categories-sort-input"
              />
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={form.active_flag}
                  onChange={(e) => setForm((prev) => ({ ...prev, active_flag: e.target.checked }))}
                  data-testid="categories-active-checkbox"
                />
                Aktif
              </label>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <button className="px-4 py-2 border rounded" onClick={() => setModalOpen(false)} data-testid="categories-cancel">
                Vazgeç
              </button>
              <button className="px-4 py-2 bg-blue-600 text-white rounded" onClick={handleSave} data-testid="categories-save">
                Kaydet
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminCategories;
