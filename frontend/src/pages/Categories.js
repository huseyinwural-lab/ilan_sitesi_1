import { useState, useEffect } from 'react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { 
  FolderTree, Plus, ChevronRight, ChevronDown, 
  Pencil, Trash2, Eye, EyeOff, GripVertical
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Categories() {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [moduleFilter, setModuleFilter] = useState('real_estate');
  const [expandedIds, setExpandedIds] = useState(new Set());
  const [showCreateModal, setShowCreateModal] = useState(false);
  const { t, getTranslated, language } = useLanguage();

  useEffect(() => {
    fetchCategories();
  }, [moduleFilter]);

  const fetchCategories = async () => {
    try {
      const response = await axios.get(`${API}/categories?module=${moduleFilter}`);
      setCategories(response.data);
    } catch (error) {
      console.error('Failed to fetch categories:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleExpand = (id) => {
    setExpandedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleToggleEnabled = async (categoryId, currentState) => {
    try {
      await axios.patch(`${API}/categories/${categoryId}`, { is_enabled: !currentState });
      fetchCategories();
    } catch (error) {
      console.error('Failed to toggle category:', error);
    }
  };

  const handleDelete = async (categoryId) => {
    if (!window.confirm('Are you sure you want to delete this category?')) return;
    try {
      await axios.delete(`${API}/categories/${categoryId}`);
      fetchCategories();
    } catch (error) {
      console.error('Failed to delete category:', error);
    }
  };

  const getTranslatedName = (translations) => {
    if (!translations || translations.length === 0) return 'Unnamed';
    const trans = translations.find(t => t.language === language) || translations[0];
    return trans?.name || 'Unnamed';
  };

  const CategoryItem = ({ category, depth = 0 }) => {
    const isExpanded = expandedIds.has(category.id);
    const hasChildren = categories.some(c => c.parent_id === category.id);
    const children = categories.filter(c => c.parent_id === category.id);

    return (
      <div className="border-b last:border-b-0">
        <div 
          className={`flex items-center gap-2 px-4 py-3 hover:bg-muted/30 transition-colors ${!category.is_enabled ? 'opacity-50' : ''}`}
          style={{ paddingLeft: `${16 + depth * 24}px` }}
          data-testid={`category-item-${category.id}`}
        >
          <button
            onClick={() => hasChildren && toggleExpand(category.id)}
            className={`w-6 h-6 flex items-center justify-center rounded hover:bg-muted ${!hasChildren ? 'invisible' : ''}`}
          >
            {hasChildren && (isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />)}
          </button>
          
          <GripVertical size={16} className="text-muted-foreground cursor-grab" />
          
          {category.icon && (
            <span className="text-primary">{category.icon}</span>
          )}
          
          <div className="flex-1 min-w-0">
            <span className="font-medium">{getTranslatedName(category.translations)}</span>
            <span className="text-xs text-muted-foreground ml-2">
              ({category.listing_count || 0} listings)
            </span>
          </div>
          
          <div className="flex items-center gap-1">
            {category.allowed_countries?.map(c => (
              <span key={c} className="text-xs px-1.5 py-0.5 rounded bg-muted">{c}</span>
            ))}
          </div>
          
          <div className="flex items-center gap-1">
            <button
              onClick={() => handleToggleEnabled(category.id, category.is_enabled)}
              className={`p-1.5 rounded hover:bg-muted ${category.is_enabled ? 'text-emerald-600' : 'text-muted-foreground'}`}
              title={category.is_enabled ? 'Disable' : 'Enable'}
            >
              {category.is_enabled ? <Eye size={16} /> : <EyeOff size={16} />}
            </button>
            <button
              onClick={() => handleDelete(category.id)}
              className="p-1.5 rounded hover:bg-muted text-destructive"
              title="Delete"
            >
              <Trash2 size={16} />
            </button>
          </div>
        </div>
        
        {isExpanded && children.map(child => (
          <CategoryItem key={child.id} category={child} depth={depth + 1} />
        ))}
      </div>
    );
  };

  const rootCategories = categories.filter(c => !c.parent_id);

  return (
    <div className="space-y-6" data-testid="categories-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Categories</h1>
          <p className="text-muted-foreground text-sm mt-1">
            {categories.length} categories in {moduleFilter.replace('_', ' ')}
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center gap-2 h-9 px-4 rounded-md bg-primary text-primary-foreground font-medium text-sm hover:bg-primary/90 transition-colors"
          data-testid="create-category-btn"
        >
          <Plus size={16} />
          Add Category
        </button>
      </div>

      {/* Module Filter */}
      <div className="flex gap-2">
        {['real_estate', 'vehicle', 'machinery', 'services', 'jobs'].map(module => (
          <button
            key={module}
            onClick={() => { setModuleFilter(module); setLoading(true); }}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors capitalize ${
              moduleFilter === module ? 'bg-primary text-primary-foreground' : 'bg-muted hover:bg-muted/80'
            }`}
          >
            {module.replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* Category Tree */}
      <div className="rounded-md border bg-card">
        {loading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
          </div>
        ) : rootCategories.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            <FolderTree size={48} className="mx-auto mb-4 opacity-50" />
            <p>No categories found for this module</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="mt-4 text-primary hover:underline"
            >
              Create your first category
            </button>
          </div>
        ) : (
          rootCategories.map(category => (
            <CategoryItem key={category.id} category={category} />
          ))
        )}
      </div>

      {showCreateModal && (
        <CreateCategoryModal 
          module={moduleFilter}
          categories={categories}
          onClose={() => setShowCreateModal(false)} 
          onCreated={fetchCategories} 
        />
      )}
    </div>
  );
}

function CreateCategoryModal({ module, categories, onClose, onCreated }) {
  const [formData, setFormData] = useState({
    parent_id: '',
    module: module,
    slug: { tr: '', de: '', fr: '' },
    icon: '',
    allowed_countries: ['DE', 'CH', 'FR', 'AT'],
    is_enabled: true,
    translations: [
      { language: 'tr', name: '', description: '' },
      { language: 'de', name: '', description: '' },
      { language: 'fr', name: '', description: '' },
    ]
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await axios.post(`${API}/categories`, {
        ...formData,
        parent_id: formData.parent_id || null
      });
      onCreated();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create category');
    } finally {
      setLoading(false);
    }
  };

  const updateTranslation = (lang, field, value) => {
    setFormData(prev => ({
      ...prev,
      translations: prev.translations.map(t => 
        t.language === lang ? { ...t, [field]: value } : t
      )
    }));
  };

  const toggleCountry = (code) => {
    setFormData(prev => ({
      ...prev,
      allowed_countries: prev.allowed_countries.includes(code)
        ? prev.allowed_countries.filter(c => c !== code)
        : [...prev.allowed_countries, code]
    }));
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-card rounded-lg border shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold">Create Category</h2>
          <button onClick={onClose} className="p-1 rounded hover:bg-muted">×</button>
        </div>
        
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {error && <div className="p-3 rounded bg-destructive/10 text-destructive text-sm">{error}</div>}

          <div>
            <label className="block text-sm font-medium mb-1">Parent Category</label>
            <select
              value={formData.parent_id}
              onChange={(e) => setFormData({ ...formData, parent_id: e.target.value })}
              className="w-full h-9 px-3 rounded-md border text-sm"
            >
              <option value="">Root (No Parent)</option>
              {categories.map(c => (
                <option key={c.id} value={c.id}>
                  {c.translations?.[0]?.name || c.slug?.tr || c.id}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Name (TR)</label>
            <input
              type="text"
              value={formData.translations.find(t => t.language === 'tr')?.name || ''}
              onChange={(e) => {
                updateTranslation('tr', 'name', e.target.value);
                setFormData(prev => ({ ...prev, slug: { ...prev.slug, tr: e.target.value.toLowerCase().replace(/\s+/g, '-') }}));
              }}
              className="w-full h-9 px-3 rounded-md border text-sm"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Name (DE)</label>
            <input
              type="text"
              value={formData.translations.find(t => t.language === 'de')?.name || ''}
              onChange={(e) => {
                updateTranslation('de', 'name', e.target.value);
                setFormData(prev => ({ ...prev, slug: { ...prev.slug, de: e.target.value.toLowerCase().replace(/\s+/g, '-') }}));
              }}
              className="w-full h-9 px-3 rounded-md border text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Name (FR)</label>
            <input
              type="text"
              value={formData.translations.find(t => t.language === 'fr')?.name || ''}
              onChange={(e) => {
                updateTranslation('fr', 'name', e.target.value);
                setFormData(prev => ({ ...prev, slug: { ...prev.slug, fr: e.target.value.toLowerCase().replace(/\s+/g, '-') }}));
              }}
              className="w-full h-9 px-3 rounded-md border text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Icon (optional)</label>
            <input
              type="text"
              value={formData.icon}
              onChange={(e) => setFormData({ ...formData, icon: e.target.value })}
              placeholder="building-2"
              className="w-full h-9 px-3 rounded-md border text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Allowed Countries</label>
            <div className="flex flex-wrap gap-2">
              {['DE', 'CH', 'FR', 'AT'].map(code => (
                <button
                  key={code}
                  type="button"
                  onClick={() => toggleCountry(code)}
                  className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    formData.allowed_countries.includes(code)
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted hover:bg-muted/80'
                  }`}
                >
                  {code}
                </button>
              ))}
            </div>
          </div>

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
