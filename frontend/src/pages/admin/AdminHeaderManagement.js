import React, { useEffect, useState } from 'react';
import axios from 'axios';
import SiteHeader from '@/components/public/SiteHeader';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const MAX_LOGO_MB = 2;
const MAX_LOGO_BYTES = MAX_LOGO_MB * 1024 * 1024;

export default function AdminHeaderManagement() {
  const [logoUrl, setLogoUrl] = useState(null);
  const [headerVersion, setHeaderVersion] = useState(null);
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');

  const fetchHeader = async () => {
    const res = await axios.get(`${API}/admin/site/header`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
    });
    setLogoUrl(res.data?.logo_url || null);
    setHeaderVersion(res.data?.version || null);
  };

  useEffect(() => {
    fetchHeader();
  }, []);

  const handleFileChange = (event) => {
    setStatus('');
    setError('');
    const selected = event.target.files?.[0] || null;
    if (!selected) {
      setFile(null);
      return;
    }
    if (selected.size > MAX_LOGO_BYTES) {
      setError(`Dosya boyutu ${MAX_LOGO_MB}MB sınırını aşıyor.`);
      setFile(null);
      return;
    }
    setFile(selected);
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Dosya seçin');
      return;
    }
    const formData = new FormData();
    formData.append('file', file);
    try {
      setError('');
      const res = await axios.post(`${API}/admin/site/header/logo`, formData, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      setStatus('Logo güncellendi');
      setFile(null);
      setLogoUrl(res.data?.logo_url || null);
      setHeaderVersion(res.data?.version || null);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Logo yükleme başarısız');
    }
  };

  return (
    <div className="space-y-6" data-testid="admin-header-management">
      <div>
        <h1 className="text-2xl font-semibold" data-testid="admin-header-title">Header Yönetimi</h1>
        <p className="text-sm text-muted-foreground" data-testid="admin-header-subtitle">
          PNG/SVG logo yükleyin ve guest/auth görünümlerini doğrulayın.
        </p>
      </div>

      <div className="rounded-lg border bg-white p-4 space-y-4" data-testid="admin-header-upload-card">
        <div className="text-sm font-semibold">Logo Upload</div>
        {logoUrl && (
          <img src={logoUrl} alt="Logo" className="h-12 object-contain" data-testid="admin-header-current-logo" />
        )}
        <div className="text-xs text-muted-foreground" data-testid="admin-header-upload-hint">
          Maksimum dosya boyutu: {MAX_LOGO_MB}MB. Yükleme sonrası cache versiyonu otomatik güncellenir.
        </div>
        <input
          type="file"
          accept=".png,.svg"
          onChange={handleFileChange}
          data-testid="admin-header-file-input"
        />
        {error && (
          <div className="text-xs text-rose-600" data-testid="admin-header-error">{error}</div>
        )}
        {status && (
          <div className="text-xs text-emerald-600" data-testid="admin-header-status">{status}</div>
        )}
        {headerVersion && (
          <div className="text-xs text-muted-foreground" data-testid="admin-header-version">Versiyon: {headerVersion}</div>
        )}
        <button
          type="button"
          onClick={handleUpload}
          className="h-9 px-4 rounded-md bg-primary text-primary-foreground text-sm"
          data-testid="admin-header-upload-button"
        >
          Logo Yükle
        </button>
      </div>

      <div className="grid gap-6 md:grid-cols-2" data-testid="admin-header-preview">
        <div className="rounded-lg border bg-white p-3" data-testid="admin-header-preview-guest">
          <div className="text-xs font-semibold text-muted-foreground mb-2">Guest Preview</div>
          <SiteHeader mode="guest" refreshToken={headerVersion} />
        </div>
        <div className="rounded-lg border bg-white p-3" data-testid="admin-header-preview-auth">
          <div className="text-xs font-semibold text-muted-foreground mb-2">Authenticated Preview</div>
          <SiteHeader mode="auth" refreshToken={headerVersion} />
        </div>
      </div>
    </div>
  );
}
