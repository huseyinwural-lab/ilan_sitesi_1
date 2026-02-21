import React, { useEffect, useMemo, useState } from 'react';
import QRCode from 'qrcode';
import { ErrorState, LoadingState } from '@/components/account/AccountStates';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const buildStrength = (value) => {
  let score = 0;
  if (value.length >= 8) score += 1;
  if (/[A-Z]/.test(value)) score += 1;
  if (/[0-9]/.test(value)) score += 1;
  if (/[^A-Za-z0-9]/.test(value)) score += 1;
  if (score <= 1) return { label: 'Zayıf', color: 'text-rose-600' };
  if (score === 2) return { label: 'Orta', color: 'text-amber-600' };
  if (score === 3) return { label: 'İyi', color: 'text-emerald-600' };
  return { label: 'Güçlü', color: 'text-emerald-700' };
};

const urlBase64ToUint8Array = (base64String) => {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
};

export default function AccountProfile() {
  const [profile, setProfile] = useState({
    full_name: '',
    phone: '',
    locale: 'tr',
    country_code: 'DE',
    display_name_mode: 'full_name',
  });
  const [prefs, setPrefs] = useState({ push_enabled: true, email_enabled: true });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [saved, setSaved] = useState(false);
  const [passwordForm, setPasswordForm] = useState({ current: '', next: '', confirm: '' });
  const [passwordMessage, setPasswordMessage] = useState('');
  const [pushSupported, setPushSupported] = useState(false);
  const [pushStatus, setPushStatus] = useState('unknown');
  const [pushMessage, setPushMessage] = useState('');
  const [twoFactorStatus, setTwoFactorStatus] = useState({ enabled: false, configured: false });
  const [setupData, setSetupData] = useState(null);
  const [qrDataUrl, setQrDataUrl] = useState('');
  const [totpCode, setTotpCode] = useState('');
  const [disableCode, setDisableCode] = useState('');
  const [twoFactorMessage, setTwoFactorMessage] = useState('');

  const strength = useMemo(() => buildStrength(passwordForm.next || ''), [passwordForm.next]);

  const fetchProfile = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/v1/users/me/profile`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      });
      if (!res.ok) {
        throw new Error('Profil yüklenemedi');
      }
      const data = await res.json();
      setProfile({
        full_name: data.full_name || '',
        phone: data.phone || '',
        locale: data.locale || 'tr',
        country_code: data.country_code || 'DE',
        display_name_mode: data.display_name_mode || 'full_name',
      });
      setPrefs(data.notification_prefs || { push_enabled: true, email_enabled: true });
      setTwoFactorStatus({
        enabled: Boolean(data.totp_enabled),
        configured: Boolean(data.totp_enabled),
      });
      setError('');
    } catch (err) {
      setError('Profil yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const fetchTwoFactorStatus = async () => {
    try {
      const res = await fetch(`${API}/users/me/2fa/status`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      });
      if (!res.ok) {
        return;
      }
      const data = await res.json();
      setTwoFactorStatus({
        enabled: Boolean(data.enabled),
        configured: Boolean(data.configured),
      });
    } catch (err) {
      // ignore
    }
  };

  const loadPushStatus = async () => {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
      setPushSupported(false);
      setPushStatus('unsupported');
      return;
    }
    setPushSupported(true);
    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();
      setPushStatus(subscription ? 'active' : 'inactive');
    } catch (err) {
      setPushStatus('inactive');
    }
  };

  useEffect(() => {
    fetchProfile();
    fetchTwoFactorStatus();
    loadPushStatus();
  }, []);

  const handleProfileSave = async () => {
    try {
      const res = await fetch(`${API}/users/me`, {
        method: 'PUT',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          full_name: profile.full_name,
          phone: profile.phone,
          locale: profile.locale,
          country_code: profile.country_code,
          display_name_mode: profile.display_name_mode,
          notification_prefs: prefs,
        }),
      });
      if (!res.ok) {
        throw new Error('Profil güncellenemedi');
      }
      setSaved(true);
      setTimeout(() => setSaved(false), 1500);
    } catch (err) {
      setError('Profil güncellenemedi');
    }
  };

  const handleTwoFactorSetup = async () => {
    setTwoFactorMessage('');
    try {
      const res = await fetch(`${API}/users/me/2fa/setup`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      });
      if (!res.ok) {
        throw new Error('2FA setup başarısız');
      }
      const data = await res.json();
      setSetupData(data);
      if (data.otpauth_url) {
        const qrUrl = await QRCode.toDataURL(data.otpauth_url);
        setQrDataUrl(qrUrl);
      }
      setTwoFactorMessage('Kurulum hazır. Doğrulama kodunu girin.');
    } catch (err) {
      setTwoFactorMessage('2FA kurulumu başarısız');
    }
  };

  const handleTwoFactorVerify = async () => {
    setTwoFactorMessage('');
    try {
      const res = await fetch(`${API}/users/me/2fa/verify`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code: totpCode }),
      });
      if (!res.ok) {
        throw new Error('Doğrulama başarısız');
      }
      setTwoFactorStatus({ enabled: true, configured: true });
      setSetupData(null);
      setQrDataUrl('');
      setTotpCode('');
      setTwoFactorMessage('2FA etkinleştirildi.');
    } catch (err) {
      setTwoFactorMessage('Doğrulama başarısız');
    }
  };

  const handleTwoFactorDisable = async () => {
    setTwoFactorMessage('');
    try {
      const res = await fetch(`${API}/users/me/2fa/disable`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code: disableCode }),
      });
      if (!res.ok) {
        throw new Error('Devre dışı başarısız');
      }
      setTwoFactorStatus({ enabled: false, configured: false });
      setDisableCode('');
      setTwoFactorMessage('2FA devre dışı bırakıldı.');
    } catch (err) {
      setTwoFactorMessage('2FA devre dışı bırakılamadı.');
    }
  };

  const handlePushSubscribe = async () => {
    setPushMessage('');
    try {
      const permission = await Notification.requestPermission();
      if (permission !== 'granted') {
        setPushStatus('denied');
        setPushMessage('Bildirim izni verilmedi.');
        return;
      }
      const keyRes = await fetch(`${API}/v1/push/vapid-public-key`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      });
      if (!keyRes.ok) {
        throw new Error('VAPID anahtarı alınamadı');
      }
      const keyData = await keyRes.json();
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(keyData.public_key),
      });
      const payload = subscription.toJSON();
      const res = await fetch(`${API}/v1/push/subscribe`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        throw new Error('Abonelik kaydedilemedi');
      }
      setPushStatus('active');
      setPrefs((prev) => ({ ...prev, push_enabled: true }));
      setPushMessage('Web push aktif.');
    } catch (err) {
      setPushStatus('inactive');
      setPushMessage('Web push etkinleştirilemedi.');
    }
  };

  const handlePushUnsubscribe = async () => {
    setPushMessage('');
    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();
      if (subscription) {
        await fetch(`${API}/v1/push/unsubscribe`, {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ endpoint: subscription.endpoint }),
        });
        await subscription.unsubscribe();
      }
      setPushStatus('inactive');
      setPrefs((prev) => ({ ...prev, push_enabled: false }));
      setPushMessage('Web push devre dışı.');
    } catch (err) {
      setPushMessage('Web push devre dışı bırakılamadı.');
    }
  };

  const handlePasswordSave = async () => {
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
    try {
      const res = await fetch(`${API}/users/change-password`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ current_password: passwordForm.current, new_password: passwordForm.next }),
      });
      if (!res.ok) {
        throw new Error('Şifre güncellenemedi');
      }
      setPasswordMessage('Şifre güncellendi.');
      setPasswordForm({ current: '', next: '', confirm: '' });
    } catch (err) {
      setPasswordMessage('Şifre güncellenemedi.');
    }
  };



  if (loading) {
    return <LoadingState label="Profil yükleniyor..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchProfile} testId="account-profile-error" />;
  }

  return (
    <div className="space-y-6" data-testid="account-profile">
      <div>
        <h1 className="text-2xl font-bold" data-testid="account-profile-title">Hesap Ayarları</h1>
        <p className="text-sm text-muted-foreground" data-testid="account-profile-subtitle">
          Profil bilgilerinizi yönetin.
        </p>
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
            <label className="text-xs text-muted-foreground">Dil</label>
            <select
              value={profile.locale}
              onChange={(e) => setProfile((prev) => ({ ...prev, locale: e.target.value }))}
              className="mt-1 h-10 w-full rounded-md border px-3 text-sm"
              data-testid="account-profile-locale"
            >
              <option value="tr">Türkçe</option>
              <option value="de">Deutsch</option>
              <option value="fr">Français</option>
              <option value="nl">Nederlands</option>
              <option value="it">Italiano</option>
              <option value="en">English</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-muted-foreground">Görünen Ad</label>
            <select
              value={profile.display_name_mode}
              onChange={(e) => setProfile((prev) => ({ ...prev, display_name_mode: e.target.value }))}
              className="mt-1 h-10 w-full rounded-md border px-3 text-sm"
              data-testid="account-profile-display-name-mode"
            >
              <option value="full_name">Ad Soyad</option>
              <option value="initials">Baş harfler</option>
              <option value="hidden">Gizli</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-muted-foreground">Ülke</label>
            <select
              value={profile.country_code}
              onChange={(e) => setProfile((prev) => ({ ...prev, country_code: e.target.value }))}
              className="mt-1 h-10 w-full rounded-md border px-3 text-sm"
              data-testid="account-profile-country"
            >
              <option value="DE">Almanya (DE)</option>
              <option value="FR">Fransa (FR)</option>
              <option value="NL">Hollanda (NL)</option>
              <option value="IT">İtalya (IT)</option>
              <option value="AT">Avusturya (AT)</option>
              <option value="CH">İsviçre (CH)</option>
            </select>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <label className="flex items-center gap-2 text-sm" data-testid="account-profile-push-pref">
            <input
              type="checkbox"
              checked={prefs.push_enabled}
              onChange={(e) => setPrefs((prev) => ({ ...prev, push_enabled: e.target.checked }))}
            />
            Web push bildirimleri
          </label>
          <label className="flex items-center gap-2 text-sm" data-testid="account-profile-email-pref">
            <input
              type="checkbox"
              checked={prefs.email_enabled}
              onChange={(e) => setPrefs((prev) => ({ ...prev, email_enabled: e.target.checked }))}
            />
            E-posta bildirimleri
          </label>
        </div>
        {pushSupported && (
          <div className="rounded-md border bg-slate-50 p-4 text-sm" data-testid="account-push-panel">
            <div className="font-semibold">Web Push Durumu</div>
            <div className="text-xs text-muted-foreground" data-testid="account-push-status">Durum: {pushStatus}</div>
            {pushMessage && (
              <div className="text-xs text-muted-foreground mt-1" data-testid="account-push-message">{pushMessage}</div>
            )}
            <div className="mt-3 flex gap-2">
              <button
                type="button"
                onClick={handlePushSubscribe}
                className="h-9 px-3 rounded-md border text-xs"
                data-testid="account-push-enable"
              >
                Web Push Aktifleştir
              </button>
              <button
                type="button"
                onClick={handlePushUnsubscribe}
                className="h-9 px-3 rounded-md border text-xs"
                data-testid="account-push-disable"
              >
                Web Push Kapat
              </button>
            </div>
          </div>
        )}
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
            <div className={`text-xs mt-1 ${strength.color}`} data-testid="account-password-strength">{strength.label}</div>
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

      <div className="rounded-lg border bg-white p-6 space-y-4" data-testid="account-2fa-card">
        <div className="text-sm font-semibold">İki Faktörlü Doğrulama (2FA)</div>
        <div className="text-xs text-muted-foreground" data-testid="account-2fa-status">
          Durum: {twoFactorStatus.enabled ? 'Etkin' : 'Kapalı'}
        </div>
        {twoFactorMessage && (
          <div className="text-xs text-muted-foreground" data-testid="account-2fa-message">{twoFactorMessage}</div>
        )}
        {!twoFactorStatus.enabled && !setupData && (
          <button
            type="button"
            onClick={handleTwoFactorSetup}
            className="h-9 px-4 rounded-md border text-sm"
            data-testid="account-2fa-setup"
          >
            2FA Kurulumu Başlat
          </button>
        )}
        {setupData && (
          <div className="space-y-3" data-testid="account-2fa-setup-panel">
            {qrDataUrl && (
              <img src={qrDataUrl} alt="QR" className="h-36 w-36" data-testid="account-2fa-qr" />
            )}
            <div className="text-xs text-muted-foreground" data-testid="account-2fa-secret">
              Secret: {setupData.secret}
            </div>
            <div className="text-xs text-muted-foreground" data-testid="account-2fa-recovery">
              Recovery codes: {setupData.recovery_codes?.join(', ')}
            </div>
            <div>
              <label className="text-xs text-muted-foreground">Doğrulama Kodu</label>
              <input
                value={totpCode}
                onChange={(e) => setTotpCode(e.target.value)}
                className="mt-1 h-10 w-full rounded-md border px-3 text-sm"
                data-testid="account-2fa-code"
              />
            </div>
            <button
              type="button"
              onClick={handleTwoFactorVerify}
              className="h-9 px-4 rounded-md border text-sm"
              data-testid="account-2fa-verify"
            >
              2FA Etkinleştir
            </button>
          </div>
        )}
        {twoFactorStatus.enabled && (
          <div className="space-y-3" data-testid="account-2fa-disable-panel">
            <label className="text-xs text-muted-foreground">Kod veya Recovery Code</label>
            <input
              value={disableCode}
              onChange={(e) => setDisableCode(e.target.value)}
              className="mt-1 h-10 w-full rounded-md border px-3 text-sm"
              data-testid="account-2fa-disable-code"
            />
            <button
              type="button"
              onClick={handleTwoFactorDisable}
              className="h-9 px-4 rounded-md border text-sm"
              data-testid="account-2fa-disable"
            >
              2FA Devre Dışı Bırak
            </button>
          </div>
        )}
      </div>


    </div>
  );
}
