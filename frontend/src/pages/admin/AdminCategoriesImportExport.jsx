import React, { useMemo, useState } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const MAX_FILE_MB = 10;
const UPDATE_PAGE_SIZE = 6;

const TABS = [
  { id: 'export', label: 'Export' },
  { id: 'import', label: 'Import' },
  { id: 'preview', label: 'Dry-run Preview' },
  { id: 'publish', label: 'Publish' },
];

export default function AdminCategoriesImportExport() {
  const [activeTab, setActiveTab] = useState('export');
  const [format, setFormat] = useState('json');
  const [file, setFile] = useState(null);
  const [dryRunResult, setDryRunResult] = useState(null);
  const [commitResult, setCommitResult] = useState(null);
  const [publishResult, setPublishResult] = useState(null);
  const [showOnlyChanged, setShowOnlyChanged] = useState(true);
  const [expandedSlug, setExpandedSlug] = useState(null);
  const [updatePage, setUpdatePage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const token = useMemo(() => localStorage.getItem('access_token'), []);

  const handleDownload = async (type) => {
    setError('');
    setLoading(true);
    try {
      const res = await fetch(`${API}/admin/categories/import-export/export/${type}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        throw new Error('Export başarısız');
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = type === 'json' ? 'categories-export.json' : 'categories-export.csv';
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
    setCommitResult(null);
    setPublishResult(null);
    setUpdatePage(1);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch(`${API}/admin/categories/import-export/import/dry-run?format=${format}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      if (!res.ok) {
        const detail = await res.json();
        throw new Error(detail?.detail || 'Dry-run başarısız');
      }
      const data = await res.json();
      setDryRunResult(data);
      setShowOnlyChanged(true);
      setExpandedSlug(null);
      setActiveTab('preview');
    } catch (err) {
      setError(err?.message || 'Dry-run başarısız');
    } finally {
      setLoading(false);
    }
  };

  const runCommit = async () => {
    setError('');
    if (!dryRunResult?.dry_run_hash) {
      setError('Commit için önce dry-run çalıştırılmalı.');
      return;
    }
    if (!validateFile(file)) return;
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch(
        `${API}/admin/categories/import-export/import/commit?format=${format}&dry_run_hash=${dryRunResult.dry_run_hash}`,
        {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
          body: formData,
        }
      );
      if (!res.ok) {
        const detail = await res.json();
        throw new Error(detail?.detail || 'Commit başarısız');
      }
      const data = await res.json();
      setCommitResult(data);
      setActiveTab('publish');
    } catch (err) {
      setError(err?.message || 'Commit başarısız');
    } finally {
      setLoading(false);
    }
  };

  const runPublish = async () => {
    if (!commitResult?.batch_id) {
      setError('Publish için batch bulunamadı.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API}/admin/categories/import-export/publish`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ batch_id: commitResult.batch_id }),
      });
      if (!res.ok) {
        const detail = await res.json();
        throw new Error(detail?.detail || 'Publish başarısız');
      }
      const data = await res.json();
      setPublishResult(data);
    } catch (err) {
      setError(err?.message || 'Publish başarısız');
    } finally {
      setLoading(false);
    }
  };

  const downloadPdfReport = async () => {
    setError('');
    if (!dryRunResult?.dry_run_hash) {
      setError('PDF için önce dry-run çalıştırılmalı.');
      return;
    }
    if (!validateFile(file)) return;
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch(
        `${API}/admin/categories/import-export/import/dry-run/pdf?format=${format}&dry_run_hash=${dryRunResult.dry_run_hash}`,
        {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
          body: formData,
        }
      );
      if (!res.ok) {
        const detail = await res.json();
        throw new Error(detail?.detail || 'PDF raporu alınamadı');
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'dry-run-report.pdf';
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err?.message || 'PDF raporu alınamadı');
    } finally {
      setLoading(false);
    }
  };

  const updates = dryRunResult?.updates || [];
  const totalUpdatePages = Math.max(1, Math.ceil(updates.length / UPDATE_PAGE_SIZE));
  const safeUpdatePage = Math.min(updatePage, totalUpdatePages);
  const pagedUpdates = updates.slice(
    (safeUpdatePage - 1) * UPDATE_PAGE_SIZE,
    safeUpdatePage * UPDATE_PAGE_SIZE
  );

  return (
    <div className="p-6" data-testid="admin-categories-import-export-page">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900" data-testid="categories-import-export-title">Import / Export</h1>
          <p className="text-sm text-slate-700" data-testid="categories-import-export-subtitle">
            Kategori master verisini JSON/CSV ile yönet.
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
            <h2 className="text-lg font-semibold mb-2" data-testid="categories-export-title">Tam Paket Export</h2>
            <p className="text-sm text-slate-600" data-testid="categories-export-desc">Tüm kategoriler + translations + schema.</p>
            <div className="flex flex-wrap gap-3 mt-4" data-testid="categories-export-actions">
              <button
                type="button"
                className="px-4 py-2 rounded-md bg-blue-600 text-white text-sm"
                onClick={() => handleDownload('json')}
                disabled={loading}
                data-testid="categories-export-json"
              >
                JSON Export
              </button>
              <button
                type="button"
                className="px-4 py-2 rounded-md bg-slate-900 text-white text-sm"
                onClick={() => handleDownload('csv')}
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
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="text-sm text-slate-600" htmlFor="import-format">Format</label>
                <select
                  id="import-format"
                  value={format}
                  onChange={(event) => setFormat(event.target.value)}
                  className="mt-1 h-10 w-full rounded-md border px-3 text-sm"
                  data-testid="categories-import-format"
                >
                  <option value="json">JSON</option>
                  <option value="csv">CSV</option>
                </select>
              </div>
              <div>
                <label className="text-sm text-slate-600" htmlFor="import-file">Dosya</label>
                <input
                  id="import-file"
                  type="file"
                  accept={format === 'json' ? '.json' : '.csv'}
                  onChange={(event) => setFile(event.target.files?.[0] || null)}
                  className="mt-1 block w-full text-sm"
                  data-testid="categories-import-file"
                />
                <p className="text-xs text-slate-500 mt-1" data-testid="categories-import-limit">
                  Maksimum dosya boyutu: {MAX_FILE_MB}MB
                </p>
              </div>
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
                onClick={runCommit}
                disabled={loading || !dryRunResult?.dry_run_hash}
                data-testid="categories-import-commit"
              >
                Commit Et
              </button>
              {!dryRunResult?.dry_run_hash && (
                <p className="text-xs text-slate-500" data-testid="categories-import-commit-hint">
                  Commit için önce başarılı bir dry-run çalıştırmalısınız.
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
                  <div className="rounded-md border p-3" data-testid="categories-preview-delete-count">Silinecek: {dryRunResult.summary?.deletes ?? 0}</div>
                  <div className="rounded-md border p-3" data-testid="categories-preview-total-count">Toplam: {dryRunResult.summary?.total ?? 0}</div>
                </div>

                <div className="flex flex-wrap items-center gap-3" data-testid="categories-preview-actions">
                  <button
                    type="button"
                    className="px-4 py-2 rounded-md bg-slate-900 text-white text-sm"
                    onClick={downloadPdfReport}
                    disabled={loading || !dryRunResult?.dry_run_hash}
                    data-testid="categories-preview-download-pdf"
                  >
                    PDF Raporu İndir
                  </button>
                  {!dryRunResult?.dry_run_hash && (
                    <span className="text-xs text-slate-500" data-testid="categories-preview-pdf-hint">
                      PDF raporu için önce dry-run çalıştırılmalı.
                    </span>
                  )}
                </div>

                {dryRunResult.warnings && dryRunResult.warnings.length > 0 && (
                  <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-700" data-testid="categories-preview-warning">
                    <div className="font-semibold mb-1" data-testid="categories-preview-warning-title">Kritik Uyarı</div>
                    <ul className="list-disc list-inside space-y-1" data-testid="categories-preview-warning-list">
                      {dryRunResult.warnings.map((warning, index) => (
                        <li key={`${warning.slug || 'warn'}-${index}`} data-testid={`categories-preview-warning-${index}`}>
                          {warning.message}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="grid gap-4 md:grid-cols-3" data-testid="categories-preview-lists">
                  <div className="border rounded-md p-3" data-testid="categories-preview-creates">
                    <h3 className="font-semibold text-sm mb-2">Eklenecek</h3>
                    {(dryRunResult.creates || []).length === 0 ? (
                      <p className="text-xs text-slate-500" data-testid="categories-preview-creates-empty">Yok</p>
                    ) : (
                      <ul className="text-xs space-y-1" data-testid="categories-preview-creates-list">
                        {dryRunResult.creates.map((item) => (
                          <li key={item.slug_tr} data-testid={`categories-preview-create-${item.slug_tr}`}>{item.slug_tr}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                  <div className="border rounded-md p-3" data-testid="categories-preview-updates">
                    <div className="flex items-center justify-between mb-2" data-testid="categories-preview-updates-header">
                      <h3 className="font-semibold text-sm">Güncellenecek</h3>
                      <label className="text-xs text-slate-500 flex items-center gap-2" data-testid="categories-preview-changed-toggle">
                        <input
                          type="checkbox"
                          checked={showOnlyChanged}
                          onChange={(event) => setShowOnlyChanged(event.target.checked)}
                          data-testid="categories-preview-changed-toggle-input"
                        />
                        Sadece değişen alanlar
                      </label>
                    </div>
                    {updates.length === 0 ? (
                      <p className="text-xs text-slate-500" data-testid="categories-preview-updates-empty">Yok</p>
                    ) : (
                      <div className="space-y-2" data-testid="categories-preview-updates-list">
                        {pagedUpdates.map((item) => (
                          <div key={item.slug} className="rounded-md border p-2" data-testid={`categories-preview-update-${item.slug}`}>
                            <button
                              type="button"
                              onClick={() => setExpandedSlug(expandedSlug === item.slug ? null : item.slug)}
                              className="w-full flex items-center justify-between text-xs font-medium"
                              data-testid={`categories-preview-update-toggle-${item.slug}`}
                            >
                              <span>{item.slug}</span>
                              <span className="text-slate-500">{item.changed_fields || 0} değişiklik</span>
                            </button>
                            {expandedSlug === item.slug && (
                              <div className="mt-2" data-testid={`categories-preview-update-detail-${item.slug}`}>
                                <div className="grid grid-cols-4 gap-2 text-[11px] font-semibold text-slate-500" data-testid={`categories-preview-update-header-${item.slug}`}>
                                  <div>Alan</div>
                                  <div>Önce</div>
                                  <div>Sonra</div>
                                  <div>Tip</div>
                                </div>
                                <div className="mt-1 space-y-1 text-[11px]" data-testid={`categories-preview-update-fields-${item.slug}`}>
                                  {(item.fields || [])
                                    .filter((field) => (showOnlyChanged ? field.change_type !== 'unchanged' : true))
                                    .map((field, idx) => (
                                      <div key={`${field.field_name}-${idx}`} className="grid grid-cols-4 gap-2" data-testid={`categories-preview-update-field-${item.slug}-${idx}`}>
                                        <div>{field.field_name}</div>
                                        <div className="truncate">{String(field.before_value ?? '')}</div>
                                        <div className="truncate">{String(field.after_value ?? '')}</div>
                                        <div>{field.change_type}</div>
                                      </div>
                                    ))}
                                </div>
                              </div>
                            )}
                          </div>
                        ))}
                        {updates.length > UPDATE_PAGE_SIZE && (
                          <div className="flex items-center justify-between text-xs pt-2" data-testid="categories-preview-updates-pagination">
                            <button
                              type="button"
                              className="px-2 py-1 border rounded"
                              onClick={() => setUpdatePage(Math.max(1, safeUpdatePage - 1))}
                              disabled={safeUpdatePage === 1}
                              data-testid="categories-preview-updates-prev"
                            >
                              Önceki
                            </button>
                            <span data-testid="categories-preview-updates-page">Sayfa {safeUpdatePage} / {totalUpdatePages}</span>
                            <button
                              type="button"
                              className="px-2 py-1 border rounded"
                              onClick={() => setUpdatePage(Math.min(totalUpdatePages, safeUpdatePage + 1))}
                              disabled={safeUpdatePage === totalUpdatePages}
                              data-testid="categories-preview-updates-next"
                            >
                              Sonraki
                            </button>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                  <div className="border rounded-md p-3" data-testid="categories-preview-deletes">
                    <h3 className="font-semibold text-sm mb-2">Silinecek</h3>
                    {(dryRunResult.deletes || []).length === 0 ? (
                      <p className="text-xs text-slate-500" data-testid="categories-preview-deletes-empty">Yok</p>
                    ) : (
                      <ul className="text-xs space-y-1" data-testid="categories-preview-deletes-list">
                        {dryRunResult.deletes.map((item) => (
                          <li key={item.slug} data-testid={`categories-preview-delete-${item.slug}`}>
                            {item.slug}{item.is_root ? ' (root)' : ''}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-sm text-slate-500" data-testid="categories-preview-empty">Önce dry-run çalıştırın.</p>
            )}
          </div>
        </div>
      )}

      {activeTab === 'publish' && (
        <div className="space-y-4" data-testid="categories-import-export-publish">
          <div className="rounded-lg border bg-white p-4">
            <h2 className="text-lg font-semibold" data-testid="categories-publish-title">Publish Batch</h2>
            <p className="text-sm text-slate-600" data-testid="categories-publish-desc">Import sonrası draft schema versiyonlarını publish eder.</p>
            <div className="mt-4">
              <div className="text-xs text-slate-500" data-testid="categories-publish-batch">
                Batch ID: {commitResult?.batch_id || '-'}
              </div>
              <button
                type="button"
                className="mt-3 px-4 py-2 rounded-md bg-emerald-600 text-white text-sm"
                onClick={runPublish}
                disabled={loading || !commitResult?.batch_id}
                data-testid="categories-publish-action"
              >
                Publish Et
              </button>
            </div>
            {publishResult && (
              <div className="mt-4 rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700" data-testid="categories-publish-result">
                Yayınlanan schema sayısı: {publishResult.published}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
