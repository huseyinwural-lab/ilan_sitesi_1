import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { 
  ArrowLeft, Check, X, Loader2, List,
  ToggleLeft, ToggleRight, GripVertical
} from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api/v1/admin/master-data`;

export default function AdminOptions() {
  const { attributeId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [attribute, setAttribute] = useState(null);
  const [options, setOptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState(null);
  const [editingField, setEditingField] = useState(null);
  const [editValue, setEditValue] = useState('');
  const [saving, setSaving] = useState(false);

  const isSuperAdmin = user?.role === 'super_admin';

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      
      // Fetch attribute info
      const attrResponse = await axios.get(`${API}/attributes`);
      const foundAttr = attrResponse.data.find(a => a.id === attributeId);
      setAttribute(foundAttr);
      
      // Fetch options
      const optResponse = await axios.get(`${API}/attributes/${attributeId}/options`);
      setOptions(optResponse.data);
    } catch (error) {
      console.error('Failed to fetch data:', error);
      if (error.response?.status === 401) {
        toast.error('Oturum süresi doldu');
      } else if (error.response?.status === 403) {
        toast.error('Bu sayfaya erişim yetkiniz yok');
      } else if (error.response?.status === 404) {
        toast.error('Özellik bulunamadı');
        navigate('/admin/master-data/attributes');
      } else {
        toast.error('Veriler yüklenemedi');
      }
    } finally {
      setLoading(false);
    }
  }, [attributeId, navigate]);

  useEffect(() => {
    if (attributeId) {
      fetchData();
    }
  }, [fetchData, attributeId]);

  const handleEdit = (option, field, value) => {
    setEditingId(option.id);
    setEditingField(field);
    setEditValue(value);
  };

  const handleSave = async (option) => {
    if (editingField === null) return;
    
    setSaving(true);
    try {
      let payload = {};
      
      if (editingField.startsWith('label.')) {
        const lang = editingField.split('.')[1];
        payload = { label: { ...option.label, [lang]: editValue } };
      } else if (editingField === 'is_active') {
        if (!isSuperAdmin) {
          toast.error('Bu alanı sadece Super Admin değiştirebilir');
          return;
        }
        payload = { is_active: editValue };
      } else if (editingField === 'sort_order') {
        if (!isSuperAdmin) {
          toast.error('Bu alanı sadece Super Admin değiştirebilir');
          return;
        }
        payload = { sort_order: parseInt(editValue) || 0 };
      }

      await axios.patch(`${API}/options/${option.id}`, payload);
      toast.success('Değişiklik kaydedildi');
      fetchData();
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

  const handleToggle = async (option, field) => {
    if (!isSuperAdmin) {
      toast.error('Bu alanı sadece Super Admin değiştirebilir');
      return;
    }
    
    setSaving(true);
    try {
      const newValue = !option[field];
      await axios.patch(`${API}/options/${option.id}`, { [field]: newValue });
      toast.success('Değişiklik kaydedildi');
      fetchData();
    } catch (error) {
      if (error.response?.status === 403) {
        toast.error('Bu işlem için yetkiniz yok');
      } else {
        toast.error('Kaydetme başarısız');
      }
    } finally {
      setSaving(false);
    }
  };

  const EditableCell = ({ option, field, value, type = 'text' }) => {
    const isEditing = editingId === option.id && editingField === field;
    const isConfigField = ['is_active', 'sort_order'].includes(field);
    const canEdit = !isConfigField || isSuperAdmin;

    if (type === 'toggle') {
      return (
        <button
          onClick={() => canEdit && handleToggle(option, field)}
          disabled={!canEdit || saving}
          className={`p-1 rounded transition-colors ${
            canEdit 
              ? 'hover:bg-muted cursor-pointer' 
              : 'cursor-not-allowed opacity-50'
          }`}
          title={!canEdit ? 'Sadece Super Admin değiştirebilir' : undefined}
          data-testid={`toggle-${field}-${option.value}`}
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
            type={type === 'number' ? 'number' : 'text'}
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            className="h-8 px-2 text-sm border rounded w-full min-w-[100px]"
            autoFocus
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleSave(option);
              if (e.key === 'Escape') handleCancel();
            }}
            data-testid={`edit-input-${field}-${option.value}`}
          />
          <button
            onClick={() => handleSave(option)}
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

    if (!canEdit && isConfigField) {
      return (
        <span 
          className="text-muted-foreground cursor-not-allowed"
          title="Sadece Super Admin değiştirebilir"
        >
          {value ?? '-'}
        </span>
      );
    }

    return (
      <span
        onClick={() => handleEdit(option, field, value || '')}
        className="cursor-pointer hover:bg-muted px-2 py-1 rounded transition-colors inline-block min-w-[60px]"
        data-testid={`cell-${field}-${option.value}`}
      >
        {value || <span className="text-muted-foreground italic">-</span>}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="admin-options-page">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <button
          onClick={() => navigate('/admin/master-data/attributes')}
          className="flex items-center gap-1 hover:text-foreground transition-colors"
          data-testid="back-to-attributes"
        >
          <ArrowLeft className="w-4 h-4" />
          Attributes
        </button>
        <span>/</span>
        <span className="text-foreground font-medium">{attribute?.name?.tr || attribute?.key}</span>
        <span>/</span>
        <span className="text-foreground">Options</span>
      </div>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <List className="w-6 h-6" />
            Seçenekler: <code className="text-lg px-2 py-1 bg-muted rounded">{attribute?.key}</code>
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            {options.length} seçenek tanımlı
            {!isSuperAdmin && (
              <span className="ml-2 text-amber-600 dark:text-amber-400">
                (Sadece etiket düzenleme yetkisi)
              </span>
            )}
          </p>
        </div>
      </div>

      {/* Table */}
      <div className="border rounded-lg overflow-hidden bg-card">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="text-left p-3 font-medium w-10">Sıra</th>
                <th className="text-left p-3 font-medium">Değer (Value)</th>
                <th className="text-left p-3 font-medium">Etiket (TR)</th>
                <th className="text-left p-3 font-medium">Etiket (DE)</th>
                <th className="text-left p-3 font-medium">Etiket (EN)</th>
                <th className="text-center p-3 font-medium">Aktif</th>
                <th className="text-center p-3 font-medium">Sıra No</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {options.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-muted-foreground">
                    <List className="w-10 h-10 mx-auto mb-2 opacity-30" />
                    <p>Seçenek bulunamadı</p>
                  </td>
                </tr>
              ) : (
                options.map((option, index) => (
                  <tr 
                    key={option.id} 
                    className={`hover:bg-muted/30 transition-colors ${!option.is_active ? 'opacity-50 bg-muted/20' : ''}`}
                    data-testid={`option-row-${option.value}`}
                  >
                    <td className="p-3 text-center text-muted-foreground">
                      <GripVertical className="w-4 h-4 inline-block" />
                    </td>
                    <td className="p-3">
                      <code className="px-2 py-1 rounded bg-muted text-xs font-mono">
                        {option.value}
                      </code>
                    </td>
                    <td className="p-3">
                      <EditableCell option={option} field="label.tr" value={option.label?.tr} />
                    </td>
                    <td className="p-3">
                      <EditableCell option={option} field="label.de" value={option.label?.de} />
                    </td>
                    <td className="p-3">
                      <EditableCell option={option} field="label.en" value={option.label?.en} />
                    </td>
                    <td className="p-3 text-center">
                      <EditableCell option={option} field="is_active" value={option.is_active} type="toggle" />
                    </td>
                    <td className="p-3 text-center">
                      <EditableCell option={option} field="sort_order" value={option.sort_order} type="number" />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Legend */}
      {!isSuperAdmin && (
        <div className="text-xs text-amber-600 dark:text-amber-400">
          ⚠️ Konfigürasyon alanları (Aktif, Sıra No) sadece Super Admin tarafından düzenlenebilir
        </div>
      )}
    </div>
  );
}
