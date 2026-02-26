import React, { useEffect, useState } from 'react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const defaultForm = {
  company_name: '',
  authorized_person: '',
  contact_email: '',
  contact_phone: '',
  address_street: '',
  address_zip: '',
  address_city: '',
  address_country: '',
  logo_url: '',
};

export default function DealerSettings() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [form, setForm] = useState(defaultForm);

  const fetchProfile = async () => {
    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`${API}/dealer/settings/profile`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(payload?.detail || 'Profil alınamadı');
      setForm({ ...defaultForm, ...(payload?.profile || {}) });
    } catch (err) {
      setError(err?.message || 'Profil alınamadı');
      setForm(defaultForm);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError('');
    setSuccess('');
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`${API}/dealer/settings/profile`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(form),
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(payload?.detail || 'Profil kaydedilemedi');
      setSuccess('Profil kaydedildi.');
    } catch (err) {
      setError(err?.message || 'Profil kaydedilemedi');
    } finally {
      setSaving(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, []);

  return (
    <div className="space-y-4" data-testid="dealer-settings-page">
      <div className="flex items-center justify-between" data-testid="dealer-settings-header">
        <h1 className="text-xl font-semibold" data-testid="dealer-settings-title">Kurumsal Ayarlar</h1>
        <button onClick={fetchProfile} className="h-9 rounded-md border px-3 text-sm" data-testid="dealer-settings-refresh-button">Yenile</button>
      </div>

      {loading ? (
        <div className="rounded-md border p-4 text-sm text-slate-500" data-testid="dealer-settings-loading">Yükleniyor...</div>
      ) : (
        <form onSubmit={handleSave} className="space-y-3" data-testid="dealer-settings-form">
          {error && <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700" data-testid="dealer-settings-error">{error}</div>}
          {success && <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700" data-testid="dealer-settings-success">{success}</div>}

          <div className="grid gap-3 md:grid-cols-2" data-testid="dealer-settings-grid">
            {Object.keys(defaultForm).map((fieldKey) => (
              <label key={fieldKey} className="space-y-1" data-testid={`dealer-settings-field-wrap-${fieldKey}`}>
                <span className="text-xs text-slate-600">{fieldKey}</span>
                <input
                  value={form[fieldKey] || ''}
                  onChange={(e) => setForm((prev) => ({ ...prev, [fieldKey]: e.target.value }))}
                  className="h-9 w-full rounded-md border px-3 text-sm"
                  data-testid={`dealer-settings-field-${fieldKey}`}
                />
              </label>
            ))}
          </div>

          <button
            type="submit"
            disabled={saving}
            className="h-9 rounded-md bg-[var(--brand-navy)] px-4 text-sm text-white"
            data-testid="dealer-settings-save-button"
          >
            {saving ? 'Kaydediliyor...' : 'Kaydet'}
          </button>
        </form>
      )}
    </div>
  );
}
