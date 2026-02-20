import React, { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';

const PROFILE_KEY = 'account_profile';

const readProfile = () => {
  try {
    return JSON.parse(localStorage.getItem(PROFILE_KEY) || '{}');
  } catch (e) {
    return {};
  }
};

export default function AccountProfile() {
  const { user } = useAuth();
  const [profile, setProfile] = useState({ full_name: '', phone: '', city: '' });
  const [saved, setSaved] = useState(false);
  const [passwordForm, setPasswordForm] = useState({ current: '', next: '', confirm: '' });
  const [passwordMessage, setPasswordMessage] = useState('');

  useEffect(() => {
    const stored = readProfile();
    setProfile({
      full_name: stored.full_name || user?.full_name || '',
      phone: stored.phone || '',
      city: stored.city || '',
    });
  }, [user]);

  const handleProfileSave = () => {
    localStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
    setSaved(true);
    setTimeout(() => setSaved(false), 1500);
  };

  const handlePasswordSave = () => {
    if (!passwordForm.current || !passwordForm.next || !passwordForm.confirm) {
      setPasswordMessage('Tüm alanlar zorunlu.');
      return;
    }
    if (passwordForm.next.length < 8) {
      setPasswordMessage('Yeni şifre en az 8 karakter olmalı.');
      return;
    }
    if (passwordForm.next !== passwordForm.confirm) {
      setPasswordMessage('Şifreler eşleşmiyor.');
      return;
    }
    setPasswordMessage('Şifre güncellendi (MOCKED).');
    setPasswordForm({ current: '', next: '', confirm: '' });
  };

  return (
    <div className="space-y-6" data-testid="account-profile">
      <div>
        <h1 className="text-2xl font-bold" data-testid="account-profile-title">Hesap Ayarları</h1>
        <p className="text-sm text-muted-foreground" data-testid="account-profile-subtitle">Profil bilgilerinizi yönetin.</p>
      </div>

      <div className="rounded-lg border bg-white p-6 space-y-4" data-testid="account-profile-card">
        <div className="text-sm font-semibold">Profil Bilgileri</div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-muted-foreground">Ad Soyad</label>
            <input
              value={profile.full_name}
              onChange={(e) => setProfile((prev) => ({ ...prev, full_name: e.target.value }))}
              className="mt-1 h-10 w-full rounded-md border px-3 text-sm"
              data-testid="account-profile-name"
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground">Telefon</label>
            <input
              value={profile.phone}
              onChange={(e) => setProfile((prev) => ({ ...prev, phone: e.target.value }))}
              className="mt-1 h-10 w-full rounded-md border px-3 text-sm"
              data-testid="account-profile-phone"
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground">Şehir</label>
            <input
              value={profile.city}
              onChange={(e) => setProfile((prev) => ({ ...prev, city: e.target.value }))}
              className="mt-1 h-10 w-full rounded-md border px-3 text-sm"
              data-testid="account-profile-city"
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground">E-posta</label>
            <input
              value={user?.email || ''}
              readOnly
              className="mt-1 h-10 w-full rounded-md border px-3 text-sm bg-muted"
              data-testid="account-profile-email"
            />
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleProfileSave}
            className="h-10 px-4 rounded-md bg-primary text-primary-foreground text-sm"
            data-testid="account-profile-save"
          >
            Kaydet
          </button>
          {saved && (
            <span className="text-xs text-emerald-600" data-testid="account-profile-saved">Kaydedildi</span>
          )}
        </div>
      </div>

      <div className="rounded-lg border bg-white p-6 space-y-4" data-testid="account-password-card">
        <div className="text-sm font-semibold">Şifre Değiştir</div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="text-xs text-muted-foreground">Mevcut Şifre</label>
            <input
              type="password"
              value={passwordForm.current}
              onChange={(e) => setPasswordForm((prev) => ({ ...prev, current: e.target.value }))}
              className="mt-1 h-10 w-full rounded-md border px-3 text-sm"
              data-testid="account-password-current"
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground">Yeni Şifre</label>
            <input
              type="password"
              value={passwordForm.next}
              onChange={(e) => setPasswordForm((prev) => ({ ...prev, next: e.target.value }))}
              className="mt-1 h-10 w-full rounded-md border px-3 text-sm"
              data-testid="account-password-next"
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground">Yeni Şifre (Tekrar)</label>
            <input
              type="password"
              value={passwordForm.confirm}
              onChange={(e) => setPasswordForm((prev) => ({ ...prev, confirm: e.target.value }))}
              className="mt-1 h-10 w-full rounded-md border px-3 text-sm"
              data-testid="account-password-confirm"
            />
          </div>
        </div>
        {passwordMessage && (
          <div className="text-xs text-muted-foreground" data-testid="account-password-message">{passwordMessage}</div>
        )}
        <button
          type="button"
          onClick={handlePasswordSave}
          className="h-10 px-4 rounded-md border text-sm"
          data-testid="account-password-save"
        >
          Şifreyi Güncelle
        </button>
      </div>

      <div className="rounded-lg border bg-white p-6" data-testid="account-gdpr-card">
        <div className="text-sm font-semibold">Veri Dışa Aktarma (Opsiyonel)</div>
        <p className="text-xs text-muted-foreground mt-1">GDPR export entegrasyonu yapılmadı.</p>
        <button
          type="button"
          disabled
          className="mt-3 h-9 px-4 rounded-md border text-sm disabled:opacity-60"
          data-testid="account-gdpr-export"
        >
          Veri Dışa Aktar (MOCKED)
        </button>
      </div>
    </div>
  );
}
