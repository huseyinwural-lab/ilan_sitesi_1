import React, { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

const emptyForm = {
  name: '',
  slug: '',
  country_code: '',
  active_flag: true,
};

const AdminVehicleMakes = () => {
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
      const res = await axios.get(`${API_BASE_URL}/api/admin/vehicle-makes${params}`, { headers: authHeader });
      setItems(res.data.items || []);
    } catch (e) {
      console.error('Failed to load makes', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItems();
  }, [urlCountry]);

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
      country_code: item.country_code || '',
      active_flag: item.active_flag !== false,
    });
    setError(null);
    setModalOpen(true);
  };

  const handleSave = async () => {
    if (!form.name || !form.slug || !form.country_code) {
      setError('Name, slug ve country zorunlu');
      return;
    }
    const payload = {
      ...form,
      slug: form.slug.trim().toLowerCase(),
      country_code: form.country_code.toUpperCase(),
    };
    try {
      if (editing) {
        await axios.patch(`${API_BASE_URL}/api/admin/vehicle-makes/${editing.id}`, payload, { headers: authHeader });
      } else {
        await axios.post(`${API_BASE_URL}/api/admin/vehicle-makes`, payload, { headers: authHeader });
      }
      setModalOpen(false);
      fetchItems();
    } catch (e) {
      setError(e?.response?.data?.detail || 'Kaydetme başarısız');
    }
  };

  const handleDelete = async (item) => {
    if (!window.confirm('Make pasif edilsin mi?')) return;
    try {
      await axios.delete(`${API_BASE_URL}/api/admin/vehicle-makes/${item.id}`, { headers: authHeader });
      fetchItems();
    } catch (e) {
      alert('Silme başarısız');
    }
  };

  return (
    <div className="p-6 space-y-6" data-testid="admin-vehicle-makes-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Araç Markaları</h1>
          <p className="text-sm text-muted-foreground">Country: {urlCountry || 'Global'}</p>
        </div>
        <button
          onClick={openCreate}
          className="bg-blue-600 text-white px-4 py-2 rounded-md"
          data-testid="vehicle-makes-create-open"
        >
          Yeni Marka
        </button>
      </div>

      <div className="border rounded-lg overflow-hidden" data-testid="vehicle-makes-table">
        <table className="min-w-full text-sm">
          <thead className="bg-muted">
            <tr>
              <th className="text-left px-3 py-2">Name</th>
              <th className="text-left px-3 py-2">Slug</th>
              <th className="text-left px-3 py-2">Country</th>
              <th className="text-left px-3 py-2">Active</th>
              <th className="text-right px-3 py-2">Aksiyon</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td className="px-3 py-4" colSpan="5">Yükleniyor...</td></tr>
            ) : items.length === 0 ? (
              <tr><td className="px-3 py-4" colSpan="5">Kayıt yok</td></tr>
            ) : (
              items.map((item) => (
                <tr key={item.id} className="border-t" data-testid={`vehicle-makes-row-${item.id}`}>
                  <td className="px-3 py-2">{item.name}</td>
                  <td className="px-3 py-2 text-muted-foreground">{item.slug}</td>
                  <td className="px-3 py-2">{item.country_code}</td>
                  <td className="px-3 py-2">{item.active_flag ? 'yes' : 'no'}</td>
                  <td className="px-3 py-2 text-right space-x-2">
                    <button
                      className="px-2 py-1 border rounded"
                      onClick={() => openEdit(item)}
                      data-testid={`vehicle-makes-edit-${item.id}`}
                    >
                      Düzenle
                    </button>
                    <button
                      className="px-2 py-1 border rounded text-red-600"
                      onClick={() => handleDelete(item)}
                      data-testid={`vehicle-makes-delete-${item.id}`}
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
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center" data-testid="vehicle-makes-modal">
          <div className="bg-white rounded-lg shadow-lg w-full max-w-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">{editing ? 'Marka Düzenle' : 'Marka Oluştur'}</h2>
              <button onClick={() => setModalOpen(false)} data-testid="vehicle-makes-modal-close">Kapat</button>
            </div>

            {error && <div className="text-sm text-red-600 mb-2" data-testid="vehicle-makes-error">{error}</div>}

            <div className="space-y-3">
              <input
                className="w-full border rounded p-2"
                placeholder="Name"
                value={form.name}
                onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
                data-testid="vehicle-makes-name-input"
              />
              <input
                className="w-full border rounded p-2"
                placeholder="Slug"
                value={form.slug}
                onChange={(e) => setForm((prev) => ({ ...prev, slug: e.target.value }))}
                data-testid="vehicle-makes-slug-input"
              />
              <input
                className="w-full border rounded p-2"
                placeholder="Country code"
                value={form.country_code}
                onChange={(e) => setForm((prev) => ({ ...prev, country_code: e.target.value.toUpperCase() }))}
                data-testid="vehicle-makes-country-input"
              />
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={form.active_flag}
                  onChange={(e) => setForm((prev) => ({ ...prev, active_flag: e.target.checked }))}
                  data-testid="vehicle-makes-active-checkbox"
                />
                Aktif
              </label>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <button className="px-4 py-2 border rounded" onClick={() => setModalOpen(false)} data-testid="vehicle-makes-cancel">
                Vazgeç
              </button>
              <button className="px-4 py-2 bg-blue-600 text-white rounded" onClick={handleSave} data-testid="vehicle-makes-save">
                Kaydet
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminVehicleMakes;
