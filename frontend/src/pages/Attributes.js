import { useState, useEffect } from 'react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { 
  Settings2, Plus, Pencil, Trash2, Filter, 
  SortAsc, ToggleLeft, ToggleRight, ChevronDown
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const typeColors = {
  text: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
  number: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400',
  select: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400',
  multi_select: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-400',
  boolean: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
  date: 'bg-rose-100 text-rose-800 dark:bg-rose-900/30 dark:text-rose-400',
  range: 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900/30 dark:text-cyan-400',
  textarea: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400',
};

export default function Attributes() {
  const [attributes, setAttributes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [expandedAttr, setExpandedAttr] = useState(null);
  const { t, getTranslated, language } = useLanguage();

  useEffect(() => {
    fetchAttributes();
  }, [typeFilter]);

  const fetchAttributes = async () => {
    try {
      const params = new URLSearchParams();
      if (typeFilter) params.append('attribute_type', typeFilter);
      const response = await axios.get(`${API}/attributes?${params}`);
      setAttributes(response.data);
    } catch (error) {
      console.error('Failed to fetch attributes:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleActive = async (attrId, currentState) => {
    try {
      await axios.patch(`${API}/attributes/${attrId}`, { is_active: !currentState });
      fetchAttributes();
    } catch (error) {
      console.error('Failed to toggle attribute:', error);
    }
  };

  return (
    <div className="space-y-6" data-testid="attributes-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Attributes</h1>
          <p className="text-muted-foreground text-sm mt-1">
            {attributes.length} attributes configured
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center gap-2 h-9 px-4 rounded-md bg-primary text-primary-foreground font-medium text-sm hover:bg-primary/90 transition-colors"
          data-testid="create-attribute-btn"
        >
          <Plus size={16} />
          Add Attribute
        </button>
      </div>

      {/* Type Filter */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => { setTypeFilter(''); setLoading(true); }}
          className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
            !typeFilter ? 'bg-primary text-primary-foreground' : 'bg-muted hover:bg-muted/80'
          }`}
        >
          All
        </button>
        {['text', 'number', 'select', 'multi_select', 'boolean', 'date', 'range'].map(type => (
          <button
            key={type}
            onClick={() => { setTypeFilter(type); setLoading(true); }}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors capitalize ${
              typeFilter === type ? 'bg-primary text-primary-foreground' : 'bg-muted hover:bg-muted/80'
            }`}
          >
            {type.replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* Attributes List */}
      <div className="space-y-3">
        {loading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
          </div>
        ) : attributes.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground bg-card rounded-md border">
            <Settings2 size={48} className="mx-auto mb-4 opacity-50" />
            <p>No attributes found</p>
          </div>
        ) : (
          attributes.map(attr => (
            <div 
              key={attr.id} 
              className="bg-card rounded-md border overflow-hidden"
              data-testid={`attribute-card-${attr.key}`}
            >
              <div 
                className="p-4 flex items-center justify-between cursor-pointer hover:bg-muted/30"
                onClick={() => setExpandedAttr(expandedAttr === attr.id ? null : attr.id)}
              >
                <div className="flex items-center gap-3">
                  <span className={`px-2 py-0.5 rounded text-xs font-semibold capitalize ${typeColors[attr.attribute_type] || 'bg-muted'}`}>
                    {attr.attribute_type.replace('_', ' ')}
                  </span>
                  <div>
                    <span className="font-medium">{getTranslated(attr.name)}</span>
                    <code className="text-xs px-1.5 py-0.5 rounded bg-muted font-mono ml-2">{attr.key}</code>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {attr.is_filterable && (
                    <span className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Filter size={12} /> Filterable
                    </span>
                  )}
                  {attr.is_sortable && (
                    <span className="flex items-center gap-1 text-xs text-muted-foreground">
                      <SortAsc size={12} /> Sortable
                    </span>
                  )}
                  {attr.unit && (
                    <span className="text-xs px-1.5 py-0.5 rounded bg-muted">{attr.unit}</span>
                  )}
                  <ChevronDown size={16} className={`transition-transform ${expandedAttr === attr.id ? 'rotate-180' : ''}`} />
                </div>
              </div>
              
              {expandedAttr === attr.id && (
                <div className="px-4 pb-4 pt-2 border-t bg-muted/20">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-4">
                    <div>
                      <p className="text-muted-foreground">Required</p>
                      <p className="font-medium">{attr.is_required ? 'Yes' : 'No'}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Filterable</p>
                      <p className="font-medium">{attr.is_filterable ? 'Yes' : 'No'}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Sortable</p>
                      <p className="font-medium">{attr.is_sortable ? 'Yes' : 'No'}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Unit</p>
                      <p className="font-medium">{attr.unit || 'None'}</p>
                    </div>
                  </div>
                  
                  {attr.options && attr.options.length > 0 && (
                    <div className="mb-4">
                      <p className="text-sm font-medium mb-2">Options ({attr.options.length})</p>
                      <div className="flex flex-wrap gap-2">
                        {attr.options.map(opt => (
                          <span key={opt.id} className="px-2 py-1 rounded bg-muted text-sm">
                            {getTranslated(opt.label)} <span className="text-muted-foreground">({opt.value})</span>
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleToggleActive(attr.id, true)}
                      className="flex items-center gap-1 px-3 py-1.5 text-sm rounded-md border text-amber-600 hover:bg-amber-50 dark:hover:bg-amber-900/20"
                    >
                      <ToggleLeft size={14} />
                      Deactivate
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {showCreateModal && (
        <CreateAttributeModal onClose={() => setShowCreateModal(false)} onCreated={fetchAttributes} />
      )}
    </div>
  );
}

function CreateAttributeModal({ onClose, onCreated }) {
  const [formData, setFormData] = useState({
    key: '',
    name: { tr: '', de: '', fr: '' },
    attribute_type: 'text',
    is_required: false,
    is_filterable: false,
    is_sortable: false,
    unit: '',
    options: []
  });
  const [newOption, setNewOption] = useState({ value: '', label: { tr: '', de: '', fr: '' } });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await axios.post(`${API}/attributes`, {
        ...formData,
        options: formData.options.map((opt, idx) => ({ ...opt, sort_order: idx }))
      });
      onCreated();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create attribute');
    } finally {
      setLoading(false);
    }
  };

  const addOption = () => {
    if (!newOption.value || !newOption.label.tr) return;
    setFormData(prev => ({
      ...prev,
      options: [...prev.options, { ...newOption }]
    }));
    setNewOption({ value: '', label: { tr: '', de: '', fr: '' } });
  };

  const removeOption = (index) => {
    setFormData(prev => ({
      ...prev,
      options: prev.options.filter((_, i) => i !== index)
    }));
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-card rounded-lg border shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold">Create Attribute</h2>
          <button onClick={onClose} className="p-1 rounded hover:bg-muted">×</button>
        </div>
        
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {error && <div className="p-3 rounded bg-destructive/10 text-destructive text-sm">{error}</div>}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Key</label>
              <input
                type="text"
                value={formData.key}
                onChange={(e) => setFormData({ ...formData, key: e.target.value.toLowerCase().replace(/[^a-z_]/g, '') })}
                placeholder="room_count"
                className="w-full h-9 px-3 rounded-md border text-sm"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Type</label>
              <select
                value={formData.attribute_type}
                onChange={(e) => setFormData({ ...formData, attribute_type: e.target.value })}
                className="w-full h-9 px-3 rounded-md border text-sm"
              >
                <option value="text">Text</option>
                <option value="number">Number</option>
                <option value="select">Select</option>
                <option value="multi_select">Multi Select</option>
                <option value="boolean">Boolean</option>
                <option value="date">Date</option>
                <option value="range">Range</option>
                <option value="textarea">Textarea</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Name (TR)</label>
            <input
              type="text"
              value={formData.name.tr}
              onChange={(e) => setFormData({ ...formData, name: { ...formData.name, tr: e.target.value } })}
              className="w-full h-9 px-3 rounded-md border text-sm"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Name (DE)</label>
              <input
                type="text"
                value={formData.name.de}
                onChange={(e) => setFormData({ ...formData, name: { ...formData.name, de: e.target.value } })}
                className="w-full h-9 px-3 rounded-md border text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Name (FR)</label>
              <input
                type="text"
                value={formData.name.fr}
                onChange={(e) => setFormData({ ...formData, name: { ...formData.name, fr: e.target.value } })}
                className="w-full h-9 px-3 rounded-md border text-sm"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Unit (optional)</label>
            <input
              type="text"
              value={formData.unit}
              onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
              placeholder="m², €, km"
              className="w-full h-9 px-3 rounded-md border text-sm"
            />
          </div>

          <div className="flex flex-wrap gap-4">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={formData.is_required}
                onChange={(e) => setFormData({ ...formData, is_required: e.target.checked })}
                className="rounded"
              />
              Required
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={formData.is_filterable}
                onChange={(e) => setFormData({ ...formData, is_filterable: e.target.checked })}
                className="rounded"
              />
              Filterable
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={formData.is_sortable}
                onChange={(e) => setFormData({ ...formData, is_sortable: e.target.checked })}
                className="rounded"
              />
              Sortable
            </label>
          </div>

          {(formData.attribute_type === 'select' || formData.attribute_type === 'multi_select') && (
            <div>
              <label className="block text-sm font-medium mb-2">Options</label>
              <div className="space-y-2 mb-2">
                {formData.options.map((opt, idx) => (
                  <div key={idx} className="flex items-center gap-2 p-2 rounded bg-muted">
                    <span className="flex-1 text-sm">{opt.label.tr} ({opt.value})</span>
                    <button type="button" onClick={() => removeOption(idx)} className="text-destructive">×</button>
                  </div>
                ))}
              </div>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newOption.value}
                  onChange={(e) => setNewOption({ ...newOption, value: e.target.value })}
                  placeholder="Value"
                  className="flex-1 h-8 px-2 rounded-md border text-sm"
                />
                <input
                  type="text"
                  value={newOption.label.tr}
                  onChange={(e) => setNewOption({ ...newOption, label: { ...newOption.label, tr: e.target.value } })}
                  placeholder="Label (TR)"
                  className="flex-1 h-8 px-2 rounded-md border text-sm"
                />
                <button type="button" onClick={addOption} className="px-3 h-8 rounded-md bg-muted text-sm">Add</button>
              </div>
            </div>
          )}

          <div className="flex justify-end gap-2 pt-4 border-t">
            <button type="button" onClick={onClose} className="px-4 py-2 rounded-md border text-sm font-medium hover:bg-muted">Cancel</button>
            <button type="submit" disabled={loading} className="px-4 py-2 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 disabled:opacity-50">
              {loading ? 'Creating...' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
