import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const API_FIELD_GROUPS = [
  {
    title: 'Temel Filtreler',
    fields: [
      { key: 'make', label: 'Make ID', type: 'text' },
      { key: 'model', label: 'Model', type: 'text' },
      { key: 'keyword', label: 'Keyword', type: 'text' },
      { key: 'body', label: 'Body', type: 'text' },
      { key: 'doors', label: 'Doors', type: 'number' },
      { key: 'drive', label: 'Drive', type: 'text' },
      { key: 'engine_position', label: 'Engine Position', type: 'text' },
      { key: 'engine_type', label: 'Engine Type', type: 'text' },
      { key: 'fuel_type', label: 'Fuel Type', type: 'text' },
      { key: 'seats', label: 'Seats', type: 'number' },
      { key: 'year', label: 'Year', type: 'number' },
    ],
  },
  {
    title: 'Range Filtreleri',
    fields: [
      { key: 'min_cylinders', label: 'Min Cylinders', type: 'number' },
      { key: 'max_cylinders', label: 'Max Cylinders', type: 'number' },
      { key: 'min_lkm_hwy', label: 'Min LKM Hwy', type: 'number' },
      { key: 'max_lkm_hwy', label: 'Max LKM Hwy', type: 'number' },
      { key: 'min_power', label: 'Min Power', type: 'number' },
      { key: 'max_power', label: 'Max Power', type: 'number' },
      { key: 'min_top_speed', label: 'Min Top Speed', type: 'number' },
      { key: 'max_top_speed', label: 'Max Top Speed', type: 'number' },
      { key: 'min_torque', label: 'Min Torque', type: 'number' },
      { key: 'max_torque', label: 'Max Torque', type: 'number' },
      { key: 'min_weight', label: 'Min Weight', type: 'number' },
      { key: 'max_weight', label: 'Max Weight', type: 'number' },
      { key: 'min_year', label: 'Min Year', type: 'number' },
      { key: 'max_year', label: 'Max Year', type: 'number' },
    ],
  },
];

const DEFAULT_API_FORM = {
  body: '',
  doors: '',
  drive: '',
  engine_position: '',
  engine_type: '',
  fuel_type: '',
  full_results: '1',
  keyword: '',
  make: '',
  model: '',
  min_cylinders: '',
  max_cylinders: '',
  min_lkm_hwy: '',
  max_lkm_hwy: '',
  min_power: '',
  max_power: '',
  min_top_speed: '',
  max_top_speed: '',
  min_torque: '',
  max_torque: '',
  min_weight: '',
  max_weight: '',
  min_year: '',
  max_year: '',
  seats: '',
  sold_in_us: '',
  year: '',
};

const formatDate = (value) => {
  if (!value) return '-';
  try {
    return new Date(value).toLocaleString('tr-TR');
  } catch (error) {
    return value;
  }
};

const buildQueryString = (form) => {
  const params = new URLSearchParams();
  Object.entries(form).forEach(([key, value]) => {
    if (value === '' || value === null || value === undefined) return;
    params.set(key, value);
  });
  return params.toString();
};

