import React, { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

const emptyForm = {
  category_id: '',
  name: '',
  key: '',
  type: 'text',
  required_flag: false,
  filterable_flag: false,
  options: '',
  country_code: '',
  active_flag: true,
};

const AdminAttributes = () => {
  const [searchParams] = useSearchParams();
  const urlCountry = (searchParams.get('country') || '').toUpperCase();
  const [items, setItems] = useState([]);
  const [categories, setCategories] = useState([]);
  const [filterCategory, setFilterCategory] = useState('');
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ ...emptyForm });
  const [error, setError] = useState(null);

  const authHeader = useMemo(() => ({
    Authorization: `Bearer ${localStorage.getItem('access_token')}`,
  }), []);

  const fetchCategories = async () => {
    try {
      const params = urlCountry ? `?country=${urlCountry}` : '';
      const res = await axios.get(`${API_BASE_URL}/api/admin/categories${params}`, { headers: authHeader });
      setCategories(res.data.items || []);
    } catch (e) {
      console.error('Failed to load categories', e);
    }
  };

  const fetchItems = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filterCategory) params.set('category_id', filterCategory);
      if (urlCountry) params.set('country', urlCountry);
      const res = await axios.get(`${API_BASE_URL}/api/admin/attributes?${params.toString()}`, { headers: authHeader });
      setItems(res.data.items || []);
    } catch (e) {
      console.error('Failed to load attributes', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCategories();
  }, [urlCountry]);

  useEffect(() => {
    fetchItems();
  }, [urlCountry, filterCategory]);

  const openCreate = () => {
    setEditing(null);
    setForm({ ...emptyForm, country_code: urlCountry || '' });
    setError(null);
    setModalOpen(true);
  };

  const openEdit = (item) => {
    setEditing(item);
    setForm({
      category_id: item.category_id || '',
      name: item.name || '',
      key: item.key || '',
      type: item.type || 'text',
      required_flag: item.required_flag || false,
      filterable_flag: item.filterable_flag || false,
      options: (item.options || []).join(','),
      country_code: item.country_code || '',
      active_flag: item.active_flag !== false,
    });
    setError(null);
    setModalOpen(true);
  };

  const handleSave = async () => {
    if (!form.category_id || !form.name || !form.key) {
      setError('Kategori, name ve key zorunlu');
      return;
    }
    const payload = {
      ...form,
      key: form.key.trim().toLowerCase(),
      options: form.type === 'select' ? form.options.split(',').map((o) => o.trim()).filter(Boolean) : null,
      country_code: form.country_code || null,
    };
    try {
      if (editing) {
        await axios.patch(`${API_BASE_URL}/api/admin/attributes/${editing.id}`, payload, { headers: authHeader });
      } else {
        await axios.post(`${API_BASE_URL}/api/admin/attributes`, payload, { headers: authHeader });
      }
      setModalOpen(false);
      fetchItems();
    } catch (e) {
      setError(e?.response?.data?.detail || 'Kaydetme başarısız');
    }
  };

  const handleDelete = async (item) => {
    if (!window.confirm('Attribute pasif edilsin mi?')) return;
    try {
      await axios.delete(`${API_BASE_URL}/api/admin/attributes/${item.id}`, { headers: authHeader });
      fetchItems();
    } catch (e) {
      alert('Silme başarısız');
    }
  };

  const categoryMap = useMemo(() => {
    const map = new Map();
    categories.forEach((cat) => map.set(cat.id, cat.name));
    return map;
  }, [categories]);

  return (
    <div className="p-6 space-y-6" data-testid="admin-attributes-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Özellikler</h1>
          <p className="text-sm text-muted-foreground">Country: {urlCountry || 'Global'}</p>
        </div>
        <button
          onClick={openCreate}
          className="bg-blue-600 text-white px-4 py-2 rounded-md"
          data-testid="attributes-create-open"
        >
          Yeni Attribute
        </button>
      </div>

      <div className="flex items-center gap-3">
        <select
          className="border rounded p-2"
          value={filterCategory}
          onChange={(e) => setFilterCategory(e.target.value)}
          data-testid="attributes-filter-category"
        >
          <option value="">Tüm Kategoriler</option>
          {categories.map((cat) => (
            <option key={cat.id} value={cat.id}>{cat.name}</option>
          ))}
        </select>
      </div>

      <div className="border rounded-lg overflow-hidden" data-testid="attributes-table">
        <table className="min-w-full text-sm">
          <thead className="bg-muted">
            <tr>
              <th className="text-left px-3 py-2">Key</th>
              <th className="text-left px-3 py-2">Name</th>
              <th className="text-left px-3 py-2">Type</th>
              <th className="text-left px-3 py-2">Category</th>
              <th className="text-left px-3 py-2">Required</th>
              <th className="text-left px-3 py-2">Filterable</th>
              <th className="text-left px-3 py-2">Country</th>
              <th className="text-left px-3 py-2">Active</th>
              <th className="text-right px-3 py-2">Aksiyon</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td className="px-3 py-4" colSpan="9">Yükleniyor...</td></tr>
            ) : items.length === 0 ? (
              <tr><td className="px-3 py-4" colSpan="9">Kayıt yok</td></tr>
            ) : (
              items.map((item) => (
                <tr key={item.id} className="border-t" data-testid={`attributes-row-${item.id}`}>
                  <td className="px-3 py-2 text-muted-foreground">{item.key}</td>
                  <td className="px-3 py-2">{item.name}</td>
                  <td className="px-3 py-2">{item.type}</td>
                  <td className="px-3 py-2">{categoryMap.get(item.category_id) || '-'}</td>
                  <td className="px-3 py-2">{item.required_flag ? 'yes' : 'no'}</td>
                  <td className="px-3 py-2">{item.filterable_flag ? 'yes' : 'no'}</td>
                  <td className="px-3 py-2">{item.country_code || 'global'}</td>
                  <td className="px-3 py-2">{item.active_flag ? 'yes' : 'no'}</td>
                  <td className="px-3 py-2 text-right space-x-2">
                    <button
                      className="px-2 py-1 border rounded"
                      onClick={() => openEdit(item)}
                      data-testid={`attributes-edit-${item.id}`}
                    >
                      Düzenle
                    </button>
                    <button
                      className="px-2 py-1 border rounded text-red-600"
                      onClick={() => handleDelete(item)}
                      data-testid={`attributes-delete-${item.id}`}
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
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center" data-testid="attributes-modal">
          <div className="bg-white rounded-lg shadow-lg w-full max-w-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">{editing ? 'Attribute Düzenle' : 'Attribute Oluştur'}</h2>
              <button onClick={() => setModalOpen(false)} data-testid="attributes-modal-close">Kapat</button>
            </div>

            {error && <div className="text-sm text-red-600 mb-2" data-testid="attributes-error">{error}</div>}

            <div className="space-y-3">
              <select
                className="w-full border rounded p-2"
                value={form.category_id}
                onChange={(e) => setForm((prev) => ({ ...prev, category_id: e.target.value }))}
                data-testid="attributes-category-select"
              >
                <option value="">Kategori seç</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>{cat.name}</option>
                ))}
              </select>
              <input
                className="w-full border rounded p-2"
                placeholder="Name"
                value={form.name}
                onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
                data-testid="attributes-name-input"
              />
              <input
                className="w-full border rounded p-2"
                placeholder="Key"
                value={form.key}
                onChange={(e) => setForm((prev) => ({ ...prev, key: e.target.value }))}
                data-testid="attributes-key-input"
              />
              <select
                className="w-full border rounded p-2"
                value={form.type}
                onChange={(e) => setForm((prev) => ({ ...prev, type: e.target.value }))}
                data-testid="attributes-type-select"
              >
                <option value="text">text</option>
                <option value="number">number</option>
                <option value="select">select</option>
                <option value="boolean">boolean</option>
              </select>
              {form.type === 'select' && (
                <input
                  className="w-full border rounded p-2"
                  placeholder="Options (comma separated)"
                  value={form.options}
                  onChange={(e) => setForm((prev) => ({ ...prev, options: e.target.value }))}
                  data-testid="attributes-options-input"
                />
              )}
              <input
                className="w-full border rounded p-2"
                placeholder="Country code (optional)"
                value={form.country_code}
                onChange={(e) => setForm((prev) => ({ ...prev, country_code: e.target.value.toUpperCase() }))}
                data-testid="attributes-country-input"
              />
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={form.required_flag}
                  onChange={(e) => setForm((prev) => ({ ...prev, required_flag: e.target.checked }))}
                  data-testid="attributes-required-checkbox"
                />
                Required
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={form.filterable_flag}
                  onChange={(e) => setForm((prev) => ({ ...prev, filterable_flag: e.target.checked }))}
                  data-testid="attributes-filterable-checkbox"
                />
                Filterable
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={form.active_flag}
                  onChange={(e) => setForm((prev) => ({ ...prev, active_flag: e.target.checked }))}
                  data-testid="attributes-active-checkbox"
                />
                Aktif
              </label>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <button className="px-4 py-2 border rounded" onClick={() => setModalOpen(false)} data-testid="attributes-cancel">
                Vazgeç
              </button>
              <button className="px-4 py-2 bg-blue-600 text-white rounded" onClick={handleSave} data-testid="attributes-save">
                Kaydet
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminAttributes;
