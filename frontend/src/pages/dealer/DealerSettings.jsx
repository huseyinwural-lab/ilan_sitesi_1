import React, { useEffect, useMemo, useState } from 'react';

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

const sectionConfig = {
  profile: {
    label: 'Hesap Bilgilerim',
    fields: ['company_name', 'authorized_person', 'contact_email', 'contact_phone'],
  },
  address: {
    label: 'İşletme Bilgileri',
    fields: ['address_street', 'address_zip', 'address_city', 'address_country', 'logo_url'],
  },
};

const fieldLabels = {
  company_name: 'Şirket Adı',
  authorized_person: 'Yetkili Kişi',
  contact_email: 'İletişim E-Postası',
  contact_phone: 'İletişim Telefonu',
  address_street: 'Adres',
  address_zip: 'Posta Kodu',
  address_city: 'Şehir',
  address_country: 'Ülke',
  logo_url: 'Logo URL',
};

export default function DealerSettings() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [activeSection, setActiveSection] = useState('profile');
  const [form, setForm] = useState(defaultForm);
  const [lastLoadedForm, setLastLoadedForm] = useState(defaultForm);

  const sectionFields = useMemo(() => sectionConfig[activeSection]?.fields || sectionConfig.profile.fields, [activeSection]);

  const fetchProfile = async () => {
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`${API}/dealer/settings/profile`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(payload?.detail || 'Profil alınamadı');
      const nextForm = { ...defaultForm, ...(payload?.profile || {}) };
      setForm(nextForm);
      setLastLoadedForm(nextForm);
    } catch (err) {
      setError(err?.message || 'Profil alınamadı');
      setForm(defaultForm);
      setLastLoadedForm(defaultForm);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (event) => {
    event.preventDefault();
    if (!form.company_name?.trim()) {
      setError('Şirket adı zorunludur.');
      setSuccess('');
      return;
    }

    if (form.contact_email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.contact_email)) {
      setError('Geçerli bir e-posta giriniz.');
      setSuccess('');
      return;
    }

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
      setLastLoadedForm({ ...form });
      setSuccess('Hesap bilgileri kaydedildi.');
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
      <div className="flex flex-wrap items-center justify-between gap-3" data-testid="dealer-settings-header">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900" data-testid="dealer-settings-title">Hesabım</h1>
          <p className="text-sm font-medium text-slate-700" data-testid="dealer-settings-subtitle">Kurumsal hesap ve mağaza bilgilerinizi yönetin.</p>
        </div>
        <button
          type="button"
          onClick={fetchProfile}
          className="h-9 rounded-md border border-slate-300 px-3 text-sm font-semibold text-slate-900"
          data-testid="dealer-settings-refresh-button"
        >
          Yenile
        </button>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-4" data-testid="dealer-settings-sections-card">
        <div className="flex flex-wrap items-center gap-2" data-testid="dealer-settings-section-tabs">
          {Object.entries(sectionConfig).map(([key, section]) => (
            <button
              key={key}
              type="button"
              onClick={() => setActiveSection(key)}
              className={`rounded-full border px-3 py-1.5 text-xs font-semibold ${activeSection === key ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-300 text-slate-800'}`}
              data-testid={`dealer-settings-section-tab-${key}`}
            >
              {section.label}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="mt-3 rounded-md border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500" data-testid="dealer-settings-loading">Yükleniyor...</div>
        ) : (
          <form onSubmit={handleSave} className="mt-3 space-y-3" data-testid="dealer-settings-form">
            {error ? <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700" data-testid="dealer-settings-error">{error}</div> : null}
            {success ? <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700" data-testid="dealer-settings-success">{success}</div> : null}

            <div className="grid gap-3 md:grid-cols-2" data-testid="dealer-settings-grid">
              {sectionFields.map((fieldKey) => (
                <label key={fieldKey} className="space-y-1" data-testid={`dealer-settings-field-wrap-${fieldKey}`}>
                  <span className="text-xs font-semibold text-slate-700" data-testid={`dealer-settings-field-label-${fieldKey}`}>{fieldLabels[fieldKey]}</span>
                  <input
                    value={form[fieldKey] || ''}
                    onChange={(event) => setForm((prev) => ({ ...prev, [fieldKey]: event.target.value }))}
                    className="h-10 w-full rounded-md border border-slate-300 px-3 text-sm text-slate-900"
                    data-testid={`dealer-settings-field-${fieldKey}`}
                  />
                </label>
              ))}
            </div>

            <div className="flex flex-wrap items-center gap-2" data-testid="dealer-settings-actions">
              <button
                type="submit"
                disabled={saving}
                className="h-9 rounded-md bg-slate-900 px-4 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-70"
                data-testid="dealer-settings-save-button"
              >
                {saving ? 'Kaydediliyor...' : 'Kaydet'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setForm({ ...lastLoadedForm });
                  setError('');
                  setSuccess('Son yüklenen profil geri getirildi.');
                }}
                className="h-9 rounded-md border border-slate-300 px-4 text-sm font-semibold text-slate-900"
                data-testid="dealer-settings-reset-button"
              >
                Son Yükleneni Geri Al
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
