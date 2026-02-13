import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { 
  ArrowLeft, Check, X, Loader2, Car, ChevronRight,
  ToggleLeft, ToggleRight, Eye, EyeOff
} from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api/v1/admin/master-data`;

export default function AdminVehicleMDM() {
  const { makeId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [makes, setMakes] = useState([]);
  const [models, setModels] = useState([]);
  const [selectedMake, setSelectedMake] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showInactive, setShowInactive] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [editingField, setEditingField] = useState(null);
  const [editValue, setEditValue] = useState('');
  const [saving, setSaving] = useState(false);
  const [viewMode, setViewMode] = useState(makeId ? 'models' : 'makes');

  const isSuperAdmin = user?.role === 'super_admin';

  const fetchMakes = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/vehicle-makes`);
      let data = response.data;
      if (!showInactive) {
        data = data.filter(m => m.is_active);
      }
      setMakes(data);
    } catch (error) {
      console.error('Failed to fetch makes:', error);
      if (error.response?.status === 401) {
        toast.error('Oturum süresi doldu');
      } else if (error.response?.status === 403) {
        toast.error('Bu sayfaya erişim yetkiniz yok');
      } else {
        toast.error('Markalar yüklenemedi');
      }
    } finally {
      setLoading(false);
    }
  }, [showInactive]);

  const fetchModels = useCallback(async (makeIdParam) => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/vehicle-makes/${makeIdParam}/models`);
      let data = response.data;
      if (!showInactive) {
        data = data.filter(m => m.is_active);
      }
      setModels(data);
      
      // Also fetch make info
      const makesResponse = await axios.get(`${API}/vehicle-makes`);
      const make = makesResponse.data.find(m => m.id === makeIdParam);
      setSelectedMake(make);
    } catch (error) {
      console.error('Failed to fetch models:', error);
      if (error.response?.status === 404) {
        toast.error('Marka bulunamadı');
        navigate('/admin/master-data/vehicle-makes');
      } else {
        toast.error('Modeller yüklenemedi');
      }
    } finally {
      setLoading(false);
    }
  }, [showInactive, navigate]);

  useEffect(() => {
    if (makeId) {
      setViewMode('models');
      fetchModels(makeId);
    } else {
      setViewMode('makes');
      fetchMakes();
    }
  }, [makeId, fetchMakes, fetchModels]);

  const handleEdit = (item, field, value) => {
    setEditingId(item.id);
    setEditingField(field);
    setEditValue(value);
  };

  const handleSaveMake = async (make) => {
    if (editingField === null) return;
    
    setSaving(true);
    try {
      let payload = {};
      
      if (editingField === 'label_tr') {
        payload = { label_tr: editValue };
      } else if (editingField === 'label_de') {
        payload = { label_de: editValue };
      } else if (editingField === 'label_fr') {
        payload = { label_fr: editValue };
      } else if (editingField === 'is_active') {
        if (!isSuperAdmin) {
          toast.error('Bu alanı sadece Super Admin değiştirebilir');
          return;
        }
        payload = { is_active: editValue };
      }

      await axios.patch(`${API}/vehicle-makes/${make.id}`, payload);
      toast.success('Değişiklik kaydedildi');
      fetchMakes();
    } catch (error) {
      if (error.response?.status === 403) {
        toast.error('Bu işlem için yetkiniz yok');
      } else if (error.response?.status === 422) {
        toast.error(error.response.data?.message || 'Geçersiz değer');
      } else {
        toast.error('Kaydetme başarısız');
      }
    } finally {
      setSaving(false);
      setEditingId(null);
      setEditingField(null);
      setEditValue('');
    }
  };

  const handleSaveModel = async (model) => {
    if (editingField === null) return;
    
    setSaving(true);
    try {
      let payload = {};
      
      if (editingField === 'label_tr') {
        payload = { label_tr: editValue };
      } else if (editingField === 'label_de') {
        payload = { label_de: editValue };
      } else if (editingField === 'label_fr') {
        payload = { label_fr: editValue };
      } else if (editingField === 'is_active') {
        if (!isSuperAdmin) {
          toast.error('Bu alanı sadece Super Admin değiştirebilir');
          return;
        }
        payload = { is_active: editValue };
      }

      await axios.patch(`${API}/vehicle-models/${model.id}`, payload);
      toast.success('Değişiklik kaydedildi');
      fetchModels(makeId);
    } catch (error) {
      if (error.response?.status === 403) {
        toast.error('Bu işlem için yetkiniz yok');
      } else if (error.response?.status === 422) {
        toast.error(error.response.data?.message || 'Geçersiz değer');
      } else {
        toast.error('Kaydetme başarısız');
      }
    } finally {
      setSaving(false);
      setEditingId(null);
      setEditingField(null);
      setEditValue('');
    }
  };

  const handleCancel = () => {
    setEditingId(null);
    setEditingField(null);
    setEditValue('');
  };

  const handleToggleMake = async (make) => {
    if (!isSuperAdmin) {
      toast.error('Bu alanı sadece Super Admin değiştirebilir');
      return;
    }
    
    setSaving(true);
    try {
      const newValue = !make.is_active;
      await axios.patch(`${API}/vehicle-makes/${make.id}`, { is_active: newValue });
      toast.success(newValue ? 'Marka aktifleştirildi' : 'Marka pasifleştirildi');
      fetchMakes();
    } catch (error) {
      toast.error('Kaydetme başarısız');
    } finally {
      setSaving(false);
    }
  };

  const handleToggleModel = async (model) => {
    if (!isSuperAdmin) {
      toast.error('Bu alanı sadece Super Admin değiştirebilir');
      return;
    }
    
    setSaving(true);
    try {
      const newValue = !model.is_active;
      await axios.patch(`${API}/vehicle-models/${model.id}`, { is_active: newValue });
      toast.success(newValue ? 'Model aktifleştirildi' : 'Model pasifleştirildi');
      fetchModels(makeId);
    } catch (error) {
      toast.error('Kaydetme başarısız');
    } finally {
      setSaving(false);
    }
  };

  const EditableCell = ({ item, field, value, onSave, type = 'text' }) => {
    const isEditing = editingId === item.id && editingField === field;
    const isConfigField = field === 'is_active';
    const canEdit = !isConfigField || isSuperAdmin;

    if (type === 'toggle') {
      return (
        <button
          onClick={() => canEdit && (viewMode === 'makes' ? handleToggleMake(item) : handleToggleModel(item))}
          disabled={!canEdit || saving}
          className={`p-1 rounded transition-colors ${
            canEdit 
              ? 'hover:bg-muted cursor-pointer' 
              : 'cursor-not-allowed opacity-50'
          }`}
          title={!canEdit ? 'Sadece Super Admin değiştirebilir' : (value ? 'Pasifleştir' : 'Aktifleştir')}
          data-testid={`toggle-${item.slug}`}
        >
          {value ? (
            <ToggleRight className="w-6 h-6 text-green-500" />
          ) : (
            <ToggleLeft className="w-6 h-6 text-muted-foreground" />
          )}
        </button>
      );
    }

    if (isEditing) {
      return (
        <div className="flex items-center gap-1">
          <input
            type="text"
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            className="h-8 px-2 text-sm border rounded w-full min-w-[100px]"
            autoFocus
            onKeyDown={(e) => {
              if (e.key === 'Enter') onSave(item);
              if (e.key === 'Escape') handleCancel();
            }}
            data-testid={`edit-input-${field}-${item.slug}`}
          />
          <button
            onClick={() => onSave(item)}
            disabled={saving}
            className="p-1 rounded hover:bg-green-100 dark:hover:bg-green-900/30 text-green-600"
          >
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
          </button>
          <button
            onClick={handleCancel}
            className="p-1 rounded hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      );
    }

    return (
      <span
        onClick={() => handleEdit(item, field, value || '')}
        className="cursor-pointer hover:bg-muted px-2 py-1 rounded transition-colors inline-block min-w-[60px]"
        data-testid={`cell-${field}-${item.slug}`}
      >
        {value || <span className="text-muted-foreground italic">-</span>}
      </span>
    );
  };

  // MAKES VIEW
  if (viewMode === 'makes') {
    return (
      <div className="space-y-6" data-testid="admin-vehicle-makes-page">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
              <Car className="w-6 h-6" />
              Araç Markaları
            </h1>
            <p className="text-muted-foreground text-sm mt-1">
              {makes.length} marka
              {!isSuperAdmin && (
                <span className="ml-2 text-amber-600 dark:text-amber-400">
                  (Sadece etiket düzenleme yetkisi)
                </span>
              )}
            </p>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={showInactive}
              onChange={(e) => setShowInactive(e.target.checked)}
              className="rounded"
              data-testid="show-inactive-checkbox"
            />
            {showInactive ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
            Pasif markaları göster
          </label>
        </div>

        {/* Table */}
        <div className="border rounded-lg overflow-hidden bg-card">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/50">
                <tr>
                  <th className="text-left p-3 font-medium">Slug</th>
                  <th className="text-left p-3 font-medium">İsim (TR)</th>
                  <th className="text-left p-3 font-medium">İsim (DE)</th>
                  <th className="text-left p-3 font-medium">İsim (FR)</th>
                  <th className="text-center p-3 font-medium">Aktif</th>
                  <th className="text-center p-3 font-medium">Modeller</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="p-8 text-center">
                      <Loader2 className="w-6 h-6 animate-spin mx-auto text-muted-foreground" />
                    </td>
                  </tr>
                ) : makes.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="p-8 text-center text-muted-foreground">
                      <Car className="w-10 h-10 mx-auto mb-2 opacity-30" />
                      <p>Marka bulunamadı</p>
                    </td>
                  </tr>
                ) : (
                  makes.map((make) => (
                    <tr 
                      key={make.id} 
                      className={`hover:bg-muted/30 transition-colors ${!make.is_active ? 'opacity-50 bg-muted/20' : ''}`}
                      data-testid={`make-row-${make.slug}`}
                    >
                      <td className="p-3">
                        <code className="px-2 py-1 rounded bg-muted text-xs font-mono">
                          {make.slug}
                        </code>
                      </td>
                      <td className="p-3">
                        <EditableCell item={make} field="label_tr" value={make.label_tr} onSave={handleSaveMake} />
                      </td>
                      <td className="p-3">
                        <EditableCell item={make} field="label_de" value={make.label_de} onSave={handleSaveMake} />
                      </td>
                      <td className="p-3">
                        <EditableCell item={make} field="label_fr" value={make.label_fr} onSave={handleSaveMake} />
                      </td>
                      <td className="p-3 text-center">
                        <EditableCell item={make} field="is_active" value={make.is_active} onSave={handleSaveMake} type="toggle" />
                      </td>
                      <td className="p-3 text-center">
                        <button
                          onClick={() => navigate(`/admin/master-data/vehicle-makes/${make.id}/models`)}
                          className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium text-primary hover:bg-primary/10 transition-colors"
                          data-testid={`models-link-${make.slug}`}
                        >
                          Modeller
                          <ChevronRight className="w-3 h-3" />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
          <div className="flex items-center gap-1">
            <ToggleRight className="w-4 h-4 text-green-500" />
            <span>Aktif</span>
          </div>
          <div className="flex items-center gap-1">
            <ToggleLeft className="w-4 h-4" />
            <span>Pasif (Soft-deleted)</span>
          </div>
        </div>
      </div>
    );
  }

  // MODELS VIEW
  return (
    <div className="space-y-6" data-testid="admin-vehicle-models-page">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <button
          onClick={() => navigate('/admin/master-data/vehicle-makes')}
          className="flex items-center gap-1 hover:text-foreground transition-colors"
          data-testid="back-to-makes"
        >
          <ArrowLeft className="w-4 h-4" />
          Markalar
        </button>
        <span>/</span>
        <span className="text-foreground font-medium">{selectedMake?.label_tr || selectedMake?.slug}</span>
        <span>/</span>
        <span className="text-foreground">Modeller</span>
      </div>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <Car className="w-6 h-6" />
            Modeller: <code className="text-lg px-2 py-1 bg-muted rounded">{selectedMake?.slug}</code>
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            {models.length} model
            {!isSuperAdmin && (
              <span className="ml-2 text-amber-600 dark:text-amber-400">
                (Sadece etiket düzenleme yetkisi)
              </span>
            )}
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <label className="flex items-center gap-2 text-sm cursor-pointer">
          <input
            type="checkbox"
            checked={showInactive}
            onChange={(e) => setShowInactive(e.target.checked)}
            className="rounded"
            data-testid="show-inactive-models-checkbox"
          />
          {showInactive ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
          Pasif modelleri göster
        </label>
      </div>

      {/* Table */}
      <div className="border rounded-lg overflow-hidden bg-card">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="text-left p-3 font-medium">Slug</th>
                <th className="text-left p-3 font-medium">İsim (TR)</th>
                <th className="text-left p-3 font-medium">İsim (DE)</th>
                <th className="text-left p-3 font-medium">İsim (FR)</th>
                <th className="text-center p-3 font-medium">Aktif</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {loading ? (
                <tr>
                  <td colSpan={5} className="p-8 text-center">
                    <Loader2 className="w-6 h-6 animate-spin mx-auto text-muted-foreground" />
                  </td>
                </tr>
              ) : models.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-muted-foreground">
                    <Car className="w-10 h-10 mx-auto mb-2 opacity-30" />
                    <p>Model bulunamadı</p>
                  </td>
                </tr>
              ) : (
                models.map((model) => (
                  <tr 
                    key={model.id} 
                    className={`hover:bg-muted/30 transition-colors ${!model.is_active ? 'opacity-50 bg-muted/20' : ''}`}
                    data-testid={`model-row-${model.slug}`}
                  >
                    <td className="p-3">
                      <code className="px-2 py-1 rounded bg-muted text-xs font-mono">
                        {model.slug}
                      </code>
                    </td>
                    <td className="p-3">
                      <EditableCell item={model} field="label_tr" value={model.label_tr} onSave={handleSaveModel} />
                    </td>
                    <td className="p-3">
                      <EditableCell item={model} field="label_de" value={model.label_de} onSave={handleSaveModel} />
                    </td>
                    <td className="p-3">
                      <EditableCell item={model} field="label_fr" value={model.label_fr} onSave={handleSaveModel} />
                    </td>
                    <td className="p-3 text-center">
                      <EditableCell item={model} field="is_active" value={model.is_active} onSave={handleSaveModel} type="toggle" />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
        <div className="flex items-center gap-1">
          <ToggleRight className="w-4 h-4 text-green-500" />
          <span>Aktif</span>
        </div>
        <div className="flex items-center gap-1">
          <ToggleLeft className="w-4 h-4" />
          <span>Pasif (Soft-deleted)</span>
        </div>
      </div>
    </div>
  );
}
