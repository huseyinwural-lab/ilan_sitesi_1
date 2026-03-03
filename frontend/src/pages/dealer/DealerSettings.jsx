import React, { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { loadStripe } from '@stripe/stripe-js';
import { CardElement, Elements, useElements, useStripe } from '@stripe/react-stripe-js';
import { useLanguage } from '@/contexts/LanguageContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const sectionList = [
  { key: 'profile' },
  { key: 'address' },
  { key: 'security' },
  { key: 'store_users' },
  { key: 'packages_services' },
  { key: 'saved_cards' },
  { key: 'invoices' },
  { key: 'account_movements' },
  { key: 'notifications' },
  { key: 'blocked' },
];

const sectionLabelFallbacks = {
  profile: 'Hesap Bilgileri',
  address: 'Mağaza Bilgileri',
  security: 'Güvenlik',
  store_users: 'Kullanıcı Listesi / Ekle',
  packages_services: 'Paket ve Hizmetler',
  saved_cards: 'Kayıtlı Kartlarım',
  invoices: 'Faturalar',
  account_movements: 'Hesap Hareketleri',
  notifications: 'Bildirim Tercihleri',
  blocked: 'Engellenen Hesaplar',
};

const defaultProfile = {
  company_name: '',
  authorized_person: '',
  contact_email: '',
  contact_phone: '',
  address_street: '',
  address_zip: '',
  address_city: '',
  address_country: 'TR',
  logo_url: '',
};

const defaultPrefs = {
  push_enabled: true,
  email_enabled: true,
  message_email_enabled: true,
  marketing_email_enabled: false,
  read_receipt_enabled: true,
  sms_enabled: false,
  recovery_email: '',
  display_name_mode: 'full_name',
  profile_photo_url: '',
  notification_matrix: { listing: true, store: true, favorite: true, native_ad: false, virtual_tour: false },
  electronic_consent: { sms: false, email: false, call: false },
  active_sessions: [],
};

const formatDate = (value) => {
  if (!value) return '-';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return '-';
  return parsed.toLocaleString('tr-TR');
};

const cardElementOptions = {
  style: {
    base: {
      color: '#0f172a',
      fontSize: '14px',
      fontFamily: 'ui-sans-serif, system-ui, -apple-system, sans-serif',
      '::placeholder': {
        color: '#94a3b8',
      },
    },
    invalid: {
      color: '#b91c1c',
    },
  },
  hidePostalCode: true,
};

function DealerStripeCardCaptureForm({
  holderName,
  setHolderName,
  isDefault,
  setIsDefault,
  autoPaymentEnabled,
  setAutoPaymentEnabled,
  billingEmail,
  submitting,
  onSubmitTokenizedCard,
}) {
  const { t } = useLanguage();
  const stripe = useStripe();
  const elements = useElements();
  const [formError, setFormError] = useState('');

  return (
    <form
      className="grid gap-3 md:grid-cols-2"
      data-testid="dealer-settings-saved-card-form"
      onSubmit={async (event) => {
        event.preventDefault();
        setFormError('');
        if (!stripe || !elements) {
          setFormError(t('dealer.settings.cards.form_not_ready', 'Stripe formu henüz hazır değil.'));
          return;
        }
        if (!holderName.trim()) {
          setFormError(t('dealer.settings.cards.holder_required', 'Kart üzerindeki isim zorunludur.'));
          return;
        }

        const cardElement = elements.getElement(CardElement);
        if (!cardElement) {
          setFormError(t('dealer.settings.cards.field_missing', 'Kart alanı bulunamadı.'));
          return;
        }

        const result = await stripe.createPaymentMethod({
          type: 'card',
          card: cardElement,
          billing_details: {
            name: holderName,
            email: billingEmail || undefined,
          },
        });

        if (result.error) {
          setFormError(result.error.message || t('dealer.settings.cards.validation_failed', 'Kart bilgisi doğrulanamadı.'));
          return;
        }

        const pm = result.paymentMethod;
        if (!pm || !pm.id || !pm.card) {
          setFormError(t('dealer.settings.cards.payment_method_failed', 'Ödeme yöntemi oluşturulamadı.'));
          return;
        }

        await onSubmitTokenizedCard({
          holder_name: holderName.trim(),
          payment_method_id: pm.id,
          last4: pm.card.last4,
          expiry_month: Number(pm.card.exp_month),
          expiry_year: Number(pm.card.exp_year),
          brand: pm.card.brand || 'unknown',
          is_default: Boolean(isDefault),
          auto_payment_enabled: Boolean(autoPaymentEnabled),
        });

        cardElement.clear();
      }}
    >
      <input
        value={holderName}
        onChange={(event) => setHolderName(event.target.value)}
        placeholder={t('dealer.settings.cards.holder_placeholder', 'Kart Üzerindeki İsim')}
        className="h-10 rounded-md border border-slate-300 px-3 text-sm"
        data-testid="dealer-settings-card-holder-name"
        required
      />
      <div className="rounded-md border border-slate-300 bg-white px-3 py-2" data-testid="dealer-settings-card-element-wrap">
        <CardElement options={cardElementOptions} data-testid="dealer-settings-card-element" />
      </div>
      <label className="flex items-center gap-2 text-sm" data-testid="dealer-settings-card-default-wrap"><input type="checkbox" checked={Boolean(isDefault)} onChange={(event) => setIsDefault(event.target.checked)} data-testid="dealer-settings-card-is-default" /> {t('dealer.settings.cards.default', 'Varsayılan kart')}</label>
      <label className="flex items-center gap-2 text-sm" data-testid="dealer-settings-card-auto-pay-wrap"><input type="checkbox" checked={Boolean(autoPaymentEnabled)} onChange={(event) => setAutoPaymentEnabled(event.target.checked)} data-testid="dealer-settings-card-auto-pay" /> {t('dealer.settings.cards.auto_pay', 'Otomatik ödeme onayı')}</label>
      {formError ? <div className="md:col-span-2 rounded-md border border-rose-200 bg-rose-50 p-2 text-xs text-rose-700" data-testid="dealer-settings-card-form-error">{formError}</div> : null}
      <button type="submit" disabled={submitting || !stripe} className="h-10 rounded-md bg-slate-900 px-4 text-sm font-semibold text-white md:col-span-2 disabled:opacity-60" data-testid="dealer-settings-card-submit">{submitting ? t('auth.register.submit_loading', 'Kaydediliyor...') : t('dealer.settings.cards.submit', 'Stripe ile Kart Kaydet')}</button>
    </form>
  );
}

