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
const API = `${BACKEND_URL}/api/v1/admin/vehicle-master`;

export default function AdminVehicleMDM() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [status, setStatus] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [validation, setValidation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activating, setActivating] = useState(false);
  const [rollingBack, setRollingBack] = useState(false);
  const [error, setError] = useState('');

  const canManage = ['super_admin', 'country_admin'].includes(user?.role);

  const fetchStatus = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/status`);
      setStatus(response.data);
    } catch (e) {
      console.error('Failed to fetch status', e);
      setError(e.response?.data?.detail || 'Durum bilgisi alınamadı');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const handleValidate = async () => {
    if (!selectedFile) return;
    setError('');
    setValidation(null);

    const form = new FormData();
    form.append('file', selectedFile);

    try {
      const response = await axios.post(`${API}/validate`, form, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setValidation(response.data);
      if (response.data.ok) {
        toast.success('Validasyon başarılı');
      } else {
        toast.error('Validasyon hatalı');
      }
    } catch (e) {
      console.error(e);
      setError(e.response?.data?.detail || 'Validasyon başarısız');
    }
  };

  const handleActivate = async () => {
    if (!validation?.staging_id) return;
    setActivating(true);
    setError('');
    try {
      await axios.post(`${API}/activate`, { staging_id: validation.staging_id });
      toast.success('Aktif versiyon güncellendi');
      setValidation(null);
      setSelectedFile(null);
      fetchStatus();
    } catch (e) {
      console.error(e);
      setError(e.response?.data?.detail || 'Aktivasyon başarısız');
    } finally {
      setActivating(false);
    }
  };

  const handleRollback = async () => {
    setRollingBack(true);
    setError('');
    try {
      await axios.post(`${API}/rollback`, {});
      toast.success('Rollback tamamlandı');
      fetchStatus();
    } catch (e) {
      console.error(e);
      setError(e.response?.data?.detail || 'Rollback başarısız');
    } finally {
      setRollingBack(false);
    }
  };

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

  const downloadValidationReport = () => {
    if (!validation) return;
    const blob = new Blob([JSON.stringify(validation, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'validation_report.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  const current = status?.current;
  const recent = status?.recent_jobs || [];

  return (
    <div className="space-y-6" data-testid="admin-vehicle-master-import">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <Car className="w-6 h-6" />
            Vehicle Master Data Import
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            File-based JSON master data (ZIP veya Bundle). DB kullanılmaz.
          </p>
        </div>
      </div>

      {!canManage && (
        <div className="p-3 rounded bg-amber-50 text-amber-900 border border-amber-200 text-sm">
          Bu ekran için yetkiniz yok.
        </div>
      )}

      {error && (
        <div className="p-3 rounded bg-destructive/10 text-destructive text-sm border">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 space-y-4">
          <div className="border rounded-lg bg-card p-4 space-y-3">
            <h2 className="font-semibold">Upload</h2>
            <input
              type="file"
              accept=".zip,.json,application/zip,application/json"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              disabled={!canManage}
              data-testid="vehicle-master-upload"
            />
            <div className="flex items-center gap-2">
              <button
                onClick={handleValidate}
                disabled={!canManage || !selectedFile}
                className="inline-flex items-center gap-2 h-9 px-4 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
                data-testid="vehicle-master-validate"
              >
                Validate
              </button>
              {validation && (
                <button
                  onClick={downloadValidationReport}
                  className="inline-flex items-center gap-2 h-9 px-4 rounded-md border text-sm font-medium hover:bg-muted"
                  data-testid="vehicle-master-download-report"
                >
                  Report indir
                </button>
              )}
              <button
                onClick={handleActivate}
                disabled={!canManage || !validation?.ok || activating}
                className="inline-flex items-center gap-2 h-9 px-4 rounded-md bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-700 disabled:opacity-50"
                data-testid="vehicle-master-activate"
              >
                {activating ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                Activate
              </button>
            </div>
          </div>

          {validation && (
            <div className="border rounded-lg bg-card p-4 space-y-3" data-testid="vehicle-master-preview">
              <h2 className="font-semibold">Validation Preview</h2>
              <div className="text-sm">
                <div>OK: <strong>{String(validation.ok)}</strong></div>
                <div>Version: <strong>{validation.version || '-'}</strong></div>
                <div>Staging: <code className="px-2 py-0.5 rounded bg-muted text-xs">{validation.staging_id}</code></div>
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="p-3 rounded bg-muted/50">
                  Make: <strong>{validation.summary?.make_count ?? '-'}</strong>
                </div>
                <div className="p-3 rounded bg-muted/50">
                  Model: <strong>{validation.summary?.model_count ?? '-'}</strong>
                </div>
                <div className="p-3 rounded bg-muted/50">
                  Inactive: <strong>{validation.summary?.inactive_count ?? '-'}</strong>
                </div>
                <div className="p-3 rounded bg-muted/50">
                  Aliases: <strong>{validation.summary?.alias_count ?? '-'}</strong>
                </div>
              </div>

              {!validation.ok && Array.isArray(validation.errors) && validation.errors.length > 0 && (
                <div className="space-y-2">
                  <div className="font-medium text-sm">Errors (sample)</div>
                  <ul className="text-sm list-disc pl-5 text-destructive">
                    {validation.errors.slice(0, 10).map((er, idx) => (
                      <li key={idx}><code>{er.code}</code> — {er.message}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="space-y-4">
          <div className="border rounded-lg bg-card p-4 space-y-2" data-testid="vehicle-master-current">
            <h2 className="font-semibold">Active Version</h2>
            {loading ? (
              <div className="text-sm text-muted-foreground">Loading...</div>
            ) : current ? (
              <div className="text-sm space-y-1">
                <div>Version: <strong>{current.active_version}</strong></div>
                <div>Activated at: <span className="text-muted-foreground">{current.activated_at}</span></div>
                <div>By: <span className="text-muted-foreground">{current.activated_by}</span></div>
                <div>Source: <span className="text-muted-foreground">{current.source}</span></div>
                <div>Checksum: <code className="text-xs">{current.checksum}</code></div>
              </div>
            ) : (
              <div className="text-sm text-muted-foreground">No active version</div>
            )}
            <button
              onClick={handleRollback}
              disabled={!canManage || rollingBack}
              className="inline-flex items-center gap-2 h-9 px-4 rounded-md border text-sm font-medium hover:bg-muted disabled:opacity-50"
              data-testid="vehicle-master-rollback"
            >
              {rollingBack ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
              Rollback
            </button>
          </div>

          <div className="border rounded-lg bg-card p-4 space-y-2" data-testid="vehicle-master-recent">
            <h2 className="font-semibold">Recent Jobs (Last 5)</h2>
            {recent.length === 0 ? (
              <div className="text-sm text-muted-foreground">No jobs yet</div>
            ) : (
              <div className="space-y-2">
                {recent.map((j, idx) => (
                  <div key={idx} className="text-xs p-2 rounded bg-muted/50">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{j.event}</span>
                      <span className="text-muted-foreground">{j.ts}</span>
                    </div>
                    <div className="text-muted-foreground">v={j.version} status={j.status}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );

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
