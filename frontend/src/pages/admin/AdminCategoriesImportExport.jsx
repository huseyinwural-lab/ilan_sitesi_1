import React, { useMemo, useState } from 'react';
import { useCountry } from '../../contexts/CountryContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const MAX_FILE_MB = 10;

const MODULE_OPTIONS = ['vehicle', 'real_estate', 'machinery', 'services', 'jobs'];

const TABS = [
  { id: 'export', label: 'Export' },
  { id: 'import', label: 'Import' },
  { id: 'preview', label: 'Dry-run Sonucu' },
];

export default function AdminCategoriesImportExport() {
  const { selectedCountry } = useCountry();
  const [activeTab, setActiveTab] = useState('export');
  const [file, setFile] = useState(null);
  const [dryRunResult, setDryRunResult] = useState(null);
  const [applyResult, setApplyResult] = useState(null);
  const [moduleFilter, setModuleFilter] = useState('vehicle');
  const [countryFilter, setCountryFilter] = useState(selectedCountry || 'DE');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const token = useMemo(() => localStorage.getItem('access_token'), []);

  const handleDownload = async () => {
    setError('');
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (moduleFilter) params.set('module', moduleFilter);
      if (countryFilter) params.set('country', countryFilter);
      const res = await fetch(`${API}/admin/categories/import-export/export/csv?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        throw new Error('Export başarısız');
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'categories-export.csv';
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err?.message || 'Export başarısız');
    } finally {
      setLoading(false);
    }
  };

  const handleSampleDownload = async () => {
    setError('');
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (moduleFilter) params.set('module', moduleFilter);
      if (countryFilter) params.set('country', countryFilter);
      const res = await fetch(`${API}/admin/categories/import-export/sample/csv?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        throw new Error('Örnek dosya indirilemedi');
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'categories-sample.csv';
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err?.message || 'Örnek dosya indirilemedi');
    } finally {
      setLoading(false);
    }
  };

  const validateFile = (selectedFile) => {
    if (!selectedFile) {
      setError('Dosya seçiniz.');
      return false;
    }
    if (selectedFile.size > MAX_FILE_MB * 1024 * 1024) {
      setError(`Dosya boyutu ${MAX_FILE_MB}MB limitini aşıyor.`);
      return false;
    }
    return true;
  };

  const runDryRun = async () => {
    setError('');
    if (!validateFile(file)) return;
    setLoading(true);
    setDryRunResult(null);
    setApplyResult(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch(`${API}/admin/categories/import-export/import/dry-run?format=csv`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data?.detail || 'Dry-run başarısız');
      }
      setDryRunResult(data);
      setActiveTab('preview');
    } catch (err) {
      setError(err?.message || 'Dry-run başarısız');
    } finally {
      setLoading(false);
    }
  };

  const runApply = async () => {
    setError('');
    if (!dryRunResult?.dry_run_hash) {
      setError('Önce dry-run çalıştırın.');
      return;
    }
    if (!validateFile(file)) return;
    setLoading(true);
    setApplyResult(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch(
        `${API}/admin/categories/import-export/import/commit?format=csv&dry_run_hash=${dryRunResult.dry_run_hash}`,
        {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
          body: formData,
        }
      );
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data?.detail || 'Import başarısız');
      }
      setApplyResult(data);
    } catch (err) {
      setError(err?.message || 'Import başarısız');
    } finally {
      setLoading(false);
    }
  };



  const previewCreates = dryRunResult?.creates || [];
  const previewUpdates = dryRunResult?.updates || [];
  const previewErrors = dryRunResult?.errors || [];

  return (
    <div className="p-6" data-testid="admin-categories-import-export-page">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900" data-testid="categories-import-export-title">Import / Export</h1>
          <p className="text-sm text-slate-700" data-testid="categories-import-export-subtitle">
            Kategori master verisini yalnızca CSV formatı ile içe/dışa aktar.
          </p>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 mb-4" data-testid="categories-import-export-tabs">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 rounded-full border text-sm ${activeTab === tab.id ? 'bg-slate-900 text-white' : 'bg-white'}`}
            data-testid={`categories-import-export-tab-${tab.id}`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700" data-testid="categories-import-export-error">
          {error}
        </div>
      )}

      {activeTab === 'export' && (
        <div className="space-y-4" data-testid="categories-import-export-export">
          <div className="rounded-lg border bg-white p-4">
            <h2 className="text-lg font-semibold mb-2" data-testid="categories-export-title">Kategori Export</h2>
            <p className="text-sm text-slate-600" data-testid="categories-export-desc">Modül ve ülke filtresiyle CSV dışa aktarım.</p>
            <div className="grid gap-4 md:grid-cols-2 mt-4" data-testid="categories-export-filters">
              <div>
                <label className="text-sm text-slate-600" htmlFor="export-module">Module</label>
                <select
                  id="export-module"
                  value={moduleFilter}
                  onChange={(event) => setModuleFilter(event.target.value)}
                  className="mt-1 h-10 w-full rounded-md border px-3 text-sm"
                  data-testid="categories-export-module"
                >
                  {MODULE_OPTIONS.map((item) => (
                    <option key={item} value={item}>{item}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-sm text-slate-600" htmlFor="export-country">Country</label>
                <input
                  id="export-country"
                  type="text"
                  value={countryFilter}
                  onChange={(event) => setCountryFilter(event.target.value.toUpperCase())}
                  className="mt-1 h-10 w-full rounded-md border px-3 text-sm"
                  placeholder="DE"
                  data-testid="categories-export-country"
                />
              </div>
            </div>
            <div className="flex flex-wrap gap-3 mt-4" data-testid="categories-export-actions">
              <button
                type="button"
                className="px-4 py-2 rounded-md bg-blue-600 text-white text-sm"
                onClick={handleDownload}
                disabled={loading}
                data-testid="categories-export-csv"
              >
                CSV Export
              </button>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'import' && (
        <div className="space-y-4" data-testid="categories-import-export-import">
          <div className="rounded-lg border bg-white p-4 space-y-4">
            <div>
              <label className="text-sm text-slate-600" htmlFor="import-file">Dosya (CSV)</label>
              <input
                id="import-file"
                type="file"
                accept=".csv"
                onChange={(event) => setFile(event.target.files?.[0] || null)}
                className="mt-1 block w-full text-sm"
                data-testid="categories-import-file"
              />
              <p className="text-xs text-slate-500 mt-1" data-testid="categories-import-limit">
                Maksimum dosya boyutu: {MAX_FILE_MB}MB
              </p>
            </div>
            <div className="grid gap-4 md:grid-cols-2" data-testid="categories-import-filters">
              <div>
                <label className="text-sm text-slate-600" htmlFor="import-module">Module</label>
                <select
                  id="import-module"
                  value={moduleFilter}
                  onChange={(event) => setModuleFilter(event.target.value)}
                  className="mt-1 h-10 w-full rounded-md border px-3 text-sm"
                  data-testid="categories-import-module"
                >
                  {MODULE_OPTIONS.map((item) => (
                    <option key={item} value={item}>{item}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-sm text-slate-600" htmlFor="import-country">Country</label>
                <input
                  id="import-country"
                  type="text"
                  value={countryFilter}
                  onChange={(event) => setCountryFilter(event.target.value.toUpperCase())}
                  className="mt-1 h-10 w-full rounded-md border px-3 text-sm"
                  placeholder="DE"
                  data-testid="categories-import-country"
                />
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3" data-testid="categories-import-sample-actions">
              <button
                type="button"
                className="px-4 py-2 rounded-md border text-sm"
                onClick={handleSampleDownload}
                disabled={loading}
                data-testid="categories-import-sample-csv"
              >
                Örnek CSV indir
              </button>
              <span className="text-xs text-slate-500" data-testid="categories-import-sample-note">
                schema_version: v1
              </span>
            </div>

            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                className="px-4 py-2 rounded-md bg-blue-600 text-white text-sm"
                onClick={runDryRun}
                disabled={loading}
                data-testid="categories-import-dryrun"
              >
                Dry-run Yap
              </button>
              <button
                type="button"
                className="px-4 py-2 rounded-md bg-slate-900 text-white text-sm"
                onClick={runApply}
                disabled={loading || !dryRunResult?.dry_run_hash}
                data-testid="categories-import-apply"
              >
                Uygula
              </button>
              {!dryRunResult?.dry_run_hash && (
                <p className="text-xs text-slate-500" data-testid="categories-import-apply-hint">
                  Uygulamak için önce başarılı bir dry-run çalıştırmalısınız.
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'preview' && (
        <div className="space-y-4" data-testid="categories-import-export-preview">
          <div className="rounded-lg border bg-white p-4">
            <h2 className="text-lg font-semibold" data-testid="categories-preview-title">Dry-run Sonucu</h2>
            {dryRunResult ? (
              <div className="mt-3 space-y-4" data-testid="categories-preview-summary">
                <div className="grid gap-3 md:grid-cols-4">
                  <div className="rounded-md border p-3" data-testid="categories-preview-create-count">Eklenecek: {dryRunResult.summary?.creates ?? 0}</div>
                  <div className="rounded-md border p-3" data-testid="categories-preview-update-count">Güncellenecek: {dryRunResult.summary?.updates ?? 0}</div>
                  <div className="rounded-md border p-3" data-testid="categories-preview-error-count">Hata: {dryRunResult.summary?.errors ?? 0}</div>
                  <div className="rounded-md border p-3" data-testid="categories-preview-total-count">Toplam: {dryRunResult.summary?.total ?? 0}</div>
                </div>

                <div className="grid gap-4 md:grid-cols-2" data-testid="categories-preview-lists">
                  <div className="border rounded-md p-3" data-testid="categories-preview-creates">
                    <h3 className="font-semibold text-sm mb-2">Eklenecek</h3>
                    {previewCreates.length === 0 ? (
                      <p className="text-xs text-slate-500" data-testid="categories-preview-creates-empty">Yok</p>
                    ) : (
                      <ul className="text-xs space-y-1" data-testid="categories-preview-creates-list">
                        {previewCreates.map((slug) => (
                          <li key={slug} data-testid={`categories-preview-create-${slug}`}>{slug}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                  <div className="border rounded-md p-3" data-testid="categories-preview-updates">
                    <h3 className="font-semibold text-sm mb-2">Güncellenecek</h3>
                    {previewUpdates.length === 0 ? (
                      <p className="text-xs text-slate-500" data-testid="categories-preview-updates-empty">Yok</p>
                    ) : (
                      <ul className="text-xs space-y-1" data-testid="categories-preview-updates-list">
                        {previewUpdates.map((slug) => (
                          <li key={slug} data-testid={`categories-preview-update-${slug}`}>{slug}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>

                <div className="border rounded-md p-3" data-testid="categories-preview-errors">
                  <h3 className="font-semibold text-sm mb-2">Hatalar</h3>
                  {previewErrors.length === 0 ? (
                    <p className="text-xs text-slate-500" data-testid="categories-preview-errors-empty">Yok</p>
                  ) : (
                    <ul className="text-xs space-y-1" data-testid="categories-preview-errors-list">
                      {previewErrors.map((err, idx) => (
                        <li key={`${err.row_number || idx}-${idx}`} data-testid={`categories-preview-error-${idx}`}>
                          Satır {err.row_number}: [{err.error_code}] {err.message}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            ) : (
              <p className="text-sm text-slate-500" data-testid="categories-preview-empty">Önce dry-run çalıştırın.</p>
            )}

            {applyResult && (
              <div className="mt-4 rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700" data-testid="categories-apply-result">
                Import uygulandı. Yeni: {applyResult.summary?.created ?? 0}, Güncellenen: {applyResult.summary?.updated ?? 0}
              </div>
            )}
          </div>
        </div>
      )}


    </div>
  );
}
