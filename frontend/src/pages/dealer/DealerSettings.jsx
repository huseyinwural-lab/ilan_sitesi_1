import React, { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const defaultProfileForm = {
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

const defaultNotificationPrefs = {
  push_enabled: true,
  email_enabled: true,
  message_email_enabled: true,
  marketing_email_enabled: false,
  read_receipt_enabled: true,
  sms_enabled: false,
};

const sectionConfig = {
  profile: { label: 'Hesap Bilgilerim', mode: 'profile' },
  address: { label: 'İşletme Bilgileri', mode: 'profile' },
  security: { label: 'Güvenlik', mode: 'security' },
  notifications: { label: 'Bildirim Tercihleri', mode: 'notifications' },
  blocked: { label: 'Engellediğim Hesaplar', mode: 'blocked' },
};

const profileFieldMap = {
  profile: ['company_name', 'authorized_person', 'contact_email', 'contact_phone'],
  address: ['address_street', 'address_zip', 'address_city', 'address_country', 'logo_url'],
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

const notificationFieldLabels = {
  push_enabled: 'Push Bildirimleri',
  email_enabled: 'E-Posta Bildirimleri',
  message_email_enabled: 'Mesaj E-Postaları',
  marketing_email_enabled: 'Kampanya ve Pazarlama E-Postaları',
  read_receipt_enabled: 'Mesaj Okundu Bilgisi',
  sms_enabled: 'SMS Bildirimleri',
};

const formatDateTime = (value) => {
  if (!value) return '-';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return '-';
  return parsed.toLocaleString('tr-TR');
};

export default function DealerSettings() {
  const [searchParams, setSearchParams] = useSearchParams();
  const requestedSection = searchParams.get('section');
  const initialSection = sectionConfig[requestedSection] ? requestedSection : 'profile';

  const [activeSection, setActiveSection] = useState(initialSection);
  const [loading, setLoading] = useState(true);

  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [profileForm, setProfileForm] = useState(defaultProfileForm);
  const [lastLoadedProfileForm, setLastLoadedProfileForm] = useState(defaultProfileForm);
  const [profileSaving, setProfileSaving] = useState(false);

  const [notificationPrefs, setNotificationPrefs] = useState(defaultNotificationPrefs);
  const [notificationSaving, setNotificationSaving] = useState(false);

  const [securityMeta, setSecurityMeta] = useState({ two_factor_enabled: false, last_login: null });
  const [passwordForm, setPasswordForm] = useState({ current_password: '', new_password: '', confirm_password: '' });
  const [passwordSaving, setPasswordSaving] = useState(false);

  const [blockedAccounts, setBlockedAccounts] = useState([]);
  const [blockedEmailInput, setBlockedEmailInput] = useState('');
  const [blockedSaving, setBlockedSaving] = useState(false);

  const profileFields = useMemo(() => profileFieldMap[activeSection] || profileFieldMap.profile, [activeSection]);
  const currentSectionMode = sectionConfig[activeSection]?.mode || 'profile';

  const fetchProfile = async () => {
    const token = localStorage.getItem('access_token');
    const res = await fetch(`${API}/dealer/settings/profile`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const payload = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(payload?.detail || 'Profil alınamadı');
    const nextForm = { ...defaultProfileForm, ...(payload?.profile || {}) };
    setProfileForm(nextForm);
    setLastLoadedProfileForm(nextForm);
  };

  const fetchPreferences = async () => {
    const token = localStorage.getItem('access_token');
    const res = await fetch(`${API}/dealer/settings/preferences`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const payload = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(payload?.detail || 'Tercihler alınamadı');

    const prefs = payload?.notification_prefs || {};
    setNotificationPrefs({ ...defaultNotificationPrefs, ...prefs });
    setBlockedAccounts(Array.isArray(payload?.blocked_accounts) ? payload.blocked_accounts : []);
    setSecurityMeta({
      two_factor_enabled: Boolean(payload?.security?.two_factor_enabled),
      last_login: payload?.security?.last_login || null,
    });
  };

  const fetchAll = async () => {
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      await Promise.all([fetchProfile(), fetchPreferences()]);
    } catch (err) {
      setError(err?.message || 'Hesap bilgileri alınamadı');
    } finally {
      setLoading(false);
    }
  };

  const handleSectionChange = (sectionKey) => {
    setActiveSection(sectionKey);
    setError('');
    setSuccess('');
    setSearchParams({ section: sectionKey });
  };

  const handleProfileSave = async (event) => {
    event.preventDefault();
    if (!profileForm.company_name?.trim()) {
      setError('Şirket adı zorunludur.');
      setSuccess('');
      return;
    }
    if (profileForm.contact_email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(profileForm.contact_email)) {
      setError('Geçerli bir e-posta giriniz.');
      setSuccess('');
      return;
    }

    setProfileSaving(true);
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
        body: JSON.stringify(profileForm),
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(payload?.detail || 'Profil kaydedilemedi');
      setLastLoadedProfileForm({ ...profileForm });
      setSuccess('Hesap bilgileri kaydedildi.');
    } catch (err) {
      setError(err?.message || 'Profil kaydedilemedi');
    } finally {
      setProfileSaving(false);
    }
  };

  const handleNotificationSave = async () => {
    setNotificationSaving(true);
    setError('');
    setSuccess('');
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`${API}/dealer/settings/preferences`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ notification_prefs: { ...notificationPrefs, blocked_accounts: blockedAccounts } }),
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(payload?.detail || 'Bildirim tercihleri kaydedilemedi');
      setNotificationPrefs({ ...defaultNotificationPrefs, ...(payload?.notification_prefs || {}) });
      setSuccess('Bildirim tercihleri kaydedildi.');
    } catch (err) {
      setError(err?.message || 'Bildirim tercihleri kaydedilemedi');
    } finally {
      setNotificationSaving(false);
    }
  };

  const handlePasswordSave = async (event) => {
    event.preventDefault();
    if (!passwordForm.current_password || !passwordForm.new_password) {
      setError('Mevcut ve yeni şifre zorunludur.');
      setSuccess('');
      return;
    }
    if ((passwordForm.new_password || '').length < 8) {
      setError('Yeni şifre en az 8 karakter olmalıdır.');
      setSuccess('');
      return;
    }
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      setError('Yeni şifre ve tekrar alanı uyuşmuyor.');
      setSuccess('');
      return;
    }

    setPasswordSaving(true);
    setError('');
    setSuccess('');
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`${API}/dealer/settings/change-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          current_password: passwordForm.current_password,
          new_password: passwordForm.new_password,
        }),
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(payload?.detail || 'Şifre güncellenemedi');
      setPasswordForm({ current_password: '', new_password: '', confirm_password: '' });
      setSuccess('Şifreniz başarıyla güncellendi.');
    } catch (err) {
      setError(err?.message || 'Şifre güncellenemedi');
    } finally {
      setPasswordSaving(false);
    }
  };

  const handleBlockedAccountAdd = async () => {
    const email = blockedEmailInput.trim().toLowerCase();
    if (!email) {
      setError('E-posta adresi giriniz.');
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError('Geçerli bir e-posta giriniz.');
      return;
    }

    setBlockedSaving(true);
    setError('');
    setSuccess('');
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`${API}/dealer/settings/blocked-accounts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ email }),
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(payload?.detail || 'Hesap engellenemedi');
      setBlockedAccounts(Array.isArray(payload?.blocked_accounts) ? payload.blocked_accounts : []);
      setBlockedEmailInput('');
      setSuccess('Hesap engelleme listesi güncellendi.');
    } catch (err) {
      setError(err?.message || 'Hesap engellenemedi');
    } finally {
      setBlockedSaving(false);
    }
  };

  const handleBlockedAccountRemove = async (email) => {
    setBlockedSaving(true);
    setError('');
    setSuccess('');
    try {
      const token = localStorage.getItem('access_token');
      const params = new URLSearchParams({ email });
      const res = await fetch(`${API}/dealer/settings/blocked-accounts?${params.toString()}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(payload?.detail || 'Engel kaldırılamadı');
      setBlockedAccounts(Array.isArray(payload?.blocked_accounts) ? payload.blocked_accounts : []);
      setSuccess('Engel listesi güncellendi.');
    } catch (err) {
      setError(err?.message || 'Engel kaldırılamadı');
    } finally {
      setBlockedSaving(false);
    }
  };

  useEffect(() => {
    fetchAll();
  }, []);

  useEffect(() => {
    const requested = searchParams.get('section');
    if (requested && sectionConfig[requested] && requested !== activeSection) {
      setActiveSection(requested);
      return;
    }
    if (!requested) {
      setSearchParams({ section: activeSection }, { replace: true });
    }
  }, [searchParams]);

  return (
    <div className="space-y-4" data-testid="dealer-settings-page">
      <div className="flex flex-wrap items-center justify-between gap-3" data-testid="dealer-settings-header">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900" data-testid="dealer-settings-title">Hesabım</h1>
          <p className="text-sm font-medium text-slate-700" data-testid="dealer-settings-subtitle">Kurumsal hesap, güvenlik ve bildirim ayarlarınızı yönetin.</p>
        </div>
        <button
          type="button"
          onClick={fetchAll}
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
              onClick={() => handleSectionChange(key)}
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
          <div className="mt-3 space-y-3" data-testid="dealer-settings-content">
            {error ? <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700" data-testid="dealer-settings-error">{error}</div> : null}
            {success ? <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700" data-testid="dealer-settings-success">{success}</div> : null}

            {currentSectionMode === 'profile' ? (
              <form onSubmit={handleProfileSave} className="space-y-3" data-testid="dealer-settings-profile-form">
                <div className="grid gap-3 md:grid-cols-2" data-testid="dealer-settings-grid">
                  {profileFields.map((fieldKey) => (
                    <label key={fieldKey} className="space-y-1" data-testid={`dealer-settings-field-wrap-${fieldKey}`}>
                      <span className="text-xs font-semibold text-slate-700" data-testid={`dealer-settings-field-label-${fieldKey}`}>{fieldLabels[fieldKey]}</span>
                      <input
                        value={profileForm[fieldKey] || ''}
                        onChange={(event) => setProfileForm((prev) => ({ ...prev, [fieldKey]: event.target.value }))}
                        className="h-10 w-full rounded-md border border-slate-300 px-3 text-sm text-slate-900"
                        data-testid={`dealer-settings-field-${fieldKey}`}
                      />
                    </label>
                  ))}
                </div>

                <div className="flex flex-wrap items-center gap-2" data-testid="dealer-settings-actions">
                  <button
                    type="submit"
                    disabled={profileSaving}
                    className="h-9 rounded-md bg-slate-900 px-4 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-70"
                    data-testid="dealer-settings-save-button"
                  >
                    {profileSaving ? 'Kaydediliyor...' : 'Kaydet'}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setProfileForm({ ...lastLoadedProfileForm });
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
            ) : null}

            {currentSectionMode === 'security' ? (
              <div className="space-y-3" data-testid="dealer-settings-security-section">
                <div className="rounded-md border border-slate-200 bg-slate-50 p-3" data-testid="dealer-settings-security-summary">
                  <div className="text-xs font-semibold text-slate-700" data-testid="dealer-settings-two-factor-label">2FA Durumu</div>
                  <div className="text-sm font-semibold text-slate-900" data-testid="dealer-settings-two-factor-value">{securityMeta.two_factor_enabled ? 'Aktif' : 'Pasif'}</div>
                  <div className="mt-2 text-xs text-slate-600" data-testid="dealer-settings-last-login">Son Giriş: {formatDateTime(securityMeta.last_login)}</div>
                </div>

                <form onSubmit={handlePasswordSave} className="space-y-3" data-testid="dealer-settings-password-form">
                  <label className="space-y-1" data-testid="dealer-settings-current-password-wrap">
                    <span className="text-xs font-semibold text-slate-700">Mevcut Şifre</span>
                    <input
                      type="password"
                      value={passwordForm.current_password}
                      onChange={(event) => setPasswordForm((prev) => ({ ...prev, current_password: event.target.value }))}
                      className="h-10 w-full rounded-md border border-slate-300 px-3 text-sm text-slate-900"
                      data-testid="dealer-settings-current-password-input"
                    />
                  </label>
                  <label className="space-y-1" data-testid="dealer-settings-new-password-wrap">
                    <span className="text-xs font-semibold text-slate-700">Yeni Şifre</span>
                    <input
                      type="password"
                      value={passwordForm.new_password}
                      onChange={(event) => setPasswordForm((prev) => ({ ...prev, new_password: event.target.value }))}
                      className="h-10 w-full rounded-md border border-slate-300 px-3 text-sm text-slate-900"
                      data-testid="dealer-settings-new-password-input"
                    />
                  </label>
                  <label className="space-y-1" data-testid="dealer-settings-confirm-password-wrap">
                    <span className="text-xs font-semibold text-slate-700">Yeni Şifre (Tekrar)</span>
                    <input
                      type="password"
                      value={passwordForm.confirm_password}
                      onChange={(event) => setPasswordForm((prev) => ({ ...prev, confirm_password: event.target.value }))}
                      className="h-10 w-full rounded-md border border-slate-300 px-3 text-sm text-slate-900"
                      data-testid="dealer-settings-confirm-password-input"
                    />
                  </label>
                  <button
                    type="submit"
                    disabled={passwordSaving}
                    className="h-9 rounded-md bg-slate-900 px-4 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-70"
                    data-testid="dealer-settings-password-save-button"
                  >
                    {passwordSaving ? 'Güncelleniyor...' : 'Şifreyi Güncelle'}
                  </button>
                </form>
              </div>
            ) : null}

            {currentSectionMode === 'notifications' ? (
              <div className="space-y-3" data-testid="dealer-settings-notifications-section">
                <div className="grid gap-2" data-testid="dealer-settings-notifications-grid">
                  {Object.keys(notificationFieldLabels).map((key) => (
                    <label key={key} className="flex items-center gap-2 rounded-md border border-slate-200 p-2 text-sm text-slate-800" data-testid={`dealer-settings-notification-item-${key}`}>
                      <input
                        type="checkbox"
                        checked={Boolean(notificationPrefs[key])}
                        onChange={(event) => setNotificationPrefs((prev) => ({ ...prev, [key]: event.target.checked }))}
                        data-testid={`dealer-settings-notification-checkbox-${key}`}
                      />
                      <span data-testid={`dealer-settings-notification-label-${key}`}>{notificationFieldLabels[key]}</span>
                    </label>
                  ))}
                </div>
                <button
                  type="button"
                  disabled={notificationSaving}
                  onClick={handleNotificationSave}
                  className="h-9 rounded-md bg-slate-900 px-4 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-70"
                  data-testid="dealer-settings-notification-save-button"
                >
                  {notificationSaving ? 'Kaydediliyor...' : 'Tercihleri Kaydet'}
                </button>
              </div>
            ) : null}

            {currentSectionMode === 'blocked' ? (
              <div className="space-y-3" data-testid="dealer-settings-blocked-section">
                <div className="flex flex-wrap items-center gap-2" data-testid="dealer-settings-blocked-add-row">
                  <input
                    type="email"
                    value={blockedEmailInput}
                    onChange={(event) => setBlockedEmailInput(event.target.value)}
                    className="h-10 min-w-[280px] flex-1 rounded-md border border-slate-300 px-3 text-sm text-slate-900"
                    placeholder="ornek@domain.com"
                    data-testid="dealer-settings-blocked-input"
                  />
                  <button
                    type="button"
                    onClick={handleBlockedAccountAdd}
                    disabled={blockedSaving}
                    className="h-10 rounded-md bg-slate-900 px-4 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-70"
                    data-testid="dealer-settings-blocked-add-button"
                  >
                    {blockedSaving ? 'Ekleniyor...' : 'Engelle'}
                  </button>
                </div>

                {blockedAccounts.length === 0 ? (
                  <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-sm text-slate-600" data-testid="dealer-settings-blocked-empty">
                    Henüz engellenen hesap yok.
                  </div>
                ) : (
                  <div className="space-y-2" data-testid="dealer-settings-blocked-list">
                    {blockedAccounts.map((email) => (
                      <div key={email} className="flex items-center justify-between rounded-md border border-slate-200 p-3" data-testid={`dealer-settings-blocked-item-${email}`}>
                        <span className="text-sm text-slate-900" data-testid={`dealer-settings-blocked-email-${email}`}>{email}</span>
                        <button
                          type="button"
                          onClick={() => handleBlockedAccountRemove(email)}
                          disabled={blockedSaving}
                          className="h-8 rounded-md border border-slate-300 px-3 text-xs font-semibold text-slate-800 disabled:cursor-not-allowed disabled:opacity-70"
                          data-testid={`dealer-settings-blocked-remove-${email}`}
                        >
                          Engeli Kaldır
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
}
