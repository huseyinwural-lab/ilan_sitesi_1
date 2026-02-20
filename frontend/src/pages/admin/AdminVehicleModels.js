import React, { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

const vehicleTypeOptions = [
  { value: 'car', label: 'Otomobil' },
  { value: 'suv', label: 'SUV' },
  { value: 'offroad', label: 'Arazi' },
  { value: 'pickup', label: 'Pickup' },
  { value: 'truck', label: 'Kamyon' },
  { value: 'bus', label: 'Otobüs' },
];

const vehicleTypeLabels = vehicleTypeOptions.reduce((acc, item) => {
  acc[item.value] = item.label;
  return acc;
}, {});

const resolveVehicleTypeLabel = (value) => vehicleTypeLabels[value] || value;

const emptyForm = {
  make_id: '',
  name: '',
  slug: '',
  vehicle_type: '',
  active_flag: true,
};

const AdminVehicleModels = () => {
  const [searchParams] = useSearchParams();
  const urlCountry = (searchParams.get('country') || '').toUpperCase();
  const [items, setItems] = useState([]);
  const [makes, setMakes] = useState([]);
  const [filterMake, setFilterMake] = useState('');
  const [filterType, setFilterType] = useState('');
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ ...emptyForm });
  const [error, setError] = useState(null);

  const authHeader = useMemo(() => ({
    Authorization: `Bearer ${localStorage.getItem('access_token')}`,
  }), []);

  const fetchMakes = async () => {
    try {
      const params = urlCountry ? `?country=${urlCountry}` : '';
      const res = await axios.get(`${API_BASE_URL}/api/admin/vehicle-makes${params}`, { headers: authHeader });
      setMakes(res.data.items || []);
    } catch (e) {
      console.error('Failed to load makes', e);
    }
  };

  const fetchItems = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filterMake) params.set('make_id', filterMake);
      if (filterType) params.set('vehicle_type', filterType);
      if (urlCountry) params.set('country', urlCountry);
      const query = params.toString();
      const res = await axios.get(`${API_BASE_URL}/api/admin/vehicle-models${query ? `?${query}` : ''}`, { headers: authHeader });
      setItems(res.data.items || []);
    } catch (e) {
      console.error('Failed to load models', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMakes();
  }, [urlCountry]);

  useEffect(() => {
    fetchItems();
  }, [filterMake, filterType, urlCountry]);

  const openCreate = () => {
    setEditing(null);
    setForm({ ...emptyForm });
    setError(null);
    setModalOpen(true);
  };

  const openEdit = (item) => {
    setEditing(item);
    setForm({
      make_id: item.make_id || '',
      name: item.name || '',
      slug: item.slug || '',
      vehicle_type: item.vehicle_type || '',
      active_flag: item.active_flag !== false,
    });
    setError(null);
    setModalOpen(true);
  };

  const handleSave = async () => {
    if (!form.make_id || !form.name || !form.slug || !form.vehicle_type) {
      setError('Make, name, slug ve vehicle type zorunlu');
      return;
    }
    const payload = {
      ...form,
      slug: form.slug.trim().toLowerCase(),
    };
    try {
      if (editing) {
        await axios.patch(`${API_BASE_URL}/api/admin/vehicle-models/${editing.id}`, payload, { headers: authHeader });
      } else {
        await axios.post(`${API_BASE_URL}/api/admin/vehicle-models`, payload, { headers: authHeader });
      }
      setModalOpen(false);
      fetchItems();
    } catch (e) {
      setError(e?.response?.data?.detail || 'Kaydetme başarısız');
    }
  };

  const handleDelete = async (item) => {
    if (!window.confirm('Model pasif edilsin mi?')) return;
    try {
      await axios.delete(`${API_BASE_URL}/api/admin/vehicle-models/${item.id}`, { headers: authHeader });
      fetchItems();
    } catch (e) {
      alert('Silme başarısız');
    }
  };

  const makeMap = useMemo(() => {
    const map = new Map();
    makes.forEach((make) => map.set(make.id, { name: make.name, country_code: make.country_code }));
    return map;
  }, [makes]);

  const resolveMakeName = (makeId) => makeMap.get(makeId)?.name || '-';
  const resolveMakeCountry = (makeId) => makeMap.get(makeId)?.country_code || '-';
  const resolveVehicleType = (value) => resolveVehicleTypeLabel(value) || '-';

  return (
    <div className="p-6 space-y-6" data-testid="admin-vehicle-models-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Araç Modelleri</h1>
          <p className="text-sm text-muted-foreground">Country: {urlCountry || 'Global'}</p>
        </div>
        <button
          onClick={openCreate}
          className="bg-blue-600 text-white px-4 py-2 rounded-md"
          data-testid="vehicle-models-create-open"
        >
          Yeni Model
        </button>
      </div>

      <div className="flex items-center gap-3" data-testid="vehicle-models-filters">
        <select
          className="border rounded p-2"
          value={filterMake}
          onChange={(e) => setFilterMake(e.target.value)}
          data-testid="vehicle-models-filter-make"
        >
          <option value="">Tüm Markalar</option>
          {makes.map((make) => (
            <option key={make.id} value={make.id}>{make.name}</option>
          ))}
        </select>
        <select
          className="border rounded p-2"
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          data-testid="vehicle-models-filter-type"
        >
          <option value="">Tüm Tipler</option>
          {vehicleTypeOptions.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
      </div>

      <div className="border rounded-lg overflow-hidden" data-testid="vehicle-models-table">
        <table className="min-w-full text-sm">
          <thead className="bg-muted">
            <tr>
              <th className="text-left px-3 py-2" data-testid="vehicle-models-header-make">Make</th>
              <th className="text-left px-3 py-2" data-testid="vehicle-models-header-name">Model</th>
              <th className="text-left px-3 py-2" data-testid="vehicle-models-header-slug">Slug</th>
              <th className="text-left px-3 py-2" data-testid="vehicle-models-header-country">Country</th>
              <th className="text-left px-3 py-2" data-testid="vehicle-models-header-type">Vehicle Type</th>
              <th className="text-left px-3 py-2" data-testid="vehicle-models-header-active">Active</th>
              <th className="text-right px-3 py-2" data-testid="vehicle-models-header-actions">Aksiyon</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td className="px-3 py-4" colSpan="7">Yükleniyor...</td></tr>
            ) : items.length === 0 ? (
              <tr><td className="px-3 py-4" colSpan="7">Kayıt yok</td></tr>
            ) : (
              items.map((item) => (
                <tr key={item.id} className="border-t" data-testid={`vehicle-models-row-${item.id}`}>
                  <td className="px-3 py-2" data-testid={`vehicle-models-make-${item.id}`}>{resolveMakeName(item.make_id)}</td>
                  <td className="px-3 py-2" data-testid={`vehicle-models-name-${item.id}`}>{item.name}</td>
                  <td className="px-3 py-2 text-muted-foreground" data-testid={`vehicle-models-slug-${item.id}`}>{item.slug}</td>
                  <td className="px-3 py-2" data-testid={`vehicle-models-country-${item.id}`}>{resolveMakeCountry(item.make_id)}</td>
                  <td className="px-3 py-2" data-testid={`vehicle-models-type-${item.id}`}>{resolveVehicleType(item.vehicle_type)}</td>
                  <td className="px-3 py-2" data-testid={`vehicle-models-active-${item.id}`}>{item.active_flag ? 'yes' : 'no'}</td>
                  <td className="px-3 py-2 text-right space-x-2" data-testid={`vehicle-models-actions-${item.id}`}>
                    <button
                      className="px-2 py-1 border rounded"
                      onClick={() => openEdit(item)}
                      data-testid={`vehicle-models-edit-${item.id}`}
                    >
                      Düzenle
                    </button>
                    <button
                      className="px-2 py-1 border rounded text-red-600"
                      onClick={() => handleDelete(item)}
                      data-testid={`vehicle-models-delete-${item.id}`}
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
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center" data-testid="vehicle-models-modal">
          <div className="bg-white rounded-lg shadow-lg w-full max-w-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">{editing ? 'Model Düzenle' : 'Model Oluştur'}</h2>
              <button onClick={() => setModalOpen(false)} data-testid="vehicle-models-modal-close">Kapat</button>
            </div>

            {error && <div className="text-sm text-red-600 mb-2" data-testid="vehicle-models-error">{error}</div>}

            <div className="space-y-3">
              <select
                className="w-full border rounded p-2"
                value={form.make_id}
                onChange={(e) => setForm((prev) => ({ ...prev, make_id: e.target.value }))}
                data-testid="vehicle-models-make-select"
              >
                <option value="">Marka seç</option>
                {makes.map((make) => (
                  <option key={make.id} value={make.id}>{make.name}</option>
                ))}
              </select>
              <select
                className="w-full border rounded p-2"
                value={form.vehicle_type}
                onChange={(e) => setForm((prev) => ({ ...prev, vehicle_type: e.target.value }))}
                data-testid="vehicle-models-type-select"
              >
                <option value="">Araç tipi seç</option>
                {vehicleTypeOptions.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
              <input
                className="w-full border rounded p-2"
                placeholder="Name"
                value={form.name}
                onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
                data-testid="vehicle-models-name-input"
              />
              <input
                className="w-full border rounded p-2"
                placeholder="Slug"
                value={form.slug}
                onChange={(e) => setForm((prev) => ({ ...prev, slug: e.target.value }))}
                data-testid="vehicle-models-slug-input"
              />
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={form.active_flag}
                  onChange={(e) => setForm((prev) => ({ ...prev, active_flag: e.target.checked }))}
                  data-testid="vehicle-models-active-checkbox"
                />
                Aktif
              </label>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <button className="px-4 py-2 border rounded" onClick={() => setModalOpen(false)} data-testid="vehicle-models-cancel">
                Vazgeç
              </button>
              <button className="px-4 py-2 bg-blue-600 text-white rounded" onClick={handleSave} data-testid="vehicle-models-save">
                Kaydet
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminVehicleModels;