export default function AdminVehicleMasterImport() {
  const [apiForm, setApiForm] = useState(DEFAULT_API_FORM);
  const [apiDryRun, setApiDryRun] = useState(false);
  const [apiPreview, setApiPreview] = useState('');
  const [apiStatus, setApiStatus] = useState('');
  const [apiError, setApiError] = useState('');
  const [apiLoading, setApiLoading] = useState(false);

  const [uploadFile, setUploadFile] = useState(null);
  const [uploadDryRun, setUploadDryRun] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');
  const [uploadError, setUploadError] = useState('');
  const [uploadErrorInfo, setUploadErrorInfo] = useState(null);
  const [uploadLoading, setUploadLoading] = useState(false);

  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [jobLoading, setJobLoading] = useState(false);

  const authHeader = useMemo(() => ({ Authorization: `Bearer ${localStorage.getItem('token')}` }), []);

  const fetchJobs = async () => {
    try {
      const res = await axios.get(`${API}/admin/vehicle-master-import/jobs`, { headers: authHeader });
      setJobs(res.data?.items || []);
      if (selectedJob?.id) {
        const updated = res.data?.items?.find((item) => item.id === selectedJob.id);
        if (updated) {
          setSelectedJob(updated);
        }
      }
    } catch (error) {
      setJobs([]);
    }
  };

  const fetchJobDetail = async (jobId) => {
    try {
      setJobLoading(true);
      const res = await axios.get(`${API}/admin/vehicle-master-import/jobs/${jobId}`, { headers: authHeader });
      setSelectedJob(res.data?.job || null);
    } catch (error) {
      setSelectedJob(null);
    } finally {
      setJobLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleApiChange = (key, value) => {
    setApiForm((prev) => ({ ...prev, [key]: value }));
  };

  const handlePreview = () => {
    setApiPreview(buildQueryString(apiForm));
  };

  const handleApiSubmit = async () => {
    setApiLoading(true);
    setApiError('');
    setApiStatus('');
    try {
      const payload = {
        ...Object.fromEntries(
          Object.entries(apiForm).filter(([, value]) => value !== '' && value !== null && value !== undefined),
        ),
        dry_run: apiDryRun,
      };
      const res = await axios.post(`${API}/admin/vehicle-master-import/jobs/api`, payload, { headers: authHeader });
      setApiStatus(`Job oluşturuldu: ${res.data?.job?.id || ''}`);
      setSelectedJob(res.data?.job || null);
      fetchJobs();
    } catch (error) {
      setApiError(error?.response?.data?.detail || 'Job oluşturulamadı.');
    } finally {
      setApiLoading(false);
    }
  };

  const handleUploadSubmit = async () => {
    if (!uploadFile) {
      setUploadError('JSON dosyası seçin.');
      setUploadErrorInfo({ error_code: 'JSON_SCHEMA_ERROR', message: 'JSON dosyası seçin.', field_errors: [] });
      return;
    }
    if (uploadFile.size > 50 * 1024 * 1024) {
      setUploadError('Dosya 50MB limitini aşıyor.');
      setUploadErrorInfo({ error_code: 'JSON_SCHEMA_ERROR', message: 'Dosya 50MB limitini aşıyor.', field_errors: [] });
      return;
    }
    setUploadLoading(true);
    setUploadError('');
    setUploadStatus('');
    setUploadErrorInfo(null);
    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      formData.append('dry_run', uploadDryRun ? 'true' : 'false');
      const res = await axios.post(`${API}/admin/vehicle-master-import/jobs/upload`, formData, {
        headers: { ...authHeader, 'Content-Type': 'multipart/form-data' },
      });
      setUploadStatus(`Job oluşturuldu: ${res.data?.job?.id || ''}`);
      setSelectedJob(res.data?.job || null);
      fetchJobs();
    } catch (error) {
      const detail = error?.response?.data;
      if (detail?.error_code) {
        setUploadErrorInfo(detail);
        setUploadError(detail.message || 'Upload başarısız.');
      } else {
        const message = detail?.message || detail || 'Upload başarısız.';
        setUploadErrorInfo({ error_code: 'UPLOAD_ERROR', message, field_errors: detail?.field_errors || [] });
        setUploadError(message);
      }
    } finally {
      setUploadLoading(false);
    }
  };

  const summary = selectedJob?.summary || {};
  const errorLog = selectedJob?.error_log || {};
  const validationErrors = errorLog?.validation_errors || summary?.validation_errors || [];
  const uploadFieldErrors = uploadErrorInfo?.field_errors || [];

  const handleDownloadExample = () => {
    const sample = [
      {
        make: "Audi",
        model: "A4",
        trim: "S Line",
        year: 2022,
        fuel_type: "gasoline",
        body: "sedan",
        transmission: "automatic",
        power: 150,
      },
    ];
    const blob = new Blob([JSON.stringify(sample, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'vehicle_master_sample.json';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6" data-testid="vehicle-master-import-page">
      <div className="flex flex-wrap items-center justify-between gap-4" data-testid="vehicle-master-import-header">
        <div>
          <h1 className="text-2xl font-semibold">Araç Master Data Import</h1>
          <p className="text-sm text-muted-foreground">
            API’den çek veya JSON yükle — job bazlı import ve log takibi.
          </p>
        </div>
        <div className="rounded-full border px-3 py-1 text-xs" data-testid="vehicle-master-import-limit">
          JSON max: 50MB
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2" data-testid="vehicle-master-import-forms">
        <div className="rounded-lg border bg-white p-4 space-y-4" data-testid="vehicle-master-import-api-card">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold">API’den Çek</h2>
              <p className="text-xs text-muted-foreground">getTrims parametreleri opsiyoneldir.</p>
            </div>
            <div className="text-xs" data-testid="vehicle-master-import-api-full-results">
              <label className="mr-2">full_results</label>
              <select
                value={apiForm.full_results}
                onChange={(e) => handleApiChange('full_results', e.target.value)}
                className="h-8 rounded-md border px-2 text-xs"
                data-testid="vehicle-import-api-full-results"
              >
                <option value="1">1 (full)</option>
                <option value="0">0 (basic)</option>
              </select>
            </div>
          </div>

          {API_FIELD_GROUPS.map((group) => (
            <div key={group.title} className="space-y-2" data-testid={`vehicle-import-api-group-${group.title.replace(/\s+/g, '-').toLowerCase()}`}>
              <div className="text-xs font-semibold text-muted-foreground">{group.title}</div>
              <div className="grid gap-3 md:grid-cols-2">
                {group.fields.map((field) => (
                  <label key={field.key} className="text-xs flex flex-col gap-1">
                    <span>{field.label}</span>
                    <input
                      type={field.type}
                      value={apiForm[field.key]}
                      onChange={(e) => handleApiChange(field.key, e.target.value)}
                      className="h-9 rounded-md border px-2"
                      data-testid={`vehicle-import-api-${field.key}`}
                    />
                  </label>
                ))}
              </div>
            </div>
          ))}

          <div className="grid gap-3 md:grid-cols-2" data-testid="vehicle-import-api-flags">
            <label className="text-xs flex flex-col gap-1">
              <span>sold_in_us</span>
              <select
                value={apiForm.sold_in_us}
                onChange={(e) => handleApiChange('sold_in_us', e.target.value)}
                className="h-9 rounded-md border px-2"
                data-testid="vehicle-import-api-sold-in-us"
              >
                <option value="">Seçiniz</option>
                <option value="true">True</option>
                <option value="false">False</option>
              </select>
            </label>
            <label className="flex items-center gap-2 text-xs mt-6" data-testid="vehicle-import-api-dry-run-toggle">
              <input
                type="checkbox"
                checked={apiDryRun}
                onChange={(e) => setApiDryRun(e.target.checked)}
                data-testid="vehicle-import-api-dry-run"
              />
              Dry-run (DB’ye yazma)
            </label>
          </div>

          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className="h-9 rounded-md border px-4 text-sm"
              onClick={handlePreview}
              data-testid="vehicle-import-api-preview-button"
            >
              İsteği Önizle
            </button>
            <button
              type="button"
              className="h-9 rounded-md bg-primary px-4 text-sm text-primary-foreground"
              onClick={handleApiSubmit}
              disabled={apiLoading}
              data-testid="vehicle-import-api-submit"
            >
              {apiLoading ? 'İşleniyor...' : 'Çek ve Import Et'}
            </button>
          </div>

          {apiPreview && (
            <div className="rounded-md border bg-slate-50 p-3 text-xs" data-testid="vehicle-import-api-preview-output">
              ?{apiPreview}
            </div>
          )}
          {apiStatus && (
            <div className="text-xs text-emerald-600" data-testid="vehicle-import-api-status">
              {apiStatus}
            </div>
          )}
          {apiError && (
            <div className="text-xs text-rose-600" data-testid="vehicle-import-api-error">
              {apiError}
            </div>
          )}
        </div>

        <div className="rounded-lg border bg-white p-4 space-y-4" data-testid="vehicle-master-import-upload-card">
          <div>
            <h2 className="text-lg font-semibold">JSON Yükle</h2>
            <p className="text-xs text-muted-foreground">Array of records formatı zorunludur.</p>
          </div>
          <div className="space-y-2">
            <input
              type="file"
              accept="application/json"
              onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
              data-testid="vehicle-import-upload-file"
            />
            <div className="flex flex-wrap items-center gap-2" data-testid="vehicle-import-upload-sample">
              <button
                type="button"
                className="h-8 rounded-md border px-3 text-xs"
                onClick={handleDownloadExample}
                data-testid="vehicle-import-upload-sample-button"
              >
                Örnek JSON indir
              </button>
              <span className="text-xs text-muted-foreground" data-testid="vehicle-import-upload-format">
                Beklenen format: Array; zorunlu alanlar: year, make, model, trim
              </span>
            </div>
            <label className="flex items-center gap-2 text-xs" data-testid="vehicle-import-upload-dry-run-toggle">
              <input
                type="checkbox"
                checked={uploadDryRun}
                onChange={(e) => setUploadDryRun(e.target.checked)}
                data-testid="vehicle-import-upload-dry-run"
              />
              Dry-run (DB’ye yazma)
            </label>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className="h-9 rounded-md bg-primary px-4 text-sm text-primary-foreground"
              onClick={handleUploadSubmit}
              disabled={uploadLoading}
              data-testid="vehicle-import-upload-submit"
            >
              {uploadLoading ? 'Yükleniyor...' : 'JSON Yükle ve Import Et'}
            </button>
          </div>
          {uploadStatus && (
            <div className="text-xs text-emerald-600" data-testid="vehicle-import-upload-status">
              {uploadStatus}
            </div>
          )}
          {uploadErrorInfo && (
            <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-xs" data-testid="vehicle-import-upload-error-box">
              <div className="font-semibold text-rose-700" data-testid="vehicle-import-upload-error-summary">
                {uploadErrorInfo.error_code} · {uploadErrorInfo.message} ({uploadFieldErrors.length} hata)
              </div>
              {uploadFieldErrors.length > 0 && (
                <div className="mt-2 space-y-1" data-testid="vehicle-import-upload-error-list">
                  {uploadFieldErrors.map((err, idx) => (
                    <div key={`${err.path}-${idx}`} className="text-rose-700" data-testid={`vehicle-import-upload-error-${idx}`}>
                      {err.path} — beklenen: {err.expected} · gelen: {String(err.got)} · {err.hint}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
          {uploadError && !uploadErrorInfo && (
            <div className="text-xs text-rose-600" data-testid="vehicle-import-upload-error">
              {uploadError}
            </div>
          )}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]" data-testid="vehicle-master-import-jobs">
        <div className="rounded-lg border bg-white p-4 space-y-3" data-testid="vehicle-import-job-list">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold">Import Jobları</h3>
            <button
              type="button"
              className="h-8 rounded-md border px-3 text-xs"
              onClick={fetchJobs}
              data-testid="vehicle-import-job-refresh"
            >
              Yenile
            </button>
          </div>
          {jobs.length === 0 && (
            <div className="text-xs text-muted-foreground" data-testid="vehicle-import-job-empty">
              Job bulunamadı.
            </div>
          )}
          <div className="space-y-2">
            {jobs.map((job) => (
              <button
                key={job.id}
                type="button"
                onClick={() => fetchJobDetail(job.id)}
                className={`w-full rounded-md border px-3 py-2 text-left text-xs ${
                  selectedJob?.id === job.id ? 'border-primary bg-primary/5' : ''
                }`}
                data-testid={`vehicle-import-job-${job.id}`}
              >
                <div className="flex items-center justify-between">
                  <div className="font-semibold">{job.source.toUpperCase()} · {job.status}</div>
                  <div>{job.progress}%</div>
                </div>
                <div className="text-muted-foreground" data-testid={`vehicle-import-job-created-${job.id}`}>
                  {formatDate(job.created_at)}
                </div>
                <div className="text-muted-foreground" data-testid={`vehicle-import-job-meta-${job.id}`}>
                  dry-run: {job.dry_run ? 'evet' : 'hayır'} · {job.total_records || 0} kayıt
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="rounded-lg border bg-white p-4 space-y-4" data-testid="vehicle-import-job-detail">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold">Job Detayı</h3>
            {jobLoading && (
              <span className="text-xs text-muted-foreground" data-testid="vehicle-import-job-detail-loading">Yükleniyor</span>
            )}
          </div>
          {!selectedJob && (
            <div className="text-xs text-muted-foreground" data-testid="vehicle-import-job-detail-empty">
              Detay görmek için bir job seçin.
            </div>
          )}
          {selectedJob && (
            <div className="space-y-4">
              <div className="space-y-2">
                <div className="text-xs" data-testid="vehicle-import-job-status">Status: {selectedJob.status}</div>
                <div className="h-2 w-full rounded-full bg-slate-100" data-testid="vehicle-import-job-progress">
                  <div
                    className="h-2 rounded-full bg-primary"
                    style={{ width: `${selectedJob.progress}%` }}
                    data-testid="vehicle-import-job-progress-bar"
                  />
                </div>
                <div className="text-xs text-muted-foreground" data-testid="vehicle-import-job-progress-text">
                  {selectedJob.processed_records || 0} / {selectedJob.total_records || 0}
                </div>
              </div>

              <div className="grid gap-3 md:grid-cols-2" data-testid="vehicle-import-job-summary">
                <div className="rounded-md border p-3" data-testid="vehicle-import-summary-new">
                  <div className="text-xs text-muted-foreground">New</div>
                  <div className="text-lg font-semibold">{summary.new ?? 0}</div>
                </div>
                <div className="rounded-md border p-3" data-testid="vehicle-import-summary-updated">
                  <div className="text-xs text-muted-foreground">Updated</div>
                  <div className="text-lg font-semibold">{summary.updated ?? 0}</div>
                </div>
                <div className="rounded-md border p-3" data-testid="vehicle-import-summary-skipped">
                  <div className="text-xs text-muted-foreground">Skipped</div>
                  <div className="text-lg font-semibold">{summary.skipped ?? 0}</div>
                </div>
                <div className="rounded-md border p-3" data-testid="vehicle-import-summary-duration">
                  <div className="text-xs text-muted-foreground">Duration (sn)</div>
                  <div className="text-lg font-semibold">{summary.duration_seconds ?? '-'}</div>
                </div>
                <div className="rounded-md border p-3" data-testid="vehicle-import-summary-distinct">
                  <div className="text-xs text-muted-foreground">Distinct (Make/Model/Trim)</div>
                  <div className="text-sm font-semibold">
                    {summary.distinct_makes ?? 0} / {summary.distinct_models ?? 0} / {summary.distinct_trims ?? 0}
                  </div>
                </div>
                <div className="rounded-md border p-3" data-testid="vehicle-import-summary-estimate">
                  <div className="text-xs text-muted-foreground">Estimated Duration (sn)</div>
                  <div className="text-lg font-semibold">{summary.estimated_duration_seconds ?? '-'}</div>
                </div>
              </div>

              <div className="space-y-2" data-testid="vehicle-import-job-validation">
                <div className="text-xs font-semibold">Validation Errors</div>
                <div className="text-xs text-muted-foreground" data-testid="vehicle-import-job-validation-count">
                  {summary.validation_error_count || 0} hata
                </div>
                {validationErrors.length === 0 && (
                  <div className="text-xs text-muted-foreground" data-testid="vehicle-import-job-validation-empty">
                    Hata yok.
                  </div>
                )}
                {validationErrors.length > 0 && (
                  <div className="space-y-1" data-testid="vehicle-import-job-validation-list">
                    {validationErrors.map((item, idx) => (
                      <div key={`${item.row}-${idx}`} className="text-xs text-rose-600">
                        #{item.row}: {item.error}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {selectedJob.error_message && (
                <div className="text-xs text-rose-600" data-testid="vehicle-import-job-error-message">
                  {selectedJob.error_message}
                </div>
              )}

              <div className="space-y-2" data-testid="vehicle-import-job-logs">
                <div className="text-xs font-semibold">Log</div>
                {selectedJob.log_entries?.length === 0 && (
                  <div className="text-xs text-muted-foreground" data-testid="vehicle-import-job-logs-empty">
                    Log bulunamadı.
                  </div>
                )}
                {selectedJob.log_entries?.length > 0 && (
                  <div className="space-y-1 max-h-48 overflow-auto">
                    {selectedJob.log_entries.map((entry, idx) => (
                      <div key={`${entry.ts}-${idx}`} className="text-xs text-muted-foreground" data-testid={`vehicle-import-job-log-${idx}`}>
                        [{entry.level}] {entry.message}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
