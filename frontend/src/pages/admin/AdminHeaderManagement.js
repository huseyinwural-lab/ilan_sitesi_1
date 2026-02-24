import React, { useEffect, useState } from 'react';
import axios from 'axios';
import SiteHeader from '@/components/public/SiteHeader';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AdminHeaderManagement() {
  const [logoUrl, setLogoUrl] = useState(null);
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState('');

  const fetchHeader = async () => {
    const res = await axios.get(`${API}/admin/site/header`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
    });
    setLogoUrl(res.data?.logo_url || null);
  };

  useEffect(() => {
    fetchHeader();
  }, []);

  const handleUpload = async () => {
    if (!file) {
      setStatus('Dosya seçin');
      return;
    }
    const formData = new FormData();
    formData.append('file', file);
    await axios.post(`${API}/admin/site/header/logo`, formData, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`,
      },
    });
    setStatus('Logo güncellendi');
    setFile(null);
    fetchHeader();
  };

  return (
    <div className="space-y-6" data-testid="admin-header-management">
      <div>
        <h1 className="text-2xl font-semibold" data-testid="admin-header-title">Header Yönetimi</h1>
        <p className="text-sm text-muted-foreground" data-testid="admin-header-subtitle">
          Logo yükleyin ve guest/auth görünümlerini doğrulayın.
        </p>
      </div>

      <div className="rounded-lg border bg-white p-4 space-y-4" data-testid="admin-header-upload-card">
        <div className="text-sm font-semibold">Logo Upload</div>
        {logoUrl && (
          <img src={logoUrl} alt="Logo" className="h-12 object-contain" data-testid="admin-header-current-logo" />
        )}
        <input
          type="file"
          accept=".png,.svg"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          data-testid="admin-header-file-input"
        />
        {status && (
          <div className="text-xs text-emerald-600" data-testid="admin-header-status">{status}</div>
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
          <SiteHeader mode="guest" />
        </div>
        <div className="rounded-lg border bg-white p-3" data-testid="admin-header-preview-auth">
          <div className="text-xs font-semibold text-muted-foreground mb-2">Authenticated Preview</div>
          <SiteHeader mode="auth" />
        </div>
      </div>
    </div>
  );
}
