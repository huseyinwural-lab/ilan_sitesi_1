import { useState, useEffect } from 'react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { 
  Flag, Search, ToggleLeft, ToggleRight, Plus, 
  ChevronDown, ChevronUp, Pencil, Trash2, X, Check
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function FeatureFlags() {
  const [flags, setFlags] = useState([]);
  const [loading, setLoading] = useState(true);
  const [scopeFilter, setScopeFilter] = useState('');
  const [expandedFlag, setExpandedFlag] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const { t, getTranslated, language } = useLanguage();

  useEffect(() => {
    fetchFlags();
  }, [scopeFilter]);

  const fetchFlags = async () => {
    try {
      const params = new URLSearchParams();
      if (scopeFilter) params.append('scope', scopeFilter);
      
      const response = await axios.get(`${API}/feature-flags?${params}`);
      setFlags(response.data);
    } catch (error) {
      console.error('Failed to fetch flags:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async (flagId) => {
    try {
      await axios.post(`${API}/feature-flags/${flagId}/toggle`);
      fetchFlags();
    } catch (error) {
      console.error('Failed to toggle flag:', error);
    }
  };

  const handleDelete = async (flagId) => {
    if (!window.confirm('Are you sure you want to delete this feature flag?')) return;
    try {
      await axios.delete(`${API}/feature-flags/${flagId}`);
      fetchFlags();
    } catch (error) {
      console.error('Failed to delete flag:', error);
    }
  };

  const modules = flags.filter(f => f.scope === 'module');
  const features = flags.filter(f => f.scope === 'feature');

  const FlagCard = ({ flag }) => {
    const isExpanded = expandedFlag === flag.id;
    const flagName = getTranslated(flag.name);
    const flagDesc = getTranslated(flag.description);

    return (
      <div 
        className="bg-card rounded-md border overflow-hidden transition-all"
        data-testid={`flag-card-${flag.key}`}
      >
        <div 
          className="p-4 flex items-center justify-between cursor-pointer hover:bg-muted/30"
          onClick={() => setExpandedFlag(isExpanded ? null : flag.id)}
        >
          <div className="flex items-center gap-3">
            <button
              onClick={(e) => { e.stopPropagation(); handleToggle(flag.id); }}
              className={`transition-colors ${flag.is_enabled ? 'text-primary' : 'text-muted-foreground'}`}
              data-testid={`flag-toggle-${flag.key}`}
            >
              {flag.is_enabled ? <ToggleRight size={28} /> : <ToggleLeft size={28} />}
            </button>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-medium">{flagName}</span>
                <code className="text-xs px-1.5 py-0.5 rounded bg-muted font-mono">{flag.key}</code>
              </div>
              {flagDesc && <p className="text-sm text-muted-foreground mt-0.5">{flagDesc}</p>}
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex gap-1">
              {flag.enabled_countries?.length > 0 ? (
                flag.enabled_countries.map(c => (
                  <span key={c} className="text-xs px-1.5 py-0.5 rounded bg-muted">{c}</span>
                ))
              ) : (
                <span className="text-xs text-muted-foreground">No countries</span>
              )}
            </div>
            {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
          </div>
        </div>
        
        {isExpanded && (
          <div className="px-4 pb-4 pt-2 border-t bg-muted/20">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-muted-foreground">Scope</p>
                <p className="font-medium capitalize">{flag.scope}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Version</p>
                <p className="font-medium">v{flag.version}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Status</p>
                <p className={`font-medium ${flag.is_enabled ? 'text-emerald-600' : 'text-muted-foreground'}`}>
                  {flag.is_enabled ? 'Enabled' : 'Disabled'}
                </p>
              </div>
              <div>
                <p className="text-muted-foreground">Dependencies</p>
                <p className="font-medium">
                  {flag.depends_on?.length > 0 ? flag.depends_on.join(', ') : 'None'}
                </p>
              </div>
            </div>
            <div className="flex gap-2 mt-4">
              <button 
                onClick={() => handleDelete(flag.id)}
                className="flex items-center gap-1 px-3 py-1.5 text-sm rounded-md border text-destructive hover:bg-destructive/10 transition-colors"
              >
                <Trash2 size={14} />
                Delete
              </button>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-6" data-testid="feature-flags-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{t('feature_flags')}</h1>
          <p className="text-muted-foreground text-sm mt-1">
            {flags.length} flags ({modules.length} modules, {features.length} features)
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center gap-2 h-9 px-4 rounded-md bg-primary text-primary-foreground font-medium text-sm hover:bg-primary/90 transition-colors"
          data-testid="create-flag-btn"
        >
          <Plus size={16} />
          Add Flag
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        <button
          onClick={() => setScopeFilter('')}
          className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
            !scopeFilter ? 'bg-primary text-primary-foreground' : 'bg-muted hover:bg-muted/80'
          }`}
        >
          All
        </button>
        <button
          onClick={() => setScopeFilter('module')}
          className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
            scopeFilter === 'module' ? 'bg-primary text-primary-foreground' : 'bg-muted hover:bg-muted/80'
          }`}
        >
          Modules
        </button>
        <button
          onClick={() => setScopeFilter('feature')}
          className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
            scopeFilter === 'feature' ? 'bg-primary text-primary-foreground' : 'bg-muted hover:bg-muted/80'
          }`}
        >
          Features
        </button>
      </div>

      {/* Loading */}
      {loading ? (
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
        </div>
      ) : (
        <>
          {/* Modules Section */}
          {(!scopeFilter || scopeFilter === 'module') && modules.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
                <span className="badge-module">Modules</span>
              </h2>
              <div className="space-y-2">
                {modules.map(flag => <FlagCard key={flag.id} flag={flag} />)}
              </div>
            </div>
          )}

          {/* Features Section */}
          {(!scopeFilter || scopeFilter === 'feature') && features.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
                <span className="badge-feature">Features</span>
              </h2>
              <div className="space-y-2">
                {features.map(flag => <FlagCard key={flag.id} flag={flag} />)}
              </div>
            </div>
          )}

          {flags.length === 0 && (
            <div className="text-center py-12 text-muted-foreground">
              No feature flags found
            </div>
          )}
        </>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <CreateFlagModal onClose={() => setShowCreateModal(false)} onCreated={fetchFlags} />
      )}
    </div>
  );
}

function CreateFlagModal({ onClose, onCreated }) {
  const [formData, setFormData] = useState({
    key: '',
    name: { tr: '', de: '', fr: '' },
    description: { tr: '', de: '', fr: '' },
    scope: 'feature',
    enabled_countries: [],
    is_enabled: false
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await axios.post(`${API}/feature-flags`, formData);
      onCreated();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create flag');
    } finally {
      setLoading(false);
    }
  };

  const toggleCountry = (code) => {
    setFormData(prev => ({
      ...prev,
      enabled_countries: prev.enabled_countries.includes(code)
        ? prev.enabled_countries.filter(c => c !== code)
        : [...prev.enabled_countries, code]
    }));
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-card rounded-lg border shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold">Create Feature Flag</h2>
          <button onClick={onClose} className="p-1 rounded hover:bg-muted">
            <X size={20} />
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {error && (
            <div className="p-3 rounded bg-destructive/10 text-destructive text-sm">{error}</div>
          )}

          <div>
            <label className="block text-sm font-medium mb-1">Key</label>
            <input
              type="text"
              value={formData.key}
              onChange={(e) => setFormData({ ...formData, key: e.target.value.toLowerCase().replace(/[^a-z_]/g, '') })}
              placeholder="feature_key"
              className="w-full h-9 px-3 rounded-md border text-sm"
              required
            />
            <p className="text-xs text-muted-foreground mt-1">Lowercase letters and underscores only</p>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Scope</label>
            <select
              value={formData.scope}
              onChange={(e) => setFormData({ ...formData, scope: e.target.value })}
              className="w-full h-9 px-3 rounded-md border text-sm"
            >
              <option value="module">Module</option>
              <option value="feature">Feature</option>
            </select>
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

          <div>
            <label className="block text-sm font-medium mb-2">Enabled Countries</label>
            <div className="flex flex-wrap gap-2">
              {['DE', 'CH', 'FR', 'AT'].map(code => (
                <button
                  key={code}
                  type="button"
                  onClick={() => toggleCountry(code)}
                  className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    formData.enabled_countries.includes(code)
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted hover:bg-muted/80'
                  }`}
                >
                  {code}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="is_enabled"
              checked={formData.is_enabled}
              onChange={(e) => setFormData({ ...formData, is_enabled: e.target.checked })}
              className="rounded"
            />
            <label htmlFor="is_enabled" className="text-sm">Enable immediately</label>
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-md border text-sm font-medium hover:bg-muted"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
            >
              {loading ? 'Creating...' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