export default function DealerSettings() {
  const { t } = useLanguage();
  const [searchParams, setSearchParams] = useSearchParams();
  const requestedSection = (searchParams.get('section') || '').toLowerCase();
  const section = sectionList.some((item) => item.key === requestedSection) ? requestedSection : 'profile';

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [profile, setProfile] = useState(defaultProfile);
  const [prefs, setPrefs] = useState(defaultPrefs);
  const [blockedAccounts, setBlockedAccounts] = useState([]);
  const [security, setSecurity] = useState({ two_factor_enabled: false, last_login: null });

  const [storeUsers, setStoreUsers] = useState([]);
  const [packages, setPackages] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [payments, setPayments] = useState([]);
  const [savedCards, setSavedCards] = useState([]);
  const [paymentApplications, setPaymentApplications] = useState([]);
  const [stripePublishableKey, setStripePublishableKey] = useState('');
  const [stripeLoading, setStripeLoading] = useState(true);

  const [passwordForm, setPasswordForm] = useState({ current_password: '', new_password: '', confirm_password: '' });
  const [storeUserForm, setStoreUserForm] = useState({ full_name: '', email: '', password: '', role: 'staff' });
  const [cardForm, setCardForm] = useState({ holder_name: '', is_default: false, auto_payment_enabled: false });
  const [cardSaving, setCardSaving] = useState(false);
  const [blockedEmailInput, setBlockedEmailInput] = useState('');
  const [applicationForm, setApplicationForm] = useState({ application_type: 'auto_payment', note: '', auto_payment_day: '', iban: '', file: null });

  const requestJson = async (url, options = {}) => {
    const token = localStorage.getItem('access_token');
    const res = await fetch(url, {
      ...options,
      headers: {
        Authorization: `Bearer ${token}`,
        ...(options.headers || {}),
      },
    });
    const payload = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(payload?.detail || payload?.message || t('dealer.settings.errors.operation_failed', 'İşlem başarısız'));
    return payload;
  };

  const fetchAll = async () => {
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      const token = localStorage.getItem('access_token');
      const [
        profileRes,
        prefRes,
        usersRes,
        pkgRes,
        invoiceRes,
        paymentRes,
        cardsRes,
        appRes,
        stripeConfigRes,
      ] = await Promise.all([
        fetch(`${API}/dealer/settings/profile`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API}/dealer/settings/preferences`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API}/dealer/consultant-tracking`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API}/pricing/packages`),
        fetch(`${API}/dealer/invoices`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API}/dealer/payments`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API}/dealer/settings/saved-cards`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API}/dealer/settings/payment-applications`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API}/payments/runtime-config`),
      ]);

      const profilePayload = await profileRes.json().catch(() => ({}));
      const prefPayload = await prefRes.json().catch(() => ({}));
      const usersPayload = await usersRes.json().catch(() => ({}));
      const pkgPayload = await pkgRes.json().catch(() => ({}));
      const invoicePayload = await invoiceRes.json().catch(() => ({}));
      const paymentPayload = await paymentRes.json().catch(() => ({}));
      const cardsPayload = await cardsRes.json().catch(() => ({}));
      const appPayload = await appRes.json().catch(() => ({}));
      const stripeConfigPayload = await stripeConfigRes.json().catch(() => ({}));

      if (!profileRes.ok) throw new Error(profilePayload?.detail || t('dealer.settings.errors.profile_fetch_failed', 'Profil alınamadı'));
      if (!prefRes.ok) throw new Error(prefPayload?.detail || t('dealer.settings.errors.preferences_fetch_failed', 'Tercihler alınamadı'));
      if (!usersRes.ok) throw new Error(usersPayload?.detail || t('dealer.settings.errors.users_fetch_failed', 'Kullanıcı listesi alınamadı'));
      if (!pkgRes.ok) throw new Error(pkgPayload?.detail || t('dealer.settings.errors.packages_fetch_failed', 'Paketler alınamadı'));
      if (!invoiceRes.ok) throw new Error(invoicePayload?.detail || t('dealer.settings.errors.invoices_fetch_failed', 'Faturalar alınamadı'));
      if (!paymentRes.ok) throw new Error(paymentPayload?.detail || t('dealer.settings.errors.movements_fetch_failed', 'Hareketler alınamadı'));
      if (!cardsRes.ok) throw new Error(cardsPayload?.detail || t('dealer.settings.errors.cards_fetch_failed', 'Kartlar alınamadı'));
      if (!appRes.ok) throw new Error(appPayload?.detail || t('dealer.settings.errors.applications_fetch_failed', 'Başvurular alınamadı'));
      if (!stripeConfigRes.ok) throw new Error(stripeConfigPayload?.detail || t('dealer.settings.errors.stripe_config_failed', 'Stripe ayarları alınamadı'));

      setProfile({ ...defaultProfile, ...(profilePayload.profile || {}) });
      setPrefs({ ...defaultPrefs, ...(prefPayload.notification_prefs || {}) });
      setBlockedAccounts(Array.isArray(prefPayload.blocked_accounts) ? prefPayload.blocked_accounts : []);
      setSecurity(prefPayload.security || { two_factor_enabled: false, last_login: null });
      setStoreUsers(Array.isArray(usersPayload.consultants) ? usersPayload.consultants : []);
      setPackages(Array.isArray(pkgPayload.packages) ? pkgPayload.packages : []);
      setInvoices(Array.isArray(invoicePayload.items) ? invoicePayload.items : []);
      setPayments(Array.isArray(paymentPayload.items) ? paymentPayload.items : []);
      setSavedCards(Array.isArray(cardsPayload.items) ? cardsPayload.items : []);
      setPaymentApplications(Array.isArray(appPayload.items) ? appPayload.items : []);
      setStripePublishableKey((stripeConfigPayload?.publishable_key || '').trim());
    } catch (requestError) {
      setError(requestError?.message || t('dealer.settings.errors.account_data_failed', 'Hesap verisi alınamadı'));
    } finally {
      setLoading(false);
      setStripeLoading(false);
    }
  };

  const stripePromise = useMemo(
    () => (stripePublishableKey ? loadStripe(stripePublishableKey) : null),
    [stripePublishableKey],
  );

  useEffect(() => {
    fetchAll();
  }, []);

  useEffect(() => {
    if (!requestedSection) {
      setSearchParams({ section }, { replace: true });
    }
  }, [requestedSection]);

  const saveProfile = async (event) => {
    event.preventDefault();
    setError('');
    setSuccess('');
    try {
      await requestJson(`${API}/dealer/settings/profile`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profile),
      });
      await requestJson(`${API}/dealer/settings/preferences`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notification_prefs: prefs }),
      });
      setSuccess(t('dealer.settings.save_success_profile', 'Profil bilgileri kaydedildi.'));
      await fetchAll();
    } catch (requestError) {
      setError(requestError?.message || t('dealer.settings.errors.profile_save_failed', 'Profil kaydedilemedi'));
    }
  };

  const savePreferences = async () => {
    setError('');
    setSuccess('');
    try {
      await requestJson(`${API}/dealer/settings/preferences`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notification_prefs: { ...prefs, blocked_accounts: blockedAccounts } }),
      });
      setSuccess(t('dealer.settings.save_success_preferences', 'Bildirim tercihleri kaydedildi.'));
      await fetchAll();
    } catch (requestError) {
      setError(requestError?.message || t('dealer.settings.errors.preferences_save_failed', 'Tercihler kaydedilemedi'));
    }
  };

  return (
    <div className="space-y-4 bg-white" data-testid="dealer-settings-page">
      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white" data-testid="dealer-settings-sections-card">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-4 py-3" data-testid="dealer-settings-header">
          <div>
            <h1 className="text-2xl font-semibold text-black" data-testid="dealer-settings-title">{t('dealer.settings.title', 'Hesabım')}</h1>
            <p className="text-sm font-medium text-slate-700" data-testid="dealer-settings-subtitle">{t('dealer.settings.subtitle', 'Hesap bilgileri, güvenlik, ödeme ve bildirim yönetimi.')}</p>
          </div>
          <button type="button" onClick={fetchAll} className="h-9 rounded-md border border-slate-300 bg-white px-3 text-sm font-semibold text-black" data-testid="dealer-settings-refresh-button">{t('dealer.settings.refresh', 'Yenile')}</button>
        </div>

        <div className="bg-white p-4" data-testid="dealer-settings-right-panel">
          <div className="mb-4 space-y-2" data-testid="dealer-settings-section-tabs-wrap">
            <div className="text-xs font-semibold uppercase tracking-wide text-slate-500" data-testid="dealer-settings-section-nav-title">
              {t('dealer.settings.section_nav_title', 'Hesap bölümleri')}
            </div>
            <div className="flex flex-wrap items-center gap-2" data-testid="dealer-settings-section-tabs">
              {sectionList.map((item) => (
                <button
                  key={item.key}
                  type="button"
                  onClick={() => setSearchParams({ section: item.key })}
                  className={`rounded-md border px-3 py-1.5 text-left text-sm font-semibold transition ${section === item.key ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-200 bg-white text-black hover:bg-slate-50'}`}
                  data-testid={`dealer-settings-section-tab-${item.key}`}
                >
                  {t(`dealer.settings.sections.${item.key}`, sectionLabelFallbacks[item.key] || item.key)}
                </button>
              ))}
            </div>
          </div>

          {loading ? <div className="rounded-md border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500" data-testid="dealer-settings-loading">{t('dealer.settings.loading', 'Yükleniyor...')}</div> : null}
            {error ? <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700" data-testid="dealer-settings-error">{error}</div> : null}
            {success ? <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700" data-testid="dealer-settings-success">{success}</div> : null}

            {!loading && (section === 'profile' || section === 'address') ? (
              <form onSubmit={saveProfile} className="space-y-3" data-testid="dealer-settings-profile-form">
                <div className="grid gap-3 md:grid-cols-2" data-testid="dealer-settings-grid">
                  {(section === 'profile'
                    ? ['company_name', 'authorized_person', 'contact_email', 'contact_phone', 'logo_url']
                    : ['address_street', 'address_zip', 'address_city', 'address_country']
                  ).map((field) => (
                    <input key={field} value={profile[field] || ''} onChange={(event) => setProfile((prev) => ({ ...prev, [field]: event.target.value }))} placeholder={field} className="h-10 rounded-md border border-slate-300 px-3 text-sm" data-testid={`dealer-settings-field-${field}`} />
                  ))}
                </div>
                {section === 'profile' ? (
                  <div className="grid gap-3 md:grid-cols-2" data-testid="dealer-settings-profile-extra-grid">
                    <input value={prefs.profile_photo_url || ''} onChange={(event) => setPrefs((prev) => ({ ...prev, profile_photo_url: event.target.value }))} placeholder="Profil Fotoğraf URL" className="h-10 rounded-md border border-slate-300 px-3 text-sm" data-testid="dealer-settings-profile-photo-url" />
                    <select value={prefs.display_name_mode || 'full_name'} onChange={(event) => setPrefs((prev) => ({ ...prev, display_name_mode: event.target.value }))} className="h-10 rounded-md border border-slate-300 px-3 text-sm" data-testid="dealer-settings-display-name-mode"><option value="full_name">Profil</option><option value="initials">İsim Baş Harfleri</option><option value="anonymous">Anonim</option></select>
                  </div>
                ) : null}
                <button type="submit" className="h-9 rounded-md bg-slate-900 px-4 text-sm font-semibold text-white" data-testid="dealer-settings-save-button">{t('dealer.settings.save', 'Kaydet')}</button>
              </form>
            ) : null}

            {!loading && section === 'security' ? (
              <div className="space-y-3" data-testid="dealer-settings-security-section">
                <div className="rounded-md border border-slate-200 bg-slate-50 p-3" data-testid="dealer-settings-security-summary">
                  <div className="text-xs font-semibold">2FA: {security.two_factor_enabled ? t('dealer.settings.security_2fa_active', 'Aktif') : t('dealer.settings.security_2fa_inactive', 'Pasif')}</div>
                  <div className="mt-1 text-xs text-slate-600">{t('dealer.settings.security_last_login', 'Son Giriş')}: {formatDate(security.last_login)}</div>
                </div>
                <form
                  className="grid gap-3 md:grid-cols-2"
                  data-testid="dealer-settings-password-form"
                  onSubmit={async (event) => {
                    event.preventDefault();
                    setError('');
                    setSuccess('');
                    if ((passwordForm.new_password || '').length < 8 || passwordForm.new_password !== passwordForm.confirm_password) {
                      setError('Şifre kuralları sağlanmıyor.');
                      return;
                    }
                    try {
                      await requestJson(`${API}/dealer/settings/change-password`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ current_password: passwordForm.current_password, new_password: passwordForm.new_password }),
                      });
                      setPasswordForm({ current_password: '', new_password: '', confirm_password: '' });
                      setSuccess(t('dealer.settings.security.password_updated', 'Şifre güncellendi.'));
                    } catch (requestError) {
                      setError(requestError?.message || 'Şifre güncellenemedi');
                    }
                  }}
                >
                  <input type="password" value={passwordForm.current_password} onChange={(event) => setPasswordForm((prev) => ({ ...prev, current_password: event.target.value }))} placeholder="Mevcut Şifre" className="h-10 rounded-md border border-slate-300 px-3 text-sm" data-testid="dealer-settings-current-password-input" />
                  <input type="password" value={passwordForm.new_password} onChange={(event) => setPasswordForm((prev) => ({ ...prev, new_password: event.target.value }))} placeholder="Yeni Şifre" className="h-10 rounded-md border border-slate-300 px-3 text-sm" data-testid="dealer-settings-new-password-input" />
                  <input type="password" value={passwordForm.confirm_password} onChange={(event) => setPasswordForm((prev) => ({ ...prev, confirm_password: event.target.value }))} placeholder="Yeni Şifre Tekrar" className="h-10 rounded-md border border-slate-300 px-3 text-sm md:col-span-2" data-testid="dealer-settings-confirm-password-input" />
                  <input type="email" value={prefs.recovery_email || ''} onChange={(event) => setPrefs((prev) => ({ ...prev, recovery_email: event.target.value }))} placeholder="Kurtarma E-Postası" className="h-10 rounded-md border border-slate-300 px-3 text-sm md:col-span-2" data-testid="dealer-settings-recovery-email" />
                  <button type="submit" className="h-9 rounded-md bg-slate-900 px-4 text-sm font-semibold text-white md:col-span-2" data-testid="dealer-settings-password-save-button">{t('dealer.settings.security.save_button', 'Güvenlik Bilgilerini Kaydet')}</button>
                </form>

                <div className="rounded-md border border-slate-200 p-3" data-testid="dealer-settings-active-sessions">
                  <div className="text-xs font-semibold text-slate-700">{t('dealer.settings.security.active_sessions', 'Aktif Oturumlar')}</div>
                  <div className="mt-2 space-y-2">
                    {(prefs.active_sessions || []).length === 0 ? <div className="text-xs text-slate-500" data-testid="dealer-settings-active-sessions-empty">{t('dealer.settings.security.no_active_sessions', 'Aktif cihaz kaydı yok.')}</div> : (prefs.active_sessions || []).map((row) => (
                      <div key={row.session_id} className="rounded border border-slate-200 p-2 text-xs" data-testid={`dealer-settings-session-${row.session_id}`}>
                        {row.device} / {row.ip} / {formatDate(row.last_seen_at)}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : null}

            {!loading && section === 'store_users' ? (
              <div className="space-y-3" data-testid="dealer-settings-store-users-section">
                <form
                  className="grid gap-3 md:grid-cols-2"
                  data-testid="dealer-settings-store-user-form"
                  onSubmit={async (event) => {
                    event.preventDefault();
                    setError('');
                    setSuccess('');
                    try {
                      await requestJson(`${API}/dealer/customers/store-users`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(storeUserForm),
                      });
                      setStoreUserForm({ full_name: '', email: '', password: '', role: 'staff' });
                      setSuccess(t('dealer.settings.users.added', 'Kullanıcı eklendi.'));
                      await fetchAll();
                    } catch (requestError) {
                      setError(requestError?.message || 'Kullanıcı eklenemedi');
                    }
                  }}
                >
                  <input value={storeUserForm.full_name} onChange={(event) => setStoreUserForm((prev) => ({ ...prev, full_name: event.target.value }))} placeholder="Ad Soyad" className="h-10 rounded-md border border-slate-300 px-3 text-sm" data-testid="dealer-settings-store-user-name" required />
                  <input type="email" value={storeUserForm.email} onChange={(event) => setStoreUserForm((prev) => ({ ...prev, email: event.target.value }))} placeholder="E-Posta" className="h-10 rounded-md border border-slate-300 px-3 text-sm" data-testid="dealer-settings-store-user-email" required />
                  <input type="password" value={storeUserForm.password} onChange={(event) => setStoreUserForm((prev) => ({ ...prev, password: event.target.value }))} placeholder="Şifre" className="h-10 rounded-md border border-slate-300 px-3 text-sm" data-testid="dealer-settings-store-user-password" required />
                  <select value={storeUserForm.role} onChange={(event) => setStoreUserForm((prev) => ({ ...prev, role: event.target.value }))} className="h-10 rounded-md border border-slate-300 px-3 text-sm" data-testid="dealer-settings-store-user-role"><option value="staff">Staff</option><option value="consultant">Consultant</option><option value="dealer_agent">Dealer Agent</option><option value="sales_agent">Sales Agent</option></select>
                  <button type="submit" className="h-10 rounded-md bg-slate-900 px-4 text-sm font-semibold text-white md:col-span-2" data-testid="dealer-settings-store-user-submit">Kullanıcı Ekle</button>
                </form>

                <div className="rounded-md border border-slate-200 overflow-x-auto" data-testid="dealer-settings-store-users-table-wrap">
                  <table className="w-full text-sm" data-testid="dealer-settings-store-users-table">
                    <thead className="bg-slate-50"><tr><th className="px-3 py-2 text-left">Ad Soyad</th><th className="px-3 py-2 text-left">E-Posta</th><th className="px-3 py-2 text-left">Rol</th><th className="px-3 py-2 text-left">Puan</th></tr></thead>
                    <tbody>{storeUsers.length === 0 ? <tr><td className="px-3 py-4 text-slate-600" colSpan={4} data-testid="dealer-settings-store-users-empty">Kayıt yok</td></tr> : storeUsers.map((row) => <tr key={row.consultant_id} className="border-t" data-testid={`dealer-settings-store-user-row-${row.consultant_id}`}><td className="px-3 py-2">{row.full_name}</td><td className="px-3 py-2">{row.email}</td><td className="px-3 py-2">{row.role}</td><td className="px-3 py-2">{row.service_score}</td></tr>)}</tbody>
                  </table>
                </div>
              </div>
            ) : null}

            {!loading && section === 'packages_services' ? (
              <div className="grid gap-3 md:grid-cols-2" data-testid="dealer-settings-packages-services-section">
                {packages.length === 0 ? <div className="rounded-md border border-slate-200 p-3 text-sm text-slate-600" data-testid="dealer-settings-packages-empty">{t('dealer.settings.packages.empty', 'Paket bulunamadı.')}</div> : packages.map((pkg) => (
                  <article key={pkg.id} className="rounded-md border border-slate-200 p-3" data-testid={`dealer-settings-package-card-${pkg.id}`}>
                    <div className="text-sm font-semibold text-slate-900">{pkg.name}</div>
                    <div className="mt-1 text-xs text-slate-600">{pkg.listing_quota || 0} ilan / {pkg.publish_days || 0} gün</div>
                    <div className="mt-2 text-lg font-semibold text-slate-900">{pkg.price_amount || 0} {pkg.currency || 'EUR'}</div>
                    <button type="button" className="mt-2 h-8 rounded-md border border-slate-300 px-3 text-xs font-semibold text-slate-900" data-testid={`dealer-settings-package-buy-${pkg.id}`}>{t('dealer.settings.packages.buy', 'Paket Satın Al')}</button>
                  </article>
                ))}
              </div>
            ) : null}

            {!loading && section === 'saved_cards' ? (
              <div className="space-y-3" data-testid="dealer-settings-saved-cards-section">
                <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-xs text-slate-700" data-testid="dealer-settings-card-pci-note">Kart numarası ve CVV sunucumuza gelmez. Stripe tokenization (Elements) kullanılır.</div>
                {stripeLoading ? <div className="rounded-md border border-slate-200 bg-white p-3 text-sm text-slate-600" data-testid="dealer-settings-card-stripe-loading">Stripe formu hazırlanıyor...</div> : null}
                {!stripeLoading && !stripePromise ? <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700" data-testid="dealer-settings-card-stripe-error">Stripe publishable key bulunamadı.</div> : null}
                {!stripeLoading && stripePromise ? (
                  <Elements stripe={stripePromise}>
                    <DealerStripeCardCaptureForm
                      holderName={cardForm.holder_name}
                      setHolderName={(value) => setCardForm((prev) => ({ ...prev, holder_name: value }))}
                      isDefault={cardForm.is_default}
                      setIsDefault={(value) => setCardForm((prev) => ({ ...prev, is_default: value }))}
                      autoPaymentEnabled={cardForm.auto_payment_enabled}
                      setAutoPaymentEnabled={(value) => setCardForm((prev) => ({ ...prev, auto_payment_enabled: value }))}
                      billingEmail={profile.contact_email}
                      submitting={cardSaving}
                      onSubmitTokenizedCard={async (payload) => {
                        setError('');
                        setSuccess('');
                        setCardSaving(true);
                        try {
                          await requestJson(`${API}/dealer/settings/saved-cards`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(payload),
                          });
                          setCardForm({ holder_name: '', is_default: false, auto_payment_enabled: false });
                          setSuccess(t('dealer.settings.cards.saved', 'Kart token ile kaydedildi.'));
                          await fetchAll();
                        } catch (requestError) {
                          setError(requestError?.message || t('dealer.settings.cards.save_error', 'Kart kaydedilemedi'));
                        } finally {
                          setCardSaving(false);
                        }
                      }}
                    />
                  </Elements>
                ) : null}

                <div className="rounded-md border border-slate-200 overflow-x-auto" data-testid="dealer-settings-saved-cards-table-wrap">
                  <table className="w-full text-sm" data-testid="dealer-settings-saved-cards-table">
                    <thead className="bg-slate-50"><tr><th className="px-3 py-2 text-left">Kart</th><th className="px-3 py-2 text-left">Sahip</th><th className="px-3 py-2 text-left">AutoPay</th><th className="px-3 py-2 text-right">İşlem</th></tr></thead>
                    <tbody>{savedCards.length === 0 ? <tr><td className="px-3 py-4 text-slate-600" colSpan={4} data-testid="dealer-settings-saved-cards-empty">{t('dealer.settings.cards.empty', 'Kart yok')}</td></tr> : savedCards.map((card) => <tr key={card.id} className="border-t" data-testid={`dealer-settings-card-row-${card.id}`}><td className="px-3 py-2">{card.brand} **** {card.last4}</td><td className="px-3 py-2">{card.holder_name}</td><td className="px-3 py-2">{card.auto_payment_enabled ? t('active', 'Açık') : t('inactive', 'Kapalı')}</td><td className="px-3 py-2 text-right"><button type="button" onClick={async () => { try { await requestJson(`${API}/dealer/settings/saved-cards/${card.id}`, { method: 'DELETE' }); setSuccess(t('dealer.settings.cards.deleted', 'Kart silindi.')); await fetchAll(); } catch (requestError) { setError(requestError?.message || t('dealer.settings.cards.delete_error', 'Kart silinemedi')); } }} className="h-8 rounded-md border border-slate-300 px-3 text-xs font-semibold" data-testid={`dealer-settings-card-delete-${card.id}`}>{t('delete', 'Sil')}</button></td></tr>)}</tbody>
                  </table>
                </div>

                <form
                  className="grid gap-3 rounded-md border border-slate-200 p-3 md:grid-cols-2"
                  data-testid="dealer-settings-payment-application-form"
                  onSubmit={async (event) => {
                    event.preventDefault();
                    setError('');
                    setSuccess('');
                    try {
                      const token = localStorage.getItem('access_token');
                      const form = new FormData();
                      form.append('application_type', applicationForm.application_type);
                      form.append('note', applicationForm.note || '');
                      if (applicationForm.auto_payment_day) form.append('auto_payment_day', applicationForm.auto_payment_day);
                      if (applicationForm.iban) form.append('iban', applicationForm.iban);
                      if (applicationForm.file) form.append('file', applicationForm.file);
                      const res = await fetch(`${API}/dealer/settings/payment-applications`, { method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: form });
                      const payload = await res.json().catch(() => ({}));
                      if (!res.ok) throw new Error(payload?.detail || t('dealer.settings.applications.save_error', 'Başvuru kaydedilemedi'));
                      setApplicationForm({ application_type: 'auto_payment', note: '', auto_payment_day: '', iban: '', file: null });
                      setSuccess(t('dealer.settings.applications.saved', 'Kurumsal başvuru oluşturuldu.'));
                      await fetchAll();
                    } catch (requestError) {
                      setError(requestError?.message || t('dealer.settings.applications.save_error', 'Başvuru kaydedilemedi'));
                    }
                  }}
                >
                  <select value={applicationForm.application_type} onChange={(event) => setApplicationForm((prev) => ({ ...prev, application_type: event.target.value }))} className="h-10 rounded-md border border-slate-300 px-3 text-sm" data-testid="dealer-settings-payment-application-type"><option value="auto_payment">Otomatik Ödeme Formu</option><option value="card_registration">Kart Kayıt Başvurusu</option><option value="corporate_document">Kurumsal Evrak</option></select>
                  <input value={applicationForm.auto_payment_day} onChange={(event) => setApplicationForm((prev) => ({ ...prev, auto_payment_day: event.target.value }))} placeholder="Otomatik Ödeme Günü (1-28)" className="h-10 rounded-md border border-slate-300 px-3 text-sm" data-testid="dealer-settings-payment-application-day" />
                  <input value={applicationForm.iban} onChange={(event) => setApplicationForm((prev) => ({ ...prev, iban: event.target.value }))} placeholder="IBAN" className="h-10 rounded-md border border-slate-300 px-3 text-sm" data-testid="dealer-settings-payment-application-iban" />
                  <input type="file" onChange={(event) => setApplicationForm((prev) => ({ ...prev, file: event.target.files?.[0] || null }))} className="h-10 rounded-md border border-slate-300 px-3 py-2 text-sm" data-testid="dealer-settings-payment-application-file" />
                  <textarea value={applicationForm.note} onChange={(event) => setApplicationForm((prev) => ({ ...prev, note: event.target.value }))} placeholder="Başvuru Notu" className="min-h-[80px] rounded-md border border-slate-300 px-3 py-2 text-sm md:col-span-2" data-testid="dealer-settings-payment-application-note" />
                  <button type="submit" className="h-10 rounded-md bg-slate-900 px-4 text-sm font-semibold text-white md:col-span-2" data-testid="dealer-settings-payment-application-submit">{t('dealer.settings.applications.submit', 'Kurumsal Alana Başvuru Gönder')}</button>
                </form>

                <div className="rounded-md border border-slate-200 p-3" data-testid="dealer-settings-payment-application-list-wrap">
                  <div className="text-xs font-semibold text-slate-700">{t('dealer.settings.applications.title', 'Başvurular')}</div>
                  <div className="mt-2 space-y-2">
                    {paymentApplications.length === 0 ? <div className="text-xs text-slate-500" data-testid="dealer-settings-payment-application-empty">{t('dealer.settings.applications.empty', 'Başvuru yok')}</div> : paymentApplications.map((row) => <div key={row.id} className="rounded border border-slate-200 p-2 text-xs" data-testid={`dealer-settings-payment-application-row-${row.id}`}>{row.application_type} / {row.status} / {formatDate(row.created_at)}</div>)}
                  </div>
                </div>
              </div>
            ) : null}

            {!loading && section === 'invoices' ? (
              <div className="rounded-md border border-slate-200 overflow-x-auto" data-testid="dealer-settings-invoices-table-wrap">
                <table className="w-full text-sm" data-testid="dealer-settings-invoices-table">
                  <thead className="bg-slate-50"><tr><th className="px-3 py-2 text-left">Fatura</th><th className="px-3 py-2 text-left">Durum</th><th className="px-3 py-2 text-left">Tutar</th><th className="px-3 py-2 text-left">Tarih</th></tr></thead>
                  <tbody>{invoices.length === 0 ? <tr><td className="px-3 py-4 text-slate-600" colSpan={4} data-testid="dealer-settings-invoices-empty">{t('dealer.settings.invoices.empty', 'Fatura yok')}</td></tr> : invoices.map((row) => <tr key={row.id} className="border-t" data-testid={`dealer-settings-invoice-row-${row.id}`}><td className="px-3 py-2">{row.invoice_no || row.id}</td><td className="px-3 py-2">{row.status}</td><td className="px-3 py-2">{row.amount_total || row.amount || 0} {row.currency || 'EUR'}</td><td className="px-3 py-2">{formatDate(row.created_at || row.issued_at)}</td></tr>)}</tbody>
                </table>
              </div>
            ) : null}

            {!loading && section === 'account_movements' ? (
              <div className="rounded-md border border-slate-200 overflow-x-auto" data-testid="dealer-settings-account-movements-table-wrap">
                <table className="w-full text-sm" data-testid="dealer-settings-account-movements-table">
                  <thead className="bg-slate-50"><tr><th className="px-3 py-2 text-left">İşlem</th><th className="px-3 py-2 text-left">Durum</th><th className="px-3 py-2 text-left">Tutar</th><th className="px-3 py-2 text-left">Tarih</th></tr></thead>
                  <tbody>{payments.length === 0 ? <tr><td className="px-3 py-4 text-slate-600" colSpan={4} data-testid="dealer-settings-account-movements-empty">{t('dealer.settings.movements.empty', 'Hareket yok')}</td></tr> : payments.map((row) => <tr key={row.id} className="border-t" data-testid={`dealer-settings-account-movement-row-${row.id}`}><td className="px-3 py-2">{row.provider || 'payment'} / {row.provider_ref || row.id}</td><td className="px-3 py-2">{row.status}</td><td className="px-3 py-2">{row.amount_total || row.amount || 0} {row.currency || 'EUR'}</td><td className="px-3 py-2">{formatDate(row.created_at)}</td></tr>)}</tbody>
                </table>
              </div>
            ) : null}

            {!loading && section === 'notifications' ? (
              <div className="space-y-3" data-testid="dealer-settings-notifications-section">
                <div className="grid gap-2 md:grid-cols-2" data-testid="dealer-settings-notification-matrix-grid">
                  {[
                    ['listing', 'İlan'],
                    ['store', 'Mağaza'],
                    ['favorite', 'Favori'],
                    ['native_ad', 'Doğal Reklam'],
                    ['virtual_tour', 'Sanal Tur'],
                  ].map(([key, label]) => (
                    <label key={key} className="flex items-center gap-2 rounded-md border border-slate-200 p-2 text-sm" data-testid={`dealer-settings-notification-matrix-item-${key}`}>
                      <input type="checkbox" checked={Boolean(prefs.notification_matrix?.[key])} onChange={(event) => setPrefs((prev) => ({ ...prev, notification_matrix: { ...(prev.notification_matrix || {}), [key]: event.target.checked } }))} data-testid={`dealer-settings-notification-matrix-checkbox-${key}`} />
                      {label}
                    </label>
                  ))}
                </div>
                <div className="grid gap-2 md:grid-cols-3" data-testid="dealer-settings-electronic-consent-grid">
                  {[
                    ['sms', 'SMS'],
                    ['email', 'E-Posta'],
                    ['call', 'Arama'],
                  ].map(([key, label]) => (
                    <label key={key} className="flex items-center gap-2 rounded-md border border-slate-200 p-2 text-sm" data-testid={`dealer-settings-electronic-consent-item-${key}`}>
                      <input type="checkbox" checked={Boolean(prefs.electronic_consent?.[key])} onChange={(event) => setPrefs((prev) => ({ ...prev, electronic_consent: { ...(prev.electronic_consent || {}), [key]: event.target.checked } }))} data-testid={`dealer-settings-electronic-consent-checkbox-${key}`} />
                      {label}
                    </label>
                  ))}
                </div>
                <button type="button" onClick={savePreferences} className="h-9 rounded-md bg-slate-900 px-4 text-sm font-semibold text-white" data-testid="dealer-settings-notification-save-button">{t('dealer.settings.notifications.save', 'Tercihleri Kaydet')}</button>
              </div>
            ) : null}

            {!loading && section === 'blocked' ? (
              <div className="space-y-3" data-testid="dealer-settings-blocked-section">
                <div className="flex flex-wrap items-center gap-2" data-testid="dealer-settings-blocked-add-row">
                  <input type="email" value={blockedEmailInput} onChange={(event) => setBlockedEmailInput(event.target.value)} className="h-10 min-w-[260px] flex-1 rounded-md border border-slate-300 px-3 text-sm" placeholder="ornek@domain.com" data-testid="dealer-settings-blocked-input" />
                  <button
                    type="button"
                    onClick={async () => {
                      try {
                        await requestJson(`${API}/dealer/settings/blocked-accounts`, {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({ email: blockedEmailInput.trim().toLowerCase() }),
                        });
                        setBlockedEmailInput('');
                        setSuccess(t('dealer.settings.blocked.added', 'Hesap engellendi.'));
                        await fetchAll();
                      } catch (requestError) {
                        setError(requestError?.message || 'Hesap engellenemedi');
                      }
                    }}
                    className="h-10 rounded-md bg-slate-900 px-4 text-sm font-semibold text-white"
                    data-testid="dealer-settings-blocked-add-button"
                  >
                    {t('dealer.settings.blocked.add_button', 'Engelle')}
                  </button>
                </div>
                {blockedAccounts.length === 0 ? <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-sm text-slate-600" data-testid="dealer-settings-blocked-empty">{t('dealer.settings.blocked.empty', 'Henüz engellenen hesap yok.')}</div> : (
                  <div className="space-y-2" data-testid="dealer-settings-blocked-list">
                    {blockedAccounts.map((email, index) => (
                      <div key={email} className="flex items-center justify-between rounded-md border border-slate-200 p-3" data-testid={`dealer-settings-blocked-item-${index}`}>
                        <span className="text-sm text-slate-900" data-testid={`dealer-settings-blocked-email-${index}`}>{email}</span>
                        <button
                          type="button"
                          onClick={async () => {
                            try {
                              const token = localStorage.getItem('access_token');
                              const params = new URLSearchParams({ email });
                              const res = await fetch(`${API}/dealer/settings/blocked-accounts?${params.toString()}`, { method: 'DELETE', headers: { Authorization: `Bearer ${token}` } });
                              const payload = await res.json().catch(() => ({}));
                              if (!res.ok) throw new Error(payload?.detail || 'Engel kaldırılamadı');
                              setSuccess(t('dealer.settings.blocked.removed', 'Engel kaldırıldı.'));
                              await fetchAll();
                            } catch (requestError) {
                              setError(requestError?.message || 'Engel kaldırılamadı');
                            }
                          }}
                          className="h-8 rounded-md border border-slate-300 px-3 text-xs font-semibold text-slate-800"
                          data-testid={`dealer-settings-blocked-remove-${index}`}
                        >
                          {t('dealer.settings.blocked.remove_button', 'Engeli Kaldır')}
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : null}
        </div>
      </div>
    </div>
  );
}
