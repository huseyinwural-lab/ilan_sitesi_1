import React, { useEffect, useMemo, useState } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function DealerCompanyProfile() {
  const [form, setForm] = useState({
    company_name: '',
    vat_id: '',
    trade_register_no: '',
    authorized_person: '',
    contact_email: '',
    contact_phone: '',
    address_country: '',
    logo_url: '',
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [saved, setSaved] = useState(false);

  const authHeader = useMemo(() => ({
    Authorization: `Bearer ${localStorage.getItem('access_token')}`,
  }), []);

  const fetchProfile = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API}/v1/users/me/dealer-profile`, { headers: authHeader });
      if (!res.ok) {
        throw new Error('Şirket profili yüklenemedi');
      }
      const data = await res.json();
      setForm({
        company_name: data.company_name || '',
        vat_id: data.vat_id || '',
        trade_register_no: data.trade_register_no || '',
        authorized_person: data.authorized_person || '',
        contact_email: data.contact_email || data.email || '',
        contact_phone: data.contact_phone || '',
        address_country: data.country_code || '',
        logo_url: data.logo_url || '',
      });
    } catch (err) {
      setError(err?.message || 'Şirket profili yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleChange = (field) => (event) => {
    setForm((prev) => ({ ...prev, [field]: event.target.value }));
    setSaved(false);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError('');
    setSaved(false);
    try {
      const payload = {
        company_name: form.company_name,
        vat_id: form.vat_id,
        trade_register_no: form.trade_register_no,
        authorized_person: form.authorized_person,
        contact_email: form.contact_email,
        contact_phone: form.contact_phone,
        address_country: form.address_country,
        logo_url: form.logo_url,
      };
      const res = await fetch(`${API}/v1/users/me/dealer-profile`, {
        method: 'PUT',
        headers: {
          ...authHeader,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail?.detail || 'Kaydedilemedi');
      }
      setSaved(true);
    } catch (err) {
      setError(err?.message || 'Kaydedilemedi');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="text-sm text-muted-foreground" data-testid="dealer-company-loading">
        Yükleniyor...
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="dealer-company-profile">
      <div>
        <h1 className="text-2xl font-bold" data-testid="dealer-company-title">Şirket Profili</h1>
        <p className="text-sm text-muted-foreground" data-testid="dealer-company-subtitle">
          Avrupa standartlarına uygun kurumsal bilgilerinizi güncelleyin.
        </p>
      </div>

      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700" data-testid="dealer-company-error">
          {error}
        </div>
      )}

      <form className="grid gap-4 md:grid-cols-2" onSubmit={handleSubmit} data-testid="dealer-company-form">
        <div className="space-y-2" data-testid="dealer-company-name-field">
          <label className="text-sm font-medium">Şirket Adı</label>
          <input
            className="w-full rounded-md border px-3 py-2 text-sm"
            value={form.company_name}
            onChange={handleChange('company_name')}
            data-testid="dealer-company-name"
          />
        </div>
        <div className="space-y-2" data-testid="dealer-company-vat-field">
          <label className="text-sm font-medium">VAT ID</label>
          <input
            className="w-full rounded-md border px-3 py-2 text-sm"
            value={form.vat_id}
            onChange={handleChange('vat_id')}
            data-testid="dealer-company-vat"
          />
        </div>
        <div className="space-y-2" data-testid="dealer-company-register-field">
          <label className="text-sm font-medium">Ticaret Sicil No</label>
          <input
            className="w-full rounded-md border px-3 py-2 text-sm"
            value={form.trade_register_no}
            onChange={handleChange('trade_register_no')}
            data-testid="dealer-company-register"
          />
        </div>
        <div className="space-y-2" data-testid="dealer-company-person-field">
          <label className="text-sm font-medium">Yetkili Kişi</label>
          <input
            className="w-full rounded-md border px-3 py-2 text-sm"
            value={form.authorized_person}
            onChange={handleChange('authorized_person')}
            data-testid="dealer-company-person"
          />
        </div>
        <div className="space-y-2" data-testid="dealer-company-email-field">
          <label className="text-sm font-medium">İletişim E-posta</label>
          <input
            className="w-full rounded-md border px-3 py-2 text-sm"
            value={form.contact_email}
            onChange={handleChange('contact_email')}
            data-testid="dealer-company-email"
          />
        </div>
        <div className="space-y-2" data-testid="dealer-company-phone-field">
          <label className="text-sm font-medium">İletişim Telefon</label>
          <input
            className="w-full rounded-md border px-3 py-2 text-sm"
            value={form.contact_phone}
            onChange={handleChange('contact_phone')}
            data-testid="dealer-company-phone"
          />
        </div>
        <div className="space-y-2" data-testid="dealer-company-country-field">
          <label className="text-sm font-medium">Ülke</label>
          <input
            className="w-full rounded-md border px-3 py-2 text-sm"
            value={form.address_country}
            onChange={handleChange('address_country')}
            data-testid="dealer-company-country"
          />
        </div>
        <div className="space-y-2" data-testid="dealer-company-logo-field">
          <label className="text-sm font-medium">Logo URL</label>
          <input
            className="w-full rounded-md border px-3 py-2 text-sm"
            value={form.logo_url}
            onChange={handleChange('logo_url')}
            data-testid="dealer-company-logo"
          />
        </div>
        <div className="md:col-span-2 flex items-center gap-3" data-testid="dealer-company-actions">
          <button
            type="submit"
            className="rounded-md bg-[var(--brand-navy)] px-4 py-2 text-sm text-white"
            disabled={saving}
            data-testid="dealer-company-save"
          >
            {saving ? 'Kaydediliyor...' : 'Kaydet'}
          </button>
          {saved && (
            <span className="text-xs text-emerald-600" data-testid="dealer-company-saved">
              Kaydedildi
            </span>
          )}
        </div>
      </form>
    </div>
  );
}
