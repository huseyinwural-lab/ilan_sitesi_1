import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { useTheme } from '../contexts/ThemeContext';
import { Lock, Mail, Eye, EyeOff, AlertCircle, Sun, Moon, Globe } from 'lucide-react';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState(null); // { code, retry_after_seconds }
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const { t, language, setLanguage } = useLanguage();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const u = await login(email, password);
      const { defaultHomeForRole } = await import('@/shared/types/portals');
      navigate(defaultHomeForRole(u?.role));
    } catch (err) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail;

      if (status === 401 && detail?.code === 'INVALID_CREDENTIALS') {
        setError({ code: 'INVALID_CREDENTIALS' });
      } else if (status === 429 && detail?.code === 'RATE_LIMITED') {
        setError({ code: 'RATE_LIMITED', retry_after_seconds: detail?.retry_after_seconds });
      } else {
        setError({ code: 'UNKNOWN' });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-background to-muted/30 p-4">
      {/* Theme and Language toggles */}
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

      <div className="w-full max-w-md">
        <div className="bg-card rounded-lg shadow-lg border p-8">
          <div className="text-center mb-8">
            <h1 className="text-2xl font-bold tracking-tight">Giriş Yap</h1>
            <p className="text-muted-foreground text-sm mt-2">Hesabınıza giriş yapın.</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="p-3 rounded-md bg-destructive/10 text-destructive text-sm" data-testid="login-error">
                <div className="flex items-center gap-2">
                  <AlertCircle size={16} />
                  <div className="font-medium">
                    {error.code === 'INVALID_CREDENTIALS' && 'E-posta veya şifre hatalı'}
                    {error.code === 'RATE_LIMITED' && 'Çok fazla deneme yaptınız. 15 dakika sonra tekrar deneyin.'}
                    {error.code === 'UNKNOWN' && (t('login_error') || 'Giriş başarısız. Lütfen tekrar deneyin.')}
                  </div>
                </div>

                {/* Helper CTAs */}
                <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs">
                  <a href="/help/forgot-password" className="underline underline-offset-2 hover:opacity-80">
                    Şifremi unuttum
                  </a>

                  {error.code === 'RATE_LIMITED' && (
                    <>
                      <span className="text-destructive/80">Güvenlik nedeniyle geçici olarak engellendi.</span>
                      <a href="/help/account-locked" className="underline underline-offset-2 hover:opacity-80">
                        Hesap kilitlendi mi?
                      </a>
                      {typeof error.retry_after_seconds === 'number' && (
                        <span className="text-destructive/80">
                          ~{Math.max(1, Math.ceil(error.retry_after_seconds / 60))} dk
                        </span>
                      )}
                    </>
                  )}
                </div>
              </div>
            )}

            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="email">{t('email')}</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={18} />
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full h-10 pl-10 pr-4 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-colors"
                  placeholder="admin@platform.com"
                  required
                  data-testid="login-email"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="password">{t('password')}</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={18} />
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full h-10 pl-10 pr-10 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-colors"
                  placeholder="••••••••"
                  required
                  data-testid="login-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full h-10 rounded-md bg-primary text-primary-foreground font-medium text-sm hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              data-testid="login-submit"
            >
              {loading ? (
                <span className="inline-flex items-center gap-2">
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Loading...
                </span>
              ) : t('login')}
            </button>
          </form>

          {/* Demo Credentials (non-prod only) */}
          {process.env.NODE_ENV !== 'production' && (
            <div className="mt-6 pt-6 border-t">
              <p className="text-xs text-muted-foreground text-center mb-3">Demo Credentials</p>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="p-2 rounded bg-muted/50">
                  <p className="font-medium">Super Admin</p>
                  <p className="text-muted-foreground">admin@platform.com</p>
                  <p className="text-muted-foreground">Admin123!</p>
                </div>
                <div className="p-2 rounded bg-muted/50">
                  <p className="font-medium">Moderator</p>
                  <p className="text-muted-foreground">moderator@platform.de</p>
                  <p className="text-muted-foreground">Demo123!</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
