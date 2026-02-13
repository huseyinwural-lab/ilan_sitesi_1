import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { 
  Settings2, Search, Filter, Check, X, Loader2,
  ChevronRight, ToggleLeft, ToggleRight, List
} from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api/v1/admin/master-data`;

const typeColors = {
  text: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
  number: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400',
  select: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400',
  boolean: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
  date: 'bg-rose-100 text-rose-800 dark:bg-rose-900/30 dark:text-rose-400',
};

export default function AdminAttributes() {
  const { user } = useAuth();
  const { getTranslated } = useLanguage();
  const [attributes, setAttributes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [editingId, setEditingId] = useState(null);
  const [editingField, setEditingField] = useState(null);
  const [editValue, setEditValue] = useState('');
  const [saving, setSaving] = useState(false);

  const isSuperAdmin = user?.role === 'super_admin';

  const fetchAttributes = useCallback(async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (searchQuery) params.append('q', searchQuery);
      if (statusFilter !== '') params.append('is_active', statusFilter);
      
      const response = await axios.get(`${API}/attributes?${params}`);
      setAttributes(response.data);
    } catch (error) {
      console.error('Failed to fetch attributes:', error);
      if (error.response?.status === 401) {
        toast.error('Oturum süresi doldu, lütfen tekrar giriş yapın');
      } else if (error.response?.status === 403) {
        toast.error('Bu sayfaya erişim yetkiniz yok');
      } else {
        toast.error('Özellikler yüklenemedi');
      }
    } finally {
      setLoading(false);
    }
  }, [searchQuery, statusFilter]);

  useEffect(() => {
    const debounce = setTimeout(() => {
      fetchAttributes();
    }, 300);
    return () => clearTimeout(debounce);
  }, [fetchAttributes]);

  const handleEdit = (attr, field, value) => {
    setEditingId(attr.id);
    setEditingField(field);
    setEditValue(value);
  };

  const handleSave = async (attr) => {
    if (editingField === null) return;
    
    setSaving(true);
    try {
      let payload = {};
      
      if (editingField.startsWith('name.')) {
        const lang = editingField.split('.')[1];
        payload = { name: { ...attr.name, [lang]: editValue } };
      } else if (editingField === 'is_active') {
        if (!isSuperAdmin) {
          toast.error('Bu alanı sadece Super Admin değiştirebilir');
          return;
        }
        payload = { is_active: editValue };
      } else if (editingField === 'is_filterable') {
        if (!isSuperAdmin) {
          toast.error('Bu alanı sadece Super Admin değiştirebilir');
          return;
        }
        payload = { is_filterable: editValue };
      } else if (editingField === 'display_order') {
        if (!isSuperAdmin) {
          toast.error('Bu alanı sadece Super Admin değiştirebilir');
          return;
        }
        payload = { display_order: parseInt(editValue) || 0 };
      }

      await axios.patch(`${API}/attributes/${attr.id}`, payload);
      toast.success('Değişiklik kaydedildi');
      fetchAttributes();
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

  const handleToggle = async (attr, field) => {
    if (!isSuperAdmin) {
      toast.error('Bu alanı sadece Super Admin değiştirebilir');
      return;
    }
    
    setSaving(true);
    try {
      const newValue = !attr[field];
      await axios.patch(`${API}/attributes/${attr.id}`, { [field]: newValue });
      toast.success('Değişiklik kaydedildi');
      fetchAttributes();
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

  const EditableCell = ({ attr, field, value, type = 'text' }) => {
    const isEditing = editingId === attr.id && editingField === field;
    const isConfigField = ['is_active', 'is_filterable', 'display_order'].includes(field);
    const canEdit = !isConfigField || isSuperAdmin;

    if (type === 'toggle') {
      return (
        <button
          onClick={() => canEdit && handleToggle(attr, field)}
          disabled={!canEdit || saving}
          className={`p-1 rounded transition-colors ${
            canEdit 
              ? 'hover:bg-muted cursor-pointer' 
              : 'cursor-not-allowed opacity-50'
          }`}
          title={!canEdit ? 'Sadece Super Admin değiştirebilir' : undefined}
          data-testid={`toggle-${field}-${attr.key}`}
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
              if (e.key === 'Enter') handleSave(attr);
              if (e.key === 'Escape') handleCancel();
            }}
            data-testid={`edit-input-${field}-${attr.key}`}
          />
          <button
            onClick={() => handleSave(attr)}
            disabled={saving}
            className="p-1 rounded hover:bg-green-100 dark:hover:bg-green-900/30 text-green-600"
            data-testid={`save-${field}-${attr.key}`}
          >
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
          </button>
          <button
            onClick={handleCancel}
            className="p-1 rounded hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600"
            data-testid={`cancel-${field}-${attr.key}`}
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
          {value || '-'}
        </span>
      );
    }

    return (
      <span
        onClick={() => handleEdit(attr, field, value || '')}
        className="cursor-pointer hover:bg-muted px-2 py-1 rounded transition-colors inline-block min-w-[60px]"
        data-testid={`cell-${field}-${attr.key}`}
      >
        {value || <span className="text-muted-foreground italic">-</span>}
      </span>
    );
  };

  return (
    <div className="space-y-6" data-testid="admin-attributes-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <Settings2 className="w-6 h-6" />
            Attributes
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            {attributes.length} özellik tanımlı
            {!isSuperAdmin && (
              <span className="ml-2 text-amber-600 dark:text-amber-400">
                (Sadece etiket düzenleme yetkisi)
              </span>
            )}
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        {/* Search */}
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Anahtar kelimeye göre ara..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full h-10 pl-10 pr-4 rounded-md border bg-background text-sm"
            data-testid="search-input"
          />
        </div>

        {/* Status Filter */}
        <div className="relative">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="h-10 pl-10 pr-8 rounded-md border bg-background text-sm appearance-none cursor-pointer"
            data-testid="status-filter"
          >
            <option value="">Tüm Durumlar</option>
            <option value="true">Aktif</option>
            <option value="false">Pasif</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="border rounded-lg overflow-hidden bg-card">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="text-left p-3 font-medium">Anahtar (Key)</th>
                <th className="text-left p-3 font-medium">İsim (TR)</th>
                <th className="text-left p-3 font-medium">İsim (DE)</th>
                <th className="text-left p-3 font-medium">Tip</th>
                <th className="text-center p-3 font-medium">Aktif</th>
                <th className="text-center p-3 font-medium">Filtrelenebilir</th>
                <th className="text-center p-3 font-medium">Sıra</th>
                <th className="text-center p-3 font-medium">Seçenekler</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {loading ? (
                <tr>
                  <td colSpan={8} className="p-8 text-center">
                    <Loader2 className="w-6 h-6 animate-spin mx-auto text-muted-foreground" />
                  </td>
                </tr>
              ) : attributes.length === 0 ? (
                <tr>
                  <td colSpan={8} className="p-8 text-center text-muted-foreground">
                    <Settings2 className="w-10 h-10 mx-auto mb-2 opacity-30" />
                    <p>Özellik bulunamadı</p>
                  </td>
                </tr>
              ) : (
                attributes.map((attr) => (
                  <tr 
                    key={attr.id} 
                    className={`hover:bg-muted/30 transition-colors ${!attr.is_active ? 'opacity-50 bg-muted/20' : ''}`}
                    data-testid={`attr-row-${attr.key}`}
                  >
                    <td className="p-3">
                      <code className="px-2 py-1 rounded bg-muted text-xs font-mono">
                        {attr.key}
                      </code>
                    </td>
                    <td className="p-3">
                      <EditableCell attr={attr} field="name.tr" value={attr.name?.tr} />
                    </td>
                    <td className="p-3">
                      <EditableCell attr={attr} field="name.de" value={attr.name?.de} />
                    </td>
                    <td className="p-3">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${typeColors[attr.attribute_type] || 'bg-muted'}`}>
                        {attr.attribute_type}
                      </span>
                    </td>
                    <td className="p-3 text-center">
                      <EditableCell attr={attr} field="is_active" value={attr.is_active} type="toggle" />
                    </td>
                    <td className="p-3 text-center">
                      <EditableCell attr={attr} field="is_filterable" value={attr.is_filterable} type="toggle" />
                    </td>
                    <td className="p-3 text-center">
                      <EditableCell attr={attr} field="display_order" value={attr.display_order} type="number" />
                    </td>
                    <td className="p-3 text-center">
                      {attr.attribute_type === 'select' && (
                        <a
                          href={`/admin/master-data/attributes/${attr.id}/options`}
                          className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium text-primary hover:bg-primary/10 transition-colors"
                          data-testid={`options-link-${attr.key}`}
                        >
                          <List className="w-3 h-3" />
                          Seçenekler
                          <ChevronRight className="w-3 h-3" />
                        </a>
                      )}
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
          <span>Pasif</span>
        </div>
        {!isSuperAdmin && (
          <div className="flex items-center gap-1 text-amber-600 dark:text-amber-400">
            <span>⚠️ Konfigürasyon alanları (Aktif, Filtrelenebilir, Sıra) sadece Super Admin tarafından düzenlenebilir</span>
          </div>
        )}
      </div>
    </div>
  );
}
