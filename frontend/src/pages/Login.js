import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { useTheme } from '../contexts/ThemeContext';
import { toast } from '@/components/ui/use-toast';
import AdSlot from '@/components/public/AdSlot';
import { Lock, Mail, Eye, EyeOff, AlertCircle, Sun, Moon, Globe } from 'lucide-react';
import { PORTALS, ROLE_TO_PORTAL, portalFromScope, defaultHomeForRole } from '@/shared/types/portals';

export default function Login({ portalContext = 'account' }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [totpCode, setTotpCode] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState(null); // { code, retry_after_seconds, expected, actual }
  const [loading, setLoading] = useState(false);
  const [socialLoading, setSocialLoading] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [portalSelection, setPortalSelection] = useState(
    portalContext === 'dealer' ? 'dealer' : 'account'
  );
  const { login, logout, startGoogleLogin } = useAuth();
  const { t, language, setLanguage } = useLanguage();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();

  const isAdminLogin = portalContext === 'admin';
  const showPortalSelector = !isAdminLogin;
  const registerPath = portalSelection === 'dealer' ? '/dealer/register' : '/register';
  const verifyPath = portalSelection === 'dealer' ? '/dealer/verify-email' : '/verify-email';
  const showTotpInput = ['TOTP_REQUIRED', 'INVALID_TOTP', 'TOTP_SETUP_INCOMPLETE'].includes(error?.code);

  const handleGoogleLogin = () => {
    if (socialLoading) return;
    setError(null);
    setSocialLoading(true);
    try {
      startGoogleLogin(portalSelection);
    } catch (err) {
      setSocialLoading(false);
      setError({ code: 'UNKNOWN', message: err?.message || 'Google giriş başlatılamadı.' });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const u = await login(email, password, totpCode || undefined);

      if (isAdminLogin) {
        toast({
          title: t('auth.login.admin.session_verified', 'Oturum doğrulandı'),
          duration: 1200,
          'data-testid': 'admin-login-toast-verified',
        });
        setTimeout(() => {
          toast({
            title: t('auth.login.admin.loading_panel', 'Admin paneli yükleniyor...'),
            duration: 1400,
            'data-testid': 'admin-login-toast-loading',
          });
        }, 300);
        setTimeout(() => {
          navigate(defaultHomeForRole(u?.role));
        }, 700);
        return;
      }

      if (showPortalSelector) {
        const userPortal = portalFromScope(u?.portal_scope) || ROLE_TO_PORTAL[u?.role] || PORTALS.PUBLIC;
        const expectedPortal = portalSelection === 'dealer' ? PORTALS.DEALER : PORTALS.INDIVIDUAL;

        if (userPortal !== expectedPortal) {
          setError({ code: 'PORTAL_MISMATCH', expected: expectedPortal, actual: userPortal });
          logout();
          return;
        }

        if (!u?.is_verified) {
          sessionStorage.setItem('pending_email', u?.email || '');
          sessionStorage.setItem('pending_portal', expectedPortal);
          navigate(expectedPortal === PORTALS.DEALER ? '/dealer/verify-email' : '/verify-email');
          return;
        }

        navigate(expectedPortal === PORTALS.DEALER ? '/dealer' : '/account');
        return;
      }

      navigate(defaultHomeForRole(u?.role));
    } catch (err) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail;

      if (status === 401 && detail?.code === 'INVALID_CREDENTIALS') {
        setError({ code: 'INVALID_CREDENTIALS' });
      } else if (status === 401 && detail?.code === 'INVALID_TOTP') {
        setError({ code: 'INVALID_TOTP' });
      } else if (status === 429 && detail?.code === 'RATE_LIMITED') {
        setError({ code: 'RATE_LIMITED', retry_after_seconds: detail?.retry_after_seconds });
      } else if (status === 403 && detail?.code === 'EMAIL_NOT_VERIFIED') {
        sessionStorage.setItem('pending_email', email);
        sessionStorage.setItem('pending_portal', portalSelection);
        setError({ code: 'EMAIL_NOT_VERIFIED' });
      } else if (status === 403 && detail?.code === 'TOTP_REQUIRED') {
        setError({ code: 'TOTP_REQUIRED' });
      } else if (status === 403 && detail?.code === 'TOTP_SETUP_INCOMPLETE') {
        setError({ code: 'TOTP_SETUP_INCOMPLETE' });
      } else if (status === 403 && detail === 'User account deleted') {
        setError({ code: 'ACCOUNT_DELETED' });
      } else if (status === 403 && detail === 'User account suspended') {
        setError({ code: 'ACCOUNT_SUSPENDED' });
      } else {
        setError({ code: 'UNKNOWN' });
      }
    } finally {
      setLoading(false);
    }
  };

  const renderPortalMismatchMessage = () => {
    if (!error || error.code !== 'PORTAL_MISMATCH') return null;

    if (error.actual === PORTALS.BACKOFFICE) {
      return t('auth.login.errors.portal_mismatch_admin', 'Bu hesap yönetici hesabı. Lütfen admin girişini kullanın.');
    }

    if (error.expected === PORTALS.DEALER) {
      return t('auth.login.errors.portal_mismatch_account', 'Bu hesap bireysel giriş içindir. Bireysel seçimini kullanın.');
    }

    return t('auth.login.errors.portal_mismatch_dealer', 'Bu hesap ticari giriş içindir. Ticari seçimini kullanın.');
  };

  return (
    <div
      className={`min-h-screen flex items-center justify-center p-4 ${
        isAdminLogin
          ? 'bg-gradient-to-br from-background via-background to-muted/30'
          : 'bg-[var(--bg-warm)]'
      }`}
      data-testid="login-page"
    >
      <div className="absolute top-4 right-4 flex items-center gap-2">
        <button
          onClick={toggleTheme}
          className="p-2 rounded-md hover:bg-muted transition-colors"
          data-testid="theme-toggle"
        >
          {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
        </button>
        <div className="relative">
          <button
            className="flex items-center gap-1 p-2 rounded-md hover:bg-muted transition-colors"
            onClick={() => {
              const langs = ['tr', 'de', 'fr'];
              const idx = langs.indexOf(language);
              setLanguage(langs[(idx + 1) % langs.length]);
            }}
            data-testid="language-toggle"
          >
            <Globe size={20} />
            <span className="uppercase text-xs font-medium">{language}</span>
          </button>
        </div>
      </div>

      <div className="w-full max-w-2xl space-y-4" data-testid="login-content">
        {!isAdminLogin && (
          <div
            className="rounded-lg border border-amber-200 bg-amber-50 px-5 py-4 text-sm text-amber-900"
            data-testid="login-info-banner"
          >
            {t('auth.login.info_banner', "Avrupa'nın en yeni ve geniş ilan platformu Annoncia'ya hoş geldiniz. Hesabınız yoksa ücretsiz hesap açabilirsiniz.")}
          </div>
        )}

        <div className="bg-white rounded-lg shadow-lg border p-8 text-slate-900" data-testid="login-card">
          <div className="text-center mb-8" data-testid="login-header">
            <h1 className="text-2xl font-bold tracking-tight">{t('auth.login.title', 'Giriş yap')}</h1>
            <p className="text-slate-600 text-sm mt-2">{t('auth.login.subtitle', 'Hesabınıza giriş yapın.')}</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6" data-testid="login-form">
            {showPortalSelector && (
              <div className="space-y-2" data-testid="login-portal-selector">
                <label className="text-sm font-medium" data-testid="login-portal-label">{t('auth.login.portal_type', 'Giriş türü')}</label>
                <div className="flex flex-wrap items-center gap-6" data-testid="login-portal-options">
                  <label className="flex items-center gap-2 text-sm" data-testid="login-portal-option-account">
                    <input
                      type="radio"
                      name="portal"
                      value="account"
                      checked={portalSelection === 'account'}
                      onChange={() => setPortalSelection('account')}
                      className="h-4 w-4"
                      data-testid="login-portal-account"
                    />
                    {t('auth.login.portal_account', 'Bireysel')}
                  </label>
                  <label className="flex items-center gap-2 text-sm" data-testid="login-portal-option-dealer">
                    <input
                      type="radio"
                      name="portal"
                      value="dealer"
                      checked={portalSelection === 'dealer'}
                      onChange={() => setPortalSelection('dealer')}
                      className="h-4 w-4"
                      data-testid="login-portal-dealer"
                    />
                    {t('auth.login.portal_dealer', 'Ticari')}
                  </label>
                </div>
              </div>
            )}

            {error && (
              <div className="p-3 rounded-md bg-destructive/10 text-destructive text-sm" data-testid="login-error">
                <div className="flex items-center gap-2">
                  <AlertCircle size={16} />
                  <div className="font-medium" data-testid="login-error-message">
                    {error.code === 'INVALID_CREDENTIALS' && t('auth.login.errors.invalid_credentials', 'E-posta veya şifre hatalı')}
                    {error.code === 'INVALID_TOTP' && t('auth.login.errors.invalid_totp', 'Doğrulama kodu hatalı')}
                    {error.code === 'TOTP_REQUIRED' && t('auth.login.errors.totp_required', '2FA doğrulama kodu gerekli')}
                    {error.code === 'TOTP_SETUP_INCOMPLETE' && t('auth.login.errors.totp_setup_incomplete', '2FA kurulumu tamamlanmamış')}
                    {error.code === 'ACCOUNT_DELETED' && t('auth.login.errors.account_deleted', 'Hesap silinmiş')}
                    {error.code === 'ACCOUNT_SUSPENDED' && t('auth.login.errors.account_suspended', 'Hesap askıya alınmış')}
                    {error.code === 'RATE_LIMITED' && t('auth.login.errors.rate_limited', 'Çok fazla deneme yaptınız. 15 dakika sonra tekrar deneyin.')}
                    {error.code === 'PORTAL_MISMATCH' && renderPortalMismatchMessage()}
                    {error.code === 'EMAIL_NOT_VERIFIED' && t('auth.login.errors.email_not_verified', 'Hesabınızı doğrulamanız gerekiyor.')}
                    {error.code === 'UNKNOWN' && t('auth.login.errors.unknown', 'Giriş başarısız. Lütfen tekrar deneyin.')}
                  </div>
                </div>

                <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs" data-testid="login-error-actions">
                  <a
                    href="/help/forgot-password"
                    className="underline underline-offset-2 hover:opacity-80"
                    data-testid="login-error-forgot-password"
                  >
                    {t('auth.login.forgot_password', 'Şifremi unuttum')}
                  </a>

                  {error.code === 'EMAIL_NOT_VERIFIED' && (
                    <a
                      href={verifyPath}
                      className="underline underline-offset-2 hover:opacity-80"
                      data-testid="login-error-verify-link"
                    >
                      {t('auth.login.errors.send_verification', 'Doğrulama kodu gönder')}
                    </a>
                  )}

                  {error.code === 'RATE_LIMITED' && (
                    <>
                      <span className="text-destructive/80">{t('auth.login.errors.temp_locked', 'Güvenlik nedeniyle geçici olarak engellendi.')}</span>
                      <a
                        href="/help/account-locked"
                        className="underline underline-offset-2 hover:opacity-80"
                        data-testid="login-error-account-locked"
                      >
                        {t('auth.login.errors.account_locked_help', 'Hesap kilitlendi mi?')}
                      </a>
                      {typeof error.retry_after_seconds === 'number' && (
                        <span className="text-destructive/80" data-testid="login-error-retry-after">
                          ~{Math.max(1, Math.ceil(error.retry_after_seconds / 60))} dk
                        </span>
                      )}
                    </>
                  )}
                </div>
              </div>
            )}

            <div className="space-y-2" data-testid="login-email-field">
              <label className="text-sm font-medium" htmlFor="email">{t('email')}</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full h-11 pl-10 pr-4 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-colors"
                  placeholder={t('auth.login.email_placeholder', 'E-posta adresi')}
                  required
                  data-testid="login-email"
                />
              </div>
            </div>

            <div className="space-y-2" data-testid="login-password-field">
              <label className="text-sm font-medium" htmlFor="password">{t('password')}</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full h-11 pl-10 pr-10 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-colors"
                  placeholder={t('auth.login.password_placeholder', 'Şifre')}
                  required
                  data-testid="login-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  data-testid="login-toggle-password"
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            {showTotpInput && (
              <div className="space-y-2" data-testid="login-totp-field">
                <label className="text-sm font-medium" htmlFor="totp">{t('auth.login.totp_label', '2FA Kodu')}</label>
                <input
                  id="totp"
                  type="text"
                  value={totpCode}
                  onChange={(e) => setTotpCode(e.target.value)}
                  className="w-full h-11 px-4 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-colors"
                  placeholder={t('auth.login.totp_placeholder', '6 haneli doğrulama kodu')}
                  data-testid="login-totp-code"
                />
                <p className="text-xs text-muted-foreground" data-testid="login-totp-help">{t('auth.login.totp_help', 'Authenticator uygulamanızdaki kodu girin.')}</p>
              </div>
            )}

            <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-slate-700" data-testid="login-helper-row">
              <label className="flex items-center gap-2" data-testid="login-remember-me">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(event) => setRememberMe(event.target.checked)}
                  className="h-4 w-4"
                  data-testid="login-remember-me-checkbox"
                />
                {t('auth.login.remember_me', 'Oturumum açık kalsın')}
              </label>
              <a
                href="/help/forgot-password"
                className="text-blue-600 underline underline-offset-2 hover:text-blue-700"
                data-testid="login-forgot-password"
              >
                {t('auth.login.forgot_password', 'Şifremi unuttum')}
              </a>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full h-11 rounded-md bg-primary text-primary-foreground font-medium text-sm hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              data-testid="login-submit"
            >
              {loading ? (
                <span className="inline-flex items-center gap-2">
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  {t('auth.login.submit_loading', 'Yükleniyor...')}
                </span>
              ) : (
                t('auth.login.submit', 'E-posta ile giriş yap')
              )}
            </button>

            {showPortalSelector && (
              <div className="text-center text-sm" data-testid="login-register">
                {t('auth.login.no_account', 'Henüz hesabın yok mu?')}{' '}
                <a
                  href={registerPath}
                  className="text-blue-600 underline underline-offset-2 hover:text-blue-700"
                  data-testid="login-register-link"
                >
                  {t('auth.login.create_account', 'Hesap aç')}
                </a>
              </div>
            )}

            {showPortalSelector && (
              <div className="flex items-center gap-4" data-testid="login-divider">
                <span className="h-px flex-1 bg-muted" />
                <span className="text-xs text-slate-500">{t('auth.login.or', 'VEYA')}</span>
                <span className="h-px flex-1 bg-muted" />
              </div>
            )}

            {showPortalSelector && (
              <div className="space-y-3" data-testid="login-social">
                <button
                  type="button"
                  onClick={handleGoogleLogin}
                  className="w-full h-11 rounded-md border text-sm font-medium hover:bg-muted/40"
                  data-testid="login-google"
                  disabled={socialLoading}
                >
                  {socialLoading
                    ? t('auth.login.submit_loading', 'Yükleniyor...')
                    : t('auth.login.google_continue', 'Google ile devam et')}
                </button>
                <button
                  type="button"
                  className="w-full h-11 rounded-md border text-sm font-medium hover:bg-muted/40"
                  data-testid="login-apple"
                  disabled
                >
                  {t('auth.login.apple_soon', 'Apple ile giriş yap (Yakında)')}
                </button>
              </div>
            )}

            {showPortalSelector && (
              <div className="text-center text-xs" data-testid="login-qr-login">
                <a
                  href="/login/qr"
                  className="text-blue-600 underline underline-offset-2 hover:text-blue-700"
                  data-testid="login-qr-link"
                >
                  {t('auth.login.qr_login', 'QR kod ile mobil uygulamadan giriş yap')}
                </a>
              </div>
            )}
          </form>
        </div>

        {!isAdminLogin && (
          <div className="grid gap-4 md:grid-cols-2" data-testid="login-ad-slots">
            <AdSlot placement="AD_LOGIN_1" className="w-full" />
            <AdSlot placement="AD_LOGIN_2" className="w-full" />
          </div>
        )}
      </div>
    </div>
  );
}
