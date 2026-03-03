import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sun, Moon, Globe } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { useTheme } from '@/contexts/ThemeContext';
import { toast } from '@/components/ui/use-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const OTP_LENGTH = 6;
const RESEND_COOLDOWN = 90;

const fallbackCountries = [{ code: 'DE', name: { tr: 'Almanya', en: 'Germany' } }];

export default function Register({ portalContext = 'account' }) {
  const navigate = useNavigate();
  const { applySession } = useAuth();
  const { language, setLanguage, t } = useLanguage();
  const { theme, toggleTheme } = useTheme();

  const [countries, setCountries] = useState(fallbackCountries);
  const [countryLoading, setCountryLoading] = useState(true);
  const [countryError, setCountryError] = useState('');
  const [countryCode, setCountryCode] = useState('DE');
  const [countryOpen, setCountryOpen] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [step, setStep] = useState('form');

  const [fullName, setFullName] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [contactName, setContactName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [taxId, setTaxId] = useState('');
  const [companyWebsite, setCompanyWebsite] = useState('');

  const [codeDigits, setCodeDigits] = useState(Array(OTP_LENGTH).fill(''));
  const [verifyLoading, setVerifyLoading] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);
  const [cooldown, setCooldown] = useState(0);
  const [attemptsLeft, setAttemptsLeft] = useState(null);
  const inputsRef = useRef([]);

  const isDealer = portalContext === 'dealer';
  const loginPath = isDealer ? '/dealer/login' : '/login';

  useEffect(() => {
    const fetchCountries = async () => {
      setCountryLoading(true);
      setCountryError('');
      try {
        const res = await fetch(`${API}/countries/public`);
        if (!res.ok) {
          throw new Error(t('auth.register.errors.countries_failed', 'Ülkeler yüklenemedi'));
        }
        const data = await res.json();
        if (Array.isArray(data) && data.length) {
          setCountries(data);
        } else {
          setCountries(fallbackCountries);
        }
      } catch (err) {
        setCountries(fallbackCountries);
        setCountryError(t('auth.register.errors.country_list_fallback', 'Ülke listesi yüklenemedi. Varsayılan ülke kullanılıyor.'));
      } finally {
        setCountryLoading(false);
      }
    };

    fetchCountries();
  }, []);

  useEffect(() => {
    if (countries.length === 0) return;
    const hasDefault = countries.some((item) => item.code === countryCode);
    if (!hasDefault) {
      setCountryCode(countries[0]?.code || 'DE');
    }
  }, [countries, countryCode]);

  useEffect(() => {
    if (cooldown <= 0) return undefined;
    const timer = setTimeout(() => setCooldown((prev) => Math.max(0, prev - 1)), 1000);
    return () => clearTimeout(timer);
  }, [cooldown]);

  const resolveCountryLabel = (country) => {
    if (!country) return '';
    if (country.name) {
      return country.name[language] || country.name.en || country.name.de || country.code;
    }
    return country.code || '';
  };

  const selectedCountry = countries.find((item) => item.code === countryCode);
  const codeValue = useMemo(() => codeDigits.join(''), [codeDigits]);
  const formDisabled = step === 'verify';

  const handleDigitChange = (index, value) => {
    const cleaned = value.replace(/\D/g, '');
    if (!cleaned) {
      const nextDigits = [...codeDigits];
      nextDigits[index] = '';
      setCodeDigits(nextDigits);
      return;
    }

    const digit = cleaned[cleaned.length - 1];
    const nextDigits = [...codeDigits];
    nextDigits[index] = digit;
    setCodeDigits(nextDigits);

    if (index < OTP_LENGTH - 1) {
      inputsRef.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index, event) => {
    if (event.key === 'Backspace' && !codeDigits[index] && index > 0) {
      inputsRef.current[index - 1]?.focus();
    }
  };

  const handlePaste = (event) => {
    const pasted = event.clipboardData.getData('text').replace(/\D/g, '').slice(0, OTP_LENGTH);
    if (!pasted) return;
    const nextDigits = Array(OTP_LENGTH).fill('');
    pasted.split('').forEach((digit, idx) => {
      nextDigits[idx] = digit;
    });
    setCodeDigits(nextDigits);
    const lastIndex = Math.min(pasted.length, OTP_LENGTH) - 1;
    if (lastIndex >= 0) {
      inputsRef.current[lastIndex]?.focus();
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');

    if (isDealer) {
      if (!companyName.trim() || !contactName.trim()) {
        setError(t('auth.register.errors.company_contact_required', 'Firma adı ve yetkili kişi zorunludur.'));
        return;
      }
    } else if (!fullName.trim()) {
      setError(t('auth.register.errors.fullname_required', 'Ad soyad zorunludur.'));
      return;
    }

    if (!email.trim()) {
      setError(t('auth.register.errors.email_required', 'E-posta zorunludur.'));
      return;
    }

    if (!password || password.length < 8) {
      setError(t('auth.register.errors.password_min', 'Şifre en az 8 karakter olmalıdır.'));
      return;
    }

    if (!countryCode) {
      setError(t('auth.register.errors.country_required', 'Ülke seçimi zorunludur.'));
      return;
    }

    setLoading(true);

    try {
      const endpoint = isDealer ? '/auth/register/dealer' : '/auth/register/consumer';
      const payload = isDealer
        ? {
            company_name: companyName.trim(),
            contact_name: contactName.trim(),
            email: email.trim().toLowerCase(),
            password,
            country_code: countryCode,
            tax_id: taxId.trim() || null,
            company_website: companyWebsite,
          }
        : {
            full_name: fullName.trim(),
            email: email.trim().toLowerCase(),
            password,
            country_code: countryCode,
            company_website: companyWebsite,
          };

      const res = await fetch(`${API}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail?.detail || t('auth.register.errors.register_failed', 'Kayıt başarısız'));
      }

      await res.json().catch(() => ({}));

      sessionStorage.setItem('pending_email', payload.email || email);
      sessionStorage.setItem('pending_portal', isDealer ? 'dealer' : 'account');

      setStep('verify');
      setCooldown(RESEND_COOLDOWN);
      toast({ title: t('auth.register.toast.code_sent_title', 'Doğrulama kodu gönderildi'), description: t('auth.register.toast.code_sent_desc', 'Lütfen e-postanızı kontrol edin.') });
    } catch (err) {
      setError(err?.message || t('auth.register.errors.register_failed', 'Kayıt başarısız'));
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (event) => {
    event.preventDefault();
    setError('');
    setAttemptsLeft(null);

    if (!email.trim()) {
      setError(t('auth.register.errors.email_required', 'E-posta zorunludur.'));
      return;
    }

    if (codeValue.length !== OTP_LENGTH) {
      setError(t('auth.register.errors.code_required', '6 haneli kodu girin.'));
      return;
    }

    setVerifyLoading(true);

    try {
      const res = await fetch(`${API}/auth/verify-email`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim().toLowerCase(), code: codeValue }),
      });

      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        if (detail?.remaining_attempts !== undefined) {
          setAttemptsLeft(detail.remaining_attempts);
        }
        if (res.status === 429) {
          setCooldown(detail?.retry_after_seconds || RESEND_COOLDOWN);
          throw new Error(t('auth.register.errors.too_many_attempts', 'Çok fazla deneme yapıldı. Lütfen bekleyin.'));
        }
        const message = typeof detail?.detail === 'string' ? detail.detail : t('auth.register.errors.code_invalid', 'Kod doğrulanamadı.');
        throw new Error(message);
      }

      const data = await res.json().catch(() => ({}));
      applySession(data);
      toast({ title: t('auth.register.toast.verify_success_title', 'Doğrulama tamamlandı'), description: t('auth.register.toast.verify_success_desc', 'Hesabınız doğrulandı.') });
      navigate(isDealer ? '/dealer' : '/account');
    } catch (err) {
      setError(err?.message || t('auth.register.errors.code_invalid', 'Kod doğrulanamadı.'));
    } finally {
      setVerifyLoading(false);
    }
  };

  const handleResend = async () => {
    if (cooldown > 0 || resendLoading) return;
    if (!email.trim()) {
      setError(t('auth.register.errors.email_required', 'E-posta zorunludur.'));
      return;
    }

    setResendLoading(true);
    setError('');
    setAttemptsLeft(null);

    try {
      const res = await fetch(`${API}/auth/resend-verification`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim().toLowerCase() }),
      });

      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        if (res.status === 429) {
          setCooldown(detail?.retry_after_seconds || RESEND_COOLDOWN);
          throw new Error(t('auth.register.errors.resend_wait', 'Kısa süre önce gönderildi. Lütfen bekleyin.'));
        }
        throw new Error(detail?.detail || t('auth.register.errors.code_send_failed', 'Kod gönderilemedi.'));
      }

      const data = await res.json().catch(() => ({}));
      const nextCooldown = data?.cooldown_seconds || RESEND_COOLDOWN;
      setCooldown(nextCooldown);

      toast({ title: t('auth.register.toast.code_resent_title', 'Kod yeniden gönderildi'), description: t('auth.register.toast.code_sent_desc', 'Lütfen e-postanızı kontrol edin.') });
    } catch (err) {
      setError(err?.message || t('auth.register.errors.code_send_failed', 'Kod gönderilemedi.'));
    } finally {
      setResendLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--bg-warm)] p-4" data-testid="register-page">
      <div className="absolute top-4 right-4 flex items-center gap-2">
        <button
          onClick={toggleTheme}
          className="p-2 rounded-md hover:bg-muted transition-colors"
          data-testid="register-theme-toggle"
        >
          {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
        </button>
        <button
          className="flex items-center gap-1 p-2 rounded-md hover:bg-muted transition-colors"
          onClick={() => {
            const langs = ['tr', 'de', 'fr'];
            const idx = langs.indexOf(language);
            setLanguage(langs[(idx + 1) % langs.length]);
          }}
          data-testid="register-language-toggle"
        >
          <Globe size={20} />
          <span className="uppercase text-xs font-medium">{language}</span>
        </button>
      </div>

      <div className="w-full max-w-2xl space-y-4" data-testid="register-content">
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-5 py-4 text-sm text-amber-900" data-testid="register-info-banner">
          {t('auth.login.info_banner', "Avrupa'nın en yeni ve geniş ilan platformu Annoncia'ya hoş geldiniz. Hesabınız yoksa ücretsiz hesap açabilirsiniz.")}
        </div>

        <div className="bg-white rounded-lg shadow-lg border p-8 text-slate-900" data-testid="register-card">
          <div className="text-center mb-8" data-testid="register-header">
            <h1 className="text-2xl font-bold tracking-tight">{isDealer ? t('auth.register.title_dealer', 'Ticari Kayıt') : t('auth.register.title_individual', 'Bireysel Kayıt')}</h1>
            <p className="text-slate-600 text-sm mt-2">{t('auth.register.subtitle', 'Bilgilerinizi girerek hesabınızı oluşturun.')}</p>
          </div>

          {step === 'verify' && (
            <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800" data-testid="register-verify-banner">
              {t('auth.register.verify_banner', 'Mail doğrulama kodu gönderildi. Lütfen 6 haneli kodu girin.')}
            </div>
          )}

          <form onSubmit={step === 'form' ? handleSubmit : handleVerify} className="space-y-5" data-testid="register-form">
            <div
              style={{ position: 'absolute', left: '-10000px', top: 'auto', width: '1px', height: '1px', overflow: 'hidden' }}
              aria-hidden="true"
              data-testid="register-honeypot-wrapper"
            >
              <label htmlFor="company-website">Company website</label>
              <input
                id="company-website"
                name="company_website"
                value={companyWebsite}
                onChange={(e) => setCompanyWebsite(e.target.value)}
                tabIndex={-1}
                autoComplete="off"
                data-testid="register-company-website"
              />
            </div>
            {error && (
              <div className="rounded-md bg-destructive/10 text-destructive text-sm px-3 py-2" data-testid="register-error">
                {error}
              </div>
            )}

            {isDealer ? (
              <>
                <div className="space-y-2" data-testid="register-company-field">
                  <label className="text-sm font-medium" htmlFor="company-name">{t('auth.register.company_name', 'Firma adı')}</label>
                  <input
                    id="company-name"
                    value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                    className="w-full h-11 rounded-md border px-3 text-sm"
                    placeholder={t('auth.register.company_name_placeholder', 'Örn: Annoncia Motors')}
                    data-testid="register-company-name"
                    disabled={formDisabled}
                  />
                </div>
                <div className="space-y-2" data-testid="register-contact-field">
                  <label className="text-sm font-medium" htmlFor="contact-name">{t('auth.register.contact_name', 'Yetkili kişi')}</label>
                  <input
                    id="contact-name"
                    value={contactName}
                    onChange={(e) => setContactName(e.target.value)}
                    className="w-full h-11 rounded-md border px-3 text-sm"
                    placeholder={t('auth.register.contact_name_placeholder', 'Örn: Ayşe Yılmaz')}
                    data-testid="register-contact-name"
                    disabled={formDisabled}
                  />
                </div>
              </>
            ) : (
              <div className="space-y-2" data-testid="register-fullname-field">
                <label className="text-sm font-medium" htmlFor="full-name">{t('auth.register.full_name', 'Ad Soyad')}</label>
                <input
                  id="full-name"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full h-11 rounded-md border px-3 text-sm"
                  placeholder={t('auth.register.full_name_placeholder', 'Örn: Ali Demir')}
                  data-testid="register-full-name"
                  disabled={formDisabled}
                />
              </div>
            )}

            <div className="space-y-2" data-testid="register-email-field">
              <label className="text-sm font-medium" htmlFor="register-email">{t('email', 'E-posta')}</label>
              <input
                id="register-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full h-11 rounded-md border px-3 text-sm"
                placeholder={t('auth.register.email_placeholder', 'mail@ornek.com')}
                data-testid="register-email"
                disabled={formDisabled}
              />
            </div>

            <div className="space-y-2" data-testid="register-password-field">
              <label className="text-sm font-medium" htmlFor="register-password">{t('password', 'Şifre')}</label>
              <input
                id="register-password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full h-11 rounded-md border px-3 text-sm"
                placeholder={t('auth.register.password_placeholder', 'En az 8 karakter')}
                data-testid="register-password"
                disabled={formDisabled}
              />
            </div>

            <div className="space-y-2" data-testid="register-country-field">
              <label className="text-sm font-medium" htmlFor="register-country">{t('auth.register.country', 'Ülke')}</label>
              <div className="relative" data-testid="register-country-dropdown">
                <button
                  type="button"
                  id="register-country"
                  onClick={() => setCountryOpen((prev) => !prev)}
                  className="w-full h-11 rounded-md border px-3 text-sm flex items-center justify-between"
                  data-testid="register-country-button"
                  disabled={formDisabled}
                >
                  <span data-testid="register-country-selected">
                    {resolveCountryLabel(selectedCountry) || t('auth.register.select_country', 'Ülke seçin')}
                  </span>
                  <span className="text-slate-400">▾</span>
                </button>
                {countryOpen && !formDisabled && (
                  <div
                    className="absolute z-10 mt-2 w-full max-h-60 overflow-auto rounded-md border bg-white shadow-lg"
                    data-testid="register-country-menu"
                  >
                    {countries.map((country) => (
                      <button
                        type="button"
                        key={country.code}
                        onClick={() => {
                          setCountryCode(country.code);
                          setCountryOpen(false);
                        }}
                        className={`w-full text-left px-3 py-2 text-sm hover:bg-muted ${
                          countryCode === country.code ? 'bg-muted' : ''
                        }`}
                        data-testid={`register-country-option-${country.code.toLowerCase()}`}
                      >
                        {resolveCountryLabel(country)}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              {countryLoading && (
                <p className="text-xs text-slate-500" data-testid="register-country-loading">
                  {t('auth.register.countries_loading', 'Ülkeler yükleniyor...')}
                </p>
              )}
              {countryError && (
                <p className="text-xs text-amber-700" data-testid="register-country-error">
                  {countryError}
                </p>
              )}
            </div>

            {isDealer && (
              <div className="space-y-2" data-testid="register-tax-field">
                <label className="text-sm font-medium" htmlFor="tax-id">{t('auth.register.tax_optional', 'Vergi / ID (opsiyonel)')}</label>
                <input
                  id="tax-id"
                  value={taxId}
                  onChange={(e) => setTaxId(e.target.value)}
                  className="w-full h-11 rounded-md border px-3 text-sm"
                  placeholder={t('auth.register.tax_placeholder', 'Vergi numarası')}
                  data-testid="register-tax-id"
                  disabled={formDisabled}
                />
              </div>
            )}

            {step === 'form' && (
              <button
                type="submit"
                disabled={loading}
                className="w-full h-11 rounded-md bg-primary text-primary-foreground font-medium text-sm hover:bg-primary/90 disabled:opacity-50"
                data-testid="register-submit"
              >
                {loading ? t('auth.register.submit_loading', 'Kaydediliyor...') : t('auth.register.submit', 'Hesap Oluştur')}
              </button>
            )}

            {step === 'verify' && (
              <div className="space-y-4" data-testid="register-verify-section">
                <div className="space-y-2" data-testid="register-verify-code-field">
                  <label className="text-sm font-medium">{t('auth.register.code_label', 'Doğrulama kodu')}</label>
                  <div className="flex items-center justify-center gap-2" onPaste={handlePaste} data-testid="register-verify-code-inputs">
                    {codeDigits.map((digit, index) => (
                      <input
                        key={index}
                        type="text"
                        inputMode="numeric"
                        maxLength={1}
                        value={digit}
                        onChange={(event) => handleDigitChange(index, event.target.value)}
                        onKeyDown={(event) => handleKeyDown(index, event)}
                        ref={(el) => {
                          inputsRef.current[index] = el;
                        }}
                        className="h-12 w-12 rounded-md border text-center text-lg font-semibold"
                        data-testid={`register-verify-digit-${index}`}
                      />
                    ))}
                  </div>
                </div>


                {attemptsLeft !== null && (
                  <div className="text-xs text-slate-500" data-testid="register-verify-attempts">
                    {t('auth.register.attempts_left', 'Kalan deneme: {{count}}', { count: attemptsLeft })}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={verifyLoading}
                  className="w-full h-11 rounded-md bg-primary text-primary-foreground font-medium text-sm hover:bg-primary/90 disabled:opacity-50"
                  data-testid="register-verify-submit"
                >
                  {verifyLoading ? t('auth.register.verify_loading', 'Doğrulanıyor...') : t('auth.register.verify_submit', 'Doğrula')}
                </button>

                <div className="flex flex-wrap items-center justify-between gap-3 text-sm" data-testid="register-verify-actions">
                  <button
                    type="button"
                    onClick={handleResend}
                    disabled={cooldown > 0 || resendLoading}
                    className="text-blue-600 underline underline-offset-2 disabled:opacity-60"
                    data-testid="register-verify-resend"
                  >
                    {cooldown > 0 ? t('auth.register.resend_code_with_timer', 'Kodu tekrar gönder ({{seconds}}s)', { seconds: cooldown }) : t('auth.register.resend_code', 'Kodu tekrar gönder')}
                  </button>
                  <button
                    type="button"
                    onClick={() => navigate(loginPath)}
                    className="text-slate-600 underline underline-offset-2"
                    data-testid="register-verify-login"
                  >
                    {t('auth.register.back_to_login', 'Girişe dön')}
                  </button>
                </div>
              </div>
            )}

            {step === 'form' && (
              <div className="text-center text-sm" data-testid="register-login-link">
                {t('auth.register.already_have_account', 'Zaten hesabın var mı?')}{' '}
                <button
                  type="button"
                  onClick={() => navigate(loginPath)}
                  className="text-blue-600 underline underline-offset-2 hover:text-blue-700"
                  data-testid="register-login-button"
                >
                  {t('auth.register.login', 'Giriş yap')}
                </button>
              </div>
            )}
          </form>
        </div>
      </div>
    </div>
  );
}
